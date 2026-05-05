import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox
)

from api_client import get_client_full_name
from validators import validate_full_name
from reporter import create_test_case_template, update_result_in_docx


class DataValidatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Валидация данных клиента")
        self.resize(600, 500)
        self.full_name = ""
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.title = QLabel("Валидация данных клиента")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title.setAlignment(self.title.alignment().AlignCenter)
        layout.addWidget(self.title)

        self.btn_load = QPushButton("📥 Получить данные")
        self.btn_load.clicked.connect(self.load_data)
        layout.addWidget(self.btn_load)

        self.label = QLabel("ФИО клиента:")
        layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Здесь появится ФИО клиента...")
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.btn_send = QPushButton("📤 Отправить результат теста")
        self.btn_send.clicked.connect(self.send_results)
        self.btn_send.setEnabled(False)
        layout.addWidget(self.btn_send)

        self.result_display = QTextEdit()
        self.result_display.setPlaceholderText("Результаты проверки появятся здесь...")
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_data(self):
        self.text_edit.clear()
        self.result_display.clear()
        self.full_name = get_client_full_name()

        if self.full_name:
            self.text_edit.setText(self.full_name)
            self.btn_send.setEnabled(True)
            QMessageBox.information(self, "✅ Успех", "Данные успешно получены!")
        else:
            QMessageBox.critical(
                self, "❌ Ошибка",
                "Не удалось получить ФИО.\n\n"
                "1. Убедитесь, что TransferSimulator запущен\n"
                "2. Или проверьте доступ к http://prb.sylas.ru"
            )

    def send_results(self):
        if not self.full_name:
            return

        errors = validate_full_name(self.full_name)

        if any("недопустимые символы" in err.lower() for err in errors):
            update_result_in_docx("RESULT_2", "ОШИБКА")
            result2 = "ОШИБКА"
        else:
            update_result_in_docx("RESULT_2", "УСПЕХ")
            result2 = "УСПЕХ"

        if any("цифры" in err.lower() for err in errors):
            update_result_in_docx("RESULT_3", "ОШИБКА")
            result3 = "ОШИБКА"
        else:
            update_result_in_docx("RESULT_3", "УСПЕХ")
            result3 = "УСПЕХ"

        update_result_in_docx("RESULT_1", "УСПЕХ")

        self.result_display.setPlainText(
            f"ФИО: {self.full_name}\n\n"
            "Результаты проверки:\n"
            f"1. Получение данных: УСПЕХ\n"
            f"2. Запрещённые символы: {result2}\n"
            f"3. Наличие цифр: {result3}"
        )

        QMessageBox.information(self, "📤 Готово", "Результаты отправлены в 'ТестКейс.docx'")


def main():
    app = QApplication(sys.argv)

    create_test_case_template()

    window = DataValidatorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()