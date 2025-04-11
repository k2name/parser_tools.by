#!/usr/bin/python3
#-*- coding: utf-8 -*-

import os
import re
import sys
import time
import tqdm
import configparser
import requests
from src.file import io
from src.help import k2
from src.telegramm import TelegramBot
from src.base import sql
from src.woocommerce import WooCommerceAPI
import xml.etree.ElementTree as ET

use_local = True
clear_db = False
global_timestamp = int(time.time())

# Загружаем настройки
cfg = configparser.ConfigParser()
cfg.read('config.ini')
src_url = cfg.get('tools', 'api_url')
params = cfg.get('tools', 'params').split(',')
wp_url = cfg.get('wp', 'wp_url')
wp_key = cfg.get('wp', 'wp_key')
wp_secret = cfg.get('wp', 'wp_secret')
wp_discount = int(cfg.get('wp', 'wp_price_discount'))
wp_img_storage = cfg.get('wp', 'wp_img_storage')
local_img_storage = cfg.get('wp', 'local_img_storage')

def download_data(url):

    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully downloaded file.")
            return response
        else:
            print(f"Error downloading file: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"Error while downloading file: {e}")
        return False


def clean_text(text):
    """
    Очищает текст от недопустимых символов.
    """
    # Удаляем управляющие символы (кроме табуляции, перевода строки и возврата каретки)
    cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return cleaned_text


def convert_value(value, target_type):
    """
    Преобразует значение в указанный тип (int или float) с обработкой ошибок.
    """
    if not value:
        return None

    try:
        # Заменяем запятую на точку для корректного преобразования в float
        value = value.replace(",", ".")
        if target_type == int:
            return int(float(value))  # Сначала преобразуем в float, затем в int
        elif target_type == float:
            return float(value)
    except (ValueError, AttributeError):
        return None  # В случае ошибки возвращаем None


def parse_large_xml(file_path):
    """
    Парсит большой XML-файл и возвращает список словарей с данными о товарах.
    """
    products = []  # Список для хранения данных о товарах

    # Используем iterparse для пошагового чтения XML
    context = ET.iterparse(file_path, events=("start", "end"))
    context = iter(context)

    # Получаем корневой элемент
    event, root = next(context)

    # Переменная для временного хранения данных о текущем товаре
    current_product = {}

    for event, elem in context:
        if event == "start" and elem.tag == "offer":
            # Начинаем новый товар
            current_product = {}

        if event == "end" and elem.tag == "offer":
            # Преобразуем числовые поля
            current_product["id"] = convert_value(current_product.get("id"), int)
            current_product["parentid1"] = convert_value(current_product.get("parentid1"), int)
            current_product["parentid2"] = convert_value(current_product.get("parentid2"), int)
            current_product["parentid3"] = convert_value(current_product.get("parentid3"), int)
            current_product["parentid4"] = convert_value(current_product.get("parentid4"), int)
            current_product["price"] = convert_value(current_product.get("price"), float)
            current_product["price_recommended"] = convert_value(current_product.get("price_recommended"), float)
            current_product["price_recommended_713"] = convert_value(current_product.get("price_recommended_713"), float)
            current_product["vat"] = convert_value(current_product.get("vat"), int)
            current_product["barcode"] = convert_value(current_product.get("barcode"), int)
            current_product["prop_new"] = convert_value(current_product.get("prop_new"), int)
            current_product["prop_warranty"] = convert_value(current_product.get("prop_warranty"), int)
            current_product["prop_quantity_min"] = convert_value(current_product.get("prop_quantity_min"), int)
            current_product["prop_length"] = convert_value(current_product.get("prop_length"), float)
            current_product["prop_width"] = convert_value(current_product.get("prop_width"), float)
            current_product["prop_height"] = convert_value(current_product.get("prop_height"), float)
            current_product["prop_weight_gross"] = convert_value(current_product.get("prop_weight_gross"), float)
            current_product["prop_promo_price"] = convert_value(current_product.get("prop_promo_price"), float)
            current_product["prop_tnved"] = convert_value(current_product.get("prop_tnved"), int)
            current_product["prop_codecustom"] = convert_value(current_product.get("prop_codecustom"), int)
            current_product["prop_713"] = convert_value(current_product.get("prop_713"), int)

            for param in current_product:
                try:
                    if param not in params:
                        del current_product[param]
                except:
                    pass

            # Сохраняем данные о текущем товаре
            if current_product["id"] != None:
                products.append(current_product)
            root.clear()  # Освобождаем память

        if event == "end" and elem.tag != "offer" and elem.tag != "offers":
            # Сохраняем данные о текущем товаре
            current_product[elem.tag] = elem.text

    return products


def get_from_site():
    if not use_local:
        xml_data = download_data(src_url)
        data = io()
        # Очищаем текст от спецсимволов
        cleaned_text = clean_text(xml_data.text)
        if cleaned_text:
            data.rewriteto('data.xml', cleaned_text)
            if data:
                print('Файл успешно сохранен.')

    return parse_large_xml('data.xml')


def parse_filedata(products_from_site):
    categories = {}
    products = {}

    for product in products_from_site:
        tmp = None
        for i in range(1, 5):
            cat_id = None
            cat_name = None
            cat_parent_id = None
            if product[f'parentid{i}'] != None:
                cat_id = product[f'parentid{i}']
                cat_name = product[f'parentid_name{i}']
                if i != 1:
                    cat_parent_id = product[f'parentid{i-1}']
                # Сохраняем значение для добавления продукта в лист
                tmp = cat_id
                # Добавляем категорию в словарь
                if cat_id and cat_id not in categories:
                    categories[cat_id] = {'id': cat_id, 'name': cat_name, 'parent_id': cat_parent_id}
            else:
                break


        # Добавляем продукт в словарь
        if product['id'] not in products:
            products[product['id']] = product
            products[product['id']]['category_id'] = tmp
            del products[product['id']]['parentid1']
            del products[product['id']]['parentid_name1']
            del products[product['id']]['parentid2']
            del products[product['id']]['parentid_name2']
            del products[product['id']]['parentid3']
            del products[product['id']]['parentid_name3']
            del products[product['id']]['parentid4']
            del products[product['id']]['parentid_name4']


    return categories, products


def rows_to_dict(rows, key_column='id'):
    result = {}
    for row in rows:
        # Создаем словарь для текущей строки
        row_dict = {key: row[key] for key in row.keys()}
        # Используем значение key_column как ключ
        result[row[key_column]] = row_dict
    return result


def compare_categories(categories_from_file, categories_from_db):
    # Сравниваем категории
    for cat_id in categories_from_file:
        keys_to_compare = ['name', 'parent_id']
        if cat_id not in categories_from_db:
            result = db.insert_categories(id=categories_from_file[cat_id]['id'], name=categories_from_file[cat_id]['name'], parent_id=categories_from_file[cat_id]['parent_id'])
            if result:
                pass
                #print(f'Добавлена категория: {categories_from_file[cat_id]["name"]}')
            else:
                print(f'Ошибка при добавлении категории')
                print(categories_from_file[cat_id])

        elif any(categories_from_file[cat_id][key] != categories_from_db[cat_id][key] for key in keys_to_compare):
            result = db.update_categories(id=cat_id, name=categories_from_file[cat_id]['name'], wp_id=categories_from_db[cat_id]['wp_id'], status='updated', parent_id=categories_from_file[cat_id]['parent_id'])
            if result:
                pass
                #print(f'Категория {categories_from_file[cat_id]["name"]} обновлена.')
            else:
                print(f'Ошибка при обновлении категории')
                print(categories_from_file[cat_id])

    for cat_id in categories_from_db:
        if cat_id not in categories_from_file:
            '''
            Тут надо дописать рекурсивное удаление. Что бы сразу находило все товары в БД по категориям и субкатегориям и удаляло внутри WP. А только потом требуется очистить БД
            '''
            result = db.update_categories(id=cat_id, name=categories_from_db[cat_id]['name'], wp_id=categories_from_db[cat_id]['wp_id'], status='deleted', wp_parent_id=categories_from_db[cat_id]['wp_parent_id'], parent_id=categories_from_db[cat_id]['parent_id'])
            #result = db.delete_categories(id=cat_id)
            if result:
                print(f'Категория {categories_from_db[cat_id]["name"]} удалена.')
            else:
                print(f'Ошибка при удалении категории')
                print(categories_from_db[cat_id])

    categories_from_file.clear()
    categories_from_db.clear()


def compare_dicts(dict1, dict2, fields):
    return all(dict1.get(field) == dict2.get(field) for field in fields)


def compare_products(products_from_file, products_from_db):
    bar = tqdm.tqdm(total=len(products_from_file))
    compare_idents = []
    # Сравниваем продукты
    for product_id in products_from_file:
        if product_id not in products_from_db:
            result = db.insert_products(products_from_file[product_id], global_timestamp)
            if result:
                pass
                #print(f'Добавлен продукт: {products_from_file[product_id]["name"]}')
            else:
                print(f'Ошибка при добавлении продукта')
                print(products_from_file[product_id])
        else:
            pr_file = products_from_file[product_id]
            pr_db = products_from_db[product_id]
            dict2compare = ['barcode', 'brand', 'country', 'description', 'media_img', 'name', 'price', 'prop_importer', 'prop_manufacturer', 'prop_purpose', 'prop_warranty']
            if compare_dicts(pr_file, pr_db, dict2compare):
                # продукты одинаковые
                compare_idents.append(product_id)
            else:
                #print(f'Продукт {products_from_file[product_id]["name"]} был обновлен.')
                result = db.update_products(products_from_file[product_id], global_timestamp)
                if result:
                    pass
                    #print(f'Продукт {products_from_file[product_id]["name"]} обновлен.')
                else:
                    print(f'Ошибка при обновлении продукта')
                    print(products_from_file[product_id])


        bar.update(1)

    bar.close()
    bar.clear()
    
    # обновляем время в продуктах где не было изменений
    if len(compare_idents) > 0:
        result = db.update_products_time(compare_idents, global_timestamp)
    if result:
        print(f'Время товаров обновлено.')
    else:
        print(f'Ошибка при обновлении времени')

    compare_idents.clear()
    products_from_file.clear()
    products_from_db.clear()


def build_category_tree(categories):
    # Создаем словарь для хранения дерева
    category_tree = {cat_id: {**cat, "subcat": {}} for cat_id, cat in categories.items()}

    # Список для хранения корневых категорий
    root_categories = {}

    # Строим дерево
    for cat_id, cat in category_tree.items():
        parent_id = cat["parent_id"]
        if parent_id is None:
            # Это корневая категория
            root_categories[cat["id"]] = cat
        else:
            # Это подкатегория, добавляем её к родителю
            if parent_id in category_tree:
                category_tree[parent_id]["subcat"][cat["id"]] = cat

    return root_categories


def process_categories(categories, wp, wp_parent_id=None):
    global db
    for category_id, category in categories.items():
        # Проверяем статус категории
        if category['status'] == 'new':
            print(f"Обрабатываем новую категорию: {category['name']} (ID: {category['id']})")
            result = wp.create_category(name=category['name'], wp_parent_id=wp_parent_id)  # Вызываем метод обработки
            if result:
                wp_id = result['id']
                wp_parent_id = result['parent'] if result['parent'] != 0 else None
                db.update_categories(id=category['id'], name=category['name'], wp_id=wp_id, status='published', parent_id=category['parent_id'], wp_parent_id=wp_parent_id)
                categories[category_id]['wp_id'] = wp_id
                categories[category_id]['wp_parent_id'] = wp_parent_id


        elif category['status'] == 'update':
            print(f"Обновляем категорию: {category['name']} (ID: {category['id']})")
            result = wp.update_category(wp_id=category['wp_id'], name=category['name'])
            if result:
                db.update_categories(id=category['id'], name=category['name'], status='published', parent_id=category['parent_id'], wp_parent_id=wp_parent_id, wp_id=category['wp_id'])

        # elif category['status'] == 'delete':
        #     print(f"Удаляем категорию: {category['name']} (ID: {category['id']})")
        #     wp.delete_category(category)

        # Рекурсивно обрабатываем подкатегории
        if 'subcat' in category and isinstance(category['subcat'], dict):
            if len(category['subcat']) > 0:
                process_categories(category['subcat'], wp, wp_parent_id=categories[category_id]['wp_id'])


def compare_wp_categories():
    global db
    global wp

    # Собираем категории
    db_categories = rows_to_dict(db.get_categories())
    categories = {}
    categories = build_category_tree(db_categories)

    # Обрабатываем категории
    process_categories(categories, wp)
    categories.clear()
    db_categories.clear()


def product_generator(product):
    global db

    # Проверяем, что product['price'] существует и является числом
    if 'price' in product and isinstance(product['price'], (int, float)):
        # Рассчитываем цену с учетом скидки
        price = product['price'] * (1 - wp_discount / 100)
        price = round(price, 2)
        price = str(price)
    else:
        # Обработка случая, когда price отсутствует или не является числом
        print("Поле 'price' отсутствует или имеет некорректный формат. Используется значение по умолчанию.")
        price = "0.00"  # Значение по умолчанию

    # Находим ID категории
    result = db.get_category_by_id(product['category_id'])
    if result:
        wp_group_id = int(result['wp_id'])
    else:
        return False

    # Обрабатываем атрибуты
    attributes = []

    if 'prop_length' in product and product['prop_length'] != None and product['prop_length'] != '':
        attributes.append({'name': 'Длина', 'options': [str(product['prop_length'])], 'visible': True, 'variation': False})

    if 'brand' in product and product['brand'] != None and product['brand'] != '':
        attributes.append({'name': 'Брэнд', 'options': [product['brand']], 'visible': True, 'variation': False})

    if 'vendor_code' in product and product['vendor_code'] != None and product['vendor_code'] != '':
        attributes.append({'name': 'Артикул производителя', 'options': [product['vendor_code']], 'visible': True, 'variation': False})

    if 'prop_purpose' in product and product['prop_purpose'] != None and product['prop_purpose'] != '':
        attributes.append({'name': 'Применение', 'options': [product['prop_purpose']], 'visible': True, 'variation': False})

    if 'prop_warranty' in product and product['prop_warranty'] != None and product['prop_warranty'] != '':
        attributes.append({'name': 'Гарантия', 'options': [str(product['prop_warranty'])], 'visible': True, 'variation': False})

    if 'prop_unit' in product and product['prop_unit'] != None and product['prop_unit'] != '':
        attributes.append({'name': 'Единица измерения', 'options': [product['prop_unit']], 'visible': True, 'variation': False})

    if 'prop_multiplicity' in product and product['prop_multiplicity'] != None and product['prop_multiplicity'] != '':
        attributes.append({'name': 'Кратность товара', 'options': [str(product['prop_multiplicity'])], 'visible': True, 'variation': False})

    if 'prop_quantity_min' in product and product['prop_quantity_min'] != None and product['prop_quantity_min'] != '':
        if product['prop_quantity_min'] != '0':
            attributes.append({'name': 'Минимальное количество для продажи', 'options': [str(product['prop_quantity_min'])], 'visible': True, 'variation': False})
        else:
            attributes.append({'name': 'Минимальное количество для продажи', 'options': ['1'], 'visible': True, 'variation': False})

    if 'prop_multiplicity_box' in product and product['prop_multiplicity_box'] != None and product['prop_multiplicity_box'] != '':
        attributes.append({'name': 'Количество в упаковке', 'options': [str(product['prop_multiplicity_box'])], 'visible': True, 'variation': False})

    if 'country' in product and product['country'] != None and product['country'] != '':
        attributes.append({'name': 'Страна производства', 'options': [product['country']], 'visible': True, 'variation': False})

    if 'prop_manufacturer' in product and product['prop_manufacturer'] != None and product['prop_manufacturer'] != '':
        attributes.append({'name': 'Производитель', 'options': [product['prop_manufacturer']], 'visible': True, 'variation': False})

    if 'prop_importer' in product and product['prop_importer'] != None and product['prop_importer'] != '':
        attributes.append({'name': 'Импортер', 'options': [product['prop_importer']], 'visible': True, 'variation': False})

    if 'barcode' in product and product['barcode'] != None and product['barcode'] != '':
        attributes.append({'name': 'Штрихкод', 'options': [str(product['barcode'])], 'visible': True, 'variation': False})

    # Dimensions
    dimensions = {}
    if 'prop_length' in product and product['prop_length'] != None and product['prop_length'] != '' and product['prop_length'] != '0':
        dimensions['length'] = str(product['prop_length'])

    if 'prop_width' in product and product['prop_width'] != None and product['prop_width'] != '' and product['prop_width'] != '0':
        dimensions['width'] = str(product['prop_width'])

    if 'prop_height' in product and product['prop_height'] != None and product['prop_height'] != '' and product['prop_height'] != '0':
        dimensions['height'] = str(product['prop_height'])

    # Обрабатываем картинки
    images = []
    i = 0
    if 'media_img' in product and product['media_img'] != None and product['media_img'] != '':
        images.append({'src': product['media_img'], 'position': i})
    path = local_img_storage + product['okdp'] + '/'
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".jpg") and file != '0.jpg':
                i += 1
                images.append({'src': wp_url + wp_img_storage + product['okdp'] + '/' + file, 'position': i})


    # Обрабатываем описание
    if product['description'] != None and product['description'] != '' and product['description'] != '---':
        description = product['description']
        html_description = description.replace("\r\n", "<br>").replace("\n", "<br>")
    else:
        html_description = 'Описание товара отсутствует.'

    # Генерируем JSON
    data = {
        'name': product['name'],
        'description': html_description,
        'type': 'simple',
        'regular_price': price,
        'sku': product['okdp'],
        'categories': [
            {'id': wp_group_id}
        ]
    }

    if 'prop_weight_gross' in product and product['prop_weight_gross'] != None and product['prop_weight_gross'] != '' and product['prop_weight_gross'] != '0':
        data['weight'] = str(product['prop_weight_gross'])

    if len(attributes) > 0:
        data['attributes'] = attributes

    if len(images) > 0:
        data['images'] = images

    if len(dimensions) > 0:
        data['dimensions'] = dimensions

    return data


