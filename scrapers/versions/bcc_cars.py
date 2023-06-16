import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString, Tag
from urllib.parse import urljoin
from selenium import webdriver
import re


filename = 'bcc_cars'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.bcccars.im'
#start_url = 'https://www.bcccars.im/index/showroom'
start_url = 'https://www.bcccars.im/usedcars'
#driver = webdriver.Chrome()

class GetProp:
    def __init__(self, s):
        self.s = s
        
    def get_prop(self, strong):
        cf = [y for y in [x for x in self.s.find('ul', class_="properties clearfix").contents if isinstance(x, Tag)] if y.name == 'li']
        for c in cf:
            if strong in c.text:
                return c.text.replace(strong, '').split(':')[1].strip()
        else:
            return ''

    def get_stat(self, tp):
        try:
            return self.s.find('span', class_="type", string=re.compile(tp)).parent.text.replace(tp, '').split(':')[1].strip()
        except:
            return ''

def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    s = BeautifulSoup(r.text, 'html.parser')
    prop = GetProp(s)
    title = s.find('div', class_="vi-inner vehicle-information").find('h2').text.strip()
    brand = [x for x in s.find('h1').strings][0].strip()
    model = [x for x in s.find('h1').strings][1].strip()
    try:
        price = [x for x in s.find('div', class_="details-price").strings if '£' in x][0].replace('£', '').replace(',', '').strip()
    except:
        price = ''
    try:
        dealer_phone = [x for x in s.find('div', class_="details-tel").strings if x.replace(' ', '').isdecimal()][0]
    except:
        dealer_phone = ''
    type_ = prop.get_prop('Body Type')
    transmission = prop.get_prop('Gearbox')
    year = prop.get_prop('Registered')
    fuel_type = prop.get_prop('Fuel Type')
    mileage = prop.get_prop('Mileage')
    engine_size = prop.get_prop('Engine Size') + ' cc'
    colour = prop.get_prop('Finished in')
    try:
        features = str([y for y in [x for x in [z for z in s.find_all('div', class_="accordion-inner") if z.find('h2', string='Vehicle Specification')][0].contents if isinstance(x, Tag)] if y.name != 'h2'][0])
    except:
        features = ''
    try:
        description = [y for y in [x for x in s.find('h2', string='Vehicle Description').next_siblings if isinstance(x, Tag)] if y.name == 'p'][0].text
    except:
        description = ''
    engine_power = prop.get_stat('Engine Power')
    engine_torque = prop.get_stat('Engine Torque')
    cylinders = prop.get_stat('Cylinders')
    top_speed = prop.get_stat('Top Speed')
    acceleration = prop.get_stat('Acceleration')
    combined_fuel_economy = prop.get_stat('\(combined\)')
    urban_fuel_economy = prop.get_stat('\(urban\)')
    extra_urban_fuel_economy = prop.get_stat('\(extra urban\)')
    co2_emission = prop.get_stat('CO2 Emission')
    length = prop.get_stat('Length')
    width = prop.get_stat('Width')
    height = prop.get_stat('Height')
    weight = prop.get_stat('Weight')
    euro_status = prop.get_stat('Euro Status')
    seats_num = prop.get_stat('Seats')
    braked = prop.get_stat('Towing Braked')
    unbraked = prop.get_stat('Towing Unbraked')
    min_kerb_weight = prop.get_stat('Min Kerb Weight')
    o.update({
        'Title': title,
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Dealer Phone': dealer_phone,
        'Type': type_,
        'Transmission': transmission,
        'Year': year,
        'Fuel Type': fuel_type,
        'Mileage': mileage,
        'Engine Size': engine_size,
        'Colour': colour,
        'Features': features,
        'Description': description,
        'Engine Power': engine_power,
        'Engine Torque': engine_torque,
        'Cylinders': cylinders,
        'Top Speed': top_speed,
        'Acceleration': acceleration,
        'Combined Fuel Economy': combined_fuel_economy,
        'Urban Fuel Economy': urban_fuel_economy,
        'Extra Urban Fuel Economy': extra_urban_fuel_economy,
        'CO2 Emission': co2_emission,
        'Length': length,
        'Width': width,
        'Height': height,
        'Weight': weight,
        'Euro Status': euro_status,
        'Number of Seats': seats_num,
        'Braked Weight': braked,
        'Unbraked Weight': unbraked,
        'Min Kerb Weight': min_kerb_weight
    })
    try:
        images = [urljoin(home_url, x['src']) for x in s.find('div', class_="carousel-inner").find_all('img', id=re.compile('mainimage-'))]
    except:
        images = []
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    while True:
        logging.info(f'{filename.upper()} - Collecting URLS - {url}')
        r = ses.get(url)
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = s.find('div', class_="vehicle-results-append").find_all('div', class_="us-result-grid flexi-height_child radius")
        for div in cars_slot:
            try:
                link = urljoin(home_url, div.find('div', class_="vehicle-name").find('a')['href'])
            except Exception as exc:
                logger.warning(exc)
                continue
            data_main.append({
                'Link': link,
                'Provider': 'BCC Cars'
            })
        try:
            next_page = urljoin(home_url, s.find('a', string=re.compile('Next'))['href'])
            url = next_page
        except:
            break
        

    for i in range(len(data_main)):
        try:
            get_data(i)
        except Exception as exc:
            print('{} - {}'.format(data_main[i]['Link'], exc))

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
