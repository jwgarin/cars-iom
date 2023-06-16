import os
import asyncio
import logging
from custom_logs import custom_logs
import shutil

logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs('FAILED RUNS', 'scheduler')
process_done = []


async def exec_scraper(scraper):
    try:
        await asyncio.get_event_loop().run_in_executor(None, os.system, scraper)
        process_done.append(scraper)
    except Exception as exc:
        logging.error('SCHEDULER - {} - {}'.format(scraper, exc))


async def async_scheduler():
    os.chdir('scrapers')
    process = [exec_scraper(scraper) for scraper in os.listdir()]
    await asyncio.gather(*process)


def scheduler():
    #asyncio.run(async_scheduler())
    os.makedirs('csv_files', exist_ok=True)
    if len(os.listdir('csv_files')) and os.path.exists('isle-of-man.csv'):
        folder_name = str(len(os.listdir('backups')))
        os.makedirs('backups\\{}'.format(folder_name))
        shutil.move('isle-of-man-cars.csv', 'backups\\{}'.format(folder_name))
        shutil.rmtree('csv_files')
        os.makedirs('csv_files')
    
    os.chdir('scrapers')
    scheduler_contents = [r'cd G:\Projects\iom_cars\scrapers', 'G:']
    for scraper in os.listdir():
        if scraper.endswith('.py') and scraper != 'custom_logs.py':
            scheduler_contents.append('{}'.format(scraper))
    #scheduler_contents.append('cd ..\\')
    #scheduler_contents.append('check.bat')            
    scheduler_contents.append('@pause')
    
    # Generate report
    os.chdir('..\\')
    with open('_scheduler.bat', 'w', encoding='utf-8') as f:
        f.write('\n'.join(scheduler_contents))
    os.system('_scheduler.bat')
    #os.remove('_scheduler.bat')


if __name__ == "__main__":
    scheduler()
