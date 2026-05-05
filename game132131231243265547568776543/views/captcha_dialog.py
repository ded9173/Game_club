from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QGridLayout, QWidget
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
import os
from utils.captcha import Captcha


class CaptchaDialog(QDialog):
    def __init__(self, captcha_service: Captcha):
        super().__init__()
        self.setWindowTitle("Соберите пазл")
        self.resize(400, 500)
        self.captcha_service = captcha_service
        self.buttons = []

        layout = QVBoxLayout()

        title = QLabel("Нажмите на части, чтобы собрать пазл")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 13px; margin: 10px;")
        layout.addWidget(title)

        self.grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        self.grid_widget.setLayout(grid_layout)
        self.buttons = []

        for i in range(4):
            btn = QPushButton()
            btn.setFixedSize(190, 190)
            btn.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
            btn.setProperty("index", i)
            btn.clicked.connect(lambda _, idx=i: self.on_piece_click(idx))
            self.buttons.append(btn)
            grid_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(self.grid_widget)
        layout.setAlignment(self.grid_widget, Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_submit = QPushButton("✅ Проверить")
        self.btn_cancel = QPushButton("❌ Отмена")

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_submit)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.btn_refresh.clicked.connect(self.refresh_puzzle)
        self.btn_submit.clicked.connect(self.on_submit)
        self.btn_cancel.clicked.connect(self.reject)

        self.refresh_puzzle()

    def refresh_puzzle(self):
        """Перегенерирует и отображает пазл."""
        try:
            self.captcha_service.reset()
            self.refresh_buttons()
        except Exception as e:
            print(f"[Ошибка в refresh_puzzle] {e}")
            QMessageBox.critical(self, "Ошибка", "Не удалось обновить пазл.")

    def refresh_buttons(self):
        """Обновляет изображения на кнопках на основе текущего порядка."""
        for i in range(4):
            piece_path = self.captcha_service.get_piece_path(i)

            if not os.path.exists(piece_path):
                self.buttons[i].setText("❓")
                self.buttons[i].setIcon(QIcon())
                self.buttons[i].setStyleSheet("background: #fee; border: 1px solid #c00;")
                continue

            pixmap = QPixmap(piece_path)
            if pixmap.isNull():
                self.buttons[i].setText("🖼️?")
                self.buttons[i].setIcon(QIcon())
                self.buttons[i].setStyleSheet("background: #fdd; border: 1px solid #c00;")
                print(f"[Ошибка] Не удалось загрузить: {piece_path}")
                continue

            self.buttons[i].setIcon(QIcon(pixmap))
            self.buttons[i].setIconSize(pixmap.size().boundedTo(self.buttons[i].size() * 0.9))
            self.buttons[i].setStyleSheet("border: 1px solid #ccc; background: white;")

    def on_piece_click(self, index):
        """Обработка клика: меняем местами с соседней частью и обновляем UI."""
        try:
            self.captcha_service.click_piece(index)
            self.refresh_buttons()

            if self.captcha_service.verify():
                QMessageBox.information(
                    self,
                    "🎉 Готово!",
                    "Пазл собран! Нажмите 'Проверить', чтобы пройти капчу."
                )
        except Exception as e:
            import traceback
            print(f"[Ошибка в on_piece_click] {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", "Не удалось обработать клик.")

    def on_submit(self):
        """Проверка решения."""
        try:
            if self.captcha_service.verify():
                self.captcha_service.solve()
                QMessageBox.information(self, "✅ Успех", "Капча успешно пройдена!")
                self.accept()
            else:
                QMessageBox.warning(self, "⏳ Ещё не готово", "Соберите пазл, прежде чем проверять.")
        except Exception as e:
            import traceback
            print(f"[Ошибка в on_submit] {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", "Не удалось проверить капчу.")