import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
from chromedriver_binary import chromedriver_filename
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import re
import bs4


filename = 'bvsvehicles'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://bvsvehicles.com'
start_url = 'https://bvsvehicles.com/our-vehicles/'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        return self.s


def get_data(idx):
    o = data_main[idx]
    for _ in range(3):
        try:
            r = ses.get(o['Link'])
            if r.status_code == 200:
                break
        except:
            pass
    else:
        logger.error('Network Error')
        raise Exception
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    title = s.find('h5', class_="elementor-heading-title elementor-size-default").text
    brand = title.split(' ')[0]
    model = ' '.join(title.split(' ')[1:])
    try:
        features = [string for string in s.find('div', attrs={'data-id': 'ce6f002'}).strings]
    except:
        features = []
    features_i = []
    year, mileage, engine_size, fuel_type, price, transmission = ['']*6
    for feature in features:
        if re.search('\d\d\d\d', feature) and not year:
            year = re.search('\d\d\d\d', feature).group()
        elif re.search('\d+,\d+ Miles', feature):
            mileage = re.search('\d+,\d+ Miles', feature).group()
        elif 'Petrol' in feature or 'Diesel' in feature or 'Gas' in feature:
            if '.' in feature:
                engine_size = [ft for ft in feature.split(' ') if '.' in ft][0]
            fuel_type = re.search('Petrol|Diesel|Gas', feature).group()
        elif re.search('£\d+,\d+', feature):
            price = re.search('£\d+,\d+', feature).group()
            price = int(price.replace('£', '').replace(',', ''))
        elif re.search('automatic|manual', feature, re.I):
            transmission = re.search('automatic|manual', feature, re.I).group()
        else:
            features_i.append(feature)
        if 'warranty' in feature or 'hand over' in feature:
            break
    try:
        images = [x.find('img')['src'] for x in s.find('div', id="gallery-1").find_all('figure', class_="gallery-item") if x.find('img')]
    except:
        images = []
    
    o.update({
        'Title': title,
        'Brand': brand,
        'Price': price,
        'Model': model,
        'Features': '<br>'.join([x for x in features_i if x.strip() != '']),
        'Year': year,
        'Mileage': mileage,
        'Engine Size': engine_size + ' L' if engine_size else engine_size,
        'Fuel Type': fuel_type,
        'Price': price,
        'Transmission': transmission.title(),
    })
        
                
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    #r = ses.get(start_url)
    driver = webdriver.Chrome(service=Service(chromedriver_filename))
    driver.get(start_url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//a[@class="elementor-post__thumbnail__link"]')))
    s = BeautifulSoup(driver.find_element('xpath', '//html').get_attribute('outerHTML'), 'html.parser')
    #list_pages = [start_url]
    #links = s.find('nav', class_="elementor-pagination").find_all('a', class_="page-numbers")
    links = [a['href'] for a in s.find_all('a', class_="elementor-post__thumbnail__link")]
    #for link in links:
    #    if link not in list_pages:
    #        list_pages.append(link['href'])
    for car_url in links:
        data_main.append({
            'Link': car_url,
            'Provider': 'BVS Vehicles'
        })
    '''for link in list_pages:
        r = ses.get(link)
        s = BeautifulSoup(r.text, 'html.parser')
        try:
            cars_slot = [article.find('a')['href'] for article in s.find('div', attrs={'data-id': '6f781b0a'}).find('div', class_="elementor-posts").find_all('article') if article.find('a')]
        except Exception as exc:
            logger.warning('{} - {}'.format('listing error', str(exc)))
            continue
        for car_url in cars_slot:
            data_main.append({
                'Link': car_url,
                'Provider': 'BVS Vehicles'
            })'''

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
