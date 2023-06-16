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


filename = 'kingswood_honda'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
#home_url = 'https://www.kingswood-honda.com'
start_url = 'https://www.kingswood-honda.com/pre-owned/'
home_url = start_url.split('.com')[0] + '.com'
#driver = webdriver.Chrome()


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    title = s.find('h1').text.strip()
    tc = title.split(' ')
    year = tc[0]
    brand = tc[1]
    try:
        engine_size = re.search(r'\d\.\d', title).group()
    except:
        engine_size = ''
    #es_idx = tc.index(engine_size)
    #specs = ' '.join(tc[es_idx +  1:])
    if engine_size:
        model = ' '.join(tc[2:]).split(engine_size)[0].strip()
        engine_size += ' L'
    else:
        model = ' '.join(tc[2:]).strip()
    price = s.find('h1', class_="price").text.replace('£', '').replace(',', '').strip()
    description = s.find('div', class_="car-description").text.strip()
    o.update({
        'Title': title,
        'Brand': brand,
        'Price': price,
        'Year': year,
        'Engine Size': engine_size,
        'Model': model,
        'Description': description,
    })
    images = [
        li.find('img')['src'] for li in
        [
            x for x in
            s.find('div', id="single-cars-slider").find('ul', class_="slides").contents
            if isinstance(x, bs4.element.Tag)
        ] if li.find('img')
    ]
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    
    
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    while True:
        r = ses.get(url)
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = [a['href'] for a in s.find('div', class_="showroom-preowned-carss-wrapper").find_all('a', class_="view-details")]
        for href in cars_slot:
                data_main.append({
                    'Link': href,
                    'Provider': filename.title().replace('-', ' ')
                })
        try:
            next_page = s.find('a', class_="next page-numbers")['href']
            if next_page == '#':
                break
        except:
            break
        url = next_page

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
