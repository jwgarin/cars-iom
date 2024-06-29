import bs4
import re
import requests
from seleniumwire import webdriver
import time
import logging
from custom_logs import custom_logs
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import csv

logger_sw = logging.getLogger('seleniumwire')
logger_sw.setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s ")
logger = custom_logs('MOTOR-MALL', 'motor_mall')


class MotorMall:
    """Scrape Motormall"""
    list_page = 'https://www.motor-mall.im/used/?stocktype=Stock&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=1'
    def __init__(self):
        self.home_url = 'https://www.motor-mall.im'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json;charset=utf-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.motor-mall.im',
            'Connection': 'keep-alive',
            'Referer': 'https://www.motor-mall.im/used/?stocktype=Stock&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=5',
            # Requests sorts cookies= alphabetically
            # 'Cookie': 'TawkConnectionTime=0; twk_idm_key=eKqDm2SXFGfSLJZzbns8L; twk_uuid_583dbc4fde6cd808f31c3cd8=%7B%22uuid%22%3A%221.18PwkMtTtDJTF1thiEsz2X60UUWCPY4iW02NlPfmWTun3K5gzxZOlxkIIhw3dHc6NiSV71fkTBI7uoDiHVUR3AixE9IhR1V7uZdOzjH2LcO59i84WbumiexpomCzw8kksipdHOT7MwalM0A761%22%2C%22version%22%3A3%2C%22domain%22%3A%22motor-mall.im%22%2C%22ts%22%3A1658844407189%7D; cookieconsent_status=dismiss',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
        }
        self.cookies_raw = None
        self.cookies = None
        self.driver = None
        self.data_main = None

    def get_cookies(self):
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.get(self.list_page)
        for _ in range(120):
            self.cookies_raw = None
            self.cookies_raw = {c['name']: c['value'] for c in self.driver.get_cookies()}
            if any(['twk_uuid' in key for key in self.cookies_raw.keys()]):
                break
            time.sleep(0.5)
        else:
            logger.error('Cookies Failed')
            raise Exception('Cookies Failed')
        self.cookies = {}
        for key in self.cookies_raw:
            if key in ['TawkConnectionTime', 'twk_idm_key', 'twk_uuid_583dbc4fde6cd808f31c3cd8', 'cookieconsent_status']:
                self.cookies[key] = self.cookies_raw[key]
        self.driver.close()
        
    @staticmethod
    def handle_none(soup):
        try:
            return soup.text
        except:
            return ''

    def get_listings(self):
        json_data = lambda offset: '{"query":"","manufacturer":"","model":"","fuel":"","min":"","max":"","offset":' + str(offset) + '}'
        offset = 0
        self.data_main = []
        while True:
            # Check condition to continue
            data = json_data(offset)
            try:
                logging.info('Loading - {}'.format('Listing Page offsets: ' + str(offset)))
                response = requests.post('https://www.motor-mall.im/used/search/', headers=self.headers, data=data)
            except Exception as exc:
                logger.error(f'Search Error - {exc}')
                raise Exception
            j = response.json()
            if not j.get('body'):
                break
            body = BeautifulSoup(j.get('body'), 'html.parser')
            vehicle_divs = body.find_all('div', class_=re.compile(r'result'))
            for vd in vehicle_divs:
                h6_el = vd.find('h6')
                try:
                    model = ' '.join(self.handle_none(h6_el).split(' ')[:1])
                except:
                    model = ''
                price = int(re.search(r'\d+,?\d*', self.handle_none(vd.find('h5'))).group().replace(',', ''))
                self.data_main.append({
                    'Title': self.handle_none(h6_el),
                    'Brand': self.handle_none(h6_el).split(' ')[0],
                    #'Model': model,
                    'Price': price,
                    'Link': urljoin(self.home_url, vd.find('a')['href']),
                    'Provider': 'Motor Mall'
                })
            '''for v in vehicles:
                car_data = {
                    'Title': v.get('webVehicleDescription'),
                    'Brand': v.get('webFranchise'),
                    'Price': v.get('webSellingPrice'),
                    'Model': v.get('webModel'),
                    'Year': v.get('regYear'),
                    'Engine Size': str(v.get('webCCBHP')) + 'cc' if v.get('webCCBHP') else None,
                    'Fuel Type': v.get('webFuelType'),
                    'Transmission': v.get('webNumberOfGears'),
                    'Mileage': v.get('webMileage'),
                    'Link': urljoin(self.home_url, v.get('url')),
                    'Colour': v.get('webColour'),
                    'Dealer Phone': v.get('dealerPhone'),
                    'Discounted Price': v.get('discountPrice') if v.get('discountPrice') else '',
                    'Doors': v.get('webNumberofDoors'),
                    'Features': ', '.join(v.get('features')) if v.get('features') else '',
                    'Purchased Date': v.get('dateOfPurchase', '').split('T')[0] if v.get('dateOfPurchase') else '',
                    'Registration Number': v.get('registrationNumber'),
                    'Stock Type': v.get('webStockType'),
                    'Type': ', '.join(v.get('vehicleType', [])),
                    'Provider': 'Motor Mall'
                }
                car_data = {k: v if v else '' for k, v in car_data.items()}
                self.data_main.append(car_data)'''
            offset += 20

    @staticmethod
    def extract_specs(label, s):
        value = s.find('h5', string=re.compile(label)).parent.find('p').text
        try:
            value = int(value.replace(',', ''))
        except:
            pass
        try:
            return value
        except:
            return ''
    
    def get_images(self):
        for j, o in enumerate(self.data_main):
            url = o.get('Link')
            if url:
                try:
                    r = requests.get(url, headers=self.headers)
                except Exception as exc:
                    logger.error(exc)
                    raise Exception
                s = BeautifulSoup(r.text, 'html.parser')
                model = s.find('h3', string=re.compile(r'\£')).parent.find('p').text
                o['Model'] = model
                o['Mileage'] = self.extract_specs('Mileage', s)
                o['Colour'] = self.extract_specs('Colour', s)
                o['Year'] = self.extract_specs('Year', s)
                o['Transmission'] = self.extract_specs('Gears', s)
                o['Fuel Type'] = self.extract_specs('Fuel', s)
                
                try:
                    if s.find('div', attrs={'x-data': "carouselSlider"}):
                        images = [
                            y for y in
                            [
                                img['src'] for img in
                                [x for x in s.find('div', attrs={'x-data': "carouselSlider"}).find('div').contents if x != '\n' and isinstance(x, bs4.element.Tag)]
                                if img.name == 'img'
                            ]
                            if 'img/play.png' not in y and y
                        ]
                    else:
                        images = []
                except Exception as exc:
                    logger.error(f'image error - {url} - {exc}')
                    raise Exception
                for i in range(len(images)):
                    o[f'Image {i+1}'] = images[i]
                logging.info(f'{j+1}/{len(self.data_main)} - {o.get("Title")} - {o.get("Link")}')

    def complete_cols(self):
        unique_cols = []
        for d in self.data_main:
            for col in d.keys():
                if col not in unique_cols:
                    unique_cols.append(col)

        for d in self.data_main:
            for col in unique_cols:
                if not d.get(col):
                    d[col] = ''

    def save(self):
        with open('../csv_files/motor_mall.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            usecols = list(self.data_main[0].keys())
            writer.writerow(usecols)
            writer = csv.DictWriter(f, fieldnames=usecols)
            for d in self.data_main:
                writer.writerow(d)
        logging.info('MOTOR MALL - Process Done!')

    def main(self):
        logging.info('Motor Mall Scrape Initiate')
        #self.get_cookies()
        self.get_listings()
        self.get_images()
        self.complete_cols()
        self.save()


def main():
    scraper = MotorMall()
    scraper.main()


if __name__ == "__main__":
    main()
