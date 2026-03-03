import os
import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from crawler import get_driver_selenium, wait_until, input_value, click_element


# ----------------------------
# Selectors (UI constants)
# ----------------------------
SEL_VENDOR = (By.ID, "vendorCode")
SEL_ACCOUNT = (By.ID, "account")
SEL_PASSWORD = (By.ID, "password")

SEL_LOGIN_BTN = (By.XPATH, "//button[.//span[normalize-space()='登入'] or normalize-space()='登入']")

SEL_MENU_PRODUCT = (By.XPATH, "//span[contains(@class,'ant-menu-title-content') and normalize-space()='商品']")
SEL_LINK_PRODUCT_APPLICATION = (By.CSS_SELECTOR, 'a[href="/product/application"]')

SEL_BTN_IMPORT = (By.XPATH, "//button[.//span[normalize-space()='提品匯入']]")
SEL_INPUT_FILE = (By.CSS_SELECTOR, "input[type='file']")


# ----------------------------
# Config models
# ----------------------------
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
    """Assume this file lives in project root. If you later move it, adjust parents[...]"""
    return Path(__file__).resolve().parent

# 讀 config/carrefour_config.json 
# 回傳 dict（帳密、URL）
def load_carrefour_config(config_path: Optional[str] = None) -> CarrefourConfig:
    """
    Load config from json.
    Priority:
      1) explicit argument
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

    return CarrefourConfig(
        login_url=str(raw["login_url"]),
        home_url=str(raw["home_url"]),
        vendor_code=str(raw["vendor_code"]),
        account=str(raw["account"]),
        password=str(raw["password"]),
        upload=upload,
    )


# ----------------------------
# File selection
# ----------------------------
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


# ----------------------------
# Login / navigation
# ----------------------------
def is_logged_in(driver) -> bool:
    return "/login" not in (driver.current_url or "")

# 如沒登入 → 開 login 頁
# 填 vendor / account / password
# 勾 reCAPTCHA 點登入等跳離 /login
def ensure_login(driver, vendor_code: str, account: str, password: str, login_url: str, home_url: str) -> None:
    driver.get(home_url)
    time.sleep(0.3)

    if is_logged_in(driver):
        print("[login] already logged in (not on /login).")
        return

    driver.get(login_url)

    wait_until(driver, *SEL_VENDOR, EC.visibility_of_element_located, seconds=60, max_attempts=3)
    wait_until(driver, *SEL_ACCOUNT, EC.visibility_of_element_located, seconds=60, max_attempts=3)
    wait_until(driver, *SEL_PASSWORD, EC.visibility_of_element_located, seconds=60, max_attempts=3)

    input_value(driver, *SEL_VENDOR, vendor_code)
    input_value(driver, *SEL_ACCOUNT, account)
    input_value(driver, *SEL_PASSWORD, password)

    print("[login] filled credentials.")
    print("[login] Please complete reCAPTCHA (checkbox) manually in the browser.")

    wait_until(driver, *SEL_LOGIN_BTN, EC.element_to_be_clickable, seconds=180, max_attempts=1)
    click_element(driver, *SEL_LOGIN_BTN)

    wait_until(driver, condition=lambda d: "/login" not in (d.current_url or ""), seconds=30, max_attempts=1)
    print("[login] success! current url:", driver.current_url)

# 確保左側「商品」選單存在
def assert_login_success(driver) -> None:
    wait_until(driver, condition=lambda d: "/login" not in (d.current_url or ""), seconds=60, max_attempts=1)
    wait_until(driver, *SEL_MENU_PRODUCT, EC.presence_of_element_located, seconds=60, max_attempts=1)
    print("✅ 登入成功，已進入後台主畫面")

# 點左側「商品」點「提品申請」
# 等 URL 變成 /product/application
def goto_product_application(driver) -> None:
    click_element(driver, *SEL_MENU_PRODUCT)
    click_element(driver, *SEL_LINK_PRODUCT_APPLICATION)
    wait_until(driver, condition=lambda d: "/product/application" in (d.current_url or ""), seconds=60, max_attempts=1)

# 點「提品匯入」找到 input[type=file]
# send_keys 上傳檔案
def upload_template_xlsx(driver, xlsx_path: str) -> None:
    p = Path(xlsx_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"找不到要上傳的檔案：{p}")

    click_element(driver, *SEL_BTN_IMPORT)
    file_input = wait_until(driver, *SEL_INPUT_FILE, EC.presence_of_element_located, seconds=60, max_attempts=1)
    file_input.send_keys(str(p))

    print(f"✅ 已送出上傳檔案：{p}")


# ----------------------------
# Driver
# ----------------------------
def build_driver():
    return get_driver_selenium(
        argument_list=[
            "--disable-popup-blocking",
            "--disable-notifications",
        ]
    )


# ----------------------------
# Main
# ----------------------------
def main():
    cfg = load_carrefour_config()

    # env override (still supported)
    vendor_code = os.getenv("CRF_VENDOR_CODE", cfg.vendor_code)
    account = os.getenv("CRF_ACCOUNT", cfg.account)
    password = os.getenv("CRF_PASSWORD", cfg.password)

    # file selection priority:
    # 1) CRF_UPLOAD_XLSX
    # 2) latest xlsx in cfg.upload.output_dir filtered by cfg.upload.filename_prefix
    xlsx_path = os.getenv("CRF_UPLOAD_XLSX")
    if not xlsx_path or not xlsx_path.strip():
        xlsx_path = get_latest_xlsx(cfg.upload.output_dir, cfg.upload.filename_prefix)

    print("[upload] will upload file:", xlsx_path)

    driver = build_driver()
    try:
        ensure_login(
            driver,
            vendor_code=vendor_code,
            account=account,
            password=password,
            login_url=cfg.login_url,
            home_url=cfg.home_url,
        )
        assert_login_success(driver)

        goto_product_application(driver)
        upload_template_xlsx(driver, xlsx_path)

        input("Done. Press Enter to quit...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()