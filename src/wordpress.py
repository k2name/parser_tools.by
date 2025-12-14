import os
import mimetypes
import requests
from requests.auth import HTTPBasicAuth

class WordpressAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()

    def get_mime_type(self, filename):
        """Определяет MIME-тип по расширению файла"""
        # Сначала пробуем определить по расширению
        mime_type, _ = mimetypes.guess_type(filename)

        # Если не удалось определить, используем fallback
        if not mime_type:
            extension = os.path.splitext(filename)[1].lower()

            # Сопоставление расширений с MIME-типами
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
                '.svg': 'image/svg+xml',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.zip': 'application/zip',
                '.mp4': 'video/mp4',
                '.mp3': 'audio/mpeg',
            }

            mime_type = mime_map.get(extension, 'application/octet-stream')

        return mime_type


    def import_media_from_url(self, image_url):
        # скачиваем изображение
        img_response = self.session.get(image_url)
        if img_response.status_code != 200:
            print("Failed to download image:", img_response.status_code)
            return None

        img_bytes = img_response.content
        filename = image_url.split('/')[-1]

        # Определяем MIME-тип
        content_type = self.get_mime_type(filename)
        # отправляем в WordPress
        wp_response = self.session.post(
            f"{self.api_url}/media",
            data=img_bytes,
            auth=self.auth,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            }
        )

        if wp_response.status_code == 201:
            return wp_response.json()
        else:
            print("Upload failed:", wp_response.status_code, wp_response.text)
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()