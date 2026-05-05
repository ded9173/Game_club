import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.db import engine, Base
from models import User, AccessLevel, Product, Customer, Order
from controllers.user_controller import UserController
from utils.captcha import Captcha
from controllers.auth_controller import AuthController
from controllers.main_controller import MainController


def main():
    app = QApplication(sys.argv)

    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_file):
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Не удалось загрузить CSS: {e}")

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        QMessageBox.critical(None, "❌ Ошибка базы данных", f"Не удалось создать таблицы:\n{str(e)}")
        sys.exit(1)

    uc = UserController()
    try:
        if not uc.get_access_level("Администратор"):
            admin_level = AccessLevel(name="Администратор")
            uc.db_session.add(admin_level)
        if not uc.get_access_level("Пользователь"):
            user_level = AccessLevel(name="Пользователь")
            uc.db_session.add(user_level)
        uc.db_session.commit()
    except Exception as e:
        QMessageBox.critical(None, "❌ Ошибка", f"Не удалось добавить уровни доступа:\n{str(e)}")
        uc.db_session.rollback()
        sys.exit(1)
    finally:
        uc.close()

    try:
        user_service = UserController()
        captcha_service = Captcha()
        auth_controller = AuthController(user_service=user_service, captcha_service=captcha_service)
    except Exception as e:
        QMessageBox.critical(None, "❌ Ошибка", f"Не удалось инициализировать сервисы:\n{str(e)}")
        sys.exit(1)

    try:
        main_controller = MainController(auth_controller=auth_controller)
        main_controller.run()
    except Exception as e:
        QMessageBox.critical(None, "❌ Критическая ошибка", f"Ошибка запуска приложения:\n{str(e)}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()