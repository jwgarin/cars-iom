import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re
import bs4
import time
import random

filename = 'best_cars'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://bestcars.im'
start_url = 'https://bestcars.im/current-stock/'
#driver = webdriver.Chrome()
cookies = {
    'STACKSCALING': 'busybees5',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://bestcars.im/current-stock/',
    # 'Cookie': 'STACKSCALING=busybees5',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return [h.text for h in self.s.find_all('h3') if keyword in h.text][0].replace(keyword.replace('\\', ''), '').strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    for _ in range(3):
        r = ses.get(o['Link'], headers=headers, cookies=cookies)
        #driver.get(o['Link'])
        #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
        s = BeautifulSoup(r.text, 'html.parser')
        specs = Specs(s)
        get_specs = specs.get_specs
        title = s.find('h2', class_="car_main_title").text
        title_comp = title.split(' ')
        price = s.find('h3', class_="cs-price-item").text.replace('Price:', '').replace('£', '').replace(',', '').strip()
        try:
            price = int(float(price))
        except:
            pass
        if title_comp[0].isdecimal():
            year = title_comp[0]
            brand = title_comp[1]
            model = ' '.join(title_comp[2:])
        else:
            try:
                year = re.search(r'\d{4}', [h.text for h in s.find_all('h3') if 'Registration' in h.text][0]).group()
            except:
                year = ''
            brand = title_comp[0]
            model = ' '.join(title_comp[1:])
        engine_size = get_specs('Engine size')
        try:
            if float(engine_size) < 20:
                engine_size = f'{float(engine_size)}L'
            else:
                engine_size = f'{float(engine_size)}cc'
        except:
            pass
        mileage = get_specs('Miles') + ' Miles' if get_specs('Miles') else get_specs('Miles')
        transmission = get_specs('Transmission')
        colour = get_specs('Exterior colour')
        try:
            images = [x for x in [li.find('img')['src'] for li in s.find('ul', class_="slides").find_all('li') if li.find('img')] if x.strip() != '']
        except:
            images = []
        description = str(s.find('div', class_="homepage_content_desc"))
        description = description if description else ''
        if colour:
            break
        time.sleep(random.uniform(0.5, 1.2))
    o.update({
        'Title': title,
        'Price': price,
        'Year': year,
        'Brand': brand,
        'Model': model,
        'Engine Size': engine_size,
        'Mileage': mileage,
        'Transmission': transmission,
        'Colour': colour,
        'Description': description,
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    r = ses.get(start_url, headers=headers)#, cookies=cookies)
    print(r.status_code)
    with open('tmp.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    s = BeautifulSoup(r.text, 'html.parser')
    cars_slot = [div.find('a', class_='loop-img')['href'] for div in s.find_all('div', class_="container")[1].find_all('div', class_="row")[1].find_all('div', class_="loop-car") if div.find('a', class_='loop-img')]
    for link in cars_slot:
        data_main.append({
            'Link': link,
            'Provider': filename.title()
        })

    for i in range(len(data_main)):
        get_data(i)
        #if i == 10:
        #    break

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
    with open(f'../csv_files/{filename}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        usecols = list(data_main[0].keys())
        writer.writerow(usecols)
        writer = csv.DictWriter(f, fieldnames=usecols)
        for d in data_main:
            writer.writerow(d)
    logging.info(f'{filename.upper()} - Process Done!')


def main():
    logging.info(f'{filename.title()} Scrape Initiate')
    get_links()
    save()
    #driver.close()


if __name__ == "__main__":
    main()
    #pass
