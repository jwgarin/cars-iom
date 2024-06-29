import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
import re
from selenium.webdriver.chrome.service import Service
from chromedriver_binary import chromedriver_filename

filename = 'franklins'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.franklins.co.im'
driver = webdriver.Chrome(service=Service(chromedriver_filename))


def get_data(idx):
    o = data_main[idx]
    #r = ses.get(o['Link'])
    driver.get(o['Link'])
    html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(html, 'html.parser')
    try:
        #images = s.find('section', id="lrgImages").find('div', class_="slick-track").find_all('div', id="image")
        images = s.find('div', class_="slick-list draggable").find_all('figure', itemprop="associatedMedia")
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
    specification_contents = s.find_all('span', class_="spec-vaule")
    specs_dict = {}
    for sv in specification_contents:
        spec_value = sv.text.strip()
        spec_key = sv.parent.find('span').text.strip()
        specs_dict[spec_key] = spec_value
    feature_box_contents = s.find('div', class_="vehicle_details_right").find_all('span', class_="feature-box-title")
    feature_dict = {}
    for fv in feature_box_contents:
        spec_key = fv.text
        spec_value = fv.parent.find('span', class_="feature-box-text").text.strip()
        feature_dict[spec_key] = spec_value
    # Save Data
    
    o.update({
        **specs_dict,
        **feature_dict
    })
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))

def get_links():
    r = ses.get('https://www.franklins.co.im/used/cars/port-erin/')
    s = BeautifulSoup(r.text, 'html.parser')

    for div in s.find('div', id="load_stock_data").contents:
        if isinstance(div, NavigableString):
            continue
        if div.name != 'div':
            continue
        c = ' '.join(div.attrs.get('class', []))
        if 'on_forecourt' in c:
            a = div.find('a', string='VIEW DETAILS')
            title = re.sub('\s+', ' ', ';'.join(x for x in div.find('div', class_="view-car-details").strings if x.strip() != ''))
            name = title.split(';')[0].strip()
            add_info = title.split(';')[1].strip()
            link = urljoin('https://www.franklins.co.im/', a['href'])
            try:
                price = int(re.sub(r'cash price', '', div.find('div', class_="car-actual-price").text.replace('£', '').replace(',', ''), flags=re.I))
            except:
                price = ''
            transmission, style, fuel_type, engine_size, mileage, dealer_phone, = ['']*6
            try:
                transmission = div.find('li', title="Transmission").text
            except:
                pass
            try:
                fuel_type = div.find('li', title="Fuel").text
            except:
                pass
            try:
                engine_size = div.find('li', title='CC').text
            except:
                pass
            try:
                mileage = div.find('li', title='Miles').text
            except:
                pass
            dealer_phone = s.find('div', class_="callus").find('a')['href'].strip('tel:')
            try:
                year = re.search(r'20\d+', title).group()
                if not year.isdecimal():
                    year = ''
            except:
                year = ''
            try:
                brand = re.sub(' +', ' ', ' '.join(title.split(';')[0:-1]))
            except:
                brand = ''
            try:
                model = title.split(';')[-1]
            except:
                model = ''

            data_main.append({
                'Title': re.sub(' +', ' ', title.replace(';', ' ')),
                'Brand': brand,
                'Price': price,
                'Model': model,
                'Year': year,
                'Engine Size': engine_size,
                'Fuel Type': fuel_type,
                'Transmission': transmission,
                'Mileage': mileage,
                'Dealer Phone': dealer_phone,
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
