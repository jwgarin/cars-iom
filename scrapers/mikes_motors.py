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
import asyncio

#raise Exception('Fix model data')
filename = 'mikes_motors'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.mikesmotors.im'
start_url = 'https://www.mikesmotors.im/search_page.php?location_id=1'
#driver = webdriver.Chrome()

class Specs:
    def __init__(self, s):
        self.s = s

    def get_specs(self, keyword):
        try:
            return self.s.find('span', class_="dt-spec-list__label", string=re.compile(keyword)).parent.text.replace(keyword.replace('\\', ''), '').strip()
        except:
            return ''

class Labels:
    def __init__(self, s):
        self.s = s

    def get_labels(self, keyword):
        try:
            return self.s.find('div', class_="list-label", string=re.compile(keyword)).parent.text.replace(keyword.replace('\\', ''), '').strip()
        except:
            return ''


def get_data(idx):
    o = data_main[idx]
    for _ in range(5):
        try:
            r = ses.get(o['Link'], timeout=20)
            if r.status_code == 200:
                break
        except:
            pass
    else:
        logger.error('Network Error - {}'.format(o['Link']))
        raise Exception
        
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    specs = Specs(s)
    labels = Labels(s)
    get_labels = labels.get_labels
    get_specs = specs.get_specs
    
    title = s.find('div', class_="vehicle-title-block__title").find('h1').text
    brand = title.split(' ')[0]
    model = title.split(' ')[1]
    images = [y for y in [a['href'] for a in s.find('div', class_="click-360-gallery__gallery").find_all('a', class_="rsImg") if a.get('href')] if '/ajax/standard_image' not in y]
    price = s.find('div', class_="vehicle-price__cash").text.replace('£', '').replace(',', '').replace('+VAT', '').strip()
    if price.isdecimal():
        price = int(price)
        status = ''
    else:
        status = price
        price = ''
    year = get_specs('Year')
    registration_num = get_specs('Registration')
    mileage = get_specs('Mileage')
    
    colour = get_specs('Colour')
    type_ = get_specs('Body Style')
    transmission = get_specs('Transmission')
    fuel_type = get_specs('Fuel Type')
    description = s.find('div', class_="dt-desctiption").text.replace('Read more', '').strip()
    length = get_labels('Length')
    width = get_labels('Width')
    height = get_labels('Height')
    if re.search(r'\d+mm', width):
        width = re.search(r'\d+mm', width).group()
    else:
        width = ''
    if re.search(r'\d+mm', height):
        height = re.search(r'\d+mm', height).group()
    else:
        height = ''
    if re.search(r'\d+mm', length):
        length = re.search(r'\d+mm', length).group()
    else:
        length = ''
    seat_num = get_labels('Number of seats')
    weight = get_labels('Gross vehicle weight') if get_labels('Gross vehicle weight') != 'kg' else ''
    engine_torque = get_labels('Engine torque \(RPM\)') + ' RPM' if  get_labels('Engine torque \(RPM\)') else ''
    engine_power = get_labels('Engine power \(BHP\)') + ' BHP' if get_labels('Engine power \(BHP\)') else ''
    engine_size = get_labels('CC').replace(',', '') + ' cc' if get_labels('CC') else ''
    if not engine_size:
        engine_size = get_specs('Engine Size').replace('ltr', 'L') if get_specs('Engine Size') else get_specs('Engine Size')
        if engine_size == 'L':
            engine_size = ''
    o.update({
        'Brand': brand,
        'Model': model,
        'Price': price,
        'Status': status,
        'Year': year,
        'Registration Number': registration_num,
        'Mileage': mileage,
        'Colour': colour,
        'Type': type_,
        'Transmission': transmission,
        'Fuel Type': fuel_type,
        'Description': description,
        'Length': length,
        'Width': width,
        'Number of Seats': seat_num,
        'Weight': weight,
        'Engine Torque': engine_torque,
        'Engine Power': engine_power,
        'Engine Size': engine_size,
    })
    for i, image in enumerate(images):
        o[f'Image {i+1}'] = image
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def get_links():
    url = start_url
    for _ in range(5):
        status_code = None
        try:
            r = ses.get(url, timeout=20)
            status_code = r.status_code
            if r.status_code == 200:
                break
        except:
            pass
    else:
        logger.error(f'Network Error - {status_code}')
        raise Exception
        
    print(url)
    s = BeautifulSoup(r.text, 'html.parser')
    cars_slot = [(urljoin(home_url, div.find('a', title="View Vehicle Details")['href']), div.find('div', class_="results-summary__title").text) for div in s.find('div', class_="results-vehicleresults grid-view").find_all('div', class_="listing")]
    for link, title in cars_slot:
        data_main.append({
            'Title': title,
            'Link': link,
            'Provider': 'Mike\'s Motors'
        })

    list_pages = [z for z in [urljoin(home_url, y.find('a')['href']) for y in [x for x in s.find('ol', class_="pagenavi").contents if isinstance(x, bs4.element.Tag)] if y.name == 'li' and not y.attrs.get('class') and y.find('a')] if 'javascript:void' not in z]
    for lp in list_pages:
        for _ in range(5):
            status_code = None
            try:
                r = ses.get(lp, timeout=20)
                status_code = r.status_code
                if r.status_code == 200:
                    break
            except:
                pass
        else:
            logger.error(f'Network Error - {status_code}')
            raise Exception
        print(lp)
        s = BeautifulSoup(r.text, 'html.parser')
        cars_slot = [(urljoin(home_url, div.find('a', title="View Vehicle Details")['href']), div.find('div', class_="results-summary__title").text) for div in s.find('div', class_="results-vehicleresults grid-view").find_all('div', class_="listing")]
        for link, title in cars_slot:
            data_main.append({
                'Title': title,
                'Link': link,
                'Provider': 'Mike\'s Motors'
            })
    #asyncio.run(iterate_data())
    for i in range(len(data_main)):
        get_data(i)
        #if i == 10:
        #    break

    unique_cols = []
    for d in data_main:
        for col in d.keys():
            if col not in unique_cols:
                unique_cols.append(col)

    for d in data_main:
        for col in unique_cols:
            if not d.get(col):
                d[col] = ''

async def cons_data(q):
    while True:
        idx = await q.get()
        asyncio.sleep(random.uniform(1.2, 1.5))
        try:
            await asyncio.get_event_loop().run_in_executor(None, get_data, idx)
        except Exception as exc:
            logger.error(exc)
        q.task_done()

async def iterate_data():
    q = asyncio.Queue()
    for i in range(len(data_main)):
        await q.put(i)
    cons = [asyncio.create_task(cons_data(q)) for _ in range(10)]
    await q.join()
    for c in cons:
        c.cancel()


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
