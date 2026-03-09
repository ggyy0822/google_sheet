from pathlib import Path
from carrefour import CarrefourBot

def list_images(folder: Path):
    patterns = ("*.jpg", "*.jpeg", "*.png", "*.webp")

    files = []
    for p in patterns:
        files.extend(folder.glob(p))

    files = sorted(files)
    return [str(p.resolve()) for p in files]


def upload_all_images(bot: CarrefourBot) -> bool:
    """供外部呼叫：上傳所有圖片"""
    base = Path("picture")   # 相對路徑

    product_dir = base / "商品圖"
    feature_dir = base / "商品特色圖"

    product_images = list_images(product_dir)
    feature_images = list_images(feature_dir)
    
    print(f"找到 {len(product_images)} 張商品圖, {len(feature_images)} 張商品特色圖")

    if product_images:
        bot.upload_images_batch_chunked("商品圖", product_images, chunk_size=30)
    else:
        print("沒有商品圖需要上傳")

    if feature_images:
        bot.upload_images_batch_chunked("商品特色圖", feature_images, chunk_size=30)
    else:
        print("沒有商品特色圖需要上傳")
        
    return True

def main():

    with CarrefourBot() as bot:
        bot.login()
        upload_all_images(bot)
        input("Done. Press Enter to quit...")


if __name__ == "__main__":
    main()