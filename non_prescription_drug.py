import dataclasses
from itertools import product
from xmlrpc.client import boolean
from bs4 import BeautifulSoup
import requests
import json
import re
import concurrent.futures

no_of_products_count = 1

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'
}


@dataclasses.dataclass
class Product():
    id: int
    images: list
    name:str
    # compounds : str #
    final_price: float
    mrp: float
    product_details:dict
    variant: str = ''
    prescription: str = 'non-prescription'
    require_rx : boolean = False
    

def get_product(url_link):

    images = []  # store one or more images details
    html_text = ''
    try:
#         print(f'fetching from {url_link}')
        html_text = requests.get(url_link, headers=headers, timeout=180).text
    except requests.exceptions.RequestException as e:
        print('connection error')
        return ''

    soup = BeautifulSoup(html_text, 'lxml')

    image_raw_list = soup.find_all(
        'figure', attrs={'class': 'figure'})

    for image_raw in image_raw_list:
        # one image blueprint
        image = {}
        try:
            image['image link'] = image_raw.img.attrs['src']
            image['image alt']= image_raw.img.attrs['alt']
            image['image title'] = image_raw.img.attrs['title']
            images.append(image)
            # print(images)

        except AttributeError:
            image=None
    try:
        name = soup.find(
            'h1', attrs={'class': 'black-txt'}).text.strip()
    except AttributeError:
        name = ''
    try:
        prescription = soup.find(
            'span', attrs={'class': 'gen_product ellipsis'}).text.strip()
    except AttributeError:
        prescription = ''
    try:
        require_rx = soup.find(
            'span', attrs={'class': 'req_Rx'}).text.strip()
    except AttributeError:
        require_rx = ''
    # try:
    #     chemicals = soup.find(
    #         'div', attrs={'class': 'product-manu'}).a.text.strip()
    # except AttributeError:
    #     chemicals = ''
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
        varient = soup.find(
            'span', attrs={'class': 'product-varient'}).text.replace('*', '')
    except AttributeError:
        varient = ''

    product_details_list = [x.ul.div for x in soup.find_all(
        'div', attrs={'class': 'manufacturer_details'})]

    product_details = {}

    for product_d in product_details_list:
        name = product_d.find('div', attrs={'class': 'manufacturer_name'}).text
        value = product_d.find(
            'div', attrs={'class': 'manufacturer__name_value'}).text
        product_details[name] = value

    global no_of_products_count

    product = Product(
        id=no_of_products_count,
        images= images,
        name=name,
        final_price=final_price,
        mrp= price,
        product_details=product_details,
        variant=varient,

    )

    no_of_products_count += 1
    product_dict = dataclasses.asdict(product)
    return product_dict




# print(product)




home_url = "https://www.netmeds.com"


def get_level_top_cats():
    html_home_page_txt = requests.get(home_url, headers=headers).text
    soup = BeautifulSoup(html_home_page_txt, 'lxml')
    level_top_cats = [link.attrs['href'] for link in soup.find_all('a', attrs={"class": "level-top"})]
    return level_top_cats




def get_sub_link(link):
    link_text = requests.get(home_url + link).text
    sub_soup = BeautifulSoup(link_text, 'lxml')
    sub_links = [url.attrs['href'] for url in sub_soup.find_all('a', attrs={"class": "category_name"})]    
    return sub_links
            # print(sub_links)



def get_level_sub_cats():
    level_sub_cats : list = []
    level_top_cats = get_level_top_cats()

    # with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executer:
    #     for sub_cat in executer.map(get_sub_link, level_top_cats):
    #         level_sub_cats.extend(sub_cat)

    for link in level_top_cats:
        level_sub_cats.extend(get_sub_link(link))
        
    # print(level_sub_cats)
    return level_sub_cats


def get_product_link(cat):
    """ get all the product from a category """
    link_text = requests.get(cat).text
    product_soup = BeautifulSoup(link_text, 'lxml')
    product_link_list = [url.attrs['href'] for url in product_soup.find_all('a', attrs={"class": "category_name"})]    
    
    # print(product_link_list)
    return product_link_list


def get_all_product_link():
    """ getting product from all categories """
    product_link = []
    sub_cat_links = get_level_sub_cats()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executer:
        for link in executer.map(get_product_link, sub_cat_links):
            product_link.extend(link)
            

    print(product_link)
    return product_link



def create_json_file(lst:list,  filename:str):
    # products_dict = {'products': lst}
    with open('./data/'+filename, 'w') as outputfile:
        json.dump(lst, outputfile, indent=4)



def main():
    i=1;
    all_product = []
    all_links = get_all_product_link()
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executer:
        for product in executer.map(get_product, all_links):
            print(f"adding product {i} to the list")
            i += 1
            all_product.append(product)

    print(f'toal no of product: {len(all_links)}')

    create_json_file(all_product, 'product_non_prescription')
  


if __name__ == "__main__":
    main()