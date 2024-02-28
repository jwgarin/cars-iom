import requests
from bs4 import BeautifulSoup
import csv
import asyncio
import random
import functools
import logging
from custom_logs import custom_logs
import re
import bs4
from selenium import webdriver


scraper_name = filename ='athol'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
driver = None
data_main = None

def process_row(row):
    global driver, data_main
    link = row['Link']
    driver.get(link)
    try:
        r = requests.get(link)
        s = BeautifulSoup(r.text, 'html.parser')
    except:
        s = None
    try:
        color = s.find('span', class_="label", string=re.compile("Exterior Colour")).parent.find('span', class_="value__field").text
    except:
        color = ''
    row['Colour'] = color
    try:
        images = [x.get_attribute('src') for x in driver.find_elements('xpath', '//img[@class="big-image"]') if x.get_attribute('src').endswith('==')]
    except:
        images = None
    for i, image in enumerate(images):
        row[f'Image {i+1}'] = image
    try:
        title = s.find('h1', class_="featuredTitle first-word").text
        row['Title'] = title
    except:
        pass
    logging.info('-'.join(['ATHOL', row['Title'], color]))
    return row


def main():
    global driver, data_main
    driver = webdriver.Chrome()
    logging.info('ATHOL Scrape Initiate')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.athol.im/',
        'Content-Type': 'application/json',
        'Authorization': '3e826840-5fc2-11eb-94bf-77637b708bd3',
        'Origin': 'https://www.athol.im',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    params = {
        'uuid': 'b03ab890-5fc0-11eb-8723-bf1709c848d3',
    }
    page = 1
    cars = []
    while True:
        print('Collecting page: {}'.format(page))
        json_data = {
            'query': 'query { allVehicles: getAll (searchParams: {or: [{groupHash: ["50d72eb984745e1bca899a05a26d577f167b1b43"], condition: "New Offer"}, {groupHash: ["50d72eb984745e1bca899a05a26d577f167b1b43"]}]}, pagination: {currentPage: ' \
            + str(page) + ', pageSize: 12}, financesDataContext: {term: 48, annualMileage: 10000, percentageDeposit: 10}, sortParams: [{fieldName: currentPrice, direction: asc}]) { companyHash id condition mainImage images type registration { year date number } cap { id } status identifiers { stockId packId } externalUrl attentionGrabber manufacturer model variant odometer { value unit } engine { description } fuel { type typeEnglish } transmission { type } finances { payment deposit productName term productType annualMileage percentageDeposit description } colour { exterior exteriorGeneric exteriorGenericEnglish exteriorCode interior } bodyStyle price { current currencyCode previous vatIncluded isPoa } location { name hash details { departments { phoneNumber isDefault } } } groupHash franchiseHash custom pageViews vin isSharedStock productionYear } }',
        }

        response = requests.post( 
            url='https://production-api.search-api.netdirector.auto/api/vehicle-search',
            params=params,
            headers=headers,
            json=json_data,
        )
        data = response.json()['data']['allVehicles']
        if data:
            cars.extend(data)
        else:
            break
        page += 1
    #response = await asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.get, url='https://www.athol.im/wp-admin/admin-ajax.php', params=params, headers=headers))    
    data_main = []

    for car in cars:
        try:
            price = int(car['price']['current'])
        except:
            price = ''
        engine_size = re.search(r'^\d+\.\d+', car['variant']).group() if re.search(r'^\d+\.\d+', car['variant']) else ''
        if engine_size:
            engine_size += ' L'
        try:
            car_data = {
                'Title': '{} {} {}'.format(car['manufacturer'], car['model'], car['variant']),
                'Brand': car['manufacturer'],
                'Price': price,
                'Model': car['model'],
                'Year': car['registration']['year'],
                'Engine Size': engine_size,
                'Fuel Type': car['fuel']['type'],
                'Transmission': car['transmission']['type'],
                'Mileage': '{} {}'.format(car['odometer']['value'], car['odometer']['unit']),
                #'Description': car['introduction'],
                'Link': f'https://www.athol.im/used-cars/{car["id"]}-{car["manufacturer"].lower()}-{car["model"].lower()}-{car["variant"].lower()}/',
                'Type': car['bodyStyle'],
                'Colour': "",
                'Provider': 'Athol'
            }
        except Exception as exc:
            print(car)
            raise Exception(exc)
        #data_main.append(car_data)
        row = process_row(car_data)
        data_main.append(row)
        print(row)

    unique_cols = []
    for d in data_main:
        for col in d.keys():
            if col not in unique_cols:
                unique_cols.append(col)

    for d in data_main:
        for col in unique_cols:
            if not d.get(col):
                d[col] = ''

    with open(f'..\\csv_files\\{filename}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        usecols = list(data_main[0].keys())
        writer.writerow(usecols)
        writer = csv.DictWriter(f, fieldnames=usecols)
        for d in data_main:
            writer.writerow(d)
    driver.close()
    logging.info(f'{filename.upper()} - Process Done!')


if __name__ == "__main__":
    main()
    pass
