import dataclasses
from fileinput import filename
from itertools import product
from time import sleep
from xmlrpc.client import boolean
from bs4 import BeautifulSoup
import requests
import json
import re
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning


# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

all_product = []

FOLDER = "data"
IMAGE_FOLDER = FOLDER + "/images"

no_of_products_count = 1


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'
}


@dataclasses.dataclass
class Product():
    id: int
    images: list
    name: str
    compounds: str
    final_price: float
    mrp: float
    product_details: dict
    variant: str = ''
    prescription: str = 'non_prescription'
    require_rx: boolean = False


def save_image_file(link: str):
    req_200 = True
    loop_cout = 0
    while (req_200):
        req_200 = False
        try:
            req = requests.get(link, verify=False)
            if req.status_code == 200:
                filename = link.split('/')[-1]
                with open('./' + IMAGE_FOLDER + '/'+filename, 'wb') as file:
                    file.write(req.content)
                    return IMAGE_FOLDER + '/'+filename
        except (requests.exceptions.RequestException, requests.exceptions.SSLError) as e:
            req_200 = True
            loop_cout += 1
            if loop_cout > 10:
                # try 10 time before exiting
                req_200 = False
                print('connection error', e)
                return ''

    return ''

def image_local_dir(link: str):
    filename = link.split('/')[-1]
    dir = IMAGE_FOLDER + '/' + filename
    return dir



def get_product(url_link):

    images = []  # store one or more images details
    html_text = ''
    req_200 = True
    loop_cout = 0
    while (req_200):
        req_200 = False
        try:
            html_text = requests.get(
                url_link, headers=headers, timeout=60, verify=False).text
        except (requests.exceptions.RequestException, requests.exceptions.SSLError) as e:
            req_200 = False
            sleep(10)
            loop_cout += 1
            if loop_cout > 10:
                # try 10 time before exiting
                req_200 = False
                print('connection error', e)
                return ''

    soup = BeautifulSoup(html_text, 'lxml')

    image_raw_list = soup.find_all(
        'figure', attrs={'class': 'figure'})
    # limits the number of images to 2
    if len(image_raw_list) > 1:
        image_raw_list = image_raw_list[:2]

    for image_raw in image_raw_list:
        # one image blueprint
        image = {}
        try:
            image_link = image_raw.img.attrs['src']
            # image['image file'] = save_image_file(image_link)
            image['image file'] = image_local_dir(image_link)
            image['image alt'] = image_raw.img.attrs['alt']
            image['image title'] = image_raw.img.attrs['title']
            images.append(image)
            # print(images)

        except AttributeError:
            image = None
    try:
        name = soup.find(
            'h1', attrs={'class': 'black-txt'}).text.strip()
    except AttributeError:
        name = ''
    try:
        prescription = soup.find(
            'span', attrs={'class': 'gen_drug ellipsis'}).text.strip()
        if re.search('non-prescriptions',url_link):
            prescription = 'non-prescriptions'
    except AttributeError:
        prescription = ''
    try:
        require_rx = soup.find(
            'span', attrs={'class': 'req_Rx'}).text.strip()
    except AttributeError:
        require_rx = ''
    try:
        chemicals = soup.find(
            'div', attrs={'class': 'product-manu'}).a.text.strip()
    except AttributeError:
        chemicals = ''
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
        images=images,
        name=name,
        compounds=chemicals,
        final_price=final_price,
        mrp=price,
        product_details=product_details,
        variant=varient,
        prescription=prescription,
        require_rx=require_rx
    )

    no_of_products_count += 1
    product_dict = dataclasses.asdict(product)
    return product_dict


# print(product)

# -------------------------- non prescription --------------------------------------
home_url = "https://www.netmeds.com"


def get_level_top_cats():
    html_home_page_txt = requests.get(
        home_url, headers=headers, verify=False).text
    soup = BeautifulSoup(html_home_page_txt, 'lxml')
    level_top_cats = [link.attrs['href']
                      for link in soup.find_all('a', attrs={"class": "level-top"})]
    return level_top_cats


def get_sub_link(link):
    link_text = requests.get(home_url + link, verify=False).text
    sub_soup = BeautifulSoup(link_text, 'lxml')
    sub_links = [url.attrs['href']
                 for url in sub_soup.find_all('a', attrs={"class": "category_name"})]
    return sub_links
    # print(sub_links)


def get_level_sub_cats():
    level_sub_cats: list = []
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
    link_text = requests.get(cat, verify=False).text
    product_soup = BeautifulSoup(link_text, 'lxml')
    product_link_list = [url.attrs['href'] for url in product_soup.find_all(
        'a', attrs={"class": "category_name"})]

    # print(product_link_list)
    return product_link_list


def get_all_product_link():
    """ getting product from all categories """
    product_link = []
    sub_cat_links = get_level_sub_cats()
    # limit the product per prescription to 20
    if len(sub_cat_links) > 20:
        sub_cat_links = sub_cat_links[:21]
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executer:
        for link in executer.map(get_product_link, sub_cat_links):
            product_link.extend(link)

    # print(product_link)
    return product_link


def create_json_file(lst: list,  filename: str):
    # products_dict = {'products': lst}
    with open('./' + FOLDER + '/'+filename, 'w') as outputfile:
        json.dump(lst, outputfile, indent=4)

# ----------------------------------------------prescription-----------------------------------------------------


def getting_urls_cat(category):
    ''' getiing url list from category and getting drug details'''
    html_txt = requests.get(category, verify=False).text
    soup_cat = BeautifulSoup(html_txt, 'lxml')
    drug_url_list = [url_link.a.attrs['href'] for url_link in soup_cat.find_all(
        'li', attrs={'class': 'product-item'})]

    drugs_of_selectd_cat_list = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executer:
        for drug in executer.map(get_product, drug_url_list):
            global all_product
            all_product.append(drug)
#             drugs_of_selectd_cat_list.append(drug)


    cat_name = category.split("/")[-1]

    print(f'adding to product list: {cat_name}')

    # create_json_file(drugs_of_selectd_cat_list, file_name)
#     return drugs_of_selectd_cat_list


# ------------------------------------------------------------------------


def main():
    global all_product

# -------------------------- non prescription --------------------------------------

    i = 1
    all_links = get_all_product_link()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executer:
        for product in executer.map(get_product, all_links):
            print(f"adding product {i} to the list")
            i += 1
            all_product.append(product)

# -------------------------------------- Prescription --------------------------------
    alpha_drug_list = []
    total_no_of_drugs_prescription = 0
    print('fetching site... from prescrition ')
    html_txt_prescript_page = requests.get(
        'https://www.netmeds.com/prescriptions', headers=headers, verify=False).text
    browser_soup = BeautifulSoup(html_txt_prescript_page, 'lxml')
    temp_list = browser_soup .select("ul.alpha-drug-list a")

    for x in temp_list:
        # print(x.text)
        z = re.findall(
            '[0-9]+', re.findall('\([0-9]+\)', x.text.strip())[0])[0]
        if z != '0':
            total_no_of_drugs_prescription += int(z)
            # adding no zero item link to be fetched
            alpha_drug_list.append(x.attrs['href'])

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executer:
        executer.map(getting_urls_cat, alpha_drug_list)
#         for cat_list in executer.map(getting_urls_cat, alpha_drug_list):
#             all_product.extend(cat_list)


# -------------------------------------------------------------------------------------
    print(
        f'toal no of product: {len(all_links) + total_no_of_drugs_prescription}')

    create_json_file(all_product, 'product_data')


if __name__ == "__main__":
    main()
