from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему.', 'warning')
            return redirect(url_for('main.login'))
        if not current_user.is_admin:
            flash('У вас нет доступа к этой странице.', 'danger')
            return redirect(url_for('main.home'))
        if current_user.is_blocked():
            flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'danger')
            return redirect(url_for('main.logout'))
        return f(*args, **kwargs)
    return decorated_function