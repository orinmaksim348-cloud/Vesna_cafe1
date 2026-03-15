"""
Скрипт для создания простых изображений-заглушек для кафе "ВЕСНА"
Запустите: python create_images.py
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random

def create_placeholder_image(filename, text, color1, color2):
    """Создает простое изображение с текстом"""
    
    # Создаем изображение 600x400
    img = Image.new('RGB', (600, 400), color=color1)
    draw = ImageDraw.Draw(img)
    
    # Рисуем полоску сверху
    draw.rectangle([0, 0, 600, 20], fill=color2)
    
    # Рисуем круг в центре
    draw.ellipse([200, 100, 400, 300], fill=color2, outline=None)
    
    # Пробуем добавить текст
    try:
        # Пробуем использовать стандартный шрифт
        font = ImageFont.load_default()
        
        # Разбиваем текст на строки
        lines = text.split('\n')
        y_position = 330
        
        for line in lines:
            # Центрируем текст
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (600 - text_width) // 2
            
            draw.text((x_position, y_position), line, fill='white', font=font)
            y_position += 20
    except:
        # Если не получается с текстом, просто рисуем точки
        pass
    
    # Сохраняем
    img.save(filename)
    print(f"✅ Создано: {filename}")

def main():
    # Создаем папку если её нет
    os.makedirs('static/images', exist_ok=True)
    
    # Список блюд с цветами
    dishes = [
        # (имя_файла, название_блюда, цвет1, цвет2)
        ("cezar-s-kuricej.jpg", "Цезарь\nс курицей", "#2e7d32", "#ff8f00"),
        ("borshch-s-pampushkami.jpg", "Борщ\nс пампушками", "#d32f2f", "#ff8f00"),
        ("stejk-ribaj.jpg", "Стейк\nРибай", "#795548", "#ff8f00"),
        ("pasta-karbonara.jpg", "Паста\nКарбонара", "#fbc02d", "#2e7d32"),
        ("picca-margarita.jpg", "Пицца\nМаргарита", "#f57c00", "#2e7d32"),
        ("tiramisu.jpg", "Тирамису", "#8d6e63", "#2e7d32"),
        ("latte.jpg", "Латте", "#bcaaa4", "#2e7d32"),
        ("grecheskij-salat.jpg", "Греческий\nсалат", "#7cb342", "#2e7d32"),
    ]
    
    print("🍽️  Создание изображений для кафе ВЕСНА...")
    print("=" * 50)
    
    for filename, text, color1, color2 in dishes:
        filepath = os.path.join('static/images', filename)
        create_placeholder_image(filepath, text, color1, color2)
    
    print("=" * 50)
    print("✅ Все изображения созданы!")
    print("📁 Папка: static/images/")
    print("\nТеперь можете заменить эти заглушки на реальные фото:")

if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw, ImageFont
        main()
    except ImportError:
        print("❌ Библиотека Pillow не установлена!")
        print("Установите её командой: pip install Pillow")
        
        # Создаем пустые файлы если Pillow не установлен
        print("\nСоздаю пустые файлы-заглушки...")
        dishes = [
            "cezar-s-kuricej.jpg",
            "borshch-s-pampushkami.jpg",
            "stejk-ribaj.jpg",
            "pasta-karbonara.jpg",
            "picca-margarita.jpg",
            "tiramisu.jpg",
            "latte.jpg",
            "grecheskij-salat.jpg",
        ]
        
        for dish in dishes:
            filepath = os.path.join('static/images', dish)
            with open(filepath, 'wb') as f:
                f.write(b'')  # Создаем пустой файл
            print(f"✅ Создан пустой файл: {filepath}")