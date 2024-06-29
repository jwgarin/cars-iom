import requests
from bs4 import BeautifulSoup
import csv
import asyncio
import random
import functools
import logging
from custom_logs import custom_logs
import sys


data_main = []
filename = 'brentmealin'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
progress = 0
total = None


def get_data(link):
    global progress
    r = requests.get(link, timeout=60)
    s = BeautifulSoup(r.text, 'html.parser')
    title = [x for x in s.find('h1').strings if x.strip() != ''][0].strip()
    description = s.find('div', class_="car-description").text.strip()
    price = s.find('h1').find('span').text.replace('£', '').replace(',', '').strip()
    images = [li.find('img')['src'] for li in s.find('ul', class_="slides").find_all('li') if li.find('img')]
    if title.startswith('Land Rover'):
        brand = 'Land Rover'
        model = title.replace('Land Rover', '').strip()
    elif title.startswith('Range Rover'):
        brand = 'Range Rover'
        model = title.replace('Range Rover', '').strip()
    else:
        brand = title.split(' ')[0]
        model = ' '.join(title.split(' ')[1:])
    car_data = {
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Description': description,
        'Price': price,
        'Link': link,
        'Provider': 'Brent Mealin',
    }
    for i, image in enumerate(images):
        car_data['Image {}'.format(i+1)] = image
    progress += 1
    logging.info('{}/{}'.format(progress, total) + ' ' + title)
    data_main.append(car_data)


async def cons_process(q):
    while True:
        link = await q.get()
        await asyncio.sleep(random.uniform(0.5, 1.2))
        try:
            await asyncio.get_event_loop().run_in_executor(None, get_data, link)
        except Exception as e:
            logging.error(e)
            if not 'timeout' in str(e).lower():
                sys.exit(1)
        q.task_done()


async def process_links(links):
    q = asyncio.Queue()
    for link in links:
        await q.put(link)
    cons = [asyncio.create_task(cons_process(q)) for _ in range(3)]
    await q.join()
    for c in cons:
        c.cancel()


def start():
    global total
    url = 'https://brentmealin.com/showroom/'
    links = []
    while True:
        r = requests.get(url)
        s = BeautifulSoup(r.text, 'html.parser')
        links.extend([div.find('a', class_="view-details")['href'] for div in s.find_all('div', class_="showroom-car-container") if div.find('a', class_="view-details")])

        try:
            next_page = s.find('nav', class_="car-pagination").find('a', class_="next page-numbers")
            url = next_page['href']
            if url == '#':
                break
        except:
            logging.info('end of page')
            break
    total = len(links)
    asyncio.run(process_links(links))

    unique_cols = []
    for d in data_main:
        for col in d.keys():
            if col not in unique_cols:
                unique_cols.append(col)

    for d in data_main:
        for col in unique_cols:
            if not d.get(col):
                d[col] = ''


def save():
    with open(f'..\\csv_files\\{filename}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        usecols = list(data_main[0].keys())
        writer.writerow(usecols)
        writer = csv.DictWriter(f, fieldnames=usecols)
        for d in data_main:
            writer.writerow(d)
    logging.info(f'{filename.upper()} - Process Done!')


def main():
    logging.info('Brent Mealin Scrape Initiate')
    start()
    save()


if __name__ == "__main__":
    main()
