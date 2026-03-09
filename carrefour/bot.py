# carrefour/bot.py
import os
import time
import re
from pathlib import Path
from typing import Optional

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# 你現有的 selenium helper（driver / wait / click / input）
from crawler import get_driver_selenium, wait_until, input_value, click_element

from .config_loader import load_carrefour_config, CarrefourConfig
from .selectors import (
    SEL_VENDOR,
    SEL_ACCOUNT,
    SEL_PASSWORD,
    SEL_LOGIN_BTN,
    SEL_MENU_PRODUCT,
    SEL_LINK_PRODUCT_APPLICATION,
    SEL_INPUT_FILE,
    SEL_MODAL_CLOSE,
    SEL_HOME_LINK,
    SEL_LINK_BATCH_IMG_UPLOAD,
    SEL_BTN_OPEN_UPLOAD,
    SEL_IMAGE_TYPE_SELECT,
    sel_image_type_option,
    SEL_INPUT_FILE_ID,
    SEL_BTN_CONFIRM,
    SEL_BTN_QUERY,
    sel_btn_img_maintenance_draft_only,
    SEL_MODAL_SEARCH_INPUT,
    SEL_MODAL_BIND_BTN_TEMPLATE,
)


class CarrefourBot:
    def __init__(self, config_path: Optional[str] = None, driver=None):
        """
        config_path: 可選，指定某份 config json 路徑
        driver: 可選，如果你想自己在外面建立 driver 再塞進來
        """
        self.cfg: CarrefourConfig = load_carrefour_config(config_path)
        self.driver = driver or self._build_driver()

    # ---- context manager: with CarrefourBot() as bot: ----
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if self.driver:
            self.driver.quit()

    # ---- driver ----
    def _build_driver(self):
        return get_driver_selenium(
            argument_list=[
                "--disable-popup-blocking",
                "--disable-notifications",
                # 螢幕縮放參數
                "--force-device-scale-factor=0.9",
            ]
        )

    # ---- file selection (latest xlsx) ----
    @staticmethod
    def get_latest_xlsx(output_dir: str, filename_prefix: str = "") -> str:
        """
        Pick latest xlsx in output_dir, optionally filtered by filename prefix.
        Uses mtime (last modified time).
        """
        out = Path(output_dir).expanduser().resolve()
        if not out.is_dir():
            raise FileNotFoundError(f"找不到資料夾：{out}")

        files = [p for p in out.iterdir() if p.is_file() and p.suffix.lower() == ".xlsx" and (not filename_prefix or p.name.startswith(filename_prefix))]

        if not files:
            raise FileNotFoundError(f"{out} 底下找不到任何符合條件的 xlsx（prefix={filename_prefix!r}）")

        latest = max(files, key=lambda x: x.stat().st_mtime)
        return str(latest)

    # ---- 點擊回到首頁 ----
    def go_home(self):
        click_element(self.driver, *SEL_HOME_LINK)
        # 驗證回到首頁：左側選單應存在
        wait_until(self.driver, *SEL_MENU_PRODUCT, EC.presence_of_element_located, seconds=20, max_attempts=2)

    # ---- login ----
    def is_logged_in(self) -> bool:
        """透過檢查左側關鍵選單元素來判斷是否已登入"""
        try:
            return self.driver.find_element(*SEL_MENU_PRODUCT).is_displayed()
        except:
            return False

    def login(self):
        """登入流程"""
        if self.is_logged_in():
            print("[login] already logged in.")
            return

        self.driver.get(self.cfg.login_url)

        wait_until(self.driver, *SEL_VENDOR, EC.visibility_of_element_located, seconds=60, max_attempts=3)
        
        vendor_code = os.getenv("CRF_VENDOR_CODE", self.cfg.vendor_code)
        account = os.getenv("CRF_ACCOUNT", self.cfg.account)
        password = os.getenv("CRF_PASSWORD", self.cfg.password)

        input_value(self.driver, *SEL_VENDOR, vendor_code)
        input_value(self.driver, *SEL_ACCOUNT, account)
        input_value(self.driver, *SEL_PASSWORD, password)

        print("[login] filled credentials. Please complete reCAPTCHA manually.")

        wait_until(self.driver, *SEL_LOGIN_BTN, EC.element_to_be_clickable, seconds=180, max_attempts=1)
        click_element(self.driver, *SEL_LOGIN_BTN)

        wait_until(self.driver, *SEL_MENU_PRODUCT, EC.presence_of_element_located, seconds=60, max_attempts=1)
        print("✅ 登入成功")

    def ensure_ready(self):
        if not self.is_logged_in():
            self.login()

    # ---- navigation utils ----
    def _expand_menu_if_needed(self, menu_selector, child_selector):
        """檢查子選單是否展開，若未展開則點擊母選單"""
        try:
            child = self.driver.find_element(*child_selector)
            if not child.is_displayed():
                click_element(self.driver, *menu_selector)
        except:
            click_element(self.driver, *menu_selector)

    def goto_product_application(self):
        """左側 商品 → 提品申請"""
        self.ensure_ready()
        if "/product/application" in (self.driver.current_url or ""):
            return

        self._expand_menu_if_needed(SEL_MENU_PRODUCT, SEL_LINK_PRODUCT_APPLICATION)
        click_element(self.driver, *SEL_LINK_PRODUCT_APPLICATION)
        wait_until(self.driver, condition=lambda d: "/product/application" in (d.current_url or ""), seconds=60)

    def goto_batch_img_upload(self):
        """商品 → 批次提品圖片上傳"""
        self.ensure_ready()
        if "/product/batch-img-upload" in (self.driver.current_url or ""):
            return

        self._expand_menu_if_needed(SEL_MENU_PRODUCT, SEL_LINK_BATCH_IMG_UPLOAD)
        click_element(self.driver, *SEL_LINK_BATCH_IMG_UPLOAD)
        wait_until(self.driver, condition=lambda d: "/product/batch-img-upload" in (d.current_url or ""), seconds=60)
        
        # 進入後點擊「上傳圖片」按鈕開啟抽屜/視窗
        click_element(self.driver, *SEL_BTN_OPEN_UPLOAD)
        wait_until(self.driver, *SEL_IMAGE_TYPE_SELECT, EC.visibility_of_element_located, seconds=20)

    # ---- actions ----
    def upload_excel_template(self, xlsx_path: str):
        """上傳 Excel 模板至後台的「提品匯入」"""
        p = Path(xlsx_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"找不到要上傳的檔案：{p}")

        self.goto_product_application()
            
        file_input = wait_until(self.driver, *SEL_INPUT_FILE, EC.presence_of_element_located, seconds=60)
        file_input.send_keys(str(p))
        print(f"✅ 已送出上傳檔案：{p}")
        
        try:
            time.sleep(3)
            click_element(self.driver, *SEL_MODAL_CLOSE)
            print(f"✅ 已關閉匯入彈窗")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 關閉彈窗時發生異常: {e}")
    
    def select_image_type(self, image_type_text: str):
        """選擇圖片類型 (商品圖/商品特色圖)"""
        click_element(self.driver, *SEL_IMAGE_TYPE_SELECT)
        opt = sel_image_type_option(image_type_text)
        click_element(self.driver, *opt)

        def _selected_ok(d):
            try:
                el = d.find_element(By.CSS_SELECTOR, "span.ant-select-selection-item")
                val = (el.get_attribute("title") or el.text).strip()
                return image_type_text == val
            except:
                return False
        wait_until(self.driver, condition=_selected_ok, seconds=10)

    def upload_images_batch(self, image_type_text: str, image_paths: list[str]):
        """上傳圖片批次"""
        self.goto_batch_img_upload()
        self.select_image_type(image_type_text)

        file_input = wait_until(self.driver, *SEL_INPUT_FILE_ID, EC.presence_of_element_located, seconds=30)
        normalized = [str(Path(p).expanduser().resolve()) for p in image_paths]
        file_input.send_keys("\n".join(normalized))

        # 直接點確認送出，避開選檔彈窗
        click_element(self.driver, *SEL_BTN_CONFIRM)
        print(f"✅ 圖片類型[{image_type_text}] 已送出上傳：{len(normalized)} 張")
        self.go_home()

    def upload_images_batch_chunked(self, image_type_text: str, image_paths: list[str], chunk_size: int = 30):
        """分段批次上傳"""
        total = len(image_paths)
        if total == 0: return
        for start in range(0, total, chunk_size):
            batch = image_paths[start:start + chunk_size]
            print(f"[chunk] {image_type_text} 上傳第 {start+1}-{min(start+chunk_size, total)} / {total}")
            self.upload_images_batch(image_type_text, batch)
            time.sleep(2)

    def goto_image_maintenance_if_draft(self, ean: str) -> bool:
        """進入圖檔維護介面"""
        self.goto_product_application()
        click_element(self.driver, *SEL_BTN_QUERY)
        time.sleep(5)

        selector = sel_btn_img_maintenance_draft_only(ean)
        try:
            print(f"正在尋找條碼 [{ean}] 的圖檔維護按鈕...")
            click_element(self.driver, *selector, max_attempts=3)
            print(f"✅ 條碼 {ean} 已順利點擊圖檔維護按鈕")
            return True
        except Exception as e:
            print(f"❌ 條碼 {ean} 定位失敗: {str(e)[:100]}")
            return False
        
    def bind_image_in_modal(self, ean: str):
        """彈窗內的圖片綁定"""
        try:
            input_value(self.driver, *SEL_MODAL_SEARCH_INPUT, ean)
            click_element(self.driver, *SEL_BTN_QUERY)
            time.sleep(3) 

            target_selector = (SEL_MODAL_BIND_BTN_TEMPLATE[0], SEL_MODAL_BIND_BTN_TEMPLATE[1].format(ean))
            bind_btns = self.driver.find_elements(*target_selector)
            
            if not bind_btns:
                print(f"⚠️ 找不到與 {ean} 相關的綁定按鈕。")
                return False

            for btn in bind_btns:
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ 圖片綁定中斷: {e}")
            return False
        
    def get_all_draft_eans_from_page(self):
        """掃描頁面所有暫存條碼"""
        self.goto_product_application()
        click_element(self.driver, *SEL_BTN_QUERY)
        time.sleep(5)
        
        print("🔍 正在掃描頁面中的暫存商品...")
        draft_rows = self.driver.find_elements(By.XPATH, "//tr[contains(., '暫存')]")
        
        found_eans = []
        for row in draft_rows:
            match = re.search(r'\d{13}', row.text)
            if match:
                found_eans.append(match.group())
        
        found_eans = list(dict.fromkeys(found_eans))
        print(f"📊 找到 {len(found_eans)} 筆暫存商品: {found_eans}")
        return found_eans