from .main_window import MainWindow
from .login_form import LoginForm
from .captcha_dialog import CaptchaDialog
from .customer_management import CustomerManagement
from .user_management import UserManagement
from .order_form import OrderForm
from .customer_form import CustomerForm
from .tournament_management import TournamentManagement
from .tournament_view import TournamentView

__all__ = [
    "MainWindow",
    "LoginForm",
    "CaptchaDialog",
    "CustomerManagement",
    "UserManagement",
    "OrderForm",
    "CustomerForm",
    "TournamentManagement",  # Новый
    "TournamentView"
]