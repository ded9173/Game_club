from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from .user_form import UserForm


class UserManagement(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("👥 Управление пользователями")
        self.resize(800, 500)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.user_table = QTableWidget(0, 4)
        self.user_table.setHorizontalHeaderLabels(["ID", "Логин", "Уровень", "Статус"])
        self.user_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.user_table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_delete = QPushButton("🗑️ Удалить")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_delete.clicked.connect(self.delete_user)

    def load_users(self):
        try:
            from controllers.user_controller import UserController
            uc = UserController()
            users = uc.get_all_users()
            self.user_table.setRowCount(0)

            for user in users:
                row = self.user_table.rowCount()
                self.user_table.insertRow(row)

                self.user_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.username or ""))

                level_name = user.access_level.name if user.access_level else "Не задан"
                self.user_table.setItem(row, 2, QTableWidgetItem(level_name))

                status = "Активен" if user.is_active else "Заблокирован"
                self.user_table.setItem(row, 3, QTableWidgetItem(status))

            uc.close()

        except Exception as e:
            import traceback
            print("❌ Ошибка при загрузке пользователей:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пользователей:\n{e}")

    def add_user(self):
        dialog = UserForm(on_saved=self.load_users)
        dialog.exec()

    def edit_user(self):
        selected = self.user_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Выберите", "Сначала выберите пользователя.")
            return
        user_id = int(self.user_table.item(selected, 0).text())
        dialog = UserForm(user_id=user_id, on_saved=self.load_users)
        dialog.exec()

    def delete_user(self):
        selected = self.user_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Выберите", "Сначала выберите пользователя.")
            return
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить этого пользователя?")
        if reply == QMessageBox.StandardButton.Yes:
            user_id = int(self.user_table.item(selected, 0).text())
            try:
                from controllers.user_controller import UserController
                uc = UserController()
                uc.delete_user(user_id)
                uc.close()
                self.load_users()
                QMessageBox.information(self, "Успех", "Пользователь удалён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {e}")