#coding: utf-8
import re

class k2:
    def clear_string(self, data):
        while '  ' in data:
            data = data.replace('  ', ' ')
        data = data.replace('\r\n', '')
        data = data.replace('\n', '')
        data = data.replace('\r', '')
        data = data.replace('\t', ' ')
        data = data.replace('«', '"')
        data = data.replace('»', '"')
        data = data.replace('""', '"')
        data = data.replace("''", "'")
        data = data.replace(';', '')
        data = data.replace('(', '')
        data = data.replace(')', '')
        data = data.strip()
        return data

    def printable_string(self, data):
        return [char for char in data if char.isprintable()]

    def get_unique_values(self, arr):
        # Преобразуем список в множество для удаления дубликатов
        unique_values = set(arr)
        # Преобразуем множество обратно в список
        return list(unique_values)


class TextProcessor:
    def __init__(self):
        # Транслитерационная таблица
        self.translit_dict = {
            'а': 'a',   'б': 'b',   'в': 'v',   'г': 'g',
            'д': 'd',   'е': 'e',   'ё': 'e',   'ж': 'zh',
            'з': 'z',   'и': 'i',   'й': 'y',   'к': 'k',
            'л': 'l',   'м': 'm',   'н': 'n',   'о': 'o',
            'п': 'p',   'р': 'r',   'с': 's',   'т': 't',
            'у': 'u',   'ф': 'f',   'х': 'kh',  'ц': 'ts',
            'ч': 'ch',  'ш': 'sh',  'щ': 'shch','ъ': '',
            'ы': 'y',   'ь': '',    'э': 'e',   'ю': 'yu',
            'я': 'ya',
            # заглавные буквы
            'А': 'A',   'Б': 'B',   'В': 'V',   'Г': 'G',
            'Д': 'D',   'Е': 'E',   'Ё': 'E',   'Ж': 'Zh',
            'З': 'Z',   'И': 'I',   'Й': 'Y',   'К': 'K',
            'Л': 'L',   'М': 'M',   'Н': 'N',   'О': 'O',
            'П': 'P',   'Р': 'R',   'С': 'S',   'Т': 'T',
            'У': 'U',   'Ф': 'F',   'Х': 'Kh',  'Ц': 'Ts',
            'Ч': 'Ch',  'Ш': 'Sh',  'Щ': 'Shch','Ъ': '',
            'Ы': 'Y',   'Ь': '',    'Э': 'E',   'Ю': 'Yu',
            'Я': 'Ya'
        }

    def is_cyrillic(self, text):
        """Проверяет, содержит ли строка кириллические символы"""
        return bool(re.search('[а-яА-ЯёЁ]', text))

    def translit_russian(self, text):
        """Простейшая транслитерация русских букв в латиницу"""
        return ''.join(self.translit_dict.get(c, c) for c in text)

    def run(self, text):
        """Обрабатывает текст: транслит (если нужно), lowercase, пробелы на _"""
        if self.is_cyrillic(text):
            text = self.translit_russian(text)

        # Переводим в нижний регистр и заменяем пробелы на подчеркивания
        return text.lower().replace(' ', '_')