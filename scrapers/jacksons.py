import requests
from bs4 import BeautifulSoup
import csv
import logging
from custom_logs import custom_logs
from bs4.element import NavigableString
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import time
import bs4


filename = 'jacksons'
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs(filename.upper(), filename)
ses = requests.Session()
data_main = []
home_url = 'https://www.jacksons.im'
start_url = 'https://www.jacksons.im/used/?stocktype=All&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=1'
#driver = webdriver.Chrome()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json;charset=utf-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://www.jacksons.im',
    'Connection': 'keep-alive',
    'Referer': 'https://www.jacksons.im/used/?stocktype=All&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=1',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 'gptr4683=1; TawkConnectionTime=0; twk_idm_key=U4omd_qOZafK2pPhtDebs; twk_uuid_583dbc4fde6cd808f31c3cd8=%7B%22uuid%22%3A%221.485CHxrtAVllClkGcyAcFcwVIKBNyBhl0g7XAUzYbBFMwqKX54G151yV3cMGZdLgbaRZscklCpNxyXWfFfpFaNqCKskoUu25igAayhDWSm8VM76ppa4UntjWlznopqQNVwhrku2xZ3SRlKH%22%2C%22version%22%3A3%2C%22domain%22%3A%22jacksons.im%22%2C%22ts%22%3A1659242358857%7D; cookieconsent_status=dismiss; ASP.NET_SessionId=re255dak22yszl3fopvyu2ha; __RequestVerificationToken=CZq9O6x3GJ4ByyXjgukXqPjjN6xK7QPJ4LHVHG2FHmR-0u5KJ3__BVTG0-YgGOhKWQTe19kRz4y8lgTaEvoHwr64wJM-qg8GuSQerHc1sCw1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}
cookies = None
idx = 0
total = None

def get_cookies():
    logging.info('Getting Cookies')
    options = Options()
    #options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(start_url)
    for _ in range(15):
        time.sleep(1)
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        if len(cookies) == 5:
            break
    else:
        logger.error('Cookies not Found!')
        raise Exception('Cookies not Found!')
    driver.close()
    logging.info('Cookies Collected')


def get_data(idx):
    o = data_main[idx]
    r = ses.get(o['Link'])
    #driver.get(o['Link'])
    #html = driver.find_element('xpath', '//html').get_attribute('innerHTML')
    s = BeautifulSoup(r.text, 'html.parser')
    data_main[idx] = o
    logging.info('{}/{} - {}'.format(idx + 1, len(data_main), o['Title']))


def load_json(page: int):
    json_data = {
        'model': {
            'stocktype': 'All',
            'isbikes': False,
            'make': '',
            'model': '',
            'minprice': 0,
            'maxprice': 0,
            'gear': '',
            'door': '',
            'cartype': '',
            'location': '',
            'segment': 'iom',
            'sortorder': 4,
            'pagesize': 24,
            'page': page,
        },
    }
    response = requests.post('https://www.jacksons.im/umbraco/surface/Search/Find', cookies=cookies, headers=headers, json=json_data)
    j = response.json()
    return j

def get_images(o):
    link = o['Link']
    try:
        r = ses.get(link)
        s = BeautifulSoup(r.text, 'html.parser')
        images = [
            div.find('img', class_="irc")['src'] for div in
            [
                x for x in s.find('div', class_="car-details-carousel").contents
                if isinstance(x, bs4.element.Tag)
            ] if div.find('img', class_="irc")
        ]
        for i, image in enumerate(images):
            o['Image {}'.format(i+1)] = image
        return o
    except Exception as exc:
        logger.warning('Image Error - {} - {}'.format(link, exc))
        return o


def get_data(j):
    global idx
    vehicles = j.get('vehicles')
    for v in vehicles:
        stock_num = v.get('stockbookNumber', '')
        brand = v.get('webFranchise', '')
        model = v.get('webModel', '')
        description = v.get('webVehicleDescription', '')
        doors = v.get('webNumberofDoors', '')
        colour = v.get('webColour', '')
        trim = v.get('webTrim', '')
        transmission = v.get('webNumberOfGears', '')
        fuel_type = v.get('webFuelType', '')
        engine_size = str(v.get('webCCBHP', '')) + ' cc' if v.get('webCCBHP', '') else ''
        features = ', '.join(v.get('webSpecifications', '').split(';'))
        mileage = v.get('webMileage', '')
        year = v.get('regYear', '')
        price = v.get('webSellingPrice', '')
        discount_price = v.get('discountPrice', '')
        type_ = v.get('webVehicleType', '')
        try:
            purchased_date = v.get('dateOfPurchase', '').split('T')[0]
        except:
            purchased_date = ''
        link = urljoin(home_url, v.get('url')) if v.get('url') else ''
        dealer_phone = v.get('dealerPhone', '')
        car_data = o = {
            'Provider': 'Jacksons',
            'Title': model + ' ' + brand,
            'Brand': brand,
            'Model': model,
            'Price': price,
            'Discounted Price': discount_price,
            'Purchased Date': purchased_date,
            'Colour': colour,
            'Doors': doors,
            'Description': description,
            'Trim': trim,
            'Transmission': transmission,
            'Fuel Type': fuel_type,
            'Engine Size': engine_size,
            'Features': features,
            'Mileage': mileage,
            'Year': year,
            'Stock Type': type_,
            'Stock Number': stock_num,
            'Dealer Phone': dealer_phone,
            'Link': link
        }
        car_data = get_images(o)
        data_main.append(car_data)
        idx += 1
        logging.info('{}/{} - {}'.format(idx, total, brand + ' ' + model))


def get_links():
    global total
    start_json = sj = load_json(1)
    total_pages = sj.get('pager', {}).get('totalPages')
    total = sj.get('pager', {}).get('totalItems')
    if not total_pages:
        err = 'Total pages not found!'
        logger.error(err)
        raise Exception(err)
    get_data(sj)
    for i in range(2, total_pages + 1):
        j = load_json(i)
        get_data(j)

    #for i in range(len(data_main)):
    #    get_data(i)

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
