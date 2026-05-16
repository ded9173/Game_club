from datetime import datetime
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db




class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='User')
    is_admin = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(255), nullable=True)
    block_until = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """Устанавливает хэш пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет вводимый пароль с сохраненным хэшем"""
        return check_password_hash(self.password_hash, password)

    def is_blocked(self):
        """Проверяет, заблокирован ли пользователь"""
        if self.block_until and datetime.utcnow() > self.block_until:
            # Автоматическая разблокировка
            self.blocked = False
            self.block_reason = None
            self.block_until = None
            db.session.commit()
            return False
        return self.blocked


class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    start_management_date = db.Column(db.DateTime, default=datetime.utcnow)
    floors = db.Column(db.Integer)
    year_built = db.Column(db.Integer)
    total_area = db.Column(db.Float)
    city = db.Column(db.String(100))
    street = db.Column(db.String(100))
    house_number = db.Column(db.String(20))

    apartments = relationship('Apartment', backref='building', lazy=True)


class Apartment(db.Model):
    __tablename__ = 'apartments'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    area = db.Column(db.Float)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=True)

    charges = relationship('Charge', backref='apartment', lazy=True)
    payments = relationship('Payment', backref='apartment', lazy=True)


class Owner(db.Model):
    __tablename__ = 'owners'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    apartments = relationship('Apartment', backref='owner', lazy=True)


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    charges = relationship('Charge', backref='service', lazy=True)
    payments = relationship('Payment', backref='service', lazy=True)


class Charge(db.Model):
    __tablename__ = 'charges'
    id = db.Column(db.Integer, primary_key=True)
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartments.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    period = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartments.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    paid_amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Новый')
    priority = db.Column(db.String(20), default='Средняя')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartments.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)


class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    requests = relationship('Request', backref='staff', lazy=True)


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))

    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)


class Resident(db.Model):
    __tablename__ = 'residents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    relation_to_owner = db.Column(db.String(20))
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartments.id'), nullable=False)

    apartment = relationship('Apartment', backref='residents', lazy=True)


# НОВАЯ МОДЕЛЬ: Логирование действий администратора
class AdminActionLog(db.Model):
    __tablename__ = 'admin_action_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # create_user, block_user, delete_user, backup, restore и т.д.
    target_type = db.Column(db.String(50), nullable=True)  # User, Backup и т.д.
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON с деталями
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin = relationship('User', backref='admin_actions', foreign_keys=[admin_id])


# НОВАЯ МОДЕЛЬ: Информация о резервных копиях
class Backup(db.Model):
    __tablename__ = 'backups'
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(20), nullable=False)  # full, incremental, differential
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filesize = db.Column(db.Integer, default=0)  # размер в байтах
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    # Для инкрементного/дифференциального бэкапа
    based_on = db.Column(db.Integer, nullable=True)  # ID полного бэкапа
    last_backup_time = db.Column(db.DateTime, nullable=True)  # время последнего изменения

    creator = relationship('User', backref='backups', foreign_keys=[created_by])