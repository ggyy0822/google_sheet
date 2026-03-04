from pathlib import Path
from carrefour import CarrefourBot

def list_images(folder: Path):
    patterns = ("*.jpg", "*.jpeg", "*.png", "*.webp")

    files = []
    for p in patterns:
        files.extend(folder.glob(p))

    files = sorted(files)
    return [str(p.resolve()) for p in files]


def main():
    base = Path("picture")   # 相對路徑

    product_dir = base / "商品圖"
    feature_dir = base / "商品特色圖"

    product_images = list_images(product_dir)
    feature_images = list_images(feature_dir)

    print("商品圖:", product_images)
    print("商品特色圖:", feature_images)

    with CarrefourBot() as bot:
        bot.login()

        if product_images:
            bot.upload_images_batch_chunked("商品圖", product_images, chunk_size=30)

        if feature_images:
            bot.upload_images_batch_chunked("商品特色圖", feature_images, chunk_size=30)

        input("Done. Press Enter to quit...")


if __name__ == "__main__":
    main()