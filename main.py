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
            if products_from_file[product_id]['category_id'] != products_from_db[product_id]['category_id']:
                print(f'Продукт {products_from_file[product_id]["name"]} был обновлен.')
                result = db.update_products(products_from_file[product_id], global_timestamp)
                if result:
                    pass
                    #print(f'Продукт {products_from_file[product_id]["name"]} обновлен.')
                else:
                    print(f'Ошибка при обновлении продукта')
                    print(products_from_file[product_id])
            else:
                compare_idents.append(product_id)

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


def compare_wp_products():
    pass


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

    # Начинаем работать с Wordpress
    wp = WooCommerceAPI(wp_url, wp_key, wp_secret)
    if wp.connect():
        compare_wp_categories()
        compare_wp_products()



if __name__ == '__main__':
    os.environ['TERM'] = 'xterm'  # Установка переменной TERM
    os.system('clear')
    main()