import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re


filename = 'franklins'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.franklins.co.im'
driver = webdriver.Chrome()


def get_data(idx):
    o = data_main[idx]
    #r = ses.get(o['Link'])
    driver.get(o['Link'])
    html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(html, 'html.parser')
    try:
        images = s.find('section', id="lrgImages").find('div', class_="slick-track").find_all('div', id="image")
    except:
        images = []
    image_list = []
    for image in images:
        try:
            image_list.append(urljoin(home_url, image.find('img')['src']))
        except:
            pass
    for i, img in enumerate(image_list):
        o[f'Image {i+1}'] = img

    try:
        top_speed = s.find('strong', string=re.compile('Top Speed')).parent.text.split(':')[1].strip()
    except:
        top_speed = ''
    try:
        acceleration = s.find('strong', string=re.compile('Acceleration')).parent.text.split(':')[1].strip()
    except:
        acceleration = ''
    try:
        engine_power = s.find('strong', string=re.compile('Engine Power')).parent.text.split(':')[1].strip()
    except:
        engine_power = ''
    try:
        engine_torque = s.find('strong', string=re.compile('Engine Torque')).parent.text.split(':')[1].strip()
    except:
        engine_torque = ''
    try:
        economy = s.find('strong', string=re.compile('Economy')).parent.text.split(':')[1].strip()
    except:
        economy = ''
    try:
        driven_wheels = s.find('strong', string=re.compile('Driven Wheels')).parent.text.split(':')[1].strip()
    except:
        driven_wheels = ''
    try:
        co2_emission = s.find('div', class_="il-co2-value").text.strip()
    except:
        co2_emission = ''
    try:
        combined = s.find('strong', string=re.compile('Combined')).parent.text.split(' ')[1].strip()
    except:
        combined = ''
    try:
        urban = s.find('strong', string=re.compile('Urban')).parent.text.split(' ')[1].strip()
    except:
        urban = ''
    try:
        height = s.find('strong', string=re.compile('Height')).parent.text.split(':')[1].strip()
    except:
        height = ''
    try:
        width = s.find('strong', string=re.compile('Width')).parent.text.split(':')[1].strip()
    except:
        width = ''
    try:
        seat_num = s.find('strong', string=re.compile('Seats')).parent.text.split(':')[1].strip()
    except:
        seat_num = ''
    try:
        length = s.find('strong', string=re.compile('Length')).parent.text.split(':')[1].strip()
    except:
        length = ''
    try:
        doors = s.find('strong', string=re.compile('Doors')).parent.text.split(':')[1].strip()
    except:
        doors = ''
    try:
        braked = s.find('strong', string=re.compile('Braked')).parent.text.split(':')[1].strip()
    except:
        braked = ''
    try:
        unbraked = s.find('strong', string=re.compile('Unbraked')).parent.text.split(':')[1].strip()
    except:
        unbraked = ''
    try:
        mkw = s.find('strong', string=re.compile('Min Kerb Weight')).parent.text.split(':')[1].strip()
    except:
        mkw = ''
    try:
        purchased_date = s.find('span', class_='awicon awicon-calendar icon').parent.find('span', class_="value").text.strip()
    except:
        purchased_date = ''
    try:
        colour = s.find('span', class_='awicon awicon-paint icon').parent.find('span', class_="value").text.strip()
    except:
        colour = ''
    try:
        seats_material = s.find('span', class_='awicon awicon-seats icon').parent.find('span', class_="value").text.strip()
    except:
        seats_material = ''
    # Save Data
    o.update({
        'Top Speed': top_speed,
        'Acceleration': acceleration,
        'Colour': colour,
        'Seats Material': seats_material,
        'Doors': doors,
        'CO2 Emission': co2_emission,
        'Engine Power': engine_power,
        'Engine Torque': engine_torque,
        'Economy': economy,
        'Driven Wheels': driven_wheels,
        'Purchased Date': purchased_date,
        'Height': height,
        'Width': width,
        'Number of Seats': seat_num,
        'Length': length,
        'Braked Weight': braked,
        'Unbraked Weight': unbraked,
        'Min Kerb Weight': mkw,
        'Combined Fuel Economy': combined,
        'Urban Fuel Economy': urban,
    })
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))

def get_links():
    r = ses.get('https://www.franklins.co.im/showroom')
    s = BeautifulSoup(r.text, 'html.parser')

    for div in s.find('div', class_="vehicle-results-append").contents:
        if isinstance(div, NavigableString):
            continue
        c = ''.join(div.attrs.get('class', []))
        if 'result' in c and 'finance' in c:
            a = div.find('div', class_="vehicle-name").find('a')
            title = a.text.strip().replace('\n', ';')
            name = title.split(';')[0]
            add_info = title.split(';')[1]
            link = urljoin('https://www.franklins.co.im/', a['href'])
            try:
                description = div.find('div', class_="vehicle-name").find('div', class_="promotion").text.strip()
            except:
                description = ''
            description = add_info + '\n' + description
            try:
                price = int(div.find('div', class_="Price").text.replace('£', '').replace(',', ''))
            except:
                price = ''
            results_left = div.find('div', class_="result-left").contents
            results_left = [x.text.strip() for x in results_left if str(x).strip() != '']
            results_contact = div.find('div', class_="result-contact").contents
            results_contact = [x.text.strip() for x in results_contact if str(x).strip() != '']
            transmission, style, fuel_type, engine_size, mileage, dealer_phone, location = ['']*7
            for rl in results_left:
                try:
                    rld = rl.split('\n')[1].strip()
                except:
                    continue
                if 'Gearbox' in rl:
                    transmission = rld
                elif 'Bodystyle' in rl:
                    style = rld
                elif 'Fuel Type' in rl:
                    fuel_type = rld
                elif 'Engine Size' in rl:
                    engine_size = rld + ' cc'
                elif 'Mileage' in rl:
                    mileage = rld
                else:
                    pass
            for rc in results_contact:
                try:
                    rcd = rc.split(':')[1].strip().strip('-')
                except:
                    continue
                if 'Location' in rc:
                    location = rcd
                elif 'Tel' in rc:
                    dealer_phone = rcd
                else:
                    pass
            try:
                year = name.split(' ')[0]
                if not year.isdecimal():
                    year = ''
            except:
                year = ''
            try:
                brand = name.split(' ')[1]
            except:
                brand = ''
            try:
                model = name.split(' ')[2]
            except:
                model = ''

            data_main.append({
                'Title': name,
                'Brand': brand,
                'Price': price,
                'Model': model,
                'Year': year,
                'Engine Size': engine_size,
                'Fuel Type': fuel_type,
                'Transmission': transmission,
                'Mileage': mileage,
                'Dealer Phone': dealer_phone,
                'Location': location,
                'Top Speed': '',
                'Acceleration': '',
                'Colour': '',
                'Seats Material': '',
                'Doors': '',
                'CO2 Emission': '',
                'Engine Power': '',
                'Engine Torque': '',
                'Economy': '',
                'Driven Wheels': '',
                'Purchased Date': '',
                'Height': '',
                'Width': '',
                'Number of Seats': '',
                'Length': '',
                'Braked Weight': '',
                'Unbraked Weight': '',
                'Min Kerb Weight': '',
                'Combined Fuel Economy': '',
                'Urban Fuel Economy': '',
                'Link': link,
                'Provider': 'Franklins'
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
    get_links()
    save()
    driver.close()

if __name__ == "__main__":
    main()
