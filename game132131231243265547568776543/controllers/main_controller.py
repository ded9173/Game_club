from PyQt6.QtWidgets import QApplication
from views.login_form import LoginForm
from views.main_window import MainWindow
from utils.logger import log_action


class MainController:
    def __init__(self, auth_controller):
        self.app = QApplication.instance() or QApplication([])
        self.auth_controller = auth_controller
        self.main_window = None
        self.current_user = None

    def run(self):
        self.show_login()

    def show_login(self):
        self.login_form = LoginForm(
            auth_controller=self.auth_controller,
            on_success=self.on_login_success
        )
        self.login_form.show()

    def on_login_success(self, user):
        self.current_user = user
        log_action(user.username, "Авторизован")
        self.login_form.close()
        self.show_main_window()

    def show_main_window(self):
        self.main_window = MainWindow(current_user=self.current_user, on_logout=self.logout)
        self.main_window.show()

    def logout(self):
        if self.main_window:
            self.main_window.close()
        if self.current_user:
            log_action(self.current_user.username, "Выход из системы")
        self.current_user = None
        self.show_login()