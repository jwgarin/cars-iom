import os
import asyncio
import logging
from custom_logs import custom_logs

logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs('FAILED RUNS', 'scheduler')


def main():
    
    for scraper in os.listdir('scrapers'):
        if scraper.endswith('.py') and scraper != 'custom_logs.py' and scraper.replace('.py', '.csv') not in os.listdir('csv_files'):
            logger.warning(scraper.replace('.py', '').upper())
    logging.info('CHECK PROCESS DONE!')
    os.chdir('logs')
    #os.system('start scheduler.log')
    
if __name__ == "__main__":
    main()
