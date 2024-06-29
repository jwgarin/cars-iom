import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re


filename = 'mylchreests'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'http://www.mylchreests.com'
start_url = 'http://www.mylchreests.com/usedcars'
#driver = webdriver.Chrome()

class SVG:
    def __init__(self, s):
        self.s = s
    def find_svg(self, keyword):
        try:
            return self.s.find('i', attrs={"data-feather": keyword}).parent.next_sibling.next_sibling.text
        except:
            return ''
        

def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    
    s = BeautifulSoup(r.text, 'html.parser')
    svg = SVG(s)
    find_svg = svg.find_svg
    title = s.find('h5').text.strip()
    if title.count('-') > 2:
        title = title.replace('-', ' ').title()
        
    title_comp = title.split(' ')
    if title_comp[0].isdecimal():
        year = title_comp[0]
        brand = title_comp[1]
        model = ' '.join(title.split(' ')[2:]).title().split('(Ref')[0].strip()
    else:
        year = ''
        brand = title_comp[0]
        model = ' '.join(title.split(' ')[1:]).title().split('(')[0].strip()
    try:
        registration = s.find('p', class_="greys-4").find('strong').text
    except:
        registration = ''
    colour, transmission, doors, mileage, engine_size, fuel_type, co2_emission = ['']*7
    colour = find_svg('droplet')
    transmission = find_svg('gearbox')
    try:
        doors = find_svg('cardoor').split('Door')[0].strip()
        doors = doors if doors.isdecimal() else ''
    except:
        pass
    mileage = find_svg('speed')
    if not mileage.isdecimal():
        mileage = ''
    fuel_type = find_svg('fuel')
    engine_size = find_svg('engine') + ' cc' if 'l' not in find_svg('engine').lower() and '.' not in find_svg('engine') else find_svg('engine')
    if '-' in engine_size:
        engine_size = engine_size.split('-')[1].strip() + ' L'
    try:
        co2_emission = find_svg('eco').split('=')[1].strip()
    except:
        co2_emission = find_svg('eco')
    if not co2_emission.isdecimal():
        co2_emission = ''
    
    price = s.find('h4', class_="m-0 reds-1").text.replace('£', '').replace(',', '').strip()
    if '.' in price:
        price = price.split('.')[0]
    image = s.find('img', class_="rounded")['src']
    o.update({
        'Title': title,
        'Brand': brand,
        'Year': year,
        'Brand': brand,
        'Model': model,
        'Registration': registration,
        'Colour': colour,
        'Transmission': transmission,
        'Doors': doors,
        'Mileage': mileage,
        'Fuel Type': fuel_type,
        'Engine Size': engine_size,
        'CO2 Emission': co2_emission,
        'Price': price,
        'Image 1': image
    })
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    r = ses.get(start_url)
    s = BeautifulSoup(r.text, 'html.parser')
    logos = [x.find('a')['href'] for x in s.find_all('div', class_="col-lg-4 col-md-6 col-sm-6 mb-4") if x.find('a')]
    if not logos:
        logger.error('Logos Changed')
        raise Exception
    for logo in logos:
        r1 = ses.get(logo)
        s1 = BeautifulSoup(r1.text, 'html.parser')
        try:
            used_cars = [div.find('a')['href'] for div in s1.find_all('div', id="usedcar") if div.find('a')]
        except Exception as exc:
            logging.warning('No results found - {}'.format(logo))
            continue
        for used_car in used_cars:
            link = used_car
            data_main.append({
                'Link': link,
                'Provider': filename.title()
            })

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
