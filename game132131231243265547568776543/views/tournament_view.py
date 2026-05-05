from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QLabel, QGroupBox, QGridLayout,
    QTabWidget
)
from PyQt6.QtCore import Qt
from controllers.tournament_controller import TournamentController
from models import TournamentStatus


class TournamentView(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("🏆 Турниры")
        self.resize(900, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Вкладки
        self.tab_widget = QTabWidget()
        self.available_tab = QWidget()
        self.my_tab = QWidget()

        self.tab_widget.addTab(self.available_tab, "📋 Доступные турниры")
        self.tab_widget.addTab(self.my_tab, "📌 Мои турниры")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        self.setup_available_tab()
        self.setup_my_tab()

    def setup_available_tab(self):
        layout = QVBoxLayout(self.available_tab)

        self.available_table = QTableWidget(0, 6)
        self.available_table.setHorizontalHeaderLabels(["ID", "Название", "Игра", "Дата", "Свободно мест", ""])
        self.available_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.available_table)

    def setup_my_tab(self):
        layout = QVBoxLayout(self.my_tab)

        self.my_tournaments_table = QTableWidget(0, 6)
        self.my_tournaments_table.setHorizontalHeaderLabels(["ID", "Название", "Игра", "Дата", "Статус", "Действия"])
        self.my_tournaments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.my_tournaments_table)

        # Сетка матчей для выбранного турнира
        self.bracket_group = QGroupBox("Сетка турнира")
        bracket_layout = QVBoxLayout()
        self.bracket_table = QTableWidget(0, 4)
        self.bracket_table.setHorizontalHeaderLabels(["Тур", "Игрок 1", "Игрок 2", "Результат"])
        bracket_layout.addWidget(self.bracket_table)
        self.bracket_group.setLayout(bracket_layout)
        layout.addWidget(self.bracket_group)
        self.bracket_group.setVisible(False)

    def load_data(self):
        self.load_available_tournaments()
        self.load_my_tournaments()

    def load_available_tournaments(self):
        controller = TournamentController()
        try:
            tournaments = controller.get_all_tournaments(include_finished=False)
            self.available_table.setRowCount(0)

            for t in tournaments:
                if t.status != TournamentStatus.PLANNED:
                    continue

                row = self.available_table.rowCount()
                self.available_table.insertRow(row)

                free_slots = t.max_participants - t.current_participants
                self.available_table.setItem(row, 0, QTableWidgetItem(str(t.id)))
                self.available_table.setItem(row, 1, QTableWidgetItem(t.name))
                self.available_table.setItem(row, 2, QTableWidgetItem(t.game_name))
                self.available_table.setItem(row, 3, QTableWidgetItem(t.start_date.strftime("%d.%m.%Y %H:%M")))
                self.available_table.setItem(row, 4, QTableWidgetItem(str(free_slots)))

                already_registered = controller.is_user_registered(t.id, self.current_user.id)

                btn = QPushButton("❌ Отменить" if already_registered else "➕ Записаться")
                btn.clicked.connect(lambda _, tid=t.id, reg=already_registered: self.toggle_registration(tid, reg))
                btn.setEnabled(free_slots > 0 or already_registered)
                self.available_table.setCellWidget(row, 5, btn)
        finally:
            controller.close()

    def load_my_tournaments(self):
        controller = TournamentController()
        try:
            tournaments = controller.get_all_tournaments(include_finished=True)
            self.my_tournaments_table.setRowCount(0)

            for t in tournaments:
                if not controller.is_user_registered(t.id, self.current_user.id):
                    continue

                row = self.my_tournaments_table.rowCount()
                self.my_tournaments_table.insertRow(row)

                self.my_tournaments_table.setItem(row, 0, QTableWidgetItem(str(t.id)))
                self.my_tournaments_table.setItem(row, 1, QTableWidgetItem(t.name))
                self.my_tournaments_table.setItem(row, 2, QTableWidgetItem(t.game_name))
                self.my_tournaments_table.setItem(row, 3, QTableWidgetItem(t.start_date.strftime("%d.%m.%Y %H:%M")))
                self.my_tournaments_table.setItem(row, 4, QTableWidgetItem(t.status.value))

                btn_view = QPushButton("👁️ Показать сетку")
                btn_view.clicked.connect(lambda _, tid=t.id: self.show_bracket(tid))
                self.my_tournaments_table.setCellWidget(row, 5, btn_view)
        finally:
            controller.close()

    def toggle_registration(self, tournament_id, currently_registered):
        controller = TournamentController()
        try:
            if currently_registered:
                controller.unregister_participant(tournament_id, self.current_user.id)
                QMessageBox.information(self, "Успех", "Вы отменили регистрацию")
            else:
                controller.register_participant(tournament_id, self.current_user.id)
                QMessageBox.information(self, "Успех", "Вы записаны на турнир!")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            controller.close()

    def show_bracket(self, tournament_id):
        controller = TournamentController()
        try:
            tournament = controller.get_tournament_by_id(tournament_id)
            if not tournament:
                QMessageBox.warning(self, "Ошибка", "Турнир не найден")
                return

            self.bracket_group.setTitle(f"Сетка турнира: {tournament.name}")
            rounds = controller.get_available_rounds(tournament_id)

            if not rounds:
                self.bracket_table.setRowCount(0)
                self.bracket_table.setRowCount(1)
                self.bracket_table.setItem(0, 0, QTableWidgetItem("Турнир ещё не начат"))
                self.bracket_group.setVisible(True)
                return

            self.bracket_table.setRowCount(0)
            for r in rounds:
                matches = controller.get_tournament_matches(tournament_id, r)
                for m in matches:
                    row = self.bracket_table.rowCount()
                    self.bracket_table.insertRow(row)

                    p1 = m.player1.username if m.player1 else "БАЙ"
                    p2 = m.player2.username if m.player2 else "БАЙ"
                    result = f"{m.player1_score}:{m.player2_score}" if m.status.value == "Завершён" else "Не сыгран"

                    self.bracket_table.setItem(row, 0, QTableWidgetItem(f"Тур {r}"))
                    self.bracket_table.setItem(row, 1, QTableWidgetItem(p1))
                    self.bracket_table.setItem(row, 2, QTableWidgetItem(p2))
                    self.bracket_table.setItem(row, 3, QTableWidgetItem(result))

            self.bracket_group.setVisible(True)
        finally:
            controller.close()