import requests
import time
import re
import unicodedata
from requests.auth import HTTPBasicAuth

# таблица транслитерации максимально близкая к WP + общая практика
TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch',
    'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya'
}

class WooCommerceAPI:
    def __init__(self, url, consumer_key, consumer_secret, api_version='wc/v3'):
        self.url = url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = api_version
        self.connection_timeout = 10
        self.read_timeout = 15

    def _get_auth(self):
        return HTTPBasicAuth(self.consumer_key, self.consumer_secret)

    def connect(self):
        """Проверяет связь с API и валидность токена"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/system_status"
        try:
            response = requests.get(
                endpoint,
                auth=self._get_auth(),
                timeout=(self.connection_timeout, self.read_timeout)
            )
            if response.status_code == 200:
                print("Соединение успешно установлено")
                return True
            else:
                print(f"Ошибка соединения: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Не удалось установить соединение: {e}")
            return False

    def slugify(self, text: str, max_length: int = 200) -> str:
        # нормализация Unicode
        text = unicodedata.normalize("NFKD", text)

        # перевод в нижний регистр
        text = text.lower()

        # транслитерация кириллицы
        result = []
        for char in text:
            if char in TRANSLIT:
                result.append(TRANSLIT[char])
            else:
                result.append(char)

        text = ''.join(result)

        # убрать все, кроме букв, цифр и дефиса
        text = re.sub(r'[^a-z0-9\- ]+', '', text)

        # заменить пробелы на дефисы
        text = text.replace(' ', '-')

        # удалить повторяющиеся дефисы
        text = re.sub(r'-+', '-', text)

        # убрать дефисы по краям
        text = text.strip('-')

        # обрезать по длине
        if len(text) > max_length:
            text = text[:max_length].rstrip('-')

        # если вдруг получилось пусто — создать slug заглушку
        if not text:
            text = "category"

        return text

    def get_all_products(self, per_page=100):
        """Получает все продукты"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"
        all_products = []
        page = 1
        while True:
            cur_time = time.time()
            if page == 5:
                break
            # Получаем продукты постранично
            data = {
                "page": page,  # Номер страницы
                "per_page": per_page  # Количество продуктов на странице (максимум 100)
            }
            # Набиваем запрос
            try:
                response = requests.get(
                    endpoint,
                    auth=self._get_auth(),
                    json = data,
                    timeout=(self.connection_timeout, self.read_timeout)
                )
                response.raise_for_status()
            except requests.exceptions.ConnectTimeout:
                print(f'Не удалось установить соединение за {self.connection_timeout} секунд')
                return None
            except requests.exceptions.ReadTimeout:
                print(f'Сервер не ответил за {self.read_timeout} секунд')
                return None
            except requests.exceptions.HTTPError as e:
                print(f"HTTP ошибка: {e}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"Другая ошибка запроса: {e}")
                return None

            print(f'Получена страница {page} за {round(time.time() - cur_time, 2)} секунд')
            if response.status_code == 200 or response.status_code == 201:
                products = response.json()
                if not products:
                    break
                all_products.extend(products)
                page += 1
            else:
                print(f"Ошибка при получении продуктов: {response.status_code}")
                print(response.text)
                break

        return all_products

    # Категории и подкатегории
    def create_category(self, name, wp_parent_id=None, description=None, image=None):
        """Создает категорию или подкатегорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories"
        data = {
            'name': name,
            'slug': self.slugify(name),
            'parent': wp_parent_id if wp_parent_id is not None else 0,
            'description': description,
            'image': image
        }
        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data,
            timeout=(self.connection_timeout, self.read_timeout)
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка при создании категории: {e}")
            print(f"Текст ответа: {response.text}")  # Выводим детали ошибки
            raise
        return response.json()

    def update_category(self, wp_id, name, description=None, image=None):
        """Обновляет категорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories/{wp_id}"
        data = {
            'name': name,
            'slug': self.slugify(name),
            'description': description,
            'image': image,
            'visibility': 'visible',
        }

        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data,
            timeout=(self.connection_timeout, self.read_timeout)
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка при создании категории: {e}")
            print(f"Текст ответа: {response.text}")  # Выводим детали ошибки
            raise
        return response.json()

    def update_category_visibility(self, wp_id, visibility=True):
        """Обновляет категорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories/{wp_id}"
        data = {
            "display": "default" if visibility else "hidden"
        }

        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data,
            timeout=(self.connection_timeout, self.read_timeout)
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка при создании категории: {e}")
            print(f"Текст ответа: {response.text}")  # Выводим детали ошибки
            raise
        return response.json()

    def delete_category(self, category_id):
        """Удаляет категорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories/{category_id}"
        response = requests.delete(
            endpoint,
            auth=self._get_auth(),
            timeout=(self.connection_timeout, self.read_timeout)
        )
        response.raise_for_status()
        return response.json()

    # Продукты

    def create_product(self, data):
        """Создает продукт с категорией и изображением"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"

        # Проверка на существование товара с этим SKU
        check_exits = self.check_sku_exists(data['sku'])
        if check_exits:
            print(f"Товар с SKU {data['sku']} уже существует.")
            count = 0
            result = False
            while not result:
                count += 1
                print(f"Попытка удалить продукт. Попытка {count}")
                result = self.delete_product(check_exits)
                if count > 3:
                    return None, False

        try:
            response = requests.post(
                endpoint,
                auth=self._get_auth(),
                json=data,
                timeout=(self.connection_timeout, self.read_timeout)
            )

            response.raise_for_status()
            if response.status_code == 201:
                return response.status_code, response.json()
            else:
                return response.status_code, False

        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Ошибка при создании продукта: {e}")
            return None, False

    def update_product(self, wp_id, data):
        """Обновляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{wp_id}"
        try:
            response = requests.put(
                endpoint,
                auth=self._get_auth(),
                json=data,
                timeout=(self.connection_timeout, self.read_timeout)
            )
            response.raise_for_status()
            if response.status_code == 201:
                return response.status_code, response.json()
            else:
                return response.status_code, False

        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Ошибка при обновлении продукта: {e}")
            return None, False

    def delete_product(self, product_id):
        """Удаляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{product_id}"
        try:
            response = requests.delete(
                endpoint,
                auth=self._get_auth(),
                params={"force": True},
                timeout=(self.connection_timeout, self.read_timeout)
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Ошибка при удалении продукта: {e}")
            return False

    def batch_delete_product(self, ids):
        """Удаляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/batch"

        if len(ids) > 0:
            data = {
                'delete': ids
            }
        else:
            return False

        try:
            response = requests.post(
                endpoint,
                auth=self._get_auth(),
                headers={"Content-Type": "application/json"},
                json=data,
                params={"force": True}
            )

            response.raise_for_status()
            if response.status_code == 201 or response.status_code == 200:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Ошибка при пакетном удалении продуктов: {e}")
            return False

    def cat_processor(self, category):
        """Обрабатывает категорию"""
        print(category)

    def check_sku_exists(self, sku):
        """Проверяет, существует ли товар с указанным SKU"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"
        try:
            response = requests.get(
                endpoint,
                auth=self._get_auth(),
                params={'sku': sku},
                timeout=(self.connection_timeout, self.read_timeout)
            ).json()

            if len(response) > 0:
                product_id = response[0]["id"]
                return product_id
            else:
                return False
        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Ошибка при проверке существования продукта: {e}")
            return False

    # Изображения
    def upload_image(self, image_url):

        endpoint = f"{self.url}/wp-json/{self.api_version}/products/images"

        try:
            response = requests.post(
                endpoint,
                auth=self._get_auth(),
                json={"src": image_url},
                timeout=(self.connection_timeout, self.read_timeout)
            )
            response.raise_for_status()
            return response.json()  # Возвращает данные изображения, включая ID
        except Exception as e:
            print(f"Ошибка загрузки изображения: {str(e)}")
            return False


    def delete_single_image(self, image_id):

        endpoint = f"{self.url}/wp-json/{self.api_version}/products/images/{image_id}"

        try:
            response = requests.delete(
                endpoint,
                auth=self._get_auth(),
                params={"force": True},
                timeout=(self.connection_timeout, self.read_timeout)
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка удаления изображения {image_id}: {str(e)}")
            return False


    def batch_delete_images(self, images, chunk_size=50):
        """
        Пакетное удаление изображений через WooCommerce API.
        Возвращает True, если все операции успешны.
        """
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/images//batch"
        all_success = True

        for i in range(0, len(images), chunk_size):
            chunk = images[i:i + chunk_size]
            data = {"delete": chunk}

            try:
                response = requests.post(
                    endpoint,
                    auth=self._get_auth(),
                    json=data,
                    params={"force": True},
                    timeout=(self.connection_timeout, self.read_timeout)
                )
                if response.status_code != 200:
                    print(f"Ошибка при удалении пачки: {response.text}")
                    all_success = False
            except Exception as e:
                print(f"Ошибка запроса: {str(e)}")
                all_success = False

        return all_success