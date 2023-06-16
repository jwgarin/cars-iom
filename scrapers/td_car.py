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
from selenium.webdriver.chrome.options import Options
import time

filename = 'td_car'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://tdcar.im'
start_url = 'https://tdcar.im/'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('ul', class_='car-attributes').find('li', class_='car_{}'.format(keyword.lower().replace(' ', '_'))).find('span', string=re.compile(keyword)).parent.text.replace(keyword, '').replace(':', '').strip()
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
    title = s.find('h1', class_="car-title").text
    title_comp = title.split(' ')
    if 'rover' in title.lower():
        brand = ' '.join(title_comp[0:2])
        model = ' '.join(title_comp[2:])
    else:
        brand = title_comp[0]
        model = ' '.join(title_comp[1:])
    #images = [img['src'] for img in s.find('div', class_="slick-track").find_all('img')]
    images = [img['src'] for img in s.find_all('img', alt=title)]
    year = get_specs('Year')
    engine_size = get_specs('Engine')
    try:
        if float(engine_size) < 20:
            engine_size = f'{float(engine_size)} L'
        else:
            engine_size = f'{float(engine_size)} cc'
    except:
        pass
    fuel_type = get_specs('Fuel Type')
    transmission = get_specs('Transmission')
    mileage = get_specs('Mileage')
    if not mileage:
        mileage = get_specs('Milage')
    doors = get_specs('Doors')
    seat_num = get_specs('Seats')
    price = s.find('h1').parent.find('span', class_="new-price").text.replace('£', '').replace(',', '').strip().split('.')[0]
    try:
        price = int(price)
    except:
        pass
    try:
        status = s.find('a', string=re.compile('Sold')).text
        price = ''
    except:
        status = ''
    try:
        description = str(s.find('div', class_='tab-content').find('div', id="tab-overview"))
    except:
        description = ''
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Year': year,
        'Engine Size': engine_size,
        'Fuel Type': fuel_type,
        'Transmission': transmission,
        'Description': description,
        'Mileage': mileage + ' Miles' if mileage else mileage,
        'Doors': doors,
        'Number of Seats': seat_num,
        'Price': price,
        'Status': status
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    page = 1
    options = Options()
    #options.headless = True
    driver = webdriver.Chrome(options=options)
    current_url = start_url
    while True:
        #r = ses.get(url(page))
        if current_url == start_url:
            driver.get(start_url)
        try:
            print(driver.current_url)
        except:
            pass
        s = BeautifulSoup(driver.find_element('xpath', '//html').get_attribute('outerHTML'), 'html.parser')
        cars_slot = [a.find('a')['href'] for a in s.find_all('div', class_="car-content") if a.find('a')]
        for link in cars_slot:
            data_main.append({
                'Link': link,
                'Provider': 'TD Car'
            })
        try:
            next_page = s.find('a', class_="next page-numbers")['href']
            driver.find_element('xpath', '//a[@class="next page-numbers"]').click()
            #url = next_page
        except:
            break
        for _ in range(30):
            time.sleep(1)
            if driver.current_url != current_url:
                current_url = driver.current_url
                break
        else:
            print('Error-New Page not waited')

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
