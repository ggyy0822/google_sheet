from carrefour import CarrefourBot

def main():
    with CarrefourBot() as bot:
        bot.login()
        xlsx = bot.get_latest_xlsx(bot.cfg.upload.output_dir, bot.cfg.upload.filename_prefix)
        bot.upload_excel_template(xlsx)
        input("Done. Press Enter to quit...")

if __name__ == "__main__":
    main()