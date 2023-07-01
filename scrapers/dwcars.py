import requests
from bs4 import BeautifulSoup
import csv

import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin


filename = 'dwcars'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []


def get_data(i):
    o = data_main[i]
    r = ses.get(o['Link'])
    s = BeautifulSoup(r.text, 'html.parser')
    if o.get('Status'):
        title = s.find('div', class_="price").text.strip()
        price = ''
    else:
        headline = s.find('div', class_="price").text.strip().split('£')
        title, price = headline[0], ', '.join(headline[1:])
        price = price.replace('£', '').replace(',', '')
    inventory_features = s.find_all('div', class_="inventory-features-item")
    make, transmission, drive, model, year, fuel_type, mileage, style = ['']*8
    for ft in inventory_features:
        h6 = ft.find('h6')
        if h6:
            if 'make' in h6.text.lower():
                make = ft.find('span').text.strip()
            elif 'transmission' in h6.text.lower():
                transmission = ft.find('span').text.strip()
            elif 'model' in h6.text.lower():
                model = ft.find('span').text.strip()
            elif 'year' in h6.text.lower():
                year = ft.find('span').text.strip().split('(')[0]
            elif 'style' in h6.text.lower():
                style = ft.find('span').text.strip()
            elif 'fuel' in h6.text.lower():
                fuel_type = ft.find('span').text.strip()
            elif 'drive' in h6.text.lower():
                drive = ft.find('span').text.strip()
            elif 'mileage' in h6.text.lower():
                mileage = ft.find('span').text.strip()
    try:
        description = s.find('div', class_="inventory-details-description").find('p').text.strip()
    except:
        description = ''
    brand = title.split(' ')[1]
    model = ' '.join(title.split(' ')[2:])
    car_data = {
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Make': make,
        'Year': year,
        'Fuel Type': fuel_type,
        'Transmission': transmission,
        'Mileage': mileage,
        'Type': style,
        'Description': description,
        'Drive': drive,
        'Status': o.get('Status'),
        'Link': o.get('Link'),
        'Provider': filename.upper()
    }
    images = [urljoin('http://www.dwcars.info/', img['src']) for img in s.find('div', class_="inventory-details-slide").find('div', class_="container-fluid").find_all('img')]
    for j, image in enumerate(images):
        car_data[f'Image {j+1}'] = image
    data_main[i] = car_data
    logging.info('{}/{} - {}'.format(i+1, len(data_main), title))


def get_links():
    r = ses.get('http://www.dwcars.info/inventory-list.html')
    s = BeautifulSoup(r.text, 'html.parser')

    for div in s.find('div', class_="row latest-car-items-active").contents:
        if div.find('a') and not isinstance(div, NavigableString):
            link = urljoin('http://www.dwcars.info/', div.find('a')['href'])
            price_soon = div.find('span', class_="pricesoon")
            price_new = div.find('span', class_="pricenew")
            if price_soon:
                status = price_soon.text
            elif price_new:
                if '£' in price_new.text:
                    status = ''
                else:
                    status = price_new.text
            else:
                if '£' not in div.find('span', class_="price").text:
                    status = div.find('span', class_="price").text
                else:
                    status = ''
            data_main.append({
                'Status': status,
                'Link': link,
            })
    for i in range(len(data_main)):
        try:
            get_data(i)
        except Exception as exc:
            print('Error on index: {}'.format(i))
            raise Exception(exc)

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
    get_links()
    save()

if __name__ == "__main__":
    main()
