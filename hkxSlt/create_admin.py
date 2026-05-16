# create_admin.py
import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin():
    """Создает администратора в существующей базе данных"""
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')

    if not os.path.exists(db_path):
        print("❌ База данных не найдена. Сначала запустите приложение.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем, есть ли уже администратор
    cursor.execute("SELECT * FROM users WHERE is_admin = 1")
    admin = cursor.fetchone()

    if admin:
        print(f"✅ Администратор уже существует:")
        cursor.execute("SELECT id, username FROM users WHERE is_admin = 1")
        admins = cursor.fetchall()
        for a in admins:
            print(f"   ID: {a[0]}, Логин: {a[1]}")
        conn.close()
        return True

    # Создаем администратора
    username = "admin"
    password = "admin123"
    password_hash = generate_password_hash(password)

    try:
        # Добавляем недостающие столбцы, если их нет
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")

        # Вставляем администратора
        cursor.execute("""
            INSERT INTO users (username, password_hash, is_admin, role, created_at, updated_at)
            VALUES (?, ?, 1, 'Admin', ?, ?)
        """, (username, password_hash, datetime.now(), datetime.now()))

        conn.commit()
        print("✅ Администратор создан успешно!")
        print(f"   Логин: {username}")
        print(f"   Пароль: {password}")
        print("\n⚠️ Обязательно смените пароль после первого входа!")

    except sqlite3.IntegrityError:
        print("❌ Пользователь 'admin' уже существует")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

    return True

if __name__ == "__main__":
    create_admin()