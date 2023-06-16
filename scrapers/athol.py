import requests
from bs4 import BeautifulSoup
import csv
import asyncio
import random
import functools
import logging
from custom_logs import custom_logs

scraper_name = filename ='athol'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)


async def cons_main(q):
    while True:
        row = await q.get()
        await asyncio.sleep(random.uniform(2, 4))
        link = row['Link']
        try:
            r = await asyncio.get_event_loop().run_in_executor(None, requests.get, link)
            s = BeautifulSoup(r.text, 'html.parser')
        except:
            s = None
        try:
            for iconbox in s.find_all('div', class_="iconBoxText2"):
                if any(['colour' in string.lower() for string in iconbox.strings]):
                    color = ''.join([x for x in iconbox.strings if x != '' and x != 'Colour']).strip()
                    break
            else:
                color = ''
        except:
            color = ''
        row['Colour'] = color
        try:
            images = [x['style'] for x in s.find_all('div', class_="propSplashImg") if 'background' in x['style']]
        except:
            images = None
        image_list = []
        if images:
            for image in images:
                process_image = image.split('(')[1].strip(')')
                if process_image:
                    image_list.append(process_image)
            for i, image in enumerate(image_list):
                row[f'Image {i+1}'] = image
        try:
            title = s.find('h1', class_="featuredTitle first-word").text
            row['Title'] = title
        except:
            pass
        logging.info('-'.join(['ATHOL', row['Title'], color]))
        q.task_done()


async def main():
    logging.info('ATHOL Scrape Initiate')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://www.athol.im/vehicle-search',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    params = {
        'action': 'flight_search',
        'price': '',
        'brand_id': '',
        'model_id': '',
        'introduction': '',
        'image_path': '',
        'title_text': '',
        'price_prefix': '',
        'year': '',
        'engine_size': '',
        'low_price': '',
        'high_price': '',
        'fuel_type': '',
        'transmission': '',
        'mileage': '',
        'car_image': '',
        'hyperlink': '',
    }
    response = await asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.get, url='https://www.athol.im/wp-admin/admin-ajax.php', params=params, headers=headers))    
    try:
        cars = response.json()
    except Exception as exc:
        logger.error('Network request error - {}'.format(exc))
        raise Exception

    data_main = []

    for car in cars:
        try:
            price = int(car['price'])
        except:
            price = ''
        car_data = {
            'Title': car['title_text'],
            'Brand': car['brand_id'],
            'Price': price,
            'Model': car['model_id'],
            'Year': car['year'],
            'Engine Size': car['engine_size'] + ' L',
            'Fuel Type': car['fuel_type'],
            'Transmission': car['transmission'],
            'Mileage': car['mileage'],
            'Description': car['introduction'],
            'Link': car['hyperlink'],
            'Colour': '',
            'Provider': 'Athol'
        }
        data_main.append(car_data)
    q = asyncio.Queue()
    for row in data_main:
        await q.put(row)
        #break
    cons = [asyncio.create_task(cons_main(q)) for _ in range(2)]
    await q.join()
    for c in cons:
        c.cancel()

    unique_cols = []
    for d in data_main:
        for col in d.keys():
            if col not in unique_cols:
                unique_cols.append(col)

    for d in data_main:
        for col in unique_cols:
            if not d.get(col):
                d[col] = ''

    with open(f'..\\csv_files\\{filename}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        usecols = list(data_main[0].keys())
        writer.writerow(usecols)
        writer = csv.DictWriter(f, fieldnames=usecols)
        for d in data_main:
            writer.writerow(d)
    logging.info(f'{filename.upper()} - Process Done!')


if __name__ == "__main__":
    asyncio.run(main())
