from bs4 import BeautifulSoup
import aiohttp
import asyncio
import requests
import json
import re
import concurrent.futures

no_of_drugs_count = 1

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'
}


def get_drug(url_link):

    drug_images = []  # store one or more images details
    html_text = ''
    try:
        #         print(f'fetching from {url_link}')
        html_text = requests.get(url_link, headers=headers, timeout=180).text
    except requests.exceptions.RequestException as e:
        print('connection error')
        return ''

    soup = BeautifulSoup(html_text, 'lxml')

    drug_image_raw_list = soup.find_all(
        'figure', attrs={'class': 'figure'})

    for drug_image_raw in drug_image_raw_list:
        # one image blueprint
        drug_image = {}
        try:
            drug_image_link = drug_image_raw.img.attrs['src']
            drug_image_alt_text = drug_image_raw.img.attrs['alt']
            drug_image_title_text = drug_image_raw.img.attrs['title']

            drug_image['image link'] = drug_image_link
            drug_image['image alt'] = drug_image_alt_text
            drug_image['image title'] = drug_image_title_text

            drug_images.append(drug_image)
            # print(drug_images)

        except AttributeError:
            drug_image_link = ''
            drug_image_alt_text = ''
            drug_image_title_text = ''

    try:
        drug_name = soup.find(
            'h1', attrs={'class': 'black-txt'}).text.strip()
    except AttributeError:
        drug_name = ''
    try:
        drug_prescription = soup.find(
            'span', attrs={'class': 'gen_drug ellipsis'}).text.strip()
    except AttributeError:
        drug_prescription = ''
    try:
        drug_require_rx = soup.find(
            'span', attrs={'class': 'req_Rx'}).text.strip()
    except AttributeError:
        drug_require_rx = ''
    try:
        drug_chemicals = soup.find(
            'div', attrs={'class': 'drug-manu'}).a.text.strip()
    except AttributeError:
        drug_chemicals = ''
    try:
        final_price = soup.find(
            'span', attrs={'class': 'final-price'}).contents[-1].replace('₹', '').strip()
    except AttributeError:
        final_price = ''
    try:
        price = soup.find(
            'span', attrs={'class': 'price'}).strike.text.replace('₹', '')
    except AttributeError:
        price = ''
    try:
        drug_varient = soup.find(
            'span', attrs={'class': 'drug-varient'}).text.replace('*', '')
    except AttributeError:
        drug_varient = ''

    product_details_list = [x.ul.div for x in soup.find_all(
        'div', attrs={'class': 'manufacturer_details'})]

    product_details = {}

    for product_d in product_details_list:
        name = product_d.find('div', attrs={'class': 'manufacturer_name'}).text
        value = product_d.find(
            'div', attrs={'class': 'manufacturer__name_value'}).text
        product_details[name] = value

    global no_of_drugs_count

    drug = {
        'id': no_of_drugs_count,
        'drug images': drug_images,
        'drug name': drug_name,
        'prescription': 'non-prescriptions',
        'require rx': False,
        'compounds': drug_chemicals,
        'final price': final_price,
        'mrp': price,
        'drug varient': drug_varient,
        'product details': product_details}

    no_of_drugs_count += 1
    return drug

    # print(drug)


# def create_json_file(lst,  filename):
#     # drugs_dict = {'drugs': lst}
#     with open('./data/'+filename, 'w') as outputfile:
#         json.dump(lst, outputfile, indent=4)



home_url = "https://www.netmeds.com"
level_sub_cats = []
product_link = []



async def get_level_top_cats():

    async with aiohttp.ClientSession() as session:

        async with session.get(home_url) as response:

            html_home_page_txt = await response.text()

            soup = BeautifulSoup(html_home_page_txt, 'lxml')
            
            level_top_cats = [link.attrs['href'] for link in soup.find_all('a', attrs={"class": "level-top"})]
            
            return level_top_cats


async def get_sub_link(link):

    async with aiohttp.ClientSession() as session:
        async with session.get(home_url + link) as response:
            link_text = await response.text()
            sub_soup = BeautifulSoup(link_text, 'lxml')
            sub_links = [url.attrs['href'] for url in sub_soup.find_all('a', attrs={"class": "category_name"})]
        
            return sub_links



async def get_level_sub_cats():
    level_top_cats = await get_level_top_cats()
    temp = await asyncio.gather(*[get_sub_link(link) for link in level_top_cats])
    for link in temp:
        level_sub_cats.extend(link)
    return level_sub_cats


async def get_links_from_single_cat(cat):
     async with aiohttp.ClientSession() as session:
        async with session.get(cat) as response:
            link_text = await response.text()
            cat_soup = BeautifulSoup(link_text, 'lxml')
            cat_links = [url.attrs['href'] for url in cat_soup.find_all('a', attrs={"class": "category_name"})]

            return cat_links


async def get_product_link():
    sub_cats = await get_level_sub_cats()
    temp = await asyncio.gather(*[get_links_from_single_cat(link) for link in sub_cats])
    # i=0
    for link in temp:
        product_link.extend(link)
        # print(i," : ", link)
    print(sub_cats)
    


asyncio.run(get_product_link())

