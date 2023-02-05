import os

from selenium import webdriver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

import requests
import json
import uuid

PATH_FOR_SAVE = '/Users/vladislav/PycharmProjects/WEBSCRAPING/trucks/data'

geckodriver = '/Users/vladislav/PycharmProjects/WEBSCRAPING/07_Sneakers/geckodriver'
driver = webdriver.Firefox(executable_path=geckodriver)

driver.get('https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault')

# Get rid of cookie
cookie = driver.find_element(By.XPATH, '//*[@id="consent-mgmt-accept-all"]')
cookie.click()

soup = BeautifulSoup(driver.page_source, 'lxml')

# Get all links for other pages
row_pagination_links = [item.a for item in soup.find('ul', class_ = 'sc-pagination').find_all(['li'])][2:-1]
pagination_links = [item['href'] for item in row_pagination_links]

# Main while-loop for parse
while True:
    # Get each first car's link
    short_link = soup.find('a', {'data-item-name': 'detail-page-link'})['href']
    full_link = 'https://www.truckscout24.de/' + short_link

    car_link = requests.get(full_link)
    soup = BeautifulSoup(car_link.text, 'lxml')

    # Get info from each car's link
    try:
        _id = int(uuid.uuid4())
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

        row_description = soup.find('div', {'data-type': 'description'}).find('p').text
        description = row_description.replace('\r\n', '').replace('\u00A0', ' ')
    except:
        pass

    # Get links for the first three images of each car
    row_images = [item.img for item in soup.find('div', class_ = 'as24-carousel__container').find_all('div', class_ = 'as24-carousel__item')]
    image_links = [item['data-src'] for item in row_images[:3]]

    # Create new directory for each car and save images
    os.makedirs(f'{PATH_FOR_SAVE}/{_id}', exist_ok=True)
    for image in image_links:
        response = requests.get(image)
        imagename = f'{PATH_FOR_SAVE}/{_id}' + '/' + f'{uuid.uuid4()}.jpg'
        with open(imagename, 'wb') as file:
            file.write(response.content)

    # Write necessary data for each car in file
    data = {
        'ads': [
            {
                'id': _id,
                'href': href,
                'title': title,
                'price': price,
                'mileage': mileage,
                'color': color,
                'power': power,
                'description': description,
            },
        ]
    }

    with open(f'{PATH_FOR_SAVE}/data.json', 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write(',')
        f.write('\n')

    # Pagenate through each page
    for link in pagination_links:
        next_page = requests.get(link)
    try:
        pagination_links.remove(link)
    except:
        break
    soup = BeautifulSoup(next_page.text, 'lxml')