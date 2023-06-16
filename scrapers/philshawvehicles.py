import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re
from datetime import datetime
import bs4
from selenium.webdriver.chrome.options import Options

filename = 'philshawvehicles'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
domain = 'http://www.philshawvehicles.im'
start_url = 'http://www.philshawvehicles.im/your-search-results/?alllistings=true#headeranchor'
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)


class FourCols:
    def __init__(self, s):
        self.s = s
        
    def find_li(self, keyword):
        try:
            return self.s.find('li', string=re.compile(keyword)).text.split(':')[1].strip()
        except:
            return ''

def get_data(idx):
    o = data_main[idx]
    try:
        #r = ses.get(o['Link'])
        pass
    except Exception as exc:
        logger.error('{} - {}'.format(o['Link'], exc))
        raise Exception
    driver.get(o['Link'])
    html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    #s = BeautifulSoup(r.text, 'html.parser')
    s = BeautifulSoup(html, 'html.parser')
    fc = FourCols(s)
    find_li = fc.find_li
    title = s.find('h2', id='title').text.strip()
    brand = title.split(' ')[0]
    model = ' '.join(title.split('.')[0].split(' ')[1:-1])
    price = s.find('span', class_="featuresprice").text.replace('£', '').replace(',', '').replace('+VAT', '').replace('NO VAT', '').strip()
    if not price.isdecimal() and 'Sold' in price:
        price = ''
        status = 'Sold'
    elif price.isdecimal():
        price = int(price)
        status = ''
    else:
        raise Exception('Price Error')
    transmission = find_li('Trans')
    fuel_type = find_li('Fuel Type')
    engine_size = find_li('Engine Size')
    try:
        registration = datetime.strptime(find_li('Registered'), '%Y (%B)').strftime('%Y-%m')        
    except:
        registration = ''
    try:
        mileage = s.find('li', string=re.compile('Miles')).text.strip()
    except:
        mileage = ''
    type_ = find_li('Body Type')
    features = str(s.find('div', id="listingcontent").find('ul'))
    images = [x.find('a')['href'] for x in [c for c in s.find('ul', class_="slides").contents if isinstance(c, bs4.element.Tag)] if x.name == 'li' and x.find('a')]
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Status': status,
        'Transmission': transmission,
        'Fuel Type': fuel_type,
        'Engine Size': engine_size,
        'Registration': registration,
        'Mileage': mileage,
        'Type': type_,
        'Features': features,
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    unique_urls = []
    while True:
        #r = ses.get(url)
        driver.get(url)
        html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
        #s = BeautifulSoup(r.text, 'html.parser')
        s = BeautifulSoup(html, 'html.parser')
        cars_slot = [x['href'] for x in [y for y in s.find_all('form') if y.find('a')][0].find_all('a')]
        for link in cars_slot:
            if '#' in link:
                continue
            if link not in unique_urls and 'alllisting' not in link:
                data_main.append({
                    'Link': link,
                    'Provider': filename.title()
                })
                unique_urls.append(link)
        try:
            next_page = s.find('a', class_="nextpostslink")['href']
            url = next_page
        except:
            break

    for i in range(len(data_main)):
        try:
            get_data(i)
        except Exception as exc:
            logger.error('{} - {}'.format(data_main[i]['Link'], exc))
            raise Exception('{} - {}'.format(data_main[i]['Link'], exc))
            

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
    
