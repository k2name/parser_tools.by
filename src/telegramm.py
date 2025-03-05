import time
import json
import requests


class TelegramBot:
    def __init__(self, token, chat_id, time_sleep=10, silent=False):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.time_sleep = time_sleep
        self.silent = silent

    def send_text_message(self, message):
        url = self.base_url + "sendMessage"
        params = {"chat_id": self.chat_id, "text": message, "disable_notification": self.silent}
        response = requests.post(url, data=params)
        return response.json()

    def send_html_message(self, message):
        url = self.base_url + "sendMessage"
        params = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML", "disable_notification": self.silent}
        response = requests.post(url, data=params)
        return response.json()

    def send_photo_message(self, photo_url, caption=""):
        url = self.base_url + "sendPhoto"
        params = {"chat_id": self.chat_id, "photo": photo_url, "caption": caption, "disable_notification": self.silent}
        response = requests.post(url, data=params)
        return response.json()

    def send_html_photo_message(self, photo_url, caption=""):
        url = self.base_url + "sendPhoto"
        params = {"chat_id": self.chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML", "disable_notification": self.silent}
        response = requests.post(url, data=params)
        return response.json()

    def send_album_message(self, photo_urls, caption=""):
        url = self.base_url + "sendMediaGroup"
        media = [{'type': 'photo', 'media': photo_urls[i], 'caption': caption if i == 0 else ''} for i in
                 range(len(photo_urls))]
        params = {"chat_id": self.chat_id, "media": json.dumps(media), "disable_notification": self.silent}
        response = requests.post(url, data=params)
        return response.json()

    def sender(self, msg_type, text=False, photo=False, chat_id=False, silent=False):
        time_sleep = self.time_sleep
        result = False
        # Добавка идентификатора чата для случаев когда надо отправить в конкретный чат а не дефолтный
        if chat_id:
            self.chat_id = chat_id
        # Добавка отдельной обработки безшумного режима
        if silent:
            self.silent = silent

        count = 0
        while not result:
            if msg_type == 'text':
                result = self.send_text_message(text)
            elif msg_type == 'photo':
                result = self.send_photo_message(photo, text)
            elif msg_type == 'album':
                result = self.send_album_message(photo, text)
            else:
                result = self.send_text_message(text)

            # проверяем рузельтат отправки сообщения и пишем в лог
            if result['ok']:
                print('Сообщение отправлено в телеграм')
                result = True
                return result
            elif result['error_code'] == 429:
                time_sleep = int(result['parameters']['retry_after'])
                print(f'Ошибка отправки сообщения в телеграм №429. Ждем {self.time_sleep} секунд.')
                result = False
            elif result['error_code'] == 400:
                print(f'Ошибка отправки сообщения в телеграм №400\n{result}\n')
                photo = 'https://dev.dlab.im/tg/broken2.jpg'
                result = False
            elif result['error_code'] == 404:
                print(f'Ошибка отправки сообщения в телеграм №404\n{result}.\n')
                result = False
            else:
                print(f'Неизвестная ошибка отправки сообщения в телеграм\n{result}')
                result = True
                return result

            if count > 5:
                print('Слишком много ошибок. Прерываем цикл')
                return result

            if not result:
                count += 1
                time.sleep(count*time_sleep)