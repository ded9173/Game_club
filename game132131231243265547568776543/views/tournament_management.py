from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QDialog, QFormLayout,
    QLineEdit, QDateTimeEdit, QSpinBox, QTextEdit, QComboBox, QTabWidget,
    QLabel, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDateTime
from controllers.tournament_controller import TournamentController
from models import TournamentStatus


class TournamentForm(QDialog):
    def __init__(self, tournament_id=None, parent=None):
        super().__init__(parent)
        self.tournament_id = tournament_id
        self.setWindowTitle("🏆 " + ("Редактировать турнир" if tournament_id else "Создать турнир"))
        self.resize(500, 450)
        self.setup_ui()
        if tournament_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название турнира")

        self.game_input = QLineEdit()
        self.game_input.setPlaceholderText("Название игры")

        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime())
        self.start_date.setCalendarPopup(True)

        self.max_participants = QSpinBox()
        self.max_participants.setRange(2, 64)
        self.max_participants.setValue(8)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)

        form.addRow("Название:", self.name_input)
        form.addRow("Игра:", self.game_input)
        form.addRow("Дата/время:", self.start_date)
        form.addRow("Макс. участников:", self.max_participants)
        form.addRow("Описание:", self.desc_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("✅ Сохранить")
        self.btn_cancel = QPushButton("❌ Отмена")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def load_data(self):
        controller = TournamentController()
        try:
            tournament = controller.get_tournament_by_id(self.tournament_id)
            if tournament:
                self.name_input.setText(tournament.name)
                self.game_input.setText(tournament.game_name)
                self.start_date.setDateTime(tournament.start_date)
                self.max_participants.setValue(tournament.max_participants)
                self.desc_input.setPlainText(tournament.description or "")
        finally:
            controller.close()

    def save(self):
        name = self.name_input.text().strip()
        game = self.game_input.text().strip()

        if not name or not game:
            QMessageBox.warning(self, "Ошибка", "Заполните название и игру")
            return

        controller = TournamentController()
        try:
            if self.tournament_id:
                controller.update_tournament(self.tournament_id, {
                    'name': name,
                    'game_name': game,
                    'start_date': self.start_date.dateTime().toPyDateTime(),
                    'max_participants': self.max_participants.value(),
                    'description': self.desc_input.toPlainText()
                })
                QMessageBox.information(self, "Успех", "Турнир обновлён")
            else:
                from controllers.user_controller import UserController
                # Здесь нужно получить текущего пользователя
                # Для демонстрации используем Admin с id=1
                controller.create_tournament(
                    name=name,
                    game_name=game,
                    start_date=self.start_date.dateTime().toPyDateTime(),
                    max_participants=self.max_participants.value(),
                    created_by=1,  # TODO: передать реального пользователя
                    description=self.desc_input.toPlainText()
                )
                QMessageBox.information(self, "Успех", "Турнир создан")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            controller.close()


class MatchResultDialog(QDialog):
    def __init__(self, match, parent=None):
        super().__init__(parent)
        self.match = match
        self.setWindowTitle(f"Результат матча")
        self.resize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        p1_name = self.match.player1.username if self.match.player1 else "БАЙ"
        p2_name = self.match.player2.username if self.match.player2 else "БАЙ"

        self.label_match = QLabel(f"{p1_name}  VS  {p2_name}")
        layout.addRow("Матч:", self.label_match)

        self.score1 = QSpinBox()
        self.score1.setRange(0, 99)
        self.score2 = QSpinBox()
        self.score2.setRange(0, 99)

        layout.addRow("Счёт игрока 1:", self.score1)
        layout.addRow("Счёт игрока 2:", self.score2)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("✅ Сохранить")
        self.btn_cancel = QPushButton("❌ Отмена")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def save(self):
        s1 = self.score1.value()
        s2 = self.score2.value()

        if s1 == s2:
            QMessageBox.warning(self, "Ошибка", "Ничья не допускается. Укажите победителя")
            return

        winner_id = self.match.player1_id if s1 > s2 else self.match.player2_id

        controller = TournamentController()
        try:
            controller.set_match_result(self.match.id, winner_id, s1, s2)
            QMessageBox.information(self, "Успех", "Результат сохранён")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            controller.close()


class TournamentManagement(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("🏆 Управление турнирами")
        self.resize(1000, 700)
        self.setup_ui()
        self.load_tournaments()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton("➕ Создать турнир")
        self.btn_refresh = QPushButton("🔄 Обновить")

        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        # Таблица турниров
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Игра", "Дата", "Участники", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Вкладки для управления выбранным турниром
        self.tab_widget = QTabWidget()
        self.participants_tab = QWidget()
        self.matches_tab = QWidget()
        self.tab_widget.addTab(self.participants_tab, "👥 Участники")
        self.tab_widget.addTab(self.matches_tab, "🎮 Сетка матчей")
        layout.addWidget(self.tab_widget)

        self.setup_participants_tab()
        self.setup_matches_tab()

        self.setLayout(layout)

        self.btn_create.clicked.connect(self.create_tournament)
        self.btn_refresh.clicked.connect(self.load_tournaments)
        self.table.selectionModel().selectionChanged.connect(self.on_tournament_selected)

        # Отключаем вкладки, пока не выбран турнир
        self.tab_widget.setEnabled(False)

    def setup_participants_tab(self):
        layout = QVBoxLayout(self.participants_tab)

        self.participants_table = QTableWidget(0, 3)
        self.participants_table.setHorizontalHeaderLabels(["ID", "Логин", "Статус"])
        layout.addWidget(self.participants_table)

        self.btn_generate_matches = QPushButton("🎲 Сформировать пары и начать турнир")
        self.btn_generate_matches.clicked.connect(self.generate_matches)
        layout.addWidget(self.btn_generate_matches)

    def setup_matches_tab(self):
        layout = QVBoxLayout(self.matches_tab)

        # Выбор раунда
        round_layout = QHBoxLayout()
        round_layout.addWidget(QLabel("Тур:"))
        self.round_combo = QComboBox()
        self.round_combo.currentIndexChanged.connect(self.load_matches)
        round_layout.addWidget(self.round_combo)
        round_layout.addStretch()
        layout.addLayout(round_layout)

        self.matches_table = QTableWidget(0, 5)
        self.matches_table.setHorizontalHeaderLabels(["ID", "Игрок 1", "Игрок 2", "Счёт", "Действия"])
        layout.addWidget(self.matches_table)

    def load_tournaments(self):
        controller = TournamentController()
        try:
            tournaments = controller.get_all_tournaments(include_finished=True)
            self.table.setRowCount(0)

            for t in tournaments:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(t.id)))
                self.table.setItem(row, 1, QTableWidgetItem(t.name))
                self.table.setItem(row, 2, QTableWidgetItem(t.game_name))
                self.table.setItem(row, 3, QTableWidgetItem(t.start_date.strftime("%d.%m.%Y %H:%M")))
                self.table.setItem(row, 4, QTableWidgetItem(f"{t.current_participants}/{t.max_participants}"))
                self.table.setItem(row, 5, QTableWidgetItem(t.status.value))
        finally:
            controller.close()

    def on_tournament_selected(self):
        selected = self.table.currentRow()
        if selected < 0:
            self.tab_widget.setEnabled(False)
            return

        self.tab_widget.setEnabled(True)
        self.selected_tournament_id = int(self.table.item(selected, 0).text())
        self.load_participants()
        self.load_rounds()

    def load_participants(self):
        controller = TournamentController()
        try:
            participants = controller.get_tournament_participants(self.selected_tournament_id)
            self.participants_table.setRowCount(0)

            for p in participants:
                row = self.participants_table.rowCount()
                self.participants_table.insertRow(row)
                self.participants_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.participants_table.setItem(row, 1, QTableWidgetItem(p.username))
                self.participants_table.setItem(row, 2, QTableWidgetItem("Зарегистрирован"))
        finally:
            controller.close()

    def load_rounds(self):
        controller = TournamentController()
        try:
            rounds = controller.get_available_rounds(self.selected_tournament_id)
            self.round_combo.clear()
            if rounds:
                for r in rounds:
                    self.round_combo.addItem(f"Тур {r}", r)
            else:
                self.round_combo.addItem("Турнир ещё не начат", 0)
        finally:
            controller.close()

    def load_matches(self):
        if not hasattr(self, 'selected_tournament_id'):
            return

        round_data = self.round_combo.currentData()
        if not round_data:
            return

        controller = TournamentController()
        try:
            matches = controller.get_tournament_matches(self.selected_tournament_id, round_data)
            self.matches_table.setRowCount(0)

            for m in matches:
                row = self.matches_table.rowCount()
                self.matches_table.insertRow(row)

                p1 = m.player1.username if m.player1 else "БАЙ"
                p2 = m.player2.username if m.player2 else "БАЙ"
                score = f"{m.player1_score} : {m.player2_score}" if m.status.value == "Завершён" else "Не сыгран"

                self.matches_table.setItem(row, 0, QTableWidgetItem(str(m.id)))
                self.matches_table.setItem(row, 1, QTableWidgetItem(p1))
                self.matches_table.setItem(row, 2, QTableWidgetItem(p2))
                self.matches_table.setItem(row, 3, QTableWidgetItem(score))

                btn_result = QPushButton("📝 Ввести результат")
                btn_result.setEnabled(m.player1_id and m.player2_id and m.status.value != "Завершён")
                btn_result.clicked.connect(lambda _, mid=m.id: self.enter_match_result(mid))
                self.matches_table.setCellWidget(row, 4, btn_result)
        finally:
            controller.close()

    def enter_match_result(self, match_id):
        controller = TournamentController()
        try:
            match = controller.db_session.query(controller.db_session.query(controller.model).model).get(match_id)
            dialog = MatchResultDialog(match, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_matches()
                self.load_rounds()
        finally:
            controller.close()

    def create_tournament(self):
        dialog = TournamentForm(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_tournaments()

    def generate_matches(self):
        if not hasattr(self, 'selected_tournament_id'):
            return

        reply = QMessageBox.question(self, "Подтверждение",
                                     "После формирования пар турнир начнётся. Продолжить?")
        if reply != QMessageBox.StandardButton.Yes:
            return

        controller = TournamentController()
        try:
            controller.generate_matches(self.selected_tournament_id)
            QMessageBox.information(self, "Успех", "Пары сформированы! Турнир начат.")
            self.load_rounds()
            self.load_matches()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            controller.close()