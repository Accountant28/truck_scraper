from selenium import webdriver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

import requests

import itertools
import json
import os

_id = itertools.count(1)

geckodriver = '/Users/vladislav/PycharmProjects/WEBSCRAPING/07_Sneakers/geckodriver'
driver = webdriver.Firefox(executable_path=geckodriver)

driver.get('https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault')

cookie = driver.find_element(By.XPATH, '//*[@id="consent-mgmt-accept-all"]')
cookie.click()

soup = BeautifulSoup(driver.page_source, 'lxml')

row_pagination_links = [item.a for item in soup.find('ul', class_ = 'sc-pagination').find_all(['li'])][2:-1]
pagination_links = [item['href'] for item in row_pagination_links]

while True:
    short_link = soup.find('a', {'data-item-name': 'detail-page-link'})['href']
    full_link = 'https://www.truckscout24.de/' + short_link

    car_link = requests.get(full_link)
    soup = BeautifulSoup(car_link.text, 'lxml')

    try:
        id = next(_id)
        href = full_link
        title = soup.find('h1', class_ = 'sc-ellipsis sc-font-xl').text
        row_price = soup.find('h2', class_ = 'sc-highlighter-4 sc-highlighter-xl sc-font-bold').text
        price = int(row_price.replace('€ ', '').replace('.', '').replace(',-', ''))
        for item in soup.find('div', class_ = 'data-basic1').find_all('div', class_ = 'itemlbl'):
            if item.text == 'Kilometer':
                row_mileage = item.find_next_sibling('div').text
                mileage = int(row_mileage.replace('.', '').replace(' km', ''))
        for item in soup.find('ul', class_ = 'columns').find_all('div', class_ = 'sc-font-bold'):
            if item.text == 'Farbe':
                color = item.find_next_sibling('div').text
        for item in soup.find('ul', class_ = 'columns').find_all('div', class_ = 'sc-font-bold'):
            if item.text == 'Leistung':
                power = int(item.find_next_sibling('div').text[:3])
        description = soup.find('div', {'data-type': 'description'}).find('p').text.replace('\r\n', '').replace('\u00A0', ' ')
    except:
        pass

    row_image = [item.img for item in soup.find('div', class_ = 'as24-carousel__container').find_all('div', class_ = 'as24-carousel__item')]
    image_links = [item['data-src'] for item in row_image[:3]]
    print(image_links)
    os.makedirs(f'/Users/vladislav/PycharmProjects/WEBSCRAPING/trucks/data/{id}', exist_ok=True)

    for link in image_links:
        response = requests.get(link)
        imagename = f'/Users/vladislav/PycharmProjects/WEBSCRAPING/trucks/data/{id}' + '/' + f'{id}.jpg'
        with open(imagename, 'wb') as file:
            file.write(response.content)

    data = {
        "ads": [
            {
                "id": next(_id),
                "href": href,
                "title":title,
                "price": price,
                "mileage": mileage,
                "color": color,
                "power": power,
                "description": description,
            },
        ]
    }

    with open('data.json', 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write(',')

    for link in pagination_links:
        next_page = requests.get(link)
    try:
        pagination_links.remove(link)
    except:
        break
    soup = BeautifulSoup(next_page.text, 'lxml')