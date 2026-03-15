from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging
import sys
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== НАСТРОЙКИ КАФЕ ====================
CAFE_NAME = "Кафе ВЕСНА"
CAFE_ADDRESS = "г. Вознесеновка, ул. Гагрина, д.16"
CAFE_PHONE = "+7 (903) 583-57-65"
CAFE_EMAIL = "info@vesna-cafe.ru"
CAFE_WORK_HOURS = "Ежедневно с 10:00 до 23:00"
CAFE_DESCRIPTION = "Уютное кафе с домашней кухней в центре города"
CAFE_SLOGAN = "Вкусно, как дома"
CAFE_LATITUDE = "48.077615660593544"
CAFE_LONGITUDE = "39.7918029284401"
CAFE_IMAGE = "/static/images/cafe.jpg"
CAFE_IMAGE2 = "/static/images/cafe-interior.jpg"

SOCIAL_INSTAGRAM = "https://instagram.com/vesna.cafe"
SOCIAL_VK = "https://vk.com/m.orin"
SOCIAL_TELEGRAM = "https://t.me/cafe_vesna"

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        DATABASE_URL = os.environ.get('DATABASE_URL')
        logger.info("📄 Загружены переменные из .env файла")
    except ImportError:
        logger.warning("⚠️ python-dotenv не установлен")

if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///cafe_vesna.db'
    logger.warning("⚠️ DATABASE_URL не найден, используется SQLite для разработки")
else:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        logger.info("🔄 Исправлен формат URL: postgres:// -> postgresql://")
    
    try:
        import psycopg
        logger.info(f"✅ Используется psycopg версии {psycopg.__version__}")
    except ImportError as e:
        logger.error(f"❌ psycopg не установлен: {e}")
        logger.error("📦 Установите: pip install psycopg[binary]==3.2.13")
        sys.exit(1)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
app.config['JSON_AS_ASCII'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ⚠️ ВАЖНО: Убираем проблемный connect_timeout
# Для PostgreSQL используем стандартные настройки пула
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True,
    # 'connect_args' убрано, так как вызывает ошибку
}

IMAGES_FOLDER = os.path.join(app.root_path, 'static', 'images')
os.makedirs(IMAGES_FOLDER, exist_ok=True)

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
    items = db.Column(db.Text)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def image_exists(image_url):
    if not image_url:
        return False
    filename = image_url.replace('/static/', 'static/')
    filepath = os.path.join(app.root_path, filename)
    return os.path.exists(filepath)

def get_safe_image_url(image_url, default='/static/images/placeholder.jpg'):
    if image_url and image_exists(image_url):
        return image_url
    return default

def create_placeholder_image(filename):
    filepath = os.path.join(IMAGES_FOLDER, filename)
    if not os.path.exists(filepath):
        try:
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
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Таблицы проверены/созданы")
            
            if MenuItem.query.count() > 0:
                logger.info(f"📊 База данных уже содержит {MenuItem.query.count()} блюд")
                return
            
            logger.info("🔄 Инициализация базы данных с тестовыми блюдами...")
            
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
            
            for dish in dishes_data:
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

with app.app_context():
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
@app.route('/')
def index():
    try:
        cafe_image_exists = image_exists(CAFE_IMAGE)
        cafe_image2_exists = image_exists(CAFE_IMAGE2)
        
        return render_template('index.html',
                             cafe_image_exists=cafe_image_exists,
                             cafe_image2_exists=cafe_image2_exists)
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {e}")
        return render_template('error.html', error=str(e)), 500

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

@app.route('/cart')
def view_cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            comment = request.form.get('comment')
            
            if not name or not phone or not address:
                flash('Пожалуйста, заполните все обязательные поля', 'danger')
                return redirect(url_for('checkout'))
            
            cart = session.get('cart', {})
            
            if not cart:
                flash('Корзина пуста', 'warning')
                return redirect(url_for('menu'))
            
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
            
            order_number = f"VESNA-{datetime.now().strftime('%y%m%d%H%M')}-{len(items_list)}"
            
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
            
            session.pop('cart', None)
            
            return render_template('order_success.html', order=order)
            
        except Exception as e:
            logger.error(f"Ошибка оформления заказа: {e}")
            db.session.rollback()
            flash('Произошла ошибка при оформлении заказа', 'danger')
            return redirect(url_for('checkout'))
    
    return render_template('checkout.html')

@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return render_template('order_success.html', order=order)
    except Exception as e:
        logger.error(f"Ошибка загрузки заказа: {e}")
        return render_template('error.html', error='Заказ не найден'), 404

@app.route('/contacts')
def contacts():
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Endpoint для проверки здоровья приложения"""
    try:
        # Используем text() для сырого SQL
        db.session.execute(text('SELECT 1')).scalar()
        
        db_driver = 'PostgreSQL' if 'postgresql' in DATABASE_URL else 'SQLite'
        psycopg_version = 'не используется'
        
        if 'postgresql' in DATABASE_URL:
            try:
                import psycopg
                psycopg_version = psycopg.__version__
            except:
                pass
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'db_driver': db_driver,
            'psycopg_version': psycopg_version,
            'python_version': sys.version.split()[0],
            'flask_version': Flask.__version__
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/debug-db')
def debug_db():
    """Диагностика подключения к БД"""
    info = {
        'database_url': DATABASE_URL.replace('://', '://***:***@') if '@' in DATABASE_URL else DATABASE_URL,
        'driver': 'PostgreSQL' if 'postgresql' in DATABASE_URL else 'SQLite',
        'tables_exist': False,
        'menu_items_count': 0
    }
    
    try:
        info['tables_exist'] = db.inspect(db.engine).has_table('menu_item')
        info['menu_items_count'] = MenuItem.query.count()
        info['connection_test'] = '✅ Успешно'
    except Exception as e:
        info['connection_test'] = f'❌ Ошибка: {str(e)}'
    
    return jsonify(info)

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info(f"🍽️  Запуск {CAFE_NAME}")
    logger.info(f"📍 Адрес: {CAFE_ADDRESS}")
    logger.info(f"🐍 Python версия: {sys.version.split()[0]}")
    logger.info(f"🔷 Flask версия: {Flask.__version__}")
    
    if 'postgresql' in DATABASE_URL:
        logger.info(f"🗄️  База данных: PostgreSQL")
        try:
            import psycopg
            logger.info(f"📦 psycopg версия: {psycopg.__version__}")
        except:
            pass
    else:
        logger.info(f"🗄️  База данных: SQLite (только для разработки)")
    
    logger.info("=" * 60)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])