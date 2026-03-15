from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging
import sqlite3

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cafe-vesna-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe_vesna.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False

# ==================== НАСТРОЙКИ КАФЕ ====================
# Вы можете изменить эти значения под свое кафе
CAFE_NAME = "Кафе ВЕСНА"
CAFE_ADDRESS = "г. Вознесеновка, ул. Гагарина 16"
CAFE_PHONE = "+7 (999) 123-45-67"
CAFE_EMAIL = "info@vesna-cafe.ru"
CAFE_WORK_HOURS = "Ежедневно с 10:00 до 23:00"
CAFE_DESCRIPTION = "Уютное кафе с домашней кухней в центре "
CAFE_SLOGAN = "Вкусно, как дома"


CAFE_LATITUDE = "48.07736898278385"  # Широта
CAFE_LONGITUDE = "39.79197807789805"  # Долгота

# Фото заведения (положите фото в static/images/)
CAFE_IMAGE = "/static/images/cafe.jpg"  # Основное фото (снаружи)
CAFE_IMAGE2 = "/static/images/cafe-interior.jpg"  # Фото интерьера

# Ссылки на соцсети (оставьте пустым, если нет)
SOCIAL_INSTAGRAM = "https://instagram.com/vesna.cafe"
SOCIAL_VK = "https://vk.com/vesna.cafe"
SOCIAL_TELEGRAM = "https://t.me/cafe_vesna"

# Убеждаемся, что папка для изображений существует
IMAGES_FOLDER = os.path.join(app.root_path, 'static', 'images')
os.makedirs(IMAGES_FOLDER, exist_ok=True)
logger.info(f"📁 Папка для изображений: {IMAGES_FOLDER}")

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

# ==================== МОДЕЛИ ДАННЫХ ====================
class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200), default='/static/images/placeholder.jpg')
    is_popular = db.Column(db.Boolean, default=False)
    is_special = db.Column(db.Boolean, default=False)
    weight = db.Column(db.String(20))
    calories = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    comment = db.Column(db.Text)
    items = db.Column(db.Text)  # JSON строка
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def image_exists(image_url):
    """Проверяет, существует ли файл изображения"""
    if not image_url:
        return False
    filename = image_url.replace('/static/', 'static/')
    filepath = os.path.join(app.root_path, filename)
    return os.path.exists(filepath)

def get_safe_image_url(image_url, default='/static/images/placeholder.jpg'):
    """Возвращает URL изображения, если файл существует, иначе заглушку"""
    if image_url and image_exists(image_url):
        return image_url
    return default

def create_placeholder_image(filename):
    """Создает простую заглушку для изображения"""
    filepath = os.path.join(IMAGES_FOLDER, filename)
    if not os.path.exists(filepath):
        try:
            # Создаем минимальный валидный JPEG
            with open(filepath, 'wb') as f:
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00')
            logger.info(f"✅ Создана заглушка: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания заглушки {filename}: {e}")
            return False
    return True

