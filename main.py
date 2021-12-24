
from bs4 import BeautifulSoup
import time
import requests
import json
import re
import threading

no_of_drugs_count = 0

drugs_list = []


def get_drug(url_link):

    drug_images = []  # store one or more images details
    html_text = ''
    try:
        html_text = requests.get(url_link).text
    except Exception :
        print('new connection error')
        print('Waiting..........')
        time.sleep(20)
        print('reconnecting...')
        html_text = requests.get(url_link).text

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

    drug = {
        'drug images': drug_images,
        'drug name': drug_name,
        'prescription': drug_prescription,
        'require rx': drug_require_rx,
        'compounds': drug_chemicals,
        'final price': final_price,
        'mrp': price,
        'drug varient': drug_varient,
        'product details': product_details

    }

    global no_of_drugs_count
    no_of_drugs_count += 1

    print('drug number: ', no_of_drugs_count)
    return drug


def getting_urls_cat(category):
    ''' getiing url list from category and getting drug details'''
    html_txt = requests.get(category).text
    soup_cat = BeautifulSoup(html_txt, 'lxml')
    drug_url_list = [url_link.a.attrs['href'] for url_link in soup_cat.find_all(
        'li', attrs={'class': 'product-item'})]
    # for link in drug_url_list:
    #     drug_ = get_drug(link)
    #     drugs_list.append(drug_)
    #     print(drug_)

    no_of_links = len(drug_url_list)

    if no_of_links == 0:
        return

    if no_of_links > 2:
        indexes_for_t1 = (0, no_of_links // 3)
        indexes_for_t2 = (no_of_links//3, (no_of_links*2)//3)
        indexes_for_t3 = ((no_of_links*2)//3, no_of_links-1)

        def fun_parts_of_link(indexes):
            a, b = indexes
            for i in range(a, b):
                drug_ = get_drug(drug_url_list[i])
                create_json_file(drug_, 'drugs.json')
                # drugs_list.append(drug_)
                # print(drug_)

        t1 = threading.Thread(target=fun_parts_of_link, args=(indexes_for_t1,))
        t2 = threading.Thread(target=fun_parts_of_link, args=(indexes_for_t2,))
        t3 = threading.Thread(target=fun_parts_of_link, args=(indexes_for_t3,))

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()
    else:
        for link in drug_url_list:
            drug_ = get_drug(link)
            create_json_file(drug_, 'drugs.json')

            # drugs_list.append(drug_)
            # print(drug_)


def create_json_file(drugs, filename):
    with open(filename, 'a') as outputfile:
        str_line = json.dumps(drugs)
        outputfile.write(str_line)
        outputfile.write(',')




html_txt_prescript_page = requests.get(
    'https://www.netmeds.com/prescriptions').text

browser_soup = BeautifulSoup(html_txt_prescript_page, 'lxml')

alpha_drug_list = browser_soup .select("ul.alpha-drug-list a")


for x in alpha_drug_list:
    # print(x.text)
    z = re.findall('[0-9]+', re.findall('\([0-9]+\)', x.text.strip())[0])[0]
    if z != '0':
        # print(z)
        link_cat = x.attrs['href']
        getting_urls_cat(link_cat)


