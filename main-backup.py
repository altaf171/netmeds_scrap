from ast import While
from bs4 import BeautifulSoup
import time
import requests
import json
import re
import concurrent.futures

all_drugs = []

no_of_drugs_count = 1

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'
}


def get_drug(url_link):

    drug_images = []  # store one or more images details
    html_text = ''
    try:
#         print(f'fetching from {url_link}')
        html_text = requests.get(url_link, headers=headers, timeout=180, verify=False).text
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
        'prescription': drug_prescription,
        'require rx': drug_require_rx,
        'compounds': drug_chemicals,
        'final price': final_price,
        'mrp': price,
        'drug varient': drug_varient,
        'product details': product_details}

    no_of_drugs_count += 1
    return drug


def create_json_file(lst,  filename):
    # drugs_dict = {'drugs': lst}
    with open('./data/'+filename, 'w') as outputfile:
        json.dump(lst, outputfile, indent=4)


def getting_urls_cat(category):
    ''' getiing url list from category and getting drug details'''
    html_txt = requests.get(category, verify=False).text
    soup_cat = BeautifulSoup(html_txt, 'lxml')
    drug_url_list = [url_link.a.attrs['href'] for url_link in soup_cat.find_all(
        'li', attrs={'class': 'product-item'})]

    drugs_of_selectd_cat_list = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executer:
        for drug in executer.map(get_drug, drug_url_list):
            drugs_of_selectd_cat_list.append(drug)

    file_name = category.split("/")[-1] + '.json'

    print(f'adding to list: {file_name}')
    
    global all_drugs
    all_drugs.extend(drugs_of_selectd_cat_list)
    

#     create_json_file(drugs_of_selectd_cat_list, file_name)



# ---------------------------------------------------------

def main():
    alpha_drug_list = []
    total_no_of_drugs = 0

    print('fetching site...')

    html_txt_prescript_page = requests.get(
        'https://www.netmeds.com/prescriptions', headers=headers, verify=False).text

    browser_soup = BeautifulSoup(html_txt_prescript_page, 'lxml')
    temp_list = browser_soup .select("ul.alpha-drug-list a")


    for x in temp_list:
        # print(x.text)
        z = re.findall('[0-9]+', re.findall('\([0-9]+\)', x.text.strip())[0])[0]
        if z != '0':
            total_no_of_drugs += int(z)
            # adding no zero item link to be fetched
            alpha_drug_list.append(x.attrs['href'])

    print('total drugs: ', total_no_of_drugs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executer:
        executer.map(getting_urls_cat, alpha_drug_list)
        
    create_json_file(all_drugs, 'data.json')

if __name__ == '__main__':
    main()
