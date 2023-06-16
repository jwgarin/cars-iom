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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time

filename = 'signature_car_sales'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.signaturecarsales.im/'
start_url = 'https://www.signaturecarsales.im/pre-owned'
#options = Options()
#options.headless = True
#driver = webdriver.Chrome(options=options)
driver = webdriver.Chrome()


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    #r = ses.get(start_url)
    driver.get(start_url)
    driver.find_element('xpath', '//html').send_keys(Keys.CONTROL+Keys.END)
    logging.info('sleep 60s')
    for _ in range(60):
        time.sleep(1)
        driver.find_element('xpath', '//html').send_keys(Keys.PAGE_UP)
    s = BeautifulSoup(driver.find_element('xpath', '//html').get_attribute('innerHTML') , 'html.parser')
    driver.close()
    gallery = [div for div in s.find('div', attrs={'data-testid': "slide-show-gallery"}).parent.contents if isinstance(div, bs4.element.Tag)][3:]
    cars_slot = ''
    i = 0
    for j, g in enumerate(gallery):
        if g.attrs.get('data-testid') == 'slide-show-gallery':
            cars_slot += '|' + str(g)
        elif g.attrs.get('data-testid') == 'richTextElement':
            cars_slot += str(g)
        if g.attrs.get('data-testid') == 'slide-show-gallery' and j != 0:
            i += 1
        
            
    for i, car_slot in enumerate(cars_slot.split('|')[1:]):
        data_main.append({
            'Link': start_url,
            'Provider': filename.title().replace('_', ' ')
        })
        o = data_main[i]
        s = BeautifulSoup(car_slot, 'html.parser')
        images = [img for img in s.find_all('img') if img.get('src')]
        for j, image in enumerate(images):
            o['Image {}'.format(j+1)] = image['src']
        title = s.find('h2').text
        brand = title.replace('Pre Registered', '').strip().split(' ')[0]
        model = []
        for x in title.replace('Pre Registered', '').strip().split(' ')[1:]:
            if '.' in x:
                break
            model.append(x)
        else:
            model = []
            for x in title.replace('Pre Registered', '').strip().split(' ')[1:]:
                if any([y.isdecimal() for y in list(x)]):
                    break
                model.append(x)
            else:
                model = ''
        if model != '':                
            model = ' '.join(model)
        status = ''
        color_15 = [x for x in s.find_all('span', class_="color_15")[1].strings]
        try:
            price = s.find('span', class_="color_15").text.replace('£', '').replace(',', '').strip()
            if 'now' in price.lower():
                price = price.lower().split('now')[1].split('.')[0].strip()
            if 'Pricing Below' in price:
                for item in color_15:
                    if 'Our Price' in item:
                        price = item.split('Our Price')[1].replace('£', '').replace(',', '').strip()
                        break
                else:
                    price = ''
            if price.isdecimal():
                price = int(price)
            
        except:
            price = ''
        if not isinstance(price, int):
            if 'SOLD' in price or 'sold' in price:
                status = 'Sold'
                price = ''
            else:
                status = ''
        features = '<br>'.join(color_15[3:-3])
        try:
            mileage = color_15[2].strip('Only').strip('only').strip().replace('miles', 'Miles') if 'miles' in color_15[2].lower() else ''
        except:
            mileage = None
        if not mileage:
            try:
                mileage_text = [c for c in color_15 if 'mile' in c][0]
                mileage = mileage_text.strip('Only').strip('only').strip().replace('miles', 'Miles') if 'miles' in mileage_text.lower() else ''
            except:
                mileage = ''
        try:
            year = color_15[0].split(' ')[0] if color_15[0].split(' ')[0].isdecimal() else ''
        except:
            year = ''
        o.update({
            'Title': title,
            'Brand': brand,
            'Model': model,
            'Status': status,
            'Price': price,
            'Features': features,
            'Mileage': mileage,
            'Year': year
        })
        logging.info(o['Title'])
        

    #for i in range(len(data_main)):
    #    get_data(i)

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
