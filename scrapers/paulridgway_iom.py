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
from selenium.webdriver.chrome.service import Service
from chromedriver_binary import chromedriver_filename


filename = 'paulridgway_iom'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'http://www.paulridgwayiom.com/'
start_url = 'https://www.paulridgwayiom.com/vehicle-sales/'
driver = webdriver.Chrome(service=Service(chromedriver_filename))

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('strong', string=re.compile(keyword)).next_sibling.replace(keyword, '').strip().strip(':').strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    s = BeautifulSoup(r.text, 'html.parser')
    specs = Specs(s)
    get_specs = specs.get_specs
    try:
        title = s.find('h2', id='title').text.split('–')[1].strip()
    except:
        title = s.find('a', class_='u-product-title-link').text.strip()
    #price = s.find('h2', id='pricebig').text.replace('£', '').replace(',', '').replace('+VAT', '').strip()
    price = s.find('div', class_=re.compile(r'u-price-wrapper')).text.replace('£', '').replace(',', '').replace('+VAT', '').strip()
    if price.isdecimal():
        price = int(price)
        status = ''
    else:
        status = price
        price = ''
    #images = [e.find('img')['src'] for e in [d for d in [c for c in s.find('ul', class_='slides').contents if isinstance(c, bs4.element.Tag)] if d.name == 'li'] if e.find('img')]
    images = [li.find('img')['src'] for li in s.find('ol', class_="u-carousel-thumbnails").find_all('li') if li.find('img')]
    type_ = get_specs('Body Type')
    mileage = get_specs(r'\d+ Miles')
    if not mileage:
        mileage = get_specs('Mileage')
    fuel_type = get_specs('Fuel Type')
    year = get_specs('Year Built')
    transmission = get_specs('Transmission')
    colour = get_specs('Exterior Colour')
    try:
        features = s.find('strong', string='Vehicle Details').parent.find_next_sibling('ul')
        if features.name == 'ul':
            features = str(features)
        else:
            features = ''
    except:
        features = ''
    title_comp = title.split(' ')
    brand = title_comp[0]
    model = ' '.join(title_comp[1:])
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Status': status,
        'Type': type_,
        'Mileage': mileage,
        'Fuel Type': fuel_type,
        'Year': year,
        'Transmission': transmission,
        'Colour': colour
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    
    
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    driver.get(url)
    print(url)
    while True:
        #r = ses.get(url)
        html = driver.find_element('xpath', '//html').get_attribute('outerHTML')
        s = BeautifulSoup(html, 'html.parser')
        cars_slot = s.find_all('a', href=re.compile(r'productId=\d+$'), attrs={'data-product-button-click-type': True})
        
        for a in cars_slot:
            link = a['href']
            data_main.append({
                'Link': link,
                'Provider': 'Paul Ridgway IOM'
            })
        # Click next page
        try:
            driver.find_element('xpath', '//a[@title="Next"]').click()
        except:
            break
        #time.sleep(3)
        #try:
        #    next_page = s.find('a', class_="nextpostslink")['href']
        #    url = next_page
        #except:
        #    break

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
    
