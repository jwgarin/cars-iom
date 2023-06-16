import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re


filename = 'mike_hewison'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'http://www.mikehewisonautos.co.uk'
start_url = 'http://www.mikehewisonautos.co.uk/car_price.html'
#driver = webdriver.Chrome()


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    engine_size, fuel_type, mileage = ['']*3
    try:
        valign = [td for td in s.find_all('td', valign="top") if td.find('h2')][0]
        strings = [x for x in valign.strings if x.strip() != '']
        engine_size, fuel_type, mileage = strings[1].split(', ')
        if not 'l' in engine_size:
            engine_size = engine_size.split('cc')[0] + ' cc'
            
    except:
        pass
    try:
        features = strings[2]
    except:
        features = ''
    images = list(set([s.find('img', alt=re.compile('Vehicle '))['src']] + [x for x in [a['onmouseover'].split('=')[1].strip('\'') for a in s.find_all('a', attrs={'onmouseover': True})] if 'car' in x]))
    images = [urljoin(home_url, img) for img in images]
    for i, image in enumerate(images):
        o['Image {}'.format(i+1)] = image
    o.update({
        'Engine Size': engine_size,
        'Fuel Type': fuel_type,
        'Mileage': mileage,
        'Features': features
    })
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    r = ses.get(start_url)
    s = BeautifulSoup(r.text, 'html.parser')
    cars_slot = s.find('table', cellpadding="3").find_all('tr')[1:]
    for div in cars_slot:
        link = urljoin(home_url, div.find('a')['href'])
        tds = div.find_all('td')
        year = tds[0].text
        title = tds[1].text
        brand = title.split(' ')[0].title()
        model = ' '.join(title.split(' ')[1:]).title()
        price = tds[2].text.replace('£', '').replace(',', '').strip().strip('.00')
        if price.isdecimal():
            price = int(price)
            status = ''
        else:
            status = price
            price = ''
        data_main.append({
            'Link': link,
            'Provider': filename.title(),
            'Year': year,
            'Title': title,
            'Brand': brand,
            'Model': model,
            'Price': price,
            'Status': status,
        })

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
