import requests
from requests.auth import HTTPBasicAuth

class WooCommerceAPI:
    def __init__(self, url, consumer_key, consumer_secret, api_version='wc/v3'):
        self.url = url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = api_version

    def _get_auth(self):
        return HTTPBasicAuth(self.consumer_key, self.consumer_secret)

    def connect(self):
        """Проверяет связь с API и валидность токена"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/system_status"
        try:
            response = requests.get(
                endpoint,
                auth=self._get_auth(),
                timeout=10  # Установка таймаута
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

    # Категории и подкатегории
    def create_category(self, name, wp_parent_id=None, description=None, image=None):
        """Создает категорию или подкатегорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories"
        data = {
            'name': name,
            'parent': wp_parent_id if wp_parent_id is not None else 0,
            'description': description,
            'image': image
        }
        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data
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
            'description': description,
            'image': image
        }

        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data
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
            auth=self._get_auth()
        )
        response.raise_for_status()
        return response.json()

    # Продукты
    def upload_image(self, image_url):
        """Загружает изображение по URL"""
        endpoint = f"{self.url}/wp-json/wp/v2/media"
        data = {
            'title': 'Uploaded Image',
            'description': 'Image uploaded via API',
            'media_type': 'image',
            'source_url': image_url
        }
        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
        return response.json()['id']

    def create_product(self, data):
        """Создает продукт с категорией и изображением"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"

        # Проверка на существование товара с этим SKU
        check_exits = self.check_sku_exists(data['sku'])
        if check_exits:
            print(f"Товар с SKU {data['sku']} уже существует.")
            self.delete_product(check_exits)

        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data
        )

        response.raise_for_status()
        if response.status_code == 201:
            return response.status_code, response.json()
        else:
            return response.status_code, False

    def update_product(self, wp_id, data):
        """Обновляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{wp_id}"
        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
        if response.status_code == 201:
            return response.status_code, response.json()
        else:
            return response.status_code, False

    def delete_product(self, product_id):
        """Удаляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{product_id}"
        response = requests.delete(
            endpoint,
            auth=self._get_auth(),
            params={"force": True}
        )

        response.raise_for_status()
        return response.json()

    def batch_delete_product(self, ids):
        """Удаляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/batch"

        if len(ids) > 0:
            data = {
                'delete': ids
            }
        else:
            return False

        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            headers={"Content-Type": "application/json"},
            json=data,
            params={"force": True}
        )

        response.raise_for_status()
        return response.json()


    def cat_processor(self, category):
        """Обрабатывает категорию"""
        print(category)

    def check_sku_exists(self, sku):
        """Проверяет, существует ли товар с указанным SKU"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"
        response = requests.get(
            endpoint,
            auth=self._get_auth(),
            params={'sku': sku}
        ).json()

        if len(response) > 0:
            product_id = response[0]["id"]
            return product_id
        else:
            return False
