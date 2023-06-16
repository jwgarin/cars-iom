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
import os


filename = 'manx_carstore'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.manxcarstore.com/'
start_url = 'https://www.manxcarstore.com/stock/used-cars-in-isle-of-man?branch='
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('span', class_='title', string=re.compile(keyword)).parent.text.replace(keyword.replace('\\', ''), '').split(':')[1].strip()
        except:
            pass
        try:
            return self.s.find('span', class_='title', string=re.compile(keyword)).parent.text.replace(keyword.replace('\\', ''), '').replace('\n', ' ').replace('  ', ' ').strip()
        except:
            pass
        return ''


def get_data(idx):
    o = data_main[idx]
    filename = o['Link'].replace('https://www.manxcarstore.com/vehicle/', '')
    with open(os.path.join(r'G:\Projects\iom_cars\ref_file\manx_carstore', filename + '.htm'), encoding='utf-8') as f:
        r = f.read()
    s = BeautifulSoup(r, 'html.parser')
    spx = Specs(s)
    get_specs = spx.get_specs
    title = ' '.join([s.find('h1', attrs={'data-v-makemodel': True}).text.strip(), s.find('h2', attrs={'data-v-version': True}).text.strip()])
    title_comp = title.split(' ')
    if 'rover' in title.lower():
        brand = ' '.join(title_comp[:2])
        model = ' '.join(title_comp[2:])
    else:
        brand = title_comp[0]
        model = ' '.join(title_comp[1:])
    images = []
    try:
        images = [div.find('a', class_="swipebox")['href'] for div in s.find('div', class_="owl-stage").find_all('div', class_="owl-item cloned") if div.find('a', class_="swipebox")]
    except:
        pass
    if not images:
        try:
            images = [div.find('a', class_="swipebox accent-alt")['href'] for div in s.find('div', class_="owl-stage").find_all('div', class_="owl-item cloned") if div.find('a', class_="swipebox accent-alt")]
        except:
            images = []
    try:
        status = s.find('span', class_="Sold").text
    except:
        status = ''
    if not status:
        try:
            status = s.find('span', class_="Reserved").text
        except:
            status = ''
    try:
        price = s.find('span', attrs={'data-v-displayprice':True}).text.replace('£', '').replace(',', '').strip()
        if price.isdecimal():
            price = int(price)
    except:
        price = ''
    try:
        features = s.find('p', attrs={'data-v-text': True}).text
    except:
        features = ''
    mileage = get_specs('Odometer')
    transmission = get_specs('Transmission')
    type_ = get_specs('Body')
    colour = get_specs('Colour')
    fuel_type = get_specs('Fuel Type')
    year = get_specs('Year').split('(')[0].strip()
    engine_size = get_specs('Engine Size').replace('L', '').replace('CC', '').replace('cc', '')
    try:
        if float(engine_size) > 20:
            engine_size = f'{int(float(engine_size))} cc'
        else:
            engine_size = f'{int(float(engine_size))} L'
    except:
        pass
    doors = get_specs('Doors')
    urban = get_specs('Urban')
    extra_urban = get_specs('Extra Urban')
    combined = get_specs('Combined')
    top_speed = get_specs('Top Speed')
    engine_power = get_specs('Max Power')
    engine_torque = get_specs('Max Torque')
    cylinders = get_specs('Cylinders')
    height = get_specs('ht.')
    width = get_specs('Width')
    length = get_specs('Length')
    seat_num = get_specs('Seats')
    try:
        braked = s.find('small', string=re.compile('Braked')).parent.parent.text.replace('Towing Weight (Braked)', '').strip()
    except:
        braked = ''
    try:
        unbraked = s.find('small', string=re.compile('Unbraked')).parent.parent.text.replace('Towing Weight (Unbraked)', '').strip()
    except:
        unbraked = ''
    try:
        co2_emission = s.find('sub', string=re.compile('2')).parent.parent.text.replace('\n', ' ').replace('Co2 Emissions', '').strip()
    except:
        co2_emission = ''
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Status': status,
        'Price': price,
        'Features': features,
        'Mileage': mileage,
        'Transmission': transmission,
        'Type': type_,
        'Colour': colour,
        'Fuel Type': fuel_type,
        'Year': year,
        'Engine Size': engine_size,
        'Doors': doors,
        'Urban Fuel Economy': urban if urban != 'mpg' else '',
        'Extra Urban Fuel Economy': extra_urban if extra_urban != 'mpg' else '',
        'Combined Fuel Economy': combined if combined != 'mpg' else '',
        'Top Speed': top_speed if top_speed != 'mph' else '',
        'Engine Power': engine_power if engine_power != 'bhp' else '',
        'Engine Torque': engine_torque if engine_torque != 'lb-ft' else '',
        'Cylinders': cylinders,
        'Height': height,
        'Width': width,
        'Length': length,
        'Number of Seats': seat_num,
        'Braked Weight': braked,
        'Unbraked Weight': unbraked,
        'CO2 Emission': co2_emission,
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    #r = ses.get(start_url)
    #driver.get(start_url)
    
    #s = BeautifulSoup(r.text, 'html.parser')
    cars_slot = [file for file in os.listdir(r'G:\Projects\iom_cars\ref_file\manx_carstore') if '.htm' in file]
    
    for file in cars_slot:
        link = urljoin('https://www.manxcarstore.com/vehicle/', os.path.basename(file)).replace('.htm', '')
        data_main.append({
            'Link': link,
            'Provider': 'MANX Carstore'
        })

    for i in range(len(data_main)):
        try:
            get_data(i)
        except Exception as exc:
            logger.error('{} - {}'.format(data_main[i]['Link'], exc))
            raise Exception

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