def compare_wp_products():
    global db
    global wp

    many_id_2del = []

    # собираем товары из БД
    db_products = rows_to_dict(db.get_all_products())
    for id in db_products:
        status = db_products[id]['status']
        if status == 'new':
            print(f"Добавляем новый продукт: {db_products[id]['name']}")
            product_json = product_generator(db_products[id])
            status_code, result = wp.create_product(product_json)
            if status_code is not None and status_code == 201:
                wp_id = int(result['id'])
                db.update_product_wpid(id, wp_id)
        elif status == 'updated':
            print(f"Обновляем продукт: {db_products[id]['name']}")
            product_json = product_generator(db_products[id])
            status_code, result = wp.update_product(db_products[id]['wp_id'], product_json)
            if status_code is not None and status_code == 201:
                wp_id = result['id']
                db.update_product_wpid(id, wp_id)
        else:
            pass

        # Обрабатываем продукты
        if db_products[id]['timedata'] != global_timestamp:
            result = db.delete_product(id)
            if db_products[id]['wp_id'] != None:
                print(f"Удаляем продукт: {db_products[id]['name']}")
                many_id_2del.append(db_products[id]['wp_id'])
                #wp.delete_product(db_products[id]['wp_id'])

    wp.batch_delete_product(many_id_2del)
    db_products.clear()


def main():
    global help
    global db
    global wp
    help = k2()
    db = sql()

    # Подключаемся к базе данных
    if not db.connect():
        print('Соединение с базой данных не установлено.')
        quit()
    # Очищаем базу данных
    if clear_db:
        db.destroy_data()
        print('База данных очищена.')

    # Получаем данные с сайта или локального файла
    products_from_site = get_from_site()
    file_categories, file_products = parse_filedata(products_from_site)
    print(f'Получено {len(file_categories)} категорий и {len(file_products)} продуктов.')

    # Получаем данные из БД
    # Собираем категории
    db_categories = rows_to_dict(db.get_categories())
    # Собираем товары
    db_products = rows_to_dict(db.get_all_products())

    # Отправляем в проверку категории
    compare_categories(file_categories, db_categories)

    # Отправляем в проверку продукты
    compare_products(file_products, db_products)

    # # Начинаем работать с Wordpress
    wp = WooCommerceAPI(wp_url, wp_key, wp_secret)
    if wp.connect():
        compare_wp_categories()
        compare_wp_products()



if __name__ == '__main__':
    os.environ['TERM'] = 'xterm'  # Установка переменной TERM
    os.system('clear')
    main()