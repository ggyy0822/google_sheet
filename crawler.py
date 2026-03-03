import os
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def get_driver_selenium(exp_option:dict={}, argument_list:list=[])->webdriver.Chrome:
        #parent_path = os.path.dirname(os.getcwd())
        try:
            # 下載driver，避免拿到不是執行檔的路徑
            chrome_path = ChromeDriverManager().install()
            if not chrome_path.endswith(".exe"):
                for root, dir, file_list in os.walk(os.path.dirname(chrome_path)):
                    for file in file_list:
                        if file.endswith(".exe"):
                            chrome_path = os.path.join(root, file)
                            break

        except Exception as e:
            print("建立driver發生錯誤，", e)
            exit()

        service = Service(
            executable_path=chrome_path,#exe_path.replace("//", "\\"),
            # port=9222,
            #service_args=[]
        )
        chrome_options = webdriver.ChromeOptions()
        if not exp_option:
            # 預設output folder
            os.makedirs("output", exist_ok=True)
            chrome_options.add_experimental_option(
                "prefs", {"download.default_directory":os.path.abspath("output")})#f"{os.path.join(os.path.dirname(parent_path), 'Excel')}
        else:
            for key, value in exp_option.items():
                chrome_options.add_experimental_option(key, value) #"prefs", self.exp_option
        
        for arg in argument_list:#user-data-dir=C:/Users/User/Desktop/Code_inuse/program/_調量相關_測試版本/temp_selenium
            chrome_options.add_argument(arg)
        #chrome_options.add_argument()
        driver = webdriver.Chrome(options=chrome_options) # 建立瀏覽器實體
        driver.maximize_window()
        return driver

def get_driver_undetected(
    # --- Browser-level settings ---
    browser_executable_path: str = None,
    user_data_dir: str = None,
    download_directory: str = None,
    headless: bool = False,
    arguments: list = None,
    page_load_strategy: str = 'normal',

    # --- Driver-level settings ---
    version_main: int = None,
    
    # --- undetected-chromedriver specific settings ---
    use_subprocess: bool = True,
    log_level: int = 0,
):
    import undetected_chromedriver as uc
    """
    建立並配置一個 undetected_chromedriver 實例。

    這個函式提供了一個高階介面，用於設定 undetected_chromedriver 
    最常用和最有用的參數。靈感來自官方 PyPI 文件。

    Args:
        browser_executable_path (str, optional): 
            瀏覽器主程式的路徑 (例如, "C:/Program Files/Google/Chrome/Application/chrome.exe")。
            如果為 None，uc 會嘗試自動尋找。預設為 None。
        
        user_data_dir (str, optional): 
            使用者設定檔的路徑。使用一個固定的資料夾可以幫助您在網站上保持登入狀態。
            如果為 None，則每次都會使用一個暫存資料夾。預設為 None。
        
        download_directory (str, optional): 
            檔案下載的預設資料夾。如果為 None，則使用瀏覽器的預設設定。預設為 None。
        
        headless (bool, optional): 
            是否以無頭模式(背景執行)運行瀏覽器。預設為 False。
        
        arguments (list, optional): 
            要傳遞給瀏覽器的額外命令列參數列表。
            例如: ["--incognito", "--disable-popup-blocking"]。預設為 None。

        page_load_strategy (str, optional): 
            定義頁面加載策略，可以是 'normal', 'eager', 或 'none'。
            預設為 'normal'。

        driver_executable_path (str, optional): 
            chromedriver.exe 驅動程式的路徑。如果為 None，webdriver-manager 
            將會自動下載。預設為 None。
        
        version_main (int, optional): 
            要使用的 Chrome 主要版本號。如果為 None，uc 將使用系統上
            找到的瀏覽器版本。預設為 None。
        
        use_subprocess (bool, optional): 
            在一個獨立的子程序中運行修補程式，這可以更穩定。
            建議保持為 True。預設為 True。
        
        log_level (int, optional): 
            設定 undetected_chromedriver 的日誌詳細程度。
            0 為靜默，數字越大越詳細。預設為 0。

    Returns:
        uc.Chrome: 一個已配置好的 WebDriver 實例。

    範例使用:
        # 基本用法
        if __name__ == '__main__':
            driver = create_driver()
            driver.get("https://nowsecure.nl")
            print("Page title is:", driver.title)
            driver.quit()

        # 進階用法: 使用現有瀏覽器、使用者設定檔及指定下載路徑
        if __name__ == '__main__':
            chrome_exe_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            user_profile_path = "C:\\Users\\YourUser\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1"
            download_path = "C:\\MyDownloads"
            
            if os.path.exists(chrome_exe_path):
                driver = create_driver(
                    browser_executable_path=chrome_exe_path,
                    user_data_dir=user_profile_path,
                    download_directory=download_path,
                    arguments=["--window-size=1920,1080"]
                )
                driver.get("https://www.google.com")
                print("Page title is:", driver.title)
                driver.quit()
    """
    options = uc.ChromeOptions()

    # --- 處理 Arguments ---
    # 使用者傳入的 arguments 優先
    final_arguments = arguments if arguments is not None else []
    # 添加一些有用的預設參數，如果使用者沒有提供的話
    if not any('--start-maximized' in s for s in final_arguments) and not headless:
        final_arguments.append('--start-maximized')
    if not any('--disable-popup-blocking' in s for s in final_arguments):
        final_arguments.append('--disable-popup-blocking')

    for arg in final_arguments:
        options.add_argument(arg)

    # --- 處理 Headless 模式 ---
    if headless:
        options.add_argument('--headless=new')
        # 在無頭模式下，通常需要指定視窗大小
        if not any('--window-size' in s for s in final_arguments):
             options.add_argument('--window-size=1920,1080')

    # --- 處理瀏覽器主程式路徑 ---
    # if browser_executable_path:
    #     if not os.path.exists(browser_executable_path):
    #         raise FileNotFoundError(f"指定的瀏覽器路徑不存在: {browser_executable_path}")
        #options.binary_location = browser_executable_path
    
    # --- 處理頁面加載策略 ---
    options.page_load_strategy = page_load_strategy

    # --- 處理下載路徑 ---
    if download_directory:
        if not os.path.exists(download_directory):
            print(f"下載路徑不存在，將自動建立: {download_directory}")
            os.makedirs(download_directory)
        # 設定下載偏好
        prefs = {"download.default_directory": os.path.abspath(download_directory)}
        options.add_experimental_option("prefs", prefs)

    from webdriver_manager.chrome import ChromeDriverManager
    driver_path = ChromeDriverManager().install()
    if not driver_path.endswith(".exe"):
        for  file in os.listdir(os.path.dirname(driver_path)):
            if file.endswith(".exe"):
                driver_path = os.path.join(os.path.dirname(driver_path), file)
                break

    # --- 建立 Driver 實例 ---
    # 將部分與 uc 直接相關的參數傳遞給建構子
    driver = uc.Chrome(
        options=options,
        browser_executable_path=browser_executable_path,
        #port=9222,
        driver_executable_path=driver_path,
        user_data_dir=user_data_dir,
        version_main=version_main,
        headless=headless,  # uc 內部也需要此參數以進行正確的修補
        use_subprocess=use_subprocess,
        log_level=log_level,
    )
    
    if not headless and not any('--start-maximized' in s for s in final_arguments):
        # 再次確保視窗最大化，如果沒有在參數中指定
        driver.maximize_window()
        
    return driver


def wait_for_dom_ready(driver):
    """等待DOM加載完成"""
    if isinstance(driver, WebDriver):
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True

def wait_until(
    driver,
    by=None,
    value=None,
    condition=EC.presence_of_element_located,
    max_attempts=3,
    seconds=60,
    before_wait=None,
):
    """
    通用等待函數（支援 element-based 與 callable EC）
    Args:
        driver: WebDriver 實例
        by: 定位方式
        value: 定位值
        condition: 等待條件(EC.visibility_of_element_located/EC.presence_of_element_located/EC.element_to_be_clickable...)
        max_attempts: 最大嘗試次數
        seconds: 等待時長
        before_wait: retry hook 不是等條件，而是「讓等條件有機會成立的補救動作」ex:driver.refresh
    使用方式：
    - wait_until(driver, by=By.ID, value="xxx", condition=EC.visibility_of_element_located)
    - wait_until(driver, condition=EC.url_changes(old_url))
    """

    for attempt in range(max_attempts):
        try:

            wait_for_dom_ready(driver)
            
            if before_wait:
                before_wait()
                #before_wait(driver)

            wait = WebDriverWait(driver, seconds)

            # --- 情況 1：element-based EC ---
            if by is not None and value is not None:
                if condition is None:
                    condition = EC.presence_of_element_located
                result = wait.until(condition((by, value)))
                print(f"成功找到元素: {value}")
                return result

            # --- 情況 2：callable EC（url/title/frame/...） ---
            if callable(condition):
                result = wait.until(condition)
                print(f"成功完成等待條件: {condition}")
                return result

            raise ValueError("wait_until 參數錯誤：必須提供 locator 或 callable condition")

        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"[Retry {attempt + 1}/{max_attempts}] wait failed")
                print(f"URL: {driver.current_url}")
                print(f"Title: {driver.title}")
                print(f"Error: {e}")
                time.sleep(2)
            else:
                print("等待失敗（最終）")
                print(f"Final URL: {driver.current_url}")
                print(f"Final Title: {driver.title}")
                raise

# --- 元素點擊 ---
def click_element(driver, by, value, max_attempts = 3):
    
    for attempt in range(max_attempts):
        try:
            element = wait_until(driver, by, value, EC.element_to_be_clickable)
            #element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))
            element.click()
            time.sleep(1)
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"[ERROR] 點擊失敗，重試 ({attempt+1}/{max_attempts})")
                time.sleep(1)
            else:
                raise e

def input_value(driver, by, value, text, clear_first = True):
    # 輸入值
    element = wait_until(driver, by, value, EC.element_to_be_clickable)
    #element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))
    if clear_first:
        try:
            element.send_keys(Keys.CONTROL, 'a')
            element.send_keys(Keys.DELETE)
        except:
            element.clear()
    element.send_keys(text)
    time.sleep(0.5)

def select_value(driver, by, value, select_by: str = "value", select_value=None, seconds: int = 30, max_attempts: int = 3):
    """
    統一的 <select> 選單操作

    Args:
        driver: WebDriver
        by, value: select 元素定位
        select_by: value | text | index
        select_value: 要選的值
    """
    last_err = None

    for attempt in range(max_attempts):
        try:
            # 等 select 出現
            el = wait_until(driver, by, value, EC.element_to_be_clickable, seconds=seconds)

            sel = Select(el)

            if select_by == "value":
                sel.select_by_value(str(select_value))
            elif select_by == "text":
                sel.select_by_visible_text(str(select_value))
            elif select_by == "index":
                sel.select_by_index(int(select_value))
            else:
                raise ValueError(f"Unknown select_by: {select_by}")
            time.sleep(0.5)

            return True

        except Exception as e:
            last_err = e
            if attempt < max_attempts - 1:
                time.sleep(1)
            else:
                raise RuntimeError(
                    f"select_value failed: by={by}, value={value}, select={select_value}"
                ) from last_err

def hover_element(driver, by, value, duration=1):
    """懸停"""
    element = wait_until(driver, by, value, EC.visibility_of_element_located)
    #element = wait_for_element(driver, by, value)
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    time.sleep(duration)
    return True
# get_driver_selenium()
pass