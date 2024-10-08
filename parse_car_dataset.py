from bs4 import BeautifulSoup
from urllib.parse import urljoin
from seleniumbase import Driver
import requests 

import logging
import time
import os
import re
import json

from typing import Any
from ultralytics import YOLO

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

# Configuration of logger
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
        logging.FileHandler('parsing.log'),  
    ]
)

class CarParser:
    def __init__(self, driver, model) -> None:
        """
        Initializes the CarParser object.
        """

        self.base_url = "https://platesmania.com"
        self.url = "https://platesmania.com/al/"
        self.driver = driver    
        self.json_data = {}   
        self.model = model 


    def get_bfsoup(self, link, sleep_time=0) -> Any:
        """
        Parses link with BeautifulSoup.
        Returns: soup of HTML page.
        """

        self.driver.get(link)
        time.sleep(sleep_time)
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        return soup


    def get_galery_links(self) -> list:
        """
        Parses type links (Автомобили (2011), Мотоциклы (2011), Прицепы (2011), Автомобили (1993)) and 
        gets links to each gallery.

        Returns list of gallery links.
        """

        soup = self.get_bfsoup(self.url)
        links = soup.find_all('a')
        type_links = []
        for link in links:
            strong_tag = link.find('strong', class_='pull-left')
            if strong_tag:
                full_link = urljoin(self.url, link['href'])
                type_links.append((full_link, strong_tag.text))

        gallery_links = []
        for link, text in type_links:
            soup = self.get_bfsoup(link)
            h3_tag = soup.find('h3', string=text)
            
            if h3_tag:
                p_tag = h3_tag.find_next('p')
                if p_tag and p_tag.find('a'):
                    gallery_link = urljoin(self.url, p_tag.find('a')['href'])
                    gallery_links.append(gallery_link)

        return gallery_links
    
    @staticmethod
    def make_dir(dir) -> bool:
        """
        Makes directory if does not exists.
        Returns True if directory was created, False otherwise
        """

        if not os.path.exists(dir):
            os.makedirs(dir)
            return True
        return False
    

    def save_image(self, img_dir, soup, name_prefix, cls) -> str:
        """
        Parses image url with class cls and saves an image to img_dir.
        Returns image url
        """

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

        image_tag = soup.find('img', class_=cls) 
        if not image_tag:
            return 
        img_url = image_tag['src'] 
        img_name = f'{name_prefix}_{img_url.split('/')[-1]}'

        img_data = requests.get(img_url, headers=headers).content

        with open(f'{img_dir}/{img_name}', 'wb') as f:
            f.write(img_data)
        return img_url
    

    @staticmethod
    def get_link_text(soup) -> str:
        """
        parses link text and returns its full text
        """
        h3_tag = soup.find('h3', class_='text-center margin-bottom-10')
        pattern = re.compile(r'^/catalog/')
        link_text = []
        if h3_tag:
            links = h3_tag.find_all('a', href=pattern)
            for link in links:
                link_text.append(link.text.strip())
        link_text = ' '.join(link_text)
        return link_text
    

    @staticmethod
    def get_place_meta(soup) -> str:
        """
        parses place meta 
        """
        pattern = re.compile(r'^/gallery.php?')
        a_tags = soup.find_all('a', href=pattern)
        place_meta = []

        for a_tag in a_tags:
            small_tags = a_tag.find_all('small')
            for small_tag in small_tags:
                if hasattr(small_tag, 'text') and not small_tag.find_all():
                    place_meta = small_tag.text
        return place_meta
    

    @staticmethod
    def get_plate_number(soup) -> str:
        """
        parses plate number
        """
        div_tag = soup.find('div', class_='col-xs-12')
        plate_number= ''

        if div_tag:
            h1_tag = div_tag.find('h1', class_='pull-left')
            plate_number = h1_tag.text.strip()
        return plate_number
    

    def save2json(self, soup, img_link, img_url, main_img_url, gen_img_url, bbox) -> None:

        """ 
        Updates JSON data with parsed data.
        """

        link_text = self.get_link_text(soup)
        place_meta = self.get_place_meta(soup)
        plate_number = self.get_plate_number(soup)

        json_object = {
            img_link['href']: {
                "ads_link": img_url,
                "link_text": link_text,
                "main_img": main_img_url,
                "generated_img": gen_img_url,
                "place_meta": place_meta,
                "plate_number": plate_number,
                "bbox": bbox
            },
        }

        self.json_data.update(json_object)
        return


    @staticmethod
    def detect_plate(img_dir, model) -> str:
        """
        Detects bbox of number plate on main image using pretrained YOLO model.

        Returns: bbox -- "x y w h" -- coordinates of number plate.
        """

        main_image = [img for img in os.listdir(img_dir) if img.startswith('real')][0]
        img_path = os.path.join(img_dir, main_image)

        result_predict = model.predict(source = img_path, imgsz=(640))

        bbox = ''
        if result_predict and result_predict[0]:
            bbox_numpy = result_predict[0].boxes.xywh.numpy()[0]
            bbox = ' '.join(str(int(num)) for num in bbox_numpy)

        return bbox            


    def get_pages(self, gallery_link):

        """
        Recursively gets all gallery links and saves them to self.pages
        """
        pattern = re.compile(r'^gallery.php(?!.*#).*$')

        soup = self.get_bfsoup(gallery_link)
        pagination = soup.find('ul', class_='pagination')
        page_links = pagination.find_all('a', href=pattern)
        pages = [page_link['href'] for page_link in page_links if page_link['href'] not in self.pages]

        if not pages:
            return
        
        self.pages.update(pages)
        self.get_pages(f'{self.url}{pages[-2]}')

        return 


    def parse(self) -> None:

        """
        gets gallery link, gets page's link while there are images on it and 
        parses all images links (main image, generated image and meta)
        """

        pattern = re.compile(r'^/al/nomer(?!.*#).*$')

        gallery_links = self.get_galery_links()
        for gallery_link in gallery_links:

            img_type_dir = f'images/al-ctype-{gallery_link.split('=')[-1]}'
            self.make_dir(img_type_dir)
            json_file = f'{img_type_dir}-meta.json'            
            
            # in case data partially parsed
            if os.path.exists(json_file):
                with open(json_file, 'r') as file:
                    self.json_data = json.load(file) 
            
            logging.info(f'Считаю страницы на {gallery_link}')
            self.pages = set([gallery_link])
            self.get_pages(gallery_link)
            logging.info(f'Найдено {len(self.pages)} страниц')

            for page in sorted(self.pages):
                page_url = f'{self.url}{page}'
                page_soup = self.get_bfsoup(page_url)

                img_links = page_soup.find_all('a', href=pattern)
                if not page_soup.find_all('img', class_='img-responsive center-block'):
                    break
                
                for img_link in img_links:
                    if not img_link.find('img', class_='img-responsive center-block'):
                        continue

                    if img_link['href'] in self.json_data:
                        logging.info(f'Объект с ID {img_link['href']} уже записан.')
                        continue

                    img_url = f'{self.base_url}{img_link['href']}'
                    img_id = img_link['href'].replace('/', '_')

                    img_dir = os.path.join(img_type_dir, img_id)

                    img_soup = self.get_bfsoup(img_url)

                    # to load a page with captcha
                    if not img_soup.find('img', class_="img-responsive center-block"):
                        img_soup = self.get_bfsoup(img_url, sleep_time=5)

                    self.make_dir(img_dir)
                    
                    # parse and save images
                    main_img = self.save_image(img_dir, img_soup, 'real', "img-responsive center-block") 
                    generated_img = self.save_image(img_dir, img_soup, 'generated', "img-responsive center-block margin-bottom-20")
                    if not main_img:
                        logging.error(f'Ошибка при загрузке страницы {img_id}.')
                        continue
                    
                    bbox = self.detect_plate(img_dir, self.model)
                    self.save2json(img_soup, img_link, img_url, main_img, generated_img, bbox)

                    logging.info(f'{img_id} -- успешно')
                    with open(json_file, 'w') as file:
                        json.dump(self.json_data, file, indent=4, ensure_ascii=False) 

                logging.info(f'{page_url} -- успешно')

            self.json_data = {}
            logging.info(f'{gallery_link} -- успешно')

        logging.info('Все данные успешно загружены')
        return


if __name__ == "__main__":

    # Initialize and configure a driver instance
    driver = Driver(uc=True, headless=True)

    # Initialize and YOLO model
    model = YOLO("best-model.pt") 

    carParser = CarParser(driver, model)
    carParser.parse()
    driver.close()
    driver.quit()