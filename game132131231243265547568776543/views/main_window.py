from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self, current_user, on_logout=None):
        super().__init__()
        self.current_user = current_user
        self.on_logout = on_logout
        self.setWindowTitle(f"📋 Главное меню — {current_user.username}")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        self.label = QLabel(
            f"Добро пожаловать, <b>{self.current_user.username}</b><br>"
            f"<span style='color:#7a6c4f;'>Уровень доступа: {self.current_user.access_level.name}</span>"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; margin-bottom: 30px;")
        layout.addWidget(self.label)

        button_container = QVBoxLayout()
        button_container.setSpacing(15)

        self.btn_order_mgmt = QPushButton("📋 Управление заказами")
        self.btn_order_mgmt.clicked.connect(self.open_order_management)

        self.btn_customer_mgmt = QPushButton("📞 Управление клиентами")
        self.btn_customer_mgmt.clicked.connect(self.open_customer_management)

        self.btn_user_mgmt = QPushButton("👥 Управление пользователями")
        if self.current_user.access_level.name != "Администратор":
            self.btn_user_mgmt.setEnabled(False)
            self.btn_user_mgmt.setToolTip("Доступно только администратору")
        else:
            self.btn_user_mgmt.clicked.connect(self.open_user_management)

        self.btn_product_mgmt = QPushButton("📦 Управление товарами")
        self.btn_product_mgmt.clicked.connect(self.open_product_management)

        # Кнопки для турниров
        self.btn_tournament_mgmt = QPushButton("🏆 Управление турнирами")
        if self.current_user.access_level.name != "Администратор":
            self.btn_tournament_mgmt.setEnabled(False)
            self.btn_tournament_mgmt.setToolTip("Доступно только администратору")
        else:
            self.btn_tournament_mgmt.clicked.connect(self.open_tournament_management)

        # Кнопка для просмотра турниров (доступна всем пользователям)
        self.btn_tournament_view = QPushButton("🏆 Турниры")
        self.btn_tournament_view.clicked.connect(self.open_tournament_view)

        self.btn_logout = QPushButton("🚪 Выйти")
        self.btn_logout.clicked.connect(self.handle_logout)

        button_container.addWidget(self.btn_order_mgmt)
        button_container.addWidget(self.btn_customer_mgmt)
        button_container.addWidget(self.btn_user_mgmt)
        button_container.addWidget(self.btn_product_mgmt)
        button_container.addWidget(self.btn_tournament_mgmt)  # для админа
        button_container.addWidget(self.btn_tournament_view)  # для всех
        button_container.addWidget(self.btn_logout)
        layout.addLayout(button_container)
        layout.addStretch()

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_order_management(self):
        """Открыть управление заказами (включая создание, редактирование, удаление)."""
        from .order_management import OrderManagement
        self.order_mgmt = OrderManagement()
        self.order_mgmt.show()

    def open_customer_management(self):
        from .customer_management import CustomerManagement
        self.customer_mgmt = CustomerManagement()
        self.customer_mgmt.show()

    def open_user_management(self):
        from .user_management import UserManagement
        self.user_mgmt = UserManagement(current_user=self.current_user)
        self.user_mgmt.show()

    def open_product_management(self):
        from .product_management import ProductManagement
        self.product_mgmt = ProductManagement()
        self.product_mgmt.show()

    def open_tournament_management(self):
        """Открыть управление турнирами (только для администратора)."""
        from .tournament_management import TournamentManagement
        self.tournament_mgmt = TournamentManagement(current_user=self.current_user)
        self.tournament_mgmt.show()

    def open_tournament_view(self):
        """Открыть просмотр турниров для всех пользователей."""
        from .tournament_view import TournamentView
        self.tournament_view = TournamentView(current_user=self.current_user)
        self.tournament_view.show()

    def handle_logout(self):
        if self.on_logout:
            self.on_logout()
        self.close()