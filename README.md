# 家樂福提品自動化系統 (Carrefour Automation System)

本專案旨在自動化家樂福後台的商品提品、圖片上傳與綁定流程。系統採用模組化設計，將資料處理、瀏覽器操作、選擇器定義完整拆分，並透過主腳本實現「一條龍」自動化。

---

## 📁 專案目錄結構與檔案說明

### 🚀 主執行程序 (Main Orchestrators)
- **`run_sheet_to_carrefour.py`**: **【核心主入口】**。
    - 結合所有模組，按順序執行：讀取 Google Sheet -> 清空 `output` -> 批次上傳圖片 -> 逐列產生 Excel -> 上傳 Excel -> 自動綁定圖片。
- **`run_upload_images.py`**: 獨立圖片上傳模組。專門處理 `picture` 資料夾內的圖片批次上傳。
- **`run_upload_excel.py`**: 獨立 Excel 上傳模組。將 `output` 資料夾中最新的 Excel 檔案上傳至後台。
- **`run_bind_images.py`**: 獨立圖片綁定模組。掃描提品列表頁面中的「暫存」商品，並自動進入綁定視窗進行掛載。

### 🛠️ 核心運作模組 (Core Modules)
- **`carrefour/bot.py`**: 機器人行為引擎。封裝了所有與家樂福後台互動的動作，包括登入驗證、智慧選單導航、視窗縮放控制等。
- **`carrefour/selectors.py`**: 定位器中心。定義了後台所有按鈕、輸入框、選單的 CSS 與 XPath 選擇器，維護方便。
- **`export_to_template.py`**: 資料轉換專家。負責將 Google Sheet 的原始資料轉換為符合家樂福規範的 Excel 模板格式。
- **`crawler.py`**: 底層驅動封裝。提供 WebDriver 的初始化設定及通用的等待 (wait)、點擊 (click) 與輸入 (input) 封裝。
- **`google_sheet.py`**: 資料來源接口。負責與 Google Sheet API 溝通，抓取指定的報表資料。

---

## 🔧 核心函式 (Key Functions) 介紹

### `carrefour/bot.py` (CarrefourBot 類別)
- `login()`: 處理登入流程，自動填充帳密並處理 native 90% 縮放。
- `_expand_menu_if_needed(menu, child)`: 智慧偵測選單狀態，確保不會因重複點擊導致選單意外收合。
- `goto_product_application()`: 導航至「提品申請」頁面。
- `upload_excel_template(path)`: 自動選取檔案並執行「提品匯入」。
- `upload_images_batch(type, paths)`: 批次將圖片塞入隱藏的 input 欄位並點擊確認，繞過 OS 選檔視窗。
- `bind_image_in_modal(ean)`: 在綁定彈窗內精準搜尋條碼，並自動點擊綁定按鈕。

### `export_to_template.py`
- `export_single_row_to_excel(row, num, ts)`: 將單筆 Google Sheet 資料導出為專屬的獨立 Excel。
- `calc_cart_type(row)`: 根據資料內容自動推算「分車類型」。
- `normalize_dropdown_text(v)`: 正規化選單文字，解決全形/半形或隱藏字元導致的下拉選單比對失敗。

---

## 🚀 快速開始
1.  確保 `config/` 資料夾內已有正確的設定檔。
2.  將待上傳圖片放入 `picture/商品圖` 或 `picture/商品特色圖`。
3.  於終端機執行：
    ```bash
    python run_sheet_to_carrefour.py
    ```
4.  依提示輸入抓取列數，接著機器人將接手所有操作。
