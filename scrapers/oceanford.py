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
import asyncio
import functools
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from chromedriver_binary import chromedriver_filename

filename = 'oceanford'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.oceanford.com/'
start_url = 'https://www.oceanford.com/used-cars/'
cookies = None
options = Options()
#options.headless = True
driver = webdriver.Chrome(options=options, service=Service(chromedriver_filename))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.oceanford.com/used-cars/',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 'PHPSESSID=7a51b6b5ef07088821a66a371081317d; wasCtwPopupSeen=true; ovs_criteria_109239={%22valuations%22:{%22details%22:{%22vehicle%22:{}}}%2C%22generalValuations%22:{%22valuationsOutstandingPaymants%22:0%2C%22priceBelow%22:0}%2C%22customFilters%22:{}%2C%22customFilterLabelsStep2%22:[]%2C%22groupUrl%22:%22%22}; searchQuery_5039=%22?finance[]=price&type[]=car&budget-program[]=pcp&section[]=109239&per_page=24&order=price&page=1&pageId=858523&all-makes=1%22; searchTags_5039=[]; sp_landing_page=https://www.oceanford.com/used-cars/; trackingIpFilter=false; recentVehicles_5039=[%2214879204%22]; lastViewedVehicles_5039=[%2214879204%22]; __ggtruid=1659874599061.507d04f4-e6aa-eef6-bae4-84b667f82bb7; __ggtrses=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

def get_cookies(page):
    global cookies
    cookies = {
        'PHPSESSID': '7a51b6b5ef07088821a66a371081317d',
        'wasCtwPopupSeen': 'true',
        'ovs_criteria_109239': '{%22valuations%22:{%22details%22:{%22vehicle%22:{}}}%2C%22generalValuations%22:{%22valuationsOutstandingPaymants%22:0%2C%22priceBelow%22:0}%2C%22customFilters%22:{}%2C%22customFilterLabelsStep2%22:[]%2C%22groupUrl%22:%22%22}',
        'searchQuery_5039': '%22?finance[]=price&type[]=car&budget-program[]=pcp&section[]=109239&per_page=24&order=price&page=' + page + '&pageId=858523&all-makes=1%22',
        'searchTags_5039': '[]',
        'sp_landing_page': 'https://www.oceanford.com/used-cars/',
        'trackingIpFilter': 'false',
        'recentVehicles_5039': '[%2214879204%22]',
        'lastViewedVehicles_5039': '[%2214879204%22]',
        '__ggtruid': '1659874599061.507d04f4-e6aa-eef6-bae4-84b667f82bb7',
        '__ggtrses': '1',
    }
def request_list(page):
    global headers, cookies
    page = str(page)
    cookies = get_cookies(page)
    params = {
        'finance[]': 'price',
        'type[]': 'car',
        'budget-program[]': 'pcp',
        'section[]': '109239',
        'per_page': '24',
        'order': 'price',
        'page': page,
        'pageId': '858523',
        'all-makes': '1',
    }
    response = requests.get('https://www.oceanford.com/ajax/stock-listing/get-items/pageId/858523/ratio/4_3/taxBandImageLink//taxBandImageHyperlink//imgWidth/400/', params=params, cookies=cookies, headers=headers)
    j = response.json()
    return j
    
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        return self.s

def get_image(idx, url=None):
    global driver, data_main
    if url:
        link = url
        o = {}
    else:
        o = data_main[idx]
        link = o['Link']
    driver.get(link)
    driver.find_element('xpath', '//html').send_keys(Keys.CONTROL+Keys.END)
    for _ in range(5):
        time.sleep(1)
        driver.find_element('xpath', '//html').send_keys(Keys.PAGE_UP)
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH, '//div[@class="item cycle-slide"]//img[@class="big-image"]')))
    for _ in range(120):
        time.sleep(1)
        if random.randint(0, 1):
            driver.find_element('xpath', '//html').send_keys(Keys.PAGE_UP)
        else:
            driver.find_element('xpath', '//html').send_keys(Keys.PAGE_DOWN)
        images = [img for img in [elem.get_attribute('src') for elem in driver.find_elements('xpath', '//div[@class="item cycle-slide"]//img[@class="big-image"]')] if not img.endswith('.gif')]
        print('\rImage Number: {}'.format(len(images)), end='')
        if len(images) > 17:
            break
    print()
        
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('Image Collected: {} - {}'.format(idx, link))

def get_data(v):
    link = v.get('url')
    if link:
        link = urljoin(home_url, link)
    else:
        raise Exception('Link not Found')
    o = {}
    #images = await get_image(link)
    registration_num = v.get('registration', '')
    year = v.get('year', '')
    fuel_type = v.get('fuel', '')
    colour = v.get('colour', '')
    mileage = v.get('mileage', '')
    engine_size = v.get('engine_size', '') if v.get('engine_size', '') else ''
    economy = v.get('mpg', '') if v.get('mpg', '') else ''
    doors = v.get('doors', '')
    transmission = v.get('transmission', '')
    brand = v.get('make', '')
    model = v.get('model', '')
    type_ = v.get('bodystyle', '')
    title = v.get('link_title', '')
    price = v.get('price_now_raw', '')
    o.update({
        'Registration Number': registration_num,
        'Year': year,
        'Fuel Type': fuel_type,
        'Colour': colour,
        'Mileage': mileage,
        'Engine Size': engine_size,
        'Economy': economy,
        'Doors': doors,
        'Transmission': transmission,
        'Brand': brand,
        'Model': model,
        'Type': type_,
        'Title': title,
        'Price': price,
        'Link': link,
        'Provider': 'Ocean Ford'
    })
    
    #for i, image in enumerate(images):
    #    o[f'Image {i+1}'] = image
    data_main.append(o)
    logging.info('{} - {}'.format(len(data_main), o['Title']))


def get_links():
    page = 1
    while True:
        print('Collecting Page {}'.format(page))
        j = request_list(page)
        vehicles = j.get('vehicles', [])
        for v in vehicles:
            get_data(v)
        has_more = j.get('hasMoreResults')
        if not has_more:
            break
        page += 1
        
    for i in range(len(data_main)):
        for _ in range(3):
            try:
                get_image(i)
                break
            except Exception as exc:
                print('retrying - {} - {}'.format(i, exc))
        
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
    
