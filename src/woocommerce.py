import os
import requests
import json

class WooCommerce:
    def __init__(self, url, api_key):
        self.url = url.rstrip('/') + '/wp-json/wc/v2/'
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        if not self.api_key:
            raise ValueError("API key is required. Set it via environment variable or pass it explicitly.")

    def connect(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                print("Successfully connected to WooCommerce API.")
                return True
            else:
                print(f"Error connecting to WooCommerce API: {response.status_code}")
                print(response.json())
                return False
        except Exception as e:
            print(f"Error while connecting to WooCommerce API: {e}")
            return False

    def add_item(self, product_data):
        try:
            api_url = self.url + 'products'
            response = requests.post(api_url, headers=self.headers, json=product_data)

            if response.status_code == 201:
                print("Product added successfully.")
                return response.json()
            else:
                print(f"Error adding product: {response.status_code}")
                print(response.json())
                return None
        except Exception as e:
            print(f"Error while adding product: {e}")
            return None
