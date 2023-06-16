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


filename = 'bespokegroup'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'http://www.bespokegroup.im'
start_url = 'http://www.bespokegroup.im/cars-for-sale'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('strong', string=re.compile(keyword)).parent.text.replace(keyword, '').strip().strip(':').strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    spx = Specs(s)
    get_specs = spx.get_specs
    title = s.find('h3').text.strip()
    try:
        brand = title.split(' ')[0] if not title.startswith('Range') or not title.startswith('Land') else ' '.join(title.split(' ')[0:2])
        model = ' '.join(title.split(' ')[1:]) if not title.startswith('Range') or not title.startswith('Land') else ' '.join(title.split(' ')[2:])
    except:
        brand = ''
        model = ''
    price = get_specs('Price').replace('£', '').replace(',', '')
    status = ''
    try:
        if 'vat' in price.lower():
            price = re.search('\d+', price).group()
    except:
        pass
    try:
        price = int(price)
    except:
        status = price
        price = ''
    
    engine_size = get_specs('Engine')
    if engine_size.isdecimal():
        if float(engine_size) < 20:
            engine_size = f'{int(float(engine_size))} L'
        else:
            engine_size = f'{int(float(engine_size))} cc'
    fuel_type = get_specs('Fuel')
    year = get_specs('Year')
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Status': status,
        'Engine Size': engine_size,
        'Fuel Type': fuel_type,
        'Year': year
    })
    images = [urljoin('http://www.bespokegroup.im', a['href']) for a in s.find_all('a', class_="swipebox") if a.get('href')]
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    while True:
        r = ses.get(url)
        print(url)
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = [urljoin(home_url, div.find('a')['href']) for div in s.find('div', role='content').find_all('article', class_="car-item") if div.find('a')]
        for link in cars_slot:
            if link == 'http://www.bespokegroup.im/car-for-sale-peel-isle-of-man/reynolds-reynolds-vehicle-sales-iom-business-park-douglas':
                continue
            data_main.append({
                'Link': link,
                'Provider': 'Bespoke Group'
            })
        try:
            next_page = urljoin(start_url, s.find('a', string=re.compile('›'))['href'])
            url = next_page
        except:
            break
        
    for i in range(len(data_main)):
        get_data(i)
    
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
