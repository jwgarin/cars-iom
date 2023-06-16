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
        #cf = [y for y in [x for x in self.s.find('div', class_="us-detailsOne-spec-highlights").contents if isinstance(x, Tag)] if y.name == 'li']
        cf = [y for y in [x for x in self.s.find_all('div', class_=re.compile('us-detailsOne-spec-item')) if isinstance(x, Tag)]]
        for c in cf:
            if strong in c.strings:
                return list(c.strings)[-1]
        else:
            return ''

    def get_stat(self, tp):
        try:
            return self.s.find('span', class_="tech-spec-title", string=re.compile(tp)).parent.text.replace(tp, '').split(':')[1].strip()
        except:
            try:
                return self.s.find('span', class_="tech-spec-title", string=re.compile(tp)).parent.text.replace(tp, '').strip()
            except:
                return ''

def get_images(car_id, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': url,
        # 'Cookie': 'AWSID=68tkergg3fvn1oua4bpetf25n4; show_popup_cookie=no; cookie-options=%7B%22ck-functional%22%3Atrue%2C%22ck-targeting%22%3Atrue%7D; term=60; deposit=10%25; mileage=10000',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    params = {
        'vid': car_id,
        'mimetypes': 'all',
        'preset': '0',
    }
    response = requests.get('https://www.bcccars.im/media/mediagallery', params=params, headers=headers)
    j = response.json()
    gallery = [urljoin(home_url, o.get('thumb')) for o in j['gallery'] if o.get('thumb')]
    return gallery

def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    car_id = o['Link'].split('/')[-1]
    s = BeautifulSoup(r.text, 'html.parser')
    prop = GetProp(s)
    #title = s.find('div', class_="vi-inner vehicle-information").find('h2').text.strip()
    title = ' '.join(h.strip() for h in s.find('h1', class_=re.compile("us-details-title")).strings).strip()
    brand = [x.strip() for x in s.find('h1').strings if x.strip() != ''][0].strip()
    model = [x.strip() for x in s.find('h1').strings if x.strip() != ''][1].strip()
    try:
        price = [x for x in s.find('div', class_=re.compile("us-details-price")).strings if '£' in x][0].replace('£', '').replace(',', '').strip()
    except:
        price = ''
    try:
        dealer_phone = [x for x in s.find('div', class_=re.compile("details-tel")).strings if x.replace(' ', '').isdecimal()][0]
    except:
        dealer_phone = ''
    type_ = prop.get_prop('Bodystyle')
    transmission = prop.get_prop('Gearbox')
    year = prop.get_prop('Registered')
    fuel_type = prop.get_prop('Fuel Type')
    mileage = prop.get_prop('Mileage')
    engine_size = prop.get_prop('Engine')
    colour = prop.get_prop('Finished in')
    try:
        features = str([y for y in [x for x in [z for z in s.find_all('div', class_="vehicle-details-list") if z.find('h2', string='Vehicle Specification')][0].contents if isinstance(x, Tag)] if y.name != 'h2'][1])
        #features = s.find('div', id="tabs-1")
        
    except:
        features = ''
    try:
        description = [y for y in [x for x in s.find('h2', string='Vehicle Description').next_siblings if isinstance(x, Tag)] if y.name == 'p'][0].text
        raise Exception
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
        #images = [urljoin(home_url, x['src']) for x in s.find('div', class_="carousel-inner").find_all('img', id=re.compile('mainimage-'))]
        images = get_images(car_id, o['Link'])
    except Exception as exc:
        logging.warning('No image - {}'.format(o['Link']))
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
                link = urljoin(home_url, div.find('div', class_="us-result-name").find('a')['href'])
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
