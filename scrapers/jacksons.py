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
logger = custom_logs('JACKSONS', 'jacksons')


class Jacksons:
    """Scrape Jacksons"""
    list_page = 'https://www.jacksons.im/used/?stocktype=All&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=1'
    def __init__(self):
        self.home_url = 'https://www.jacksons.im'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.jacksons.im/used/?stocktype=All&isbikes=false&make=&model=&minprice=0&maxprice=0&gear=&door=&cartype=&location=&segment=iom&sortorder=4&pagesize=24&page=1',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Origin': 'https://www.jacksons.im',
            'Alt-Used': 'www.jacksons.im',
            'Connection': 'keep-alive',
            # 'Cookie': 'S=gos8otbq2jecmu1g3pn000k614; TawkConnectionTime=0; twk_idm_key=IgCCIJiR2Vr6IR-SIPigh; twk_uuid_583dbc4fde6cd808f31c3cd8=%7B%22uuid%22%3A%221.70hV0k02AJS1FL47pSzhYC5p0Ky0i2fDVzKuWjYB6lhj727fJI6dvv3UAdPVnmHVt2txpPhGruf8BQkpxwJ2EtmVPfI4GPHZ1PnIluCfJ6pDS3fDUznt%22%2C%22version%22%3A3%2C%22domain%22%3A%22jacksons.im%22%2C%22ts%22%3A1719642248728%7D',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            # Requests doesn't support trailers
            # 'TE': 'trailers',
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
                response = requests.post('https://www.jacksons.im/used/search/', headers=self.headers, data=data)
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
                    'Provider': 'Jacksons'
                })
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
        with open('../csv_files/jacksons.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            usecols = list(self.data_main[0].keys())
            writer.writerow(usecols)
            writer = csv.DictWriter(f, fieldnames=usecols)
            for d in self.data_main:
                writer.writerow(d)
        logging.info('JACKSONS - Process Done!')

    def main(self):
        logging.info('Jacksons Scrape Initiate')
        #self.get_cookies()
        self.get_listings()
        self.get_images()
        self.complete_cols()
        self.save()


def main():
    scraper = Jacksons()
    scraper.main()


if __name__ == "__main__":
    main()
