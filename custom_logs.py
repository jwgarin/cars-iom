import logging


def custom_logs(scraper_name, filename):
    logger = logging.getLogger(scraper_name)
    logger.setLevel(logging.DEBUG)
    ch = logging.FileHandler(f"G:\\Projects\\iom_cars\\logs\\{filename}.log", mode='w', encoding="utf-8")
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

if __name__ == "__main__":
    logger1 = custom_logs('FAILED RUNS', 'scheduler')
    logger2 = custom_logs('BETTRIDGES', 'athol')
    logger1.error('test')