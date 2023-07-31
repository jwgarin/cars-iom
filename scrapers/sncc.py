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


filename = 'sncc'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://sncc.im/'
start_url = 'https://sncc.im/'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('li', class_=f"car_{keyword}").find('strong').text.strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    #s = BeautifulSoup(html, 'html.parser')
    spx = Specs(s)
    get_specs = spx.get_specs
    title = s.find('h2').text
    price = s.find('bdi', class_="new-price").text.replace('£', '').replace(',', '')
    try:
        price = int(price)
    except:
        pass
    try:
        status = s.find('span', class_="label car-status sold").text
        price = ''
    except:
        status = ''
    images = list(set([figure.find('img')['src'] for figure in s.find_all('figure') if figure.find('img')]))
    year = get_specs('year')
    model = get_specs('model')
    type_ = get_specs('body_style')
    mileage = get_specs('mileage') + ' Miles' if get_specs('mileage') else get_specs('mileage')
    transmission = get_specs('transmission')
    engine = get_specs('engine')
    engine_comp = engine.split(' ')
    try:
        engine_size = engine_comp[0]
    except:
        engine_size = ''
    try:
        fuel_type = engine_comp[-1]
    except:
        fuel_type = ''
    try:
        cylinders = [x for x in engine_comp if 'cylinder' in x.lower()][0]
    except:
        cylinders = ''
    colour = get_specs('exterior_color')
    try:
        lis = s.find('ul', class_="tabs").find_all('li')
        for li in lis:
            if 'Overview' in li.text:
                tab = li.find('a')['aria-controls']
                break
        else:
            raise Exception
        div_tab = s.find('div', id=tab)
        description = str(div_tab)
    except:
        description = ''
    title_comp = title.split(' ')
    brand = title_comp[1]
    o.update({
        'Title': title,
        'Brand': brand,
        'Price': price,
        'Status': status,
        'Year': year,
        'Model': model,
        'Type': type_,
        'Mileage': mileage,
        'Transmission': transmission,
        'Engine Size': engine_size,
        'Fuel Type': fuel_type,
        'Cylinders': cylinders,
        'Colour': colour,
        'Description': description,
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    r = ses.get(start_url)
    #driver.get(start_url)
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    #s = BeautifulSoup(html, 'html.parser')
    showrooms = [a['href'] for a in s.find('a', string=re.compile('Douglas HQ Showroom Inventory')).find_parent('ul').find_all('a')]
    #showrooms = driver.find_elements('xpath', '//a[text()="Douglas HQ Showroom Inventory"]')
    for showroom in showrooms:
        url = showroom
        print(url)
        while True:
            r2 = ses.get(url)
            print(url)
            s2 = BeautifulSoup(r2.text, 'html.parser')
            cars = [a.find('a')['href'] for a in [div for div in s2.find('div', class_="all-cars-list-arch").contents if isinstance(div, bs4.element.Tag)] if a.find('a')]
            for link in cars:
                data_main.append({
                    'Link': link,
                    'Provider': filename.upper()
                })
            try:
                next_page = s2.find('a', class_="next page-numbers")['href']
                url = next_page
            except:
                break

    for i in range(len(data_main)):
        for _ in range(3):
            try:
                get_data(i)
                break
            except Exception as exc:
                print('{} - {}'.format(i, exc))

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
    pass
    
