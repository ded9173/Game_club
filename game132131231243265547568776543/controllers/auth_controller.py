from datetime import datetime, timedelta


class AuthController:
    def __init__(self, user_service, captcha_service, lockout_minutes=15):
        self.user_service = user_service
        self.captcha_service = captcha_service
        self.lockout_time = timedelta(minutes=lockout_minutes)
        self.failed_attempts = {}

    def is_locked(self, username):
        if username not in self.failed_attempts:
            return False
        last_attempt, count = self.failed_attempts[username]
        if datetime.now() - last_attempt > self.lockout_time:
            del self.failed_attempts[username]
            return False
        return count >= 5

    def reset_attempts(self, username):
        if username in self.failed_attempts:
            del self.failed_attempts[username]

    def increment_attempts(self, username):
        now = datetime.now()
        count = self.failed_attempts.get(username, (now, 0))[1] + 1
        self.failed_attempts[username] = (now, count)

    def login(self, username, password):
        try:
            if self.is_locked(username):
                return False, "Слишком много попыток. Подождите."

            if not self.captcha_service.verify():
                return False, "Пройдите проверку капчи."

            user = self.user_service.get_user(username)
            if not user:
                self.increment_attempts(username)
                return False, "Неверный логин или пароль."

            if user.is_active and self.user_service.security.verify_password(user.password, password):
                self.reset_attempts(username)
                return True, "Успешный вход."
            else:
                self.increment_attempts(username)
                return False, "Неверный пароль или аккаунт заблокирован."
        except Exception as e:
            return False, f"Ошибка системы: {str(e)}"