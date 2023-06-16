import requests
from bs4 import BeautifulSoup
import asyncio
import functools
import csv
import logging
from custom_logs import custom_logs


logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs('BETTRIDGES', 'bettridges')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://www.bettridges.com',
    'Connection': 'keep-alive',
    'Referer': 'https://www.bettridges.com/motor/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}
data_main = []
MAX_TASKS = 3
filename = 'bettridges'


def get_links(page):
    global headers
    #print('\rLink Extraction: page {}'.format(page), end='')
    logging.info('BETTRIDGE - Link Extraction: page {}'.format(page))
    data = {
        'action': 'infinite_scroll',
        'loop_file': 'loop',
        'keyword': '',
        'make': '',
        'age': '',
        'transmission': '',
        'type': '',
        'fuel': '',
        'sort': 'price,asc',
        'price_min': '0',
        'price_max': '43000',
        'page_no': str(page),
    }

    response = requests.post('https://www.bettridges.com/wp-admin/admin-ajax.php', headers=headers, data=data)
    if response.text.strip() == "":
        raise Exception('end of page')
    s = BeautifulSoup(response.text, 'html.parser')
    if "To help us keep this website secure, please wait while we verify you're not a robot! It will only take a few seconds..." in s.text:
        raise Exception('Recaptcha Error')
    vehicles = s.contents
    links = []
    for vehicle in vehicles:
        try:
            anchor = vehicle.find('a')
            if anchor:
                links.append(anchor['href'])
        except:
            pass
    return links


async def get_data(link):
    r = await asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.get, url=link, timeout=60))
    s = BeautifulSoup(r.text, 'html.parser')
    # Title
    title = s.find('h2').text.strip()
    # Brand
    brand = title.split(' ')[0]
    # Price
    try:
        price = int(s.find('span', class_="price blue_grad").text.replace('£', '').replace(',', ''))
    except:
        price = ''
    # Model
    try:
        model = ' '.join(title.split(' ')[1:])
    except:
        model = ''
    # Engine Size
    try:
        engine = s.find('span', class_="detail engine").text.replace('Engine', '')
    except:
        engine = ''
    # Year
    try:
        year = s.find('span', class_="detail year").text.replace('Year', '')
    except:
        year = ''
    # Mileage
    try:
        mileage = s.find('span', class_="detail mileage").text.replace('Mileage', '')
    except:
        mileage = ''
    # Fuel Type
    try:
        fuel_type = s.find('span', class_="detail fuel").text.replace('Fuel', '')
    except:
        fuel_type = ''
    # Doors
    try:
        doors = s.find('span', class_="detail doors").text.replace('Doors', '')
    except:
        doors = ''
    # Transmission
    try:
        transmission = s.find('span', class_="detail transmission").text.replace('Transmission', '')
    except:
        transmission = ''
    # Status
    try:
        status = s.find('span', class_="status blue_grad status").text
    except:
        status = ''
    # Link
    #link = link
    # Images
    try:
        images = [y.find('img')['src'] for y in [x for x in s.find('ul', id="lightSlider").contents if x != '\n'] if y.find('img')]
    except:
        images = None
    #TODO: images
    data_row = {
        'Title': title,
        'Brand': brand,
        'Price': price,
        'Model': model,
        'Year': year,
        'Engine Size': engine + ' L',
        'Fuel Type': fuel_type,
        'Transmission': transmission,
        'Mileage': mileage,
        'Doors': doors,
        'Status': status,
        'Link': link,
        'Provider': 'Bettridges'
    }
    idx = 0
    if images:
        for image in images:
            if not 'images/holder.jpg'in image and image:
                idx += 1
                data_row[f'Image {idx}'] = image
    logging.info('-'.join(['BETTRIDGE', title, link]))
    return data_row


async def cons_r(q):
    while True:
        link = await q.get()
        try:
            data_row = await get_data(link)
            data_main.append(data_row)
        except Exception as exc:
            logging.info('-'.join(['BETTRIDGE', link, str(exc)]))
        q.task_done()


async def main():
    logging.info('Bettridge Scrape Initiate')
    page = 1
    links_list = []
    while True:
        try:
            links = await asyncio.get_event_loop().run_in_executor(None, get_links, page)
        except Exception as exc:
            if 'end of page' not in str(exc):
                raise Exception('-'.join(['BETTRIDGE', str(exc)]))
            else:
                break
        links_list.extend(links)
        page += 1
    q = asyncio.Queue()
    for link in links_list:
        await q.put(link)
    cons = [asyncio.create_task(cons_r(q)) for _ in range(MAX_TASKS)]
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
    save()


def save():
    with open(f'../csv_files/{filename}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        usecols = list(data_main[0].keys())
        writer.writerow(usecols)
        writer = csv.DictWriter(f, fieldnames=usecols)
        for d in data_main:
            writer.writerow(d)
    logging.info(f'{filename.upper()} - Process Done!')


if __name__ == "__main__":
    asyncio.run(main())
    #pass
