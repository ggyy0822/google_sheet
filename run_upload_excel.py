from carrefour import CarrefourBot

def upload_excel(bot: CarrefourBot, xlsx_path: str):
    """供外部呼叫：上傳寫好的 Excel 到家樂福"""
    bot.upload_excel_template(xlsx_path)

def main():
    with CarrefourBot() as bot:
        bot.login()
        xlsx = bot.get_latest_xlsx(bot.cfg.upload.output_dir, bot.cfg.upload.filename_prefix)
        upload_excel(bot, xlsx)
        input("Done. Press Enter to quit...")

if __name__ == "__main__":
    main()