#coding: utf-8

import sqlite3

class sql:
    def __init__(self):
        self.conn = None

    def usage(self, status):
        self.status = status
        return status


    def connect(self):
        if not self.conn:
            try:
                self.conn = sqlite3.connect('db/base.db', check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
                self.conn.isolation_level = None
                self.conn.text_factory = str
                return True
            except sqlite3.Error as e:
                print("Соединение с БД НЕ установлено!!! Ошибка: {e}")
                return False
        else:
            return True


    def destroy_data(self):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("DELETE from `products`;")
            cur.execute("DELETE from `categories`;")
            cur.execute("DELETE FROM sqlite_sequence;")
            self.conn.commit()
            cur.close()
            return True
        except:
            return False


    # =========Категории========
    def get_categories(self):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `categories`;")
            result = cur.fetchall()
            cur.close()
            return result
        except:
            return False


    def get_category_by_id(self, id):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute(f"SELECT * FROM `categories` WHERE `id`={id};")
            result = cur.fetchone()
            cur.close()
            return result
        except:
            return False


    def get_category_by_parent_id(self, parent_id):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute(f"SELECT * FROM `categories` WHERE `parent_id`={parent_id};")
            result = cur.fetchall()
            cur.close()
            return result
        except:
            return False


    def get_category_by_status(self, status='new'):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute(f"SELECT * FROM `categories` WHERE `status`={status};")
            result = cur.fetchall()
            cur.close()
            return result
        except:
            return False


    def insert_categories(self, id, name, parent_id, wp_id=None, status='new'):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO `categories` (`id`, `wp_id`, `name`, `parent_id`, `status`) VALUES (?,?,?,?,?);", (id, wp_id, name, parent_id, status))
            # Получаем последний автоинкрементный id
            last_id = cur.lastrowid
            self.conn.commit()
            cur.close()
            return last_id
        except:
            return False


    def update_categories(self, id, name, parent_id, wp_id=None, wp_parent_id=None, status='updated', ):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE `categories` SET `wp_id`=?, `wp_parent_id`=?, `name`=?, `parent_id`=?, status=? WHERE `id`=?;", (wp_id, wp_parent_id, name, parent_id, status, id))
            self.conn.commit()
            cur.close()
            return True
        except:
            return False


    def update_many_categories_status(self, ids, status='updated', ):
        if not ids:
            return False

        if not self.conn:
            self.connect()

        placeholders = ', '.join(['?'] * len(ids))  # Создаем плейсхолдеры для каждого id
        sql = f"UPDATE `categories` SET `status` = ? WHERE id IN ({placeholders});"

        # Значения для обновления: status + список id
        values = [status] + ids

        try:
            # Выполняем запрос
            cur = self.conn.cursor()
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении статуса категорий: {e}")
            return False


    def delete_categories(self, id):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("DELETE FROM `categories` WHERE `id`=?;", (id,))
            self.conn.commit()
            cur.close()
            return True
        except:
            return False

    # =========Товары===========
    def get_all_products(self):
        if not self.conn:
            self.connect()

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `products`;")
            result = cur.fetchall()
            cur.close()
            return result
        except:
            return False


    def insert_products(self, product, global_timestamp):
        if not self.conn:
            self.connect()

        # Обязательные поля
        required_fields = ['category_id', 'okdp', 'name']

        # Проверяем наличие обязательных полей
        for field in required_fields:
            if field not in product:
                print(f"Ошибка: отсутствует обязательное поле '{field}'.")
                return False

        if 'id' in product:
            del product['id']

        # Добавляем timedata в product, если его нет
        if 'timedata' not in product:
            product['timedata'] = global_timestamp

        # Формируем SQL-запрос
        columns = ', '.join(product.keys())  # Имена столбцов
        placeholders = ', '.join(['?'] * len(product))  # Плейсхолдеры для параметров
        sql = f"INSERT INTO products ({columns}) VALUES ({placeholders});"

        # Значения для вставки (в том же порядке, что и столбцы)
        values = tuple(product.values())

        # Выполняем запрос
        cur = self.conn.cursor()
        try:
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Ошибка целостности данных: {e}")
            print(sql)
            return False
        except sqlite3.OperationalError as e:
            print(f"Ошибка выполнения запроса: {e}")
            print(sql)
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            print(sql)
            return False


    def update_products(self, product, global_timestamp):
        if not self.conn:
            self.connect()

        # Проверяем наличие обязательного поля 'okdp'
        if 'okdp' not in product:
            print("Ошибка: отсутствует обязательное поле 'okdp'.")
            return False

        if 'id' in product:
            del product['id']

        # Добавляем timedata в product, если его нет
        if 'timedata' not in product:
            product['timedata'] = global_timestamp
            product['status'] = 'updated'

        # Убираем 'okdp' из словаря, так как он используется в WHERE
        product_okdp = product['okdp']
        del product['okdp']

        # Формируем SQL-запрос
        set_clause = ', '.join([f"{key} = ?" for key in product.keys()])  # SET column1 = ?, column2 = ?
        sql = f"UPDATE products SET {set_clause} WHERE okdp = ?;"

        # Значения для обновления (в том же порядке, что и в SET) + okdp для WHERE
        values = tuple(product.values()) + (product_okdp,)

        # Выполняем запрос
        cur = self.conn.cursor()
        try:
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Ошибка целостности данных: {e}")
            print(sql)
            return False
        except sqlite3.OperationalError as e:
            print(f"Ошибка выполнения запроса: {e}")
            print(sql)
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            print(sql)
            return False


    def update_product_wpid(self, okdp, wp_id):
        if not self.conn:
            self.connect()

        product = {'wp_id': wp_id, 'status': 'published'}

        # Формируем SQL-запрос
        set_clause = ', '.join([f"{key} = ?" for key in product.keys()])  # SET column1 = ?, column2 = ?
        sql = f"UPDATE products SET {set_clause} WHERE okdp = ?;"

        # Значения для обновления (в том же порядке, что и в SET) + id для WHERE
        values = tuple(product.values()) + (okdp,)

        # Выполняем запрос
        cur = self.conn.cursor()
        try:
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Ошибка целостности данных: {e}")
            return False
        except sqlite3.OperationalError as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            return False


    def update_product_status(self, okdp, global_timestamp, status='updated'):
        # Проверяем, что соединение с базой данных установлено
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = f"UPDATE products SET timestamp = ?, status = ? WHERE okdp = ?;"

        # Значения для обновления: status + okdp
        values = (global_timestamp, status, okdp)

        # Выполняем запрос
        cur = self.conn.cursor()
        try:
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()
            return True
        except sqlite3.OperationalError as e:
            print(f"Ошибка выполнения запроса: {e}")
            print(sql)
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            print(sql)
            return False


    def update_products_time(self, product_okdp, timedata):
        # Проверяем, что соединение с базой данных установлено
        if not self.conn:
            self.connect()

        # Проверяем, что массив okdp не пустой и является списком
        if not isinstance(product_okdp, list) or not product_okdp:
            print("Ошибка: массив okdp должен быть непустым списком.")
            return False

        # Проверяем, что timedata имеет корректный тип (например, int или float)
        if not isinstance(timedata, (int, float)):
            print("Ошибка: timedata должен быть числовым значением.")
            return False

        try:
            # Формируем SQL-запрос
            placeholders = ', '.join(['?'] * len(product_okdp))  # Создаем плейсхолдеры для каждого okdp
            sql = f"UPDATE products SET timedata = ? WHERE okdp IN ({placeholders});"

            # Значения для обновления: timedata + список okdp
            values = [timedata] + product_okdp

            # Выполняем запрос
            cur = self.conn.cursor()
            cur.execute(sql, values)
            self.conn.commit()
            cur.close()

            return True

        except sqlite3.IntegrityError as e:
            print(f"Ошибка целостности данных: {e}")
            print(sql)
            return False
        except sqlite3.OperationalError as e:
            print(f"Ошибка выполнения запроса: {e}")
            print(sql)
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            print(sql)
            return False


    def get_product_by_id(self, product_okdp):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "SELECT * FROM products WHERE okdp = ?;"

        # Выполняем запрос
        cur = self.conn.cursor()
        cur.execute(sql, (product_okdp,))
        result = cur.fetchone()
        cur.close()

        if result:
            return result
        else:
            return False


    def get_products_by_status(self, status):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "SELECT * FROM products WHERE status = ?;"

        try:
            # Выполняем запрос
            cur = self.conn.cursor()
            cur.execute(sql, (status,))
            result = cur.fetchall()
            cur.close()

            return result
        except:
            return False

    def delete_product(self, okdp):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "DELETE FROM products WHERE okdp = ?;"

        # Выполняем запрос
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (okdp,))
            self.conn.commit()
            cur.close()
            return True
        except:
            return False

    # =========Изображения===========
    def get_all_images(self):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "SELECT * FROM images;"

        # Выполняем запрос
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()

            return result
        except:
            return False

    def get_image_by_url(self, orig_url):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "SELECT * FROM images WHERE orig_url = ?;"

        # Выполняем запрос
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (orig_url,))
            result = cur.fetchone()
            cur.close()

            return result
        except:
            return False

    def insert_image(self, okdp, orig_url):
        if not self.conn:
            self.connect()

        # Формируем SQL-запрос
        sql = "INSERT INTO images (okdp, orig_url) VALUES (?, ?);"

        # Выполняем запрос
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (okdp, orig_url))
            self.conn.commit()
            cur.close()
            return True
        except:
            return False
