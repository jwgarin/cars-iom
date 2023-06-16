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


filename = 'cars_for_you'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://cars4you.im/'
start_url = 'https://cars4you.im/cars'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('div', string=re.compile(keyword)).text.split(':')[1].strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    specs = Specs(s)
    get_specs = specs.get_specs
    title = s.find('h2', class_="djc_title").text.strip()
    try:
        price = s.find('div', class_="djc_price").text.split('GBP')[1].strip().replace(',', '')
    except:
        price = ''
    try:
        now_only = s.find('div', dir='auto', string=re.compile('Now Only')).text.replace('Now Only £', '').replace('.', '').replace('£', '').strip()
    except:
        now_only = ''
    if now_only:
        price = now_only
        if 'Now Sold' in price:
            price = 'Sold'
    try:
        now_sold = s.find('h3', string=re.compile('Now Sold')).text
    except:
        now_sold = ''
    if now_sold:
        status = now_sold.replace('Now Sold', 'Sold', ).replace('.', '').strip()
    else:
        status = ''
    if 'SOLD' in title:
        status = 'Sold'
    transmission = get_specs('Transmission')
    brand = get_specs('Make')
    model = get_specs('Model')
    year = get_specs('Year')
    fuel_type = get_specs('Fuel').replace('Perol', 'Petrol')
    engine_size = get_specs('Engine Size').replace(',', '').replace('ccm', 'cc')
    mileage = get_specs('Mileage').replace(',', '').replace('Mile', 'Miles')
    feature = ''.join([str(text) for text in s.find('div', class_="djc_fulltext").find_all('div', dir='auto')if ':' not in text.text and text.text.strip() != '' and '●' in text.text])
    if s.find('h3', string=re.compile('Features Include')):
        try:
            feature = s.find('h3', string=re.compile('Features Include')).next_sibling.next_sibling
        except:
            feature = ''
    title_comp = title.split(' ')
    if title_comp[0].isdecimal():
        if not year:
            year = title_comp[0]
        if not brand:
            brand = title_comp[1]
    
        
    text_html = s.find('html').text
    if not engine_size:
        try:
            engine_size = re.search(r'(?<=Engine Size: )\d,\d+ cc(?=m)', text_html).group().replace(',', '')
        except:
            pass
    if not fuel_type:
        try:
            fuel_type = re.search(r'(?<=Fuel: )\w+', text_html).group()
        except:
            pass
    if not mileage:
        try:
            mileage = re.search(r'(?<=Mileage: )\d+,\d+ (?=Mile)', text_html).group() + 'Miles'
        except:
            pass
    if not transmission:
        try:
            transmission = re.search(r'(?<=Transmission: )[\d\w\s]*', text_html).group()
        except:
            pass
    if not year:
        try:
            year = re.search(r'(?<=Year: )[\d\w\s]*', text_html).group()
        except:
            pass
    if not brand:
        try:
            brand = re.search(r'(?<=Make: )[\d\w\s]*', text_html).group()
        except:
            pass
    if not model:
        try:
            model = re.search(r'(?<=Model: )[\d\w\s]*', text_html).group()
        except:
            pass
    if not feature:
        try:
            feature = str(s.find('div', class_="text_exposed_show"))
            if feature == 'None':
                feature = ''
        except:
            pass
    engine_size = engine_size if 'cc' in engine_size else ''
    if engine_size:
        engine_size = engine_size.split('cc')[0] + ' cc'
    mileage = mileage.replace('Miless', '').replace('Miles', '').replace('Mile', '').strip()
    if mileage:
        mileage += ' Miles'
    brand = brand.replace('Model', '')
    model = model.replace('Year', '')
    title_comp = title.strip().split(' ')
    if not brand:
        if not title_comp[0].isdecimal():
            brand = title_comp[0]
            
        else:
            brand = title_comp[1]
            
    if not model:
        if not title_comp[0].isdecimal():
            model = ' '.join(title_comp[1:]).replace('SOLD', '').replace('***', '').replace('Now Sold', '').replace('!', '').strip()
        else:
            model = ' '.join(title_comp[2:]).replace('SOLD', '').replace('***', '').replace('Now Sold', '').replace('!', '').strip()
    o.update({
        'Title': title,
        'Price': price,
        'Status': status,
        'Transmission': transmission,
        'Brand': brand,
        'Model': model,
        'Year': year.replace('Transmission', ''),
        'Fuel Type': fuel_type.replace('Engine', ''),
        'Engine Size': engine_size,
        'Mileage':  mileage,
        'Feature': feature
    })
    images = [s.find('div', class_="djc_mainimage").find('img', id="djc_mainimage")['src']] + [div.find('img', class_="img-polaroid")['src'] for div in s.find('div', id="djc_thumbnails").find_all('div', class_="djc_thumbnail") if div.find('img')]
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    while True:
        print(url)
        r = ses.get(url)
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = [div for div in [item for item in s.find('div', class_="djc_listing_items").contents if isinstance(item, bs4.element.Tag)] if div.name == 'div']
        
        for div in cars_slot:
            listings = [d for d in [item for item in div.contents if isinstance(item, bs4.element.Tag)] if d.name == 'div']
            for listing in listings:
                link = urljoin(home_url, listing.find('h3').find('a')['href'])
                data_main.append({
                    'Link': link,
                    'Provider': filename.title().replace('_', ' ')
                })
        try:
            next_page = urljoin('https://cars4you.im/cars', s.find('a', string=re.compile('Next'))['href'])
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
    pass
    
    
