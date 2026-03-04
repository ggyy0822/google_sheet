# carrefour/config_loader.py
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class UploadConfig:
    output_dir: str
    filename_prefix: str


@dataclass(frozen=True)
class CarrefourConfig:
    login_url: str
    home_url: str
    vendor_code: str
    account: str
    password: str
    upload: UploadConfig


def _project_root() -> Path:
    """
    carrefour/ 在專案根目錄底下，因此 parent.parent 會回到專案根目錄
    project/
      carrefour/
        config_loader.py  <- this file
    """
    return Path(__file__).resolve().parent.parent


def load_carrefour_config(config_path: Optional[str] = None) -> CarrefourConfig:
    """
    Load config from json.
    Priority:
      1) explicit argument config_path
      2) env CARREFOUR_CONFIG
      3) project_root/config/carrefour_config.json
    """
    root = _project_root()
    path = config_path or os.getenv("CARREFOUR_CONFIG") or str(root / "config" / "carrefour_config.json")
    cfg_path = Path(path).expanduser().resolve()

    if not cfg_path.exists():
        raise FileNotFoundError(f"找不到設定檔：{cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    upload_raw = raw.get("upload", {})
    upload = UploadConfig(
        output_dir=str(upload_raw.get("output_dir", "output")),
        filename_prefix=str(upload_raw.get("filename_prefix", "")),
    )

    # 必要欄位檢查（避免 config 少 key）
    required = ["login_url", "home_url", "vendor_code", "account", "password"]
    missing = [k for k in required if k not in raw]
    if missing:
        raise KeyError(f"carrefour_config.json 缺少必要欄位：{missing}")

    return CarrefourConfig(
        login_url=str(raw["login_url"]),
        home_url=str(raw["home_url"]),
        vendor_code=str(raw["vendor_code"]),
        account=str(raw["account"]),
        password=str(raw["password"]),
        upload=upload,
    )