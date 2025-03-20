from sqlalchemy import (
    Column, Integer, String, REAL, ForeignKey, Text, Boolean, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

# Base = declarative_base()


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wp_id = Column(Integer)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=True)
    status = Column(String(50), default='new')

    # Связь с подкатегориями
    subcategories = relationship("Category", backref=backref("parent", remote_side=[id]))

    # Связь с продуктами
    products = relationship("Product", backref="category",
                            foreign_keys="[Product.category_id]")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=False)
    okdp = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    vendor_code = Column(String(100))
    brand = Column(String(100))
    price = Column(REAL)
    price_recommended = Column(REAL)
    price_recommended_713 = Column(REAL)
    warehouse_main = Column(String(255))
    warehouse_add = Column(String(255))
    warehouse_rb = Column(String(255))
    warehouse_all = Column(String(255))
    delivery = Column(String(255))
    vat = Column(Integer)
    barcode = Column(Integer)
    barcode_old = Column(Integer)
    country = Column(String(100))
    description = Column(Text)
    prop_new = Column(Boolean)
    prop_purpose = Column(String(255))
    prop_warranty = Column(Integer)
    prop_shelf_life = Column(String(50))
    prop_quantity_min = Column(String(50))
    prop_length = Column(REAL)
    prop_width = Column(REAL)
    prop_height = Column(REAL)
    prop_weight_gross = Column(REAL)
    prop_unit = Column(String(50))
    prop_multiplicity = Column(Integer)
    prop_multiplicity_box = Column(Integer)
    prop_tnved = Column(Integer)
    prop_codecustom = Column(Integer)
    prop_manufacturer = Column(String(255))
    prop_importer = Column(String(255))
    prop_713 = Column(Integer)
    prop_promo_price = Column(REAL)
    prop_promo_date_finish = Column(String(50))
    media_img = Column(String(255))
    media_video = Column(String(255))
    timedata = Column(Integer)
    status = Column(String(50), default='new')

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name})>"


# # Подключение к базе
# engine = create_engine('sqlite:///mydatabase.db', echo=False)
# Base.metadata.create_all(engine)  # Создаем таблицы (если их нет)
#
# # Создаем сессию
# Session = sessionmaker(bind=engine)
# session = Session()

# 1. Добавление категории
# # Создаем родительскую категорию
# parent_category = Category(name="Электроника")
# session.add(parent_category)
# session.commit()
#
# # Создаем подкатегорию
# child_category = Category(
#     name="Фены",
#     parent_id=parent_category.id  # Связь через parent_id
# )
# session.add(child_category)
# session.commit()
#
# 2. Добавление товара
# # Добавляем товар в подкатегорию "Фены"
# new_product = Product(
#     category_id=child_category.id,
#     okdp="123456789",
#     name="Тестовый фен",
#     price=99.99,
#     media_img="https://example.com/fen.jpg",
#     prop_new=True
# )
# session.add(new_product)
# session.commit()
#
# 3. Обновление данных
# # Находим категорию
# category = session.query(Category).filter_by(name="Фены").first()
# category.status = "active"
# session.commit()
#
#
# 4. Выборка с связями
# # Получаем все товары категории "Фены"
# products = session.query(Product).join(Category).filter(
#     Category.name == "Фены"
# ).all()
#
# for product in products:
#     print(f"Товар: {product.name}, Категория: {product.category.name}")
#
# 5. Удаление
# # Удаляем категорию (удалит все подкатегории из-за CASCADE)
# session.delete(parent_category)
# session.commit()

# Полезные методы:
# # Фильтрация
# products = session.query(Product).filter(
#     Product.price > 100,
#     Product.category.has(name="Фены")
# ).all()
#
# # Обновление нескольких записей
# session.query(Category).filter(Category.status == 'new').update({
#     Category.status: 'active'
# }, synchronize_session=False)
#
# # Удаление через запрос
# session.query(Product).filter(Product.id == 123).delete()
#
# Для сложных запросов :
# Используйте join и filter для работы с связанными таблицами:
# from sqlalchemy import or_
#
# results = session.query(Product).join(Category).filter(
#     or_(
#         Category.name == "Фены",
#         Product.brand == "Braun"
#     )
# ).all()
#
# Транзакции :
# try:
#     session.add(new_product)
#     session.commit()
# except Exception as e:
#     session.rollback()
#     print(f"Ошибка: {e}")
#
# Автокоммит
# with Session() as session:
#     product = Product(...)
#     session.add(product)
#     session.commit()