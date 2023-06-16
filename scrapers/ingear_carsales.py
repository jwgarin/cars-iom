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
import itertools


filename = 'ingear_carsales'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.ingearcarsales.co.uk'
start_url = 'https://www.ingearcarsales.co.uk/cars/'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        return self.s


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    title = s.find('h1').text.strip()
    overview = s.find('div', class_="overview").find('div')
    status = ' '.join(overview.attrs['class']).replace('title', '').strip().title()
    price = ''
    if status == 'Available':
        price = s.find('span', class_="price").text.replace('£', '').replace(',', '').strip()
        status = ''
    try:
        price = int(float(price))
    except:
        pass
    images = [a['href'] for a in s.find_all('a', attrs={'data-fancybox': 'gallery'}) if a.get('href')]
    description = s.find('div', class_="vehicle_description")
    try:
        description.h3.extract()
    except:
        pass
    data = [div.find_all('span') for div in s.find_all('div', class_="data")]
    data = list(itertools.chain.from_iterable(data))
    data_dict = dd = {}
    for i in range(len(data)):
        if 'title' in data[i].get('class') and 'value' in data[i+1].get('class') and i < len(data) - 1:
            data_dict[data[i].text] = data[i+1].text
    engine_size = dd.get('Engine Size', '').replace('(', '').replace(')', '').replace('cc', '').strip()
    try:
        if float(engine_size) < 20:
            engine_size = f'{float(engine_size)} L'
        else:
            engine_size = f'{float(engine_size)} cc'
    except:
        pass
    o.update({
        'Title': title,
        'Status': status,
        'Price': price,
        'Description': description,
        'Year': dd.get('Year', ''),
        'Brand': dd.get('Make', ''),
        'Model': dd.get('Model', ''),
        'Colour': dd.get('Colour', ''),
        'Fuel Type': dd.get('Fuel', ''),
        'Transmission': dd.get('Transmission', ''),
        'Engine Size': engine_size,
        'Mileage': dd.get('Mileage', '').replace('mi', 'Miles'),
        'Engine Power': dd.get('Power (BHP)', '')
    })
        
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    r = ses.get(start_url)
    s = BeautifulSoup(r.text, 'html.parser')
    cars_slot = [div.find('a')['href'] for div in s.find('div', id='results').find_all('div', class_="vehicle") if div.find('a')]
    for link in cars_slot:    
        data_main.append({
            'Link': link,
            'Provider': 'Ingear Car Sales'
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
    #pass