# ==================== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ====================
def init_database():
    """Принудительно создает базу данных и заполняет тестовыми данными"""
    with app.app_context():
        try:
            # Удаляем старые таблицы, если они есть
            logger.info("🔄 Удаление старых таблиц...")
            db.drop_all()
            
            # Создаем таблицы заново
            logger.info("🔄 Создание новых таблиц...")
            db.create_all()
            
            logger.info("✅ Таблицы успешно созданы!")
            
            # Данные о блюдах для меню
            dishes_data = [
                {
                    "name": "Цезарь с курицей",
                    "description": "Классический салат с куриным филе, пармезаном, сухариками и соусом",
                    "price": 450,
                    "category": "Салаты",
                    "weight": "250г",
                    "calories": 380,
                    "filename": "cezar-s-kuricej.jpg",
                    "is_popular": True,
                    "is_special": False
                },
                {
                    "name": "Борщ с пампушками",
                    "description": "Традиционный украинский борщ с мясом, подается с чесночными пампушками",
                    "price": 320,
                    "category": "Супы",
                    "weight": "350г",
                    "calories": 250,
                    "filename": "borshch-s-pampushkami.jpg",
                    "is_popular": True,
                    "is_special": False
                },
                {
                    "name": "Стейк Рибай",
                    "description": "Мраморная говядина, прожарка medium, подается с овощами гриль",
                    "price": 890,
                    "category": "Горячее",
                    "weight": "300г",
                    "calories": 520,
                    "filename": "stejk-ribaj.jpg",
                    "is_popular": False,
                    "is_special": True
                },
                {
                    "name": "Паста Карбонара",
                    "description": "Спагетти с беконом в сливочном соусе, пармезан",
                    "price": 420,
                    "category": "Паста",
                    "weight": "280г",
                    "calories": 550,
                    "filename": "pasta-karbonara.jpg",
                    "is_popular": True,
                    "is_special": False
                },
                {
                    "name": "Пицца Маргарита",
                    "description": "Томатный соус, моцарелла, базилик, оливковое масло",
                    "price": 480,
                    "category": "Пицца",
                    "weight": "400г",
                    "calories": 680,
                    "filename": "picca-margarita.jpg",
                    "is_popular": False,
                    "is_special": False
                },
                {
                    "name": "Тирамису",
                    "description": "Классический итальянский десерт с маскарпоне и кофе",
                    "price": 280,
                    "category": "Десерты",
                    "weight": "150г",
                    "calories": 320,
                    "filename": "tiramisu.jpg",
                    "is_popular": True,
                    "is_special": False
                },
                {
                    "name": "Латте",
                    "description": "Кофе с молоком, нежная пенка",
                    "price": 210,
                    "category": "Напитки",
                    "weight": "300мл",
                    "calories": 150,
                    "filename": "latte.jpg",
                    "is_popular": False,
                    "is_special": False
                },
                {
                    "name": "Греческий салат",
                    "description": "Свежие овощи, сыр фета, оливки, орегано",
                    "price": 380,
                    "category": "Салаты",
                    "weight": "270г",
                    "calories": 210,
                    "filename": "grecheskij-salat.jpg",
                    "is_popular": False,
                    "is_special": False
                }
            ]
            
            # Создаем элементы меню
            for dish in dishes_data:
                # Создаем заглушку для изображения, если файла нет
                create_placeholder_image(dish['filename'])
                
                image_url = f"/static/images/{dish['filename']}"
                
                item = MenuItem(
                    name=dish["name"],
                    description=dish["description"],
                    price=dish["price"],
                    category=dish["category"],
                    weight=dish["weight"],
                    calories=dish["calories"],
                    image_url=image_url,
                    is_popular=dish["is_popular"],
                    is_special=dish["is_special"]
                )
                db.session.add(item)
            
            db.session.commit()
            logger.info(f"✅ База данных инициализирована! Добавлено блюд: {len(dishes_data)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
            db.session.rollback()

# Функция для принудительного удаления и создания БД
def force_recreate_db():
    """Полностью удаляет и пересоздает базу данных"""
    db_path = os.path.join(app.root_path, 'cafe_vesna.db')
    
    # Удаляем старый файл базы данных
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.info(f"🗑️ Удален старый файл базы данных: {db_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления БД: {e}")
    
    # Инициализируем заново
    init_database()

# ==================== КОНТЕКСТНЫЙ ПРОЦЕССОР ====================
@app.context_processor
def utility_processor():
    return {
        'image_exists': image_exists,
        'get_safe_image_url': get_safe_image_url,
        'now': datetime.now(),
        'cafe_name': CAFE_NAME,
        'cafe_address': CAFE_ADDRESS,
        'cafe_phone': CAFE_PHONE,
        'cafe_email': CAFE_EMAIL,
        'cafe_work_hours': CAFE_WORK_HOURS,
        'cafe_description': CAFE_DESCRIPTION,
        'cafe_slogan': CAFE_SLOGAN,
        'cafe_latitude': CAFE_LATITUDE,
        'cafe_longitude': CAFE_LONGITUDE,
        'cafe_image': CAFE_IMAGE,
        'cafe_image2': CAFE_IMAGE2,
        'social_instagram': SOCIAL_INSTAGRAM,
        'social_vk': SOCIAL_VK,
        'social_telegram': SOCIAL_TELEGRAM
    }

# ==================== МАРШРУТЫ ====================

# Главная страница (только информация о кафе)
@app.route('/')
def index():
    try:
        # Проверяем, существуют ли фото кафе
        cafe_image_exists = image_exists(CAFE_IMAGE)
        cafe_image2_exists = image_exists(CAFE_IMAGE2)
        
        return render_template('index.html',
                             cafe_image_exists=cafe_image_exists,
                             cafe_image2_exists=cafe_image2_exists)
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {e}")
        return render_template('error.html', error=str(e)), 500

# Страница меню
@app.route('/menu')
def menu():
    try:
        category = request.args.get('category', 'all')
        search = request.args.get('search', '')
        
        query = MenuItem.query
        
        if category and category != 'all':
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(MenuItem.name.ilike(f'%{search}%'))
        
        items = query.all()
        categories = db.session.query(MenuItem.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        return render_template('menu.html', 
                             items=items,
                             categories=categories,
                             selected_category=category,
                             search=search)
    except Exception as e:
        logger.error(f"Ошибка в меню: {e}")
        return render_template('error.html', error=str(e)), 500

# API для корзины
@app.route('/api/cart')
def get_cart():
    try:
        cart = session.get('cart', {})
        items = []
        total = 0
        
        for item_id, quantity in cart.items():
            item = MenuItem.query.get(int(item_id))
            if item:
                items.append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'quantity': quantity,
                    'total': item.price * quantity,
                    'image': get_safe_image_url(item.image_url)
                })
                total += item.price * quantity
        
        return jsonify({
            'success': True,
            'items': items,
            'total': total,
            'count': len(items)
        })
    except Exception as e:
        logger.error(f"Ошибка в API корзины: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cart/add/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    try:
        cart = session.get('cart', {})
        
        if str(item_id) in cart:
            cart[str(item_id)] += 1
        else:
            cart[str(item_id)] = 1
        
        session['cart'] = cart
        total_count = sum(cart.values())
        
        return jsonify({'success': True, 'cart_count': total_count})
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        cart = session.get('cart', {})
        
        if quantity > 0:
            cart[str(item_id)] = quantity
        else:
            cart.pop(str(item_id), None)
        
        session['cart'] = cart
        
        # Пересчет итогов
        total = 0
        items = []
        for id, qty in cart.items():
            item = MenuItem.query.get(int(id))
            if item:
                total += item.price * qty
                items.append({
                    'id': item.id,
                    'total': item.price * qty
                })
        
        return jsonify({
            'success': True,
            'cart_count': sum(cart.values()),
            'total': total,
            'items': items
        })
    except Exception as e:
        logger.error(f"Ошибка обновления корзины: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Страница корзины
@app.route('/cart')
def view_cart():
    return render_template('cart.html')

# Оформление заказа
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            comment = request.form.get('comment')
            
            # Валидация
            if not name or not phone or not address:
                flash('Пожалуйста, заполните все обязательные поля', 'danger')
                return redirect(url_for('checkout'))
            
            cart = session.get('cart', {})
            
            if not cart:
                flash('Корзина пуста', 'warning')
                return redirect(url_for('menu'))
            
            # Подсчет суммы и подготовка данных
            total = 0
            items_list = []
            for item_id, quantity in cart.items():
                item = MenuItem.query.get(int(item_id))
                if item:
                    items_list.append({
                        'name': item.name,
                        'price': item.price,
                        'quantity': quantity
                    })
                    total += item.price * quantity
            
            # Создание номера заказа
            order_number = f"VESNA-{datetime.now().strftime('%y%m%d%H%M')}-{len(items_list)}"
            
            # Создаем заказ
            order = Order(
                order_number=order_number,
                customer_name=name,
                phone=phone,
                address=address,
                comment=comment,
                items=str(items_list),
                total=total,
                status='new'
            )
            
            db.session.add(order)
            db.session.commit()
            
            # Очищаем корзину
            session.pop('cart', None)
            
            return render_template('order_success.html', order=order)
            
        except Exception as e:
            logger.error(f"Ошибка оформления заказа: {e}")
            db.session.rollback()
            flash('Произошла ошибка при оформлении заказа', 'danger')
            return redirect(url_for('checkout'))
    
    return render_template('checkout.html')

# Страница успешного заказа
@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return render_template('order_success.html', order=order)
    except Exception as e:
        logger.error(f"Ошибка загрузки заказа: {e}")
        return render_template('error.html', error='Заказ не найден'), 404

# Страница контактов (перенаправляем на главную)
@app.route('/contacts')
def contacts():
    return redirect(url_for('index'))

# Страница о нас (перенаправляем на главную)
@app.route('/about')
def about():
    return redirect(url_for('index'))

# ==================== ДИАГНОСТИЧЕСКИЕ МАРШРУТЫ ====================

@app.route('/debug')
def debug():
    """Общая диагностика"""
    with app.app_context():
        try:
            info = {
                'app_name': CAFE_NAME,
                'debug_mode': app.debug,
                'database': app.config['SQLALCHEMY_DATABASE_URI'],
                'images_folder': IMAGES_FOLDER,
                'images_folder_exists': os.path.exists(IMAGES_FOLDER),
                'database_exists': os.path.exists('cafe_vesna.db'),
                'menu_items_count': MenuItem.query.count(),
                'orders_count': Order.query.count(),
                'session_cart': session.get('cart', {}),
                'cafe_address': CAFE_ADDRESS,
                'cafe_coordinates': f"{CAFE_LATITUDE}, {CAFE_LONGITUDE}"
            }
            return render_template('debug.html', info=info)
        except Exception as e:
            return f"<h1>Ошибка диагностики</h1><p>{str(e)}</p>"

@app.route('/reset-db-force')
def reset_db_force():
    """Принудительно пересоздает базу данных"""
    if app.config['DEBUG']:
        try:
            force_recreate_db()
            return """
            <h1>✅ База данных пересоздана!</h1>
            <p>База данных успешно пересоздана с правильной структурой.</p>
            <a href="/">На главную</a> | <a href="/menu">В меню</a>
            """
        except Exception as e:
            return f"<h1>❌ Ошибка</h1><p>{str(e)}</p>"
    return "❌ Доступно только в режиме отладки"

# ==================== ОБРАБОТЧИКИ ОШИБОК ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Внутренняя ошибка сервера: {error}")
    return render_template('500.html'), 500

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info(f"🍽️  Запуск {CAFE_NAME}")
    logger.info(f"📍 Адрес: {CAFE_ADDRESS}")
    logger.info(f"📁 Папка с изображениями: {IMAGES_FOLDER}")
    logger.info(f"🗄️  База данных: {os.path.join(app.root_path, 'cafe_vesna.db')}")
    logger.info("=" * 60)
    
    # Принудительно пересоздаем БД при первом запуске
    with app.app_context():
        try:
            # Проверяем, есть ли уже таблицы
            inspector = db.inspect(db.engine)
            if 'menu_item' not in inspector.get_table_names():
                logger.info("🆕 База данных не найдена, создаем новую...")
                init_database()
            else:
                # Проверяем наличие колонки created_at
                columns = [col['name'] for col in inspector.get_columns('menu_item')]
                if 'created_at' not in columns:
                    logger.warning("⚠️ Отсутствует колонка created_at, пересоздаем БД...")
                    force_recreate_db()
                else:
                    logger.info("✅ База данных имеет правильную структуру")
                    
                    # Проверяем наличие данных
                    if MenuItem.query.count() == 0:
                        logger.info("🔄 База данных пуста, добавляем тестовые данные...")
                        init_database()
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке БД: {e}")
            logger.info("🔄 Пробуем пересоздать БД...")
            force_recreate_db()
    
    app.run(debug=True)