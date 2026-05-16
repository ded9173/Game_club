# migrations/fix_user_table.py
import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def fix_user_table():
    """Добавляет недостающие столбцы в таблицу users и создает админа"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')

    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем текущие столбцы
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    print(f"📋 Существующие столбцы: {columns}")

    # Создаем новую временную таблицу с правильной структурой
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            email VARCHAR(120) UNIQUE,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) DEFAULT 'User',
            blocked BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            block_reason VARCHAR(255),
            block_until DATETIME,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)

    # Копируем данные из старой таблицы
    old_columns = []
    new_columns = ['id', 'username', 'password_hash', 'role', 'blocked',
                   'is_admin', 'block_reason', 'block_until', 'is_active']

    # Проверяем какие столбцы есть в старой таблице
    available_columns = []
    for col in new_columns:
        if col in columns:
            available_columns.append(col)
        elif col == 'is_admin':
            available_columns.append('is_admin')
        elif col == 'block_reason':
            available_columns.append('block_reason')
        elif col == 'block_until':
            available_columns.append('block_until')
        elif col == 'is_active':
            available_columns.append('is_active')

    # Добавляем created_at если есть
    if 'created_at' in columns:
        available_columns.append('created_at')

    # Добавляем email если есть
    if 'email' in columns:
        available_columns.append('email')

    # Формируем запрос на копирование
    columns_str = ', '.join(available_columns)
    cursor.execute(f"""
        INSERT INTO users_new ({columns_str})
        SELECT {columns_str} FROM users
    """)

    # Удаляем старую таблицу и переименовываем новую
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_new RENAME TO users")

    # Обновляем created_at для существующих записей
    try:
        cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        cursor.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        cursor.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")
        cursor.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")
        cursor.execute("UPDATE users SET role = 'User' WHERE role IS NULL")
        print("✅ Обновлены значения по умолчанию")
    except Exception as e:
        print(f"⚠️ Ошибка обновления: {e}")

    # Проверяем, есть ли администратор
    cursor.execute("SELECT * FROM users WHERE is_admin = 1")
    admin_exists = cursor.fetchone()

    if not admin_exists:
        print("\n👤 Создаем администратора по умолчанию...")
        username = "admin"
        password = "admin123"
        password_hash = generate_password_hash(password)

        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, is_admin, is_active, role, created_at, updated_at)
                VALUES (?, ?, 1, 1, 'Admin', ?, ?)
            """, (username, password_hash, datetime.now(), datetime.now()))
            conn.commit()
            print(f"✅ Администратор создан:")
            print(f"   Логин: {username}")
            print(f"   Пароль: {password}")
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Ошибка создания: {e}")
            if "UNIQUE constraint failed" in str(e):
                print("   Пользователь 'admin' уже существует")
    else:
        # Показываем существующего администратора
        cursor.execute("SELECT id, username FROM users WHERE is_admin = 1")
        admins = cursor.fetchall()
        print(f"\n👤 Существующие администраторы:")
        for admin in admins:
            print(f"   ID: {admin[0]}, Логин: {admin[1]}")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")
    return True

if __name__ == "__main__":
    fix_user_table()