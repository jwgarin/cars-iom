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


filename = 'swift_motors'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'http://www.swiftmotors.net'
start_url = 'http://www.swiftmotors.net/search/'
#driver = webdriver.Chrome()


class SpecFull:
    def __init__(self, s):
        self.s = s

    def get_spec(self, keyword):
        try:
            return self.s.find('table', class_="spec full").find('td', string=re.compile(keyword)).parent.text.replace(keyword, '').strip()
        except Exception as exc:
            print(exc)
            return ''



def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    s = BeautifulSoup(r.text, 'html.parser')
    sf = SpecFull(s)
    get_spec = sf.get_spec
    title = s.find('h1', class_="vehicle-title").text
    title_comp = re.sub('\(\d+\)', '', title).replace('  ', ' ').split(' ')
    year = ''
    if title_comp[0].isdecimal():
        year = title_comp[0]
    if title_comp[1] == 'Land':
        brand = 'Land Rover'
        model = ' '.join(title_comp[3:])
    else:
        brand = title_comp[1]
        model = ' '.join(title_comp[2:])
    try:
        price_raw = s.find('span', class_="vehicle-price").text.replace('£', '').replace(',', '')
        if 'Save' in price_raw:
            price_raw = price_raw.split('Save')[0].strip()
        price = int(price_raw)
    except:
        price = ''
    try:
        mileage = get_spec('Mileage') + ' Miles' if 'Miles' not in get_spec('Mileage') else get_spec('Mileage')
        if mileage.strip() == 'Miles':
            mileage = ''
    except:
        mileage = ''
    fuel_type = get_spec('Fuel Type')
    engine_size = get_spec('Engine Size')
    transmission = get_spec('Transmission')
    registration = get_spec('Reg Date')
    registration_number = get_spec('Registration')
    type_ = get_spec('Body Style')
    colour = get_spec('Colour')
    doors = get_spec('No Doors')
    try:
        description = s.find('li', id="Description").text
    except:
        description = ''
    images = [li.find('a')['href'] for li in [content for content in s.find('ul', class_="vehicle-thumbs cf").contents if isinstance(content, bs4.element.Tag)] if li.find('a')]
    for i, image in enumerate(images):
        o['Image {}'.format(i+1)] = image
    o.update({
        'Title': title,
        'Year': year,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Mileage': mileage,
        'Fuel Type': fuel_type,
        'Engine Size': engine_size,
        'Transmission': transmission,
        'Registration': registration,
        'Registration Number': registration_number,
        'Type': type_,
        'Colour': colour,
        'Doors': doors,
        'Description': description,
    })
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    i = 1
    while True:
        r = ses.get(url)
        
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = [y for y in [x for x in s.find('ul', class_="showroom sh-standard").contents if isinstance(x, bs4.element.Tag)] if y.name == 'li']
        if not cars_slot:
            break
        logging.info(url)
        for div in cars_slot:
            link = div.find('a', class_="cf title-link")['href']
            data_main.append({
                'Link': link,
                'Provider': filename.title().replace('_', ' ')
            })
        i += 5
        url = start_url + '?startrow=' + str(i)

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
    
    
