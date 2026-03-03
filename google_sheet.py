"""
Google_sheet_main.py
注意：
- Google Sheet 的 headers 固定在第 2 行（A2:）
- 資料從第 4 行開始
"""

import os
import json
import pandas as pd
import glob
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


@dataclass
class SheetCol:
    col_letter: str # 英文欄位
    col_idx: int  # 1-based 數字欄位

class GoogleSheetManager:
    def __init__(
        self,
        sheet_config_file="config/google_sheet_config.json"
    ):
        sheet_settings = self._read_config(sheet_config_file)
        # auth
        self.SCOPES = sheet_settings["scopes"]
        self.token_path = sheet_settings["token_filename"]
        self.client_secret_path = self._resolve_client_secret_path(sheet_settings["client_secret_filename"])#client_secret_filename
        # sheet info
        self.spreadsheet_id = sheet_settings["spreadsheet_id"]
        self.gid = sheet_settings["gid"]
        self.sheet_name = sheet_settings["sheet_name"] # 工作表名稱
        self.dic_path = sheet_settings["dic_filename"] # 欄位字典存檔
        self.header_range = sheet_settings["header_range"] # 程式內部命名位置
        self.data_start_row = sheet_settings["data_start_row"] # 資料起始行
        self.verbose = sheet_settings["verbose"] # 要不要印 log
        self.GOOGLE_SHEET_DIC: Dict[str, SheetCol] = {} # sheet content
        self._schema_hash: Optional[str] = None
        # get auth
        self.SPREADSHEETS = self._authenticate()

        # 初始化就先載入 dic（必要時會 refresh）
        self.load_google_sheet_dic()

    # ----------------------------
    # Auth
    # ----------------------------
    def _resolve_client_secret_path(self, client_secret_filename: Optional[str]) -> str:

        # 自動找 config 下的 client_secret*.json
        candidates = sorted(glob.glob(client_secret_filename))
        if not candidates:
            raise FileNotFoundError(
                f"找不到 {client_secret_filename}，請確認檔案存在"
            )
        return candidates[0]

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path, self.SCOPES)
                creds = flow.run_local_server(port = 0)
            
            with open(self.token_path, "w", encoding = "utf-8") as f:
                f.write(creds.to_json())

        service = build("sheets", "v4", credentials = creds)
        return service.spreadsheets()

    # ----------------------------
    # Utilities
    # ----------------------------
    @staticmethod
    def _col_idx_to_letter(n: int) -> str:
        """把 1-based 欄位數字轉成 A, B, ..., Z, AA, AB"""
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    @staticmethod
    def _schema_hash_from_headers(headers: List[str]) -> str:
        """偵測 header 是否被改過"""
        joined = "|".join(headers).encode("utf-8")
        return hashlib.md5(joined).hexdigest()

    def _log(self, msg: str):
        """只有 verbose = True 才 print"""
        if self.verbose:
            print(msg)

    def _read_config(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                return json.load(json_file)
        except FileNotFoundError as e:
            print("找不到對應的 Config 檔案", e)
            raise
        except Exception as e:
            print("讀取 Config 檔案未知錯誤", e)
            raise

    # ----------------------------
    # GOOGLE_SHEET_DIC (A2:AI2)
    # ----------------------------
    def refresh_google_sheet_dic(self) -> Dict[str, SheetCol]:
        """從 Google Sheet 第 2 行讀 headers，重建 dic，並寫入 google_sheet_dic.json"""
        rng = f"{self.sheet_name}!{self.header_range}"
        resp = self.SPREADSHEETS.values().get(
            spreadsheetId = self.spreadsheet_id,
            range = rng
        ).execute()

        values = resp.get("values", [])
        header_row = values[0] if values else []

        # 去除尾端空白欄位
        while header_row and (header_row[-1] is None or str(header_row[-1]).strip() == ""):
            header_row.pop()

        if not header_row:
            raise ValueError(f"[GOOGLE_SHEET_DIC] 讀不到 header（{rng} 為空）。請確認 Google Sheet 第 2 行有欄位名稱")

        dic: Dict[str, SheetCol] = {}
        for i, h in enumerate(header_row, start = 1):
            key = str(h).strip()
            if not key:
                continue
            dic[key] = SheetCol(col_letter = self._col_idx_to_letter(i), col_idx = i)

        schema_hash = self._schema_hash_from_headers([str(h).strip() for h in header_row])

        payload = {
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec = "seconds"),
            "sheet_name": self.sheet_name,
            "header_range": self.header_range,
            "data_start_row": self.data_start_row,
            "schema_hash": schema_hash,
            "dic": {k: {"col_letter": v.col_letter, "col_idx": v.col_idx} for k, v in dic.items()},
        }
        os.makedirs(os.path.dirname(self.dic_path), exist_ok = True)
        with open(self.dic_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        self._log(f"[GOOGLE_SHEET_DIC] 已刷新並寫入：{self.dic_path}")
        self.GOOGLE_SHEET_DIC = dic
        self._schema_hash = schema_hash
        return dic

    def load_google_sheet_dic(self, force_refresh: bool = False) -> Dict[str, SheetCol]:
        """優先讀 json；若 schema 不符則自動 refresh or 直接更新字典並使用"""
        if force_refresh or not os.path.exists(self.dic_path):
            return self.refresh_google_sheet_dic()

        try:
            with open(self.dic_path, "r", encoding = "utf-8") as f:
                payload = json.load(f)

            dic_raw = payload.get("dic", {})
            dic: Dict[str, SheetCol] = {
                k: SheetCol(col_letter = v["col_letter"], col_idx = int(v["col_idx"]))
                for k, v in dic_raw.items()
            }
            saved_hash = payload.get("schema_hash")
            self.GOOGLE_SHEET_DIC = dic
            self._schema_hash = saved_hash

            # 驗證 schema 是否仍一致（避免 header 被改動）
            try:
                current_headers = self._fetch_current_headers()
                current_hash = self._schema_hash_from_headers(current_headers)
                if saved_hash != current_hash:
                    self._log("[GOOGLE_SHEET_DIC] 偵測到 header 變更，將自動刷新 dic")
                    return self.refresh_google_sheet_dic()
            except Exception:
                # 若驗證失敗，不阻擋使用（也可以改成強制 refresh）
                pass

            self._log(f"[GOOGLE_SHEET_DIC] 已載入：{self.dic_path}")
            return dic

        except Exception as e:
            self._log(f"[GOOGLE_SHEET_DIC] 讀取失敗，改為刷新：{e}")
            return self.refresh_google_sheet_dic()

    def _fetch_current_headers(self) -> List[str]:
        rng = f"{self.sheet_name}!{self.header_range}"
        resp = self.SPREADSHEETS.values().get(
            spreadsheetId = self.spreadsheet_id,
            range = rng
        ).execute()
        values = resp.get("values", [])
        header_row = values[0] if values else []
        while header_row and (header_row[-1] is None or str(header_row[-1]).strip() == ""):
            header_row.pop()
        return [str(x).strip() for x in header_row]


    def load_gs_data(self, end_cell="AI5") -> pd.DataFrame:#Dict[str, Any]:
        """

        """
        ranges = [
            f"{self.sheet_name}!A{self.data_start_row}:{end_cell}",
        ]
        resp = self.SPREADSHEETS.values().batchGet(
            spreadsheetId=self.spreadsheet_id,
            ranges=ranges
        ).execute()

        value_ranges = resp.get("valueRanges", [])
        cols = []
        print(cols)
        rows = value_ranges[0].get("values", [])
        headers = list(self.GOOGLE_SHEET_DIC.keys())
        n_cols = len(headers)

        # 補齊尾端空白欄位
        fixed_rows = [
            (r + [""] * (n_cols - len(r)))[:n_cols]
            for r in rows
        ]

        sheet_df = pd.DataFrame(fixed_rows, columns=headers)
        # sheet_df = pd.DataFrame(value_ranges[0].get("values", []), columns=self.GOOGLE_SHEET_DIC.keys())
        # sheet_df["index"] = sheet_df.index
        os.makedirs("data", exist_ok=True)
        sheet_df.to_excel("data/key對照表.xlsx", index=False)
        print("實際抓取範圍：", f"{self.sheet_name}!A{self.data_start_row}:{end_cell}")
        return sheet_df
        # for vr in value_ranges:
        #     vals = vr.get("values", [])
        #     flat = [row[0] if row else "" for row in vals]
        #     cols.append(flat)
    
        # return 


if __name__ == "__main__":

    gs = GoogleSheetManager(
        sheet_config_file="config/google_sheet_config.json"
    )
    # 範例：載入既有資料索引
    data =  gs.load_gs_data()
    print(data)
    pass
