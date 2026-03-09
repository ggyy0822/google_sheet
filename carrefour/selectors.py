# carrefour/selectors.py
from selenium.webdriver.common.by import By

# --- 家樂福圖示 ---
SEL_HOME_LINK = (By.CSS_SELECTOR, 'a[href="/"]')
# --- Login page ---
SEL_VENDOR = (By.ID, "vendorCode")
SEL_ACCOUNT = (By.ID, "account")
SEL_PASSWORD = (By.ID, "password")
SEL_LOGIN_BTN = (By.XPATH, "//button[.//span[normalize-space()='登入'] or normalize-space()='登入']")

# --- Left menu / navigation ---
SEL_MENU_PRODUCT = (By.XPATH, "//span[contains(@class,'ant-menu-title-content') and normalize-space()='商品']")
SEL_LINK_PRODUCT_APPLICATION = (By.CSS_SELECTOR, 'a[href="/product/application"]')

# --- Upload excel ---
SEL_BTN_IMPORT = (By.XPATH, "//button[.//span[normalize-space()='提品匯入']]")
SEL_INPUT_FILE = (By.CSS_SELECTOR, "input[type='file']")

# ============================
# 批次提品圖片上傳 /product/batch-img-upload
# ============================

# 開啟圖片上傳區
SEL_BTN_OPEN_UPLOAD = (
    By.XPATH,
    "//button[.//span[normalize-space()='上傳圖片'] or normalize-space()='上傳圖片']"
)

# 左側「商品」底下的頁面連結（你已在截圖確認）
SEL_LINK_BATCH_IMG_UPLOAD = (By.CSS_SELECTOR, 'a[href="/product/batch-img-upload"]')

# 圖片類型下拉（placeholder 是「請選擇圖片類型」）
SEL_IMAGE_TYPE_SELECT = (
    By.XPATH,
    "//span[contains(@class,'ant-select-selection-placeholder') and contains(normalize-space(),'請選擇圖片類型')]"
    "/ancestor::div[contains(@class,'ant-select')]"
    "//div[contains(@class,'ant-select-selector')]"
)

# 下拉選項（點開後出現在 ant-select-dropdown）
def sel_image_type_option(text: str):
    return (
        By.XPATH,
        f"//div[contains(@class,'ant-select-dropdown')]"
        f"//div[contains(@class,'ant-select-item-option-content') and normalize-space()='{text}']"
    )

# 檔案 input：你截圖顯示 id="file" multiple display:none，最穩
SEL_INPUT_FILE_ID = (By.CSS_SELECTOR, "input#file[type='file']")

# 彈窗/區塊內的「上傳」按鈕（secondary）
SEL_BTN_UPLOAD = (By.XPATH, "//button[normalize-space()='上傳' or .//span[normalize-space()='上傳']]")

# 「確認」按鈕（type=submit）
SEL_BTN_CONFIRM = (By.XPATH, "//button[@type='submit' and (normalize-space()='確認' or .//span[normalize-space()='確認'])]")

# 查詢按鈕
SEL_BTN_QUERY = (By.XPATH,"//button[.//span[normalize-space()='查詢'] or normalize-space()='查詢']")

def sel_btn_img_maintenance_draft_only(ean: str):
    """
    定位條件：
    1. 該 tr 包含指定條碼 (ean)
    2. 該 tr 的儲存格包含 '暫存'
    3. 找到內部的商品維護超連結 (a 標籤)
    """
    return (
        By.XPATH, 
        f"//tr[contains(., '{ean}') and .//td[contains(., '暫存')]]//a[contains(., '商品相關圖檔維護')]"
    )

# 1. 搜尋輸入框：使用最穩定的 ID 定位 (取代 placeholder)
SEL_MODAL_SEARCH_INPUT = (By.ID, "fileName")

# 綁定按鈕
SEL_MODAL_BIND_BTN_TEMPLATE = (By.XPATH, "//tr[contains(., '{}')]//button[contains(@class, 'sc-9a1a20db-0')]")