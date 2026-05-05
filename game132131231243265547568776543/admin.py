from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import AccessLevel, User

from utils.security import Security

DATABASE_URL = "postgresql://postgres:12345@localhost:5432/game_club"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

try:
    admin_level = session.query(AccessLevel).filter_by(name="Администратор").first()
    if admin_level is None:
        admin_level = AccessLevel(name="Администратор")
        session.add(admin_level)
        session.commit()
        print("Уровень доступа 'Администратор' создан.")

    hashed_password = Security.hash_password("12345")

    existing_admin = session.query(User).filter_by(username="Admin").first()
    if existing_admin:
        print("Пользователь 'Admin' уже существует.")
    else:
        new_admin = User(
            username="Admin",
            password=hashed_password,
            access_level=admin_level
        )
        session.add(new_admin)
        session.commit()
        print("Пользователь 'Admin' успешно создан с правами администратора.")

except OperationalError as e:
    print(f"Ошибка подключения к базе данных: {e}")
except Exception as e:
    print(f"Произошла ошибка при создании пользователя: {e}")
    raise
finally:
    session.close()