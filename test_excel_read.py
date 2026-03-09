# test_excel_read.py
import pandas as pd
from pathlib import Path

def test_read_eans():
    # 1. 尋找 output 資料夾
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ 找不到 output 資料夾")
        return

    # 2. 找到最新的 Excel 檔案
    files = list(output_dir.glob("*.xlsx"))
    if not files:
        print("❌ 資料夾內沒有 Excel 檔案")
        return
    
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    print(f"✅ 找到檔案: {latest_file.name}")

    # 3. 讀取並顯示條碼
    try:
        df = pd.read_excel(latest_file)
        
        # 檢查是否有「條碼」欄位
        if '條碼' not in df.columns:
            print(f"❌ 錯誤：Excel 中找不到「條碼」欄位。目前的欄位有: {list(df.columns)}")
            return
            
        eans = df['條碼'].dropna().astype(str).str.strip().tolist()
        
        print(f"📊 成功讀取到 {len(eans)} 筆條碼：")
        print(eans[:10]) # 先印出前 10 筆看看
        
        if len(eans) > 10:
            print("... (省略後續資料)")
            
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")

if __name__ == "__main__":
    test_read_eans()