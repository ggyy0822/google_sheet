# carrefour/bot.py
import os
import time
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
    SEL_BTN_IMPORT,
    SEL_INPUT_FILE,
    SEL_HOME_LINK,
    SEL_LINK_BATCH_IMG_UPLOAD,
    SEL_BTN_OPEN_UPLOAD,
    SEL_IMAGE_TYPE_SELECT,
    sel_image_type_option,
    SEL_INPUT_FILE_ID,
    SEL_BTN_UPLOAD,
    SEL_BTN_CONFIRM,
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

        files = []
        for p in out.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() != ".xlsx":
                continue
            if filename_prefix and not p.name.startswith(filename_prefix):
                continue
            files.append(p)

        if not files:
            raise FileNotFoundError(f"{out} 底下找不到任何符合條件的 xlsx（prefix={filename_prefix!r}）")

        latest = max(files, key=lambda x: x.stat().st_mtime)
        return str(latest)
    # ---- 點擊回到首頁 ----
    def go_home(self):
        click_element(self.driver, *SEL_HOME_LINK)
        wait_until(
            self.driver,
            condition=lambda d: (d.current_url or "").rstrip("/").endswith("scm.carrefour.com.tw")
                                or (d.current_url or "").endswith("/"),
            seconds=20,
            max_attempts=2,
        )
    # ---- login ----
    def is_logged_in(self) -> bool:
        return "/login" not in (self.driver.current_url or "")

    def login(self):
        """
        登入流程：
        1) 先去 home_url，看是不是已登入（不在 /login）
        2) 若未登入 → 開 login_url，填 vendor/account/password
        3) 等你手動勾 reCAPTCHA 後，按登入
        4) 驗證左側「商品」選單出現
        """
        self.driver.get(self.cfg.home_url)
        time.sleep(0.3)

        if self.is_logged_in():
            print("[login] already logged in.")
            return

        self.driver.get(self.cfg.login_url)

        wait_until(self.driver, *SEL_VENDOR, EC.visibility_of_element_located, seconds=60, max_attempts=3)
        wait_until(self.driver, *SEL_ACCOUNT, EC.visibility_of_element_located, seconds=60, max_attempts=3)
        wait_until(self.driver, *SEL_PASSWORD, EC.visibility_of_element_located, seconds=60, max_attempts=3)

        # env override：允許你不把密碼寫進 json（更安全）
        vendor_code = os.getenv("CRF_VENDOR_CODE", self.cfg.vendor_code)
        account = os.getenv("CRF_ACCOUNT", self.cfg.account)
        password = os.getenv("CRF_PASSWORD", self.cfg.password)

        input_value(self.driver, *SEL_VENDOR, vendor_code)
        input_value(self.driver, *SEL_ACCOUNT, account)
        input_value(self.driver, *SEL_PASSWORD, password)

        print("[login] filled credentials.")
        print("[login] Please complete reCAPTCHA manually in the browser.")

        wait_until(self.driver, *SEL_LOGIN_BTN, EC.element_to_be_clickable, seconds=180, max_attempts=1)
        click_element(self.driver, *SEL_LOGIN_BTN)

        wait_until(self.driver, condition=lambda d: "/login" not in (d.current_url or ""), seconds=60, max_attempts=1)

        # 驗證登入成功：左側「商品」選單存在
        wait_until(self.driver, *SEL_MENU_PRODUCT, EC.presence_of_element_located, seconds=60, max_attempts=1)
        print("✅ 登入成功")

    def ensure_ready(self):
        if not self.is_logged_in():
            self.login()

    # ---- navigation ----
    def goto_product_application(self):
        """
        左側 商品 → 提品申請
        """
        click_element(self.driver, *SEL_MENU_PRODUCT)
        click_element(self.driver, *SEL_LINK_PRODUCT_APPLICATION)
        wait_until(self.driver, condition=lambda d: "/product/application" in (d.current_url or ""), seconds=60, max_attempts=1)

    # ---- actions ----
    def upload_excel_template(self, xlsx_path: str):
        """
        上傳 Excel 模板至後台的「提品匯入」
        """
        self.ensure_ready()

        p = Path(xlsx_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"找不到要上傳的檔案：{p}")

        self.goto_product_application()

        click_element(self.driver, *SEL_BTN_IMPORT)
        file_input = wait_until(self.driver, *SEL_INPUT_FILE, EC.presence_of_element_located, seconds=60, max_attempts=1)
        file_input.send_keys(str(p))

        print(f"✅ 已送出上傳檔案：{p}")
    
    def goto_batch_img_upload(self):
        """
        商品 → 批次提品圖片上傳
        """
        self.ensure_ready()

        # 展開左側「商品」選單（你原本就有）
        click_element(self.driver, *SEL_MENU_PRODUCT)

        # 點「批次提品圖片上傳」
        click_element(self.driver, *SEL_LINK_BATCH_IMG_UPLOAD)

        # 等頁面切到正確 URL
        wait_until(
            self.driver,
            condition=lambda d: "/product/batch-img-upload" in (d.current_url or ""),
            seconds=60,
            max_attempts=1,
        )
        # 4️⃣ ⭐ 點「上傳圖片」按鈕
        click_element(self.driver, *SEL_BTN_OPEN_UPLOAD)
        wait_until(
        self.driver,
        *SEL_IMAGE_TYPE_SELECT,
        EC.visibility_of_element_located,
        seconds=20,
        max_attempts=3,
        )


    def select_image_type(self, image_type_text: str):
        """
        image_type_text: '商品圖' 或 '商品特色圖'
        """
        # 點開下拉
        click_element(self.driver, *SEL_IMAGE_TYPE_SELECT)

        # 點選選項
        opt = sel_image_type_option(image_type_text)
        click_element(self.driver, *opt)

        # 驗證：已選取的值會出現在 selection-item 的 title
        def _selected_ok(d):
            try:
                el = d.find_element(By.CSS_SELECTOR, "span.ant-select-selection-item")
                title = (el.get_attribute("title") or "").strip()
                text = (el.text or "").strip()
                return (image_type_text == title) or (image_type_text == text)
            except Exception:
                return False

        wait_until(self.driver, condition=_selected_ok, seconds=10, max_attempts=1)

    def upload_images_batch(self, image_type_text: str, image_paths: list[str]):
        """
        一次上傳一種圖片類型的一批圖：
        1) 進入批次提品圖片上傳頁
        2) 選圖片類型（商品圖/商品特色圖）
        3) input#file send_keys 圖片路徑（可多張）
        4) 點「上傳」→ 點「確認」
        """
        self.goto_batch_img_upload()
        self.select_image_type(image_type_text)

        # input#file (display:none 也能 send_keys)
        file_input = wait_until(
            self.driver,
            *SEL_INPUT_FILE_ID,
            EC.presence_of_element_located,
            seconds=30,
            max_attempts=2,
        )

        normalized = []
        for p in image_paths:
            fp = str(Path(p).expanduser().resolve())
            if not Path(fp).exists():
                raise FileNotFoundError(f"找不到圖片檔：{fp}")
            normalized.append(fp)

        # 多檔案一次送出（Chrome 支援用 \n）
        file_input.send_keys("\n".join(normalized))

        # 點「上傳」
        click_element(self.driver, *SEL_BTN_UPLOAD)

        # 點「確認」（你截圖顯示有 submit 按鈕）
        click_element(self.driver, *SEL_BTN_CONFIRM)

        print(f"✅ 圖片類型[{image_type_text}] 已送出上傳：{len(normalized)} 張")
        self.go_home()

    def upload_images_batch_chunked(self, image_type_text: str, image_paths: list[str], chunk_size: int = 30):
        """
        分批上傳：預設每批 30 張
        - image_type_text: '商品圖' / '商品特色圖'
        - image_paths: 所有要上傳的圖片路徑
        - chunk_size: 每批張數（預設 30）
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size 必須 > 0")

        total = len(image_paths)
        if total == 0:
            print(f"⚠️ 圖片類型[{image_type_text}] 沒有圖片可上傳")
            return

        for start in range(0, total, chunk_size):
            end = min(start + chunk_size, total)
            batch = image_paths[start:end]

            print(f"[chunk] {image_type_text} 上傳第 {start+1}-{end} / {total} 張")

            # 直接沿用你原本已驗證成功的單批流程
            self.upload_images_batch(image_type_text, batch)