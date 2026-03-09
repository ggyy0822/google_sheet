# run_bind_images.py
import time
from carrefour import CarrefourBot

def main():
    print("🚀 啟動全自動『暫存商品』圖片綁定任務...")

    with CarrefourBot() as bot:
        bot.login()
        
        # 這裡假設登入後需要點擊選單進入「提品申請」頁面
        # bot.goto_product_application() 
        
        # 1. 現場偵測：直接從網頁抓取目標
        target_eans = bot.get_all_draft_eans_from_page()

        if not target_eans:
            print("📭 畫面上沒有發現任何狀態為『暫存』的商品。")
            input("Press Enter to quit...")
            return

        # 2. 依照偵測到的清單執行
        for ean in target_eans:
            print(f"\n🔎 處理偵測到的條碼: {ean}")
            
            try:
                # 使用你精準的 XPATH 選擇器進入維護視窗
                if bot.goto_image_maintenance_if_draft(ean):
                    print(f"🎯 進入 {ean} 維護視窗")
                    
                    # 執行綁定邏輯
                    success = bot.bind_image_in_modal(ean)
                    
                    if success:
                        print(f"✨ {ean} 圖片綁定成功")
                    
                    # 結束後回到列表頁面
                    bot.go_home()
                    time.sleep(1)
                else:
                    print(f"⏭️ {ean} 狀態已改變或找不到按鈕，跳過。")

            except Exception as e:
                print(f"❌ 處理 {ean} 時發生錯誤: {e}")
                bot.go_home()

    print("\n✅ 任務結束。")
    input("Done. Press Enter to quit...")

if __name__ == "__main__":
    main()