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
        """Подключается к API"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"
        response = requests.get(
            endpoint,
            auth=self._get_auth()
        )
        response.raise_for_status()
        return response.json()


    # Категории и подкатегории
    def create_category(self, name, parent_id=None):
        """Создает категорию или подкатегорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories"
        data = {
            'name': name,
            'parent': parent_id  # None для основной категории
        }
        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def update_category(self, category_id, data):
        """Обновляет категорию"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/categories/{category_id}"
        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
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

    def create_product(self, name, description, price, category_id, image_id):
        """Создает продукт с категорией и изображением"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products"
        data = {
            'name': name,
            'description': description,
            'regular_price': str(price),
            'categories': [{'id': category_id}],
            'images': [{'id': image_id}]
        }
        response = requests.post(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def update_product(self, product_id, data):
        """Обновляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{product_id}"
        response = requests.put(
            endpoint,
            auth=self._get_auth(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_product(self, product_id):
        """Удаляет продукт"""
        endpoint = f"{self.url}/wp-json/{self.api_version}/products/{product_id}"
        response = requests.delete(
            endpoint,
            auth=self._get_auth()
        )
        response.raise_for_status()
        return response.json()