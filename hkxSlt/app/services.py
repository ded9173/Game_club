from app import db
from app.models import User, Building, Apartment, Owner, Service, Charge, Payment, Request, Staff, Expense, Resident


def create_user(username, password):
      """
      Регистрация нового пользователя.
      """
      user = User(username=username)
      user.set_password(password)
      db.session.add(user)
      db.session.commit()
      return user


def register_building(address, floors=None, year_built=None, total_area=None, city=None, street=None, house_number=None):
      """
      Регистрация нового здания.
      """
      building = Building(address=address, floors=floors, year_built=year_built, total_area=total_area, city=city, street=street, house_number=house_number)
      db.session.add(building)
      db.session.commit()
      return building


def register_apartment(number, area, building_id, owner_id=None):
      """
      Регистрация новой квартиры.
      """
      apartment = Apartment(number=number, area=area, building_id=building_id, owner_id=owner_id)
      db.session.add(apartment)
      db.session.commit()
      return apartment


def register_owner(full_name, phone, email=None):
      """
      Регистрация нового владельца.
      """
      owner = Owner(full_name=full_name, phone=phone, email=email)
      db.session.add(owner)
      db.session.commit()
      return owner


def register_service(name):
      """
      Регистрация новой услуги.
      """
      service = Service(name=name)
      db.session.add(service)
      db.session.commit()
      return service


def register_charge(apartment_id, service_id, period, amount):
      """
      Регистрация нового начисления.
      """
      charge = Charge(apartment_id=apartment_id, service_id=service_id, period=period, amount=amount)
      db.session.add(charge)
      db.session.commit()
      return charge


def register_payment(apartment_id, service_id, paid_amount, payment_date=None):
      """
      Регистрация нового платежа.
      """
      payment = Payment(apartment_id=apartment_id, service_id=service_id, paid_amount=paid_amount, payment_date=payment_date)
      db.session.add(payment)
      db.session.commit()
      return payment


def register_request(title, description, status, priority, apartment_id):
      """
      Регистрация новой заявки.
      """
      request = Request(title=title, description=description, status=status, priority=priority, apartment_id=apartment_id)
      db.session.add(request)
      db.session.commit()
      return request


def register_staff(first_name, last_name, position, phone, email):
      """
      Регистрация нового сотрудника.
      """
      staff = Staff(first_name=first_name, last_name=last_name, position=position, phone=phone, email=email)
      db.session.add(staff)
      db.session.commit()
      return staff


def register_expense(date, amount, description, category):
      """
      Регистрация нового расхода.
      """
      expense = Expense(date=date, amount=amount, description=description, category=category)
      db.session.add(expense)
      db.session.commit()
      return expense


def register_resident(name, phone, email, relation_to_owner, apartment_id):
      """
      Регистрация нового жителя.
      """
      resident = Resident(name=name, phone=phone, email=email, relation_to_owner=relation_to_owner, apartment_id=apartment_id)
      db.session.add(resident)
      db.session.commit()
      return resident


def calculate_debt(apartment_id):
      """
      Рассчитывает текущую задолженность по квартире.
      """
      charges_total = sum(charge.amount for charge in Charge.query.filter_by(apartment_id=apartment_id).all())
      payments_total = sum(payment.paid_amount for payment in Payment.query.filter_by(apartment_id=apartment_id).all())
      return charges_total - payments_total

def create_user_with_email(username, password, email=None, is_admin=False, is_active=True):
    """
    Создание нового пользователя с email и правами администратора.
    """
    user = User(username=username, email=email, is_admin=is_admin, is_active=is_active)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def get_user_by_username(username):
    """Получение пользователя по имени"""
    return User.query.filter_by(username=username).first()


def get_user_by_email(email):
    """Получение пользователя по email"""
    return User.query.filter_by(email=email).first() if email else None


def get_user_by_id(user_id):
    """Получение пользователя по ID"""
    return User.query.get(user_id)


def update_user(user_id, **kwargs):
    """Обновление информации о пользователе"""
    user = User.query.get(user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key) and key not in ['id', 'password_hash', 'created_at']:
            setattr(user, key, value)

    db.session.commit()
    return user


def change_user_password(user_id, new_password):
    """Смена пароля пользователя"""
    user = User.query.get(user_id)
    if not user:
        return False
    user.set_password(new_password)
    db.session.commit()
    return True


def block_user(user_id, reason, block_days=0):
    """Блокировка пользователя"""
    from datetime import datetime, timedelta

    user = User.query.get(user_id)
    if not user:
        return False

    user.blocked = True
    user.block_reason = reason

    if block_days > 0:
        user.block_until = datetime.utcnow() + timedelta(days=block_days)
    else:
        user.block_until = None

    db.session.commit()
    return True


def unblock_user(user_id):
    """Разблокировка пользователя"""
    user = User.query.get(user_id)
    if not user:
        return False

    user.blocked = False
    user.block_reason = None
    user.block_until = None

    db.session.commit()
    return True


def soft_delete_user(user_id):
    """Мягкое удаление пользователя (деактивация)"""
    user = User.query.get(user_id)
    if not user:
        return False

    user.is_active = False
    db.session.commit()
    return True


def hard_delete_user(user_id):
    """Полное удаление пользователя из БД"""
    user = User.query.get(user_id)
    if not user:
        return False

    db.session.delete(user)
    db.session.commit()
    return True


def get_all_users(page=1, per_page=20, search=None, role=None, status=None):
    """Получение списка пользователей с фильтрацией и пагинацией"""
    query = User.query

    # Поиск
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    # Фильтр по роли
    if role == 'admin':
        query = query.filter_by(is_admin=True)
    elif role == 'user':
        query = query.filter_by(is_admin=False)

    # Фильтр по статусу
    if status == 'active':
        query = query.filter_by(is_active=True, blocked=False)
    elif status == 'blocked':
        query = query.filter_by(blocked=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    return query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)


def get_user_stats():
    """Получение статистики по пользователям"""
    return {
        'total': User.query.count(),
        'active': User.query.filter_by(is_active=True, blocked=False).count(),
        'blocked': User.query.filter_by(blocked=True).count(),
        'admin': User.query.filter_by(is_admin=True).count()
    }