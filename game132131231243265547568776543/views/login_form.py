from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from .captcha_dialog import CaptchaDialog
from utils.logger import log_action
import os


class LoginForm(QWidget):
    def __init__(self, auth_controller, on_success):
        super().__init__()
        self.auth_controller = auth_controller
        self.on_success = on_success
        self.setWindowTitle("🔐 Вход в систему")
        self.resize(340, 200)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Добро пожаловать")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Логин:", self.login_input)
        form_layout.addRow("Пароль:", self.password_input)
        layout.addLayout(form_layout)

        btn_layout = QVBoxLayout()
        self.btn_login = QPushButton("Войти")
        self.btn_cancel = QPushButton("Отмена")

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.btn_login.clicked.connect(self.try_login)
        self.btn_cancel.clicked.connect(self.close)

    def try_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "⚠️ Ошибка", "Заполните все поля")
            return

        try:
            captcha_dialog = CaptchaDialog(self.auth_controller.captcha_service)

            from config import CAPTCHA_PATH
            if not os.path.exists(CAPTCHA_PATH):
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Файл капчи не найден:\n{CAPTCHA_PATH}\nЗагрузите captcha_full.png в папку images/"
                )
                return

            result = captcha_dialog.exec()
            if result != captcha_dialog.DialogCode.Accepted:
                QMessageBox.information(self, "Капча", "Вы не прошли проверку капчи.")
                return

        except Exception as e:
            import traceback
            print("[FATAL] Ошибка при открытии капчи:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть капчу:\n{str(e)}")
            return

        try:
            success = self.auth_controller.login(login, password)
            if not success:
                self.password_input.clear()
                return

            from controllers.user_controller import UserController
            user_service = UserController()
            user = user_service.get_user(login)
            user_service.close()

            if not user:
                QMessageBox.critical(self, "Ошибка", "Пользователь не найден.")
                return

            if not user.is_active:
                QMessageBox.critical(self, "❌ Ошибка", "Аккаунт деактивирован.")
                return

            log_action(user.username, "Авторизован")
            self.on_success(user)
            self.close()

        except Exception as e:
            import traceback
            print("[FATAL] Ошибка при входе:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось войти: {e}")