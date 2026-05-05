from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QCheckBox
)
from utils.validators import validate_username


class UserForm(QDialog):
    def __init__(self, user_id=None, on_saved=None):
        super().__init__()
        self.user_id = user_id
        self.on_saved = on_saved
        self.setWindowTitle("👤 " + ("Редактировать пользователя" if user_id else "Добавить пользователя"))
        self.resize(350, 250)
        self.setup_ui()
        if user_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["Администратор", "Пользователь"])

        self.is_active_check = QCheckBox("Аккаунт активен")
        self.is_active_check.setChecked(True)

        form.addRow("Логин:", self.username_input)
        form.addRow("Пароль:", self.password_input)
        form.addRow("Уровень:", self.level_combo)
        form.addRow("", self.is_active_check)

        layout.addLayout(form)

        buttons = QVBoxLayout()
        self.save_btn = QPushButton("✅ Сохранить")
        self.cancel_btn = QPushButton("❌ Отмена")
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self):
        try:
            from controllers.user_controller import UserController
            uc = UserController()
            user = uc.get_user_by_id(self.user_id)
            uc.close()

            if user:
                self.username_input.setText(user.username)
                self.password_input.clear()
                if user.access_level:
                    self.level_combo.setCurrentText(user.access_level.name)
                self.is_active_check.setChecked(user.is_active)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e}")
            self.reject()

    def save(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        access_level_name = self.level_combo.currentText()
        is_active = self.is_active_check.isChecked()

        errors = []
        if not username:
            errors.append("Логин обязателен")
        elif not validate_username(username):
            errors.append("Логин: только буквы, цифры, _, от 3 до 20 символов")

        if not self.user_id and not password:
            errors.append("Пароль обязателен при создании")

        if len(password) < 4 and not self.user_id:
            errors.append("Пароль должен быть не менее 4 символов")

        if errors:
            QMessageBox.warning(self, "Ошибки ввода", "\n".join(errors))
            return

        try:
            from controllers.user_controller import UserController
            uc = UserController()

            level = uc.get_access_level(access_level_name)
            if not level:
                QMessageBox.critical(self, "Ошибка", "Уровень доступа не найден.")
                uc.close()
                return

            data = {
                "username": username,
                "access_level_id": level.id,
                "is_active": is_active
            }

            if self.user_id:
                uc.update_user(self.user_id, data)

                if password:
                    from utils.security import Security
                    hashed = Security.hash_password(password)
                    user = uc.get_user_by_id(self.user_id)
                    user.password = hashed
                    uc.db_session.commit()

                msg = "Пользователь обновлён"
            else:
                uc.create_user(
                    username=username,
                    password=password,
                    access_level=access_level_name,
                    is_active=is_active
                )
                msg = "Пользователь добавлен"

            uc.close()
            QMessageBox.information(self, "Готово", msg)
            if self.on_saved:
                self.on_saved()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")