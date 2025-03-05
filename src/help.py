#coding: utf-8

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
