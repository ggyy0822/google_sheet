import os
import shutil
import time
from datetime import datetime

from google_sheet import GoogleSheetManager
from carrefour import CarrefourBot

# 引入整理好的各模組獨立功能
from export_to_template import ask_last_row, export_single_row_to_excel
from run_upload_images import upload_all_images
from run_upload_excel import upload_excel
from run_bind_images import bind_image

def main():
    # 1. 準備 Google Sheet 資料
    gs = GoogleSheetManager(sheet_config_file="config/google_sheet_config.json")

    # 建立與清空 output 資料夾
    output_dir = "output"
    if os.path.exists(output_dir):
        print(f"清空 {output_dir} 資料夾...")
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                pass
    else:
        os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 詢問要抓取幾列
    last_row = ask_last_row(min_row=gs.data_start_row)
    end_cell = f"AI{last_row}" # 預設 AI 欄位為最後一欄
    print(f"\n將抓取範圍：{gs.sheet_name}!A{gs.data_start_row}:{end_cell}\n")

    df = gs.load_gs_data(end_cell=end_cell)
    print("抓到總筆數：", len(df))

    if len(df) == 0:
        print("沒有資料可處理，程式結束。")
        return

    # 2. 開啟瀏覽器並登入一次
    with CarrefourBot() as bot:
        bot.login()
        
        # ========== 【步驟 A：上傳所有新圖片】 ==========
        print("\n--- 步驟 A：開始批次上傳圖片 ---")
        upload_all_images(bot)

        # ========== 【步驟 B：逐列匯入提品並綁定】 ==========
        print("\n--- 步驟 B：開始逐列匯入提品並綁定 ---")
        for index, row in df.iterrows():
            current_row_number = gs.data_start_row + index
            print(f"\n--- 正在處理第 {index + 1}/{len(df)} 筆資料 (對應 GS 第 {current_row_number} 列) ---")
            
            try:
                # 1. 產出該列專屬的 Excel 檔案
                xlsx_path = export_single_row_to_excel(
                    row_series=row, 
                    current_row_number=current_row_number, 
                    timestamp=timestamp, 
                    output_dir=output_dir
                )
                print(f"檔案已輸出到：{xlsx_path}")
                
                # 2. 執行單獨檔案的上傳
                upload_excel(bot, xlsx_path)
                print(f"第 {index + 1} 筆 Excel 上傳完成，等待 3 秒...\n")
                time.sleep(3)
                
                # 3. 提品完馬上綁定圖片
                current_ean = str(row.get("barcode", "")).strip() 
                if current_ean and current_ean.replace('.', '').isdigit(): # 確保有條碼且格式類似數字
                    print(f"準備進入條碼 {current_ean} 的圖檔維護...")
                    success = bind_image(bot, current_ean)
                    if success:
                        print(f"✨ 條碼 {current_ean} 圖片綁定成功")
                    else:
                        print(f"⚠️ 條碼 {current_ean} 綁定失敗、找不到按鈕或狀態非暫存")
                else:
                    print(f"⚠️ 這筆資料沒有有效的條碼 ({current_ean})，跳過圖片綁定步驟。")

            except Exception as e:
                print(f"處理第 {current_row_number} 列時發生錯誤: {e}")
                print("繼續處理下一筆...")

        print("\n=== 所有資料處理完成 ===")
        input("Done. Press Enter to quit...")

if __name__ == "__main__":
    main()
