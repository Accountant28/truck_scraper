import os
from decouple import config

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from bs4 import BeautifulSoup

import requests
import json
import uuid
from collections import deque


PATH_FOR_SAVE = config('PATH_FOR_SAVE')

options = Options()
options.headless = True

geckodriver = config('GECODRIVER') + 'geckodriver'
driver = webdriver.Firefox(options=options, executable_path=geckodriver)

PAGE = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault'


def parsing_site(start_page):
    """
    Main function for parsing site
    """
    pages = get_all_pages(get_html(start_page), start_page)
    info = []
    for page in pages:
        info += get_info(get_html(page))
        normilize_data(info)
        get_images(get_html(page))

def get_html(url):
    """
    Get html code from page and get rid of cookies
    """
    driver.get(url)
    try:
        cookie = driver.find_element(By.XPATH, '//*[@id="consent-mgmt-accept-all"]')
        cookie.click()
    except:
        pass
    return BeautifulSoup(driver.page_source, 'lxml')

def get_all_pages(html, start_page):
    """
    Get all pages for parse
    """
    row_pagination_links = html.find('ul', class_ = 'sc-pagination').find_all('li')
    pagination_links = [item for item in row_pagination_links]
    count_pages = 0
    for link in pagination_links:
        try:
            page = int(link.getText()) + 1
            if page > count_pages:
                count_pages = page
        except:
            pass
    pages = []
    for i in range(1, count_pages):
        pages.append(start_page + '?currentpage=' + str(i))
    return pages

def get_info(html):
    """
    Get all neccesary information from the first on each page
    """
    short_link = html.find('a', {'data-item-name': 'detail-page-link'})['href']
    full_link = 'https://www.truckscout24.de/' + short_link

    car_link = requests.get(full_link)
    soup = BeautifulSoup(car_link.text, 'lxml')

    _ids = []
    hrefs = []
    titles = []
    prices = []
    mileages = []
    colors = []
    powers = []
    descriptions = []

    global _id

    try:
        _id = int(uuid.uuid4())
        _ids.append(_id)
        href = full_link
        hrefs.append(href)
        title = soup.find('h1', class_ = 'sc-ellipsis sc-font-xl').text
        titles.append(title)
        try:
            row_price = soup.find('h2', class_ = 'sc-highlighter-4 sc-highlighter-xl sc-font-bold').text
            price = int(row_price.replace('€ ', '').replace('.', '').replace(',-', ''))
        except:
            price = 0
        prices.append(price)
        try:
            for item in soup.find('div', class_ = 'data-basic1').find_all('div', class_ = 'itemlbl'):
                if item.text == 'Kilometer':
                    mileage = int(item.find_next_sibling('div').text.replace('.', '').replace(' km', ''))
        except:
            mileage = 0
        mileages.append(mileage)
        try:
            for item in soup.find('ul', class_ = 'columns').find_all('div', class_ = 'sc-font-bold'):
                if item.text == 'Farbe':
                    color = item.find_next_sibling('div').text
        except:
            color = ''
        colors.append(color)
        try:
            for item in soup.find('ul', class_ = 'columns').find_all('div', class_ = 'sc-font-bold'):
                if item.text == 'Leistung':
                    power = int(item.find_next_sibling('div').text[:3])
        except:
            power = 0
        powers.append(power)
        try:
            row_description = soup.find('div', {'data-type': 'description'}).text
            description = row_description.replace('\r', '').replace('\n', '')
        except:
            description = ''
        descriptions.append(description)
    except:
        pass
    return _ids, hrefs, titles, prices, mileages, colors, powers, descriptions

def get_images(html):
    """
    Get the first three images of each the first car on each page.
    Create directory for the photos of each car and save it
    """
    short_link = html.find('a', {'data-item-name': 'detail-page-link'})['href']
    full_link = 'https://www.truckscout24.de/' + short_link

    car_link = requests.get(full_link)
    soup = BeautifulSoup(car_link.text, 'lxml')

    try:
        row_images = [item.img for item in soup.find('div', class_ = 'as24-carousel__container').find_all('div', class_ = 'as24-carousel__item')]
        image_links = [item['data-src'] for item in row_images[:3]]
    except:
        pass

    os.makedirs(f'{PATH_FOR_SAVE}/{_id}', exist_ok=True)
    for image in image_links:
        response = requests.get(image)
        imagename = f'{PATH_FOR_SAVE}/{_id}' + '/' + f'{uuid.uuid4()}.jpg'
        with open(imagename, 'wb') as file:
            file.write(response.content)

def normilize_data(info):
    """
    Convert data to the orrect format.
    """
    keys = deque(['id', 'href', 'title', 'price', 'mileage', 'color', 'power', 'description'])
    flatList = []

    for element in info:
        for item in element:
            flatList.append(item)

    data = {}
    for car in flatList:
        number = keys.popleft()
        data[car] = number
        keys.append(number)

    write_data(data)

def write_data(data):
    """
    Write data of each car
    """
    json_data = {'ads': [{v: k for k, v in data.items()}]}
    with open(f'{PATH_FOR_SAVE}/data.json', 'a', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False)
        f.write(',' + '\n')

if __name__ == '__main__':
    parsing_site(PAGE)