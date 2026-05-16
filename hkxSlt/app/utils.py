from datetime import datetime
from flask import abort, session
from app.models import Building, Apartment, Owner, Charge, Payment
from PIL import Image, ImageDraw
from app import db
from app.services import Service
import random
import io
import base64
import os
import shutil
import zipfile
from flask import current_app


def parse_address(raw_address):
    """
    Парсинг полного адреса на отдельные компоненты: город, улица, номер дома.
    Пример: "Москва, Ленина ул., 15" → {'city': 'Москва', 'street': 'Ленина ул.', 'house_number': '15'}
    Возвращает словарь. Если формат некорректен — возвращает пустой словарь.
    """
    if not raw_address or not isinstance(raw_address, str):
        return {}
    parts = [part.strip() for part in raw_address.split(',') if part.strip()]
    components = {}
    if len(parts) >= 3:
        components['city'] = parts[0]
        components['street'] = parts[1]
        components['house_number'] = parts[2]
    elif len(parts) == 2:
        components['city'] = parts[0]
        components['street'] = parts[1]
        components['house_number'] = ''
    elif len(parts) == 1:
        components['city'] = parts[0]
        components['street'] = ''
        components['house_number'] = ''
    return components


def calculate_current_debt(apartment_id):
    """
    Вычисляет текущую задолженность по квартире.
    Возвращает сумму: (начисления - платежи).
    Если квартира не найдена — возвращает 0.
    """
    if not apartment_id:
        return 0

    try:
        charges_sum = db.session.query(db.func.coalesce(db.func.sum(Charge.amount), 0)) \
                                .filter(Charge.apartment_id == apartment_id).scalar()

        payments_sum = db.session.query(db.func.coalesce(db.func.sum(Payment.paid_amount), 0)) \
                                 .filter(Payment.apartment_id == apartment_id).scalar()

        return float(charges_sum - payments_sum)
    except Exception as e:
        print(f"[ERROR] Failed to calculate debt for apartment {apartment_id}: {str(e)}")
        return 0


def get_all_houses_and_addresses():
    """
    Возвращает список всех домов с их ID и адресами.
    Формат: [{'id': 1, 'address': 'г. Москва, ул. Ленина, д. 15'}, ...]
    """
    try:
        houses = Building.query.with_entities(Building.id, Building.address).all()
        return [{'id': h.id, 'address': h.address} for h in houses]
    except Exception as e:
        print(f"[ERROR] Failed to fetch buildings: {str(e)}")
        return []


def get_available_services():
    """
    Возвращает список всех доступных услуг.
    """
    try:
        services = Service.query.all()
        return services
    except Exception as e:
        print(f"[ERROR] Failed to fetch services: {str(e)}")
        return []


def log_activity(description):
    """
    Запись активности в консоль с временной меткой.
    Можно заменить на запись в файл или логгер.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {description}")


def convert_period(period_str):
    """
    Преобразует строку формата 'YYYY-MM' в объект даты (первый день месяца).
    При ошибке выбрасывает HTTP 400.
    """
    if not period_str or not isinstance(period_str, str):
        abort(400, description="Период не указан.")
    try:
        return datetime.strptime(period_str.strip(), '%Y-%m').date()
    except ValueError:
        abort(400, description="Некорректный формат периода. Ожидается ГГГГ-ММ.")


def extract_phone(phone_str):
    """
    Извлекает только цифры из строки и возвращает первые 11 (российский формат).
    Если вход None или не строка — возвращает пустую строку.
    """
    if not phone_str or not isinstance(phone_str, str):
        return ""
    digits = ''.join(filter(str.isdigit, phone_str))
    return digits[:11] if digits else ""


PUZZLE_WIDTH = 200
PUZZLE_HEIGHT = 100
SLICE_WIDTH = 50

def generate_puzzle():
    """
    Генерирует фоновое изображение и фрагмент для капчи-пазла.
    Сохраняет правильную позицию в сессии.
    Возвращает: (bg_image_b64, piece_image_b64, slice_width, max_width)
    """
    img = Image.new('RGB', (PUZZLE_WIDTH, PUZZLE_HEIGHT), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)

    for _ in range(10):
        x1 = random.randint(0, PUZZLE_WIDTH)
        y1 = random.randint(0, PUZZLE_HEIGHT)
        x2 = random.randint(0, PUZZLE_WIDTH)
        y2 = random.randint(0, PUZZLE_HEIGHT)
        draw.line((x1, y1, x2, y2),
                  fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)),
                  width=2)

    slice_x = random.randint(10, PUZZLE_WIDTH - SLICE_WIDTH - 10)
    slice_box = (slice_x, 0, slice_x + SLICE_WIDTH, PUZZLE_HEIGHT)
    puzzle_piece = img.crop(slice_box)

    draw.rectangle(slice_box, fill=(200, 200, 200))

    def image_to_b64(image):
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    bg_image = image_to_b64(img)
    piece_image = image_to_b64(puzzle_piece)

    session['captcha_correct_x'] = slice_x
    session['captcha_shown'] = True

    return bg_image, piece_image, SLICE_WIDTH, PUZZLE_WIDTH
def get_database_size():
    """
    Возвращает размер базы данных в байтах и в человеко-читаемом формате.
    """
    db_path = os.path.join(current_app.root_path, 'app.db')
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_bytes, f"{size_mb:.2f} МБ"
    return 0, "0 Б"


def get_backups_info():
    """
    Возвращает информацию о всех резервных копиях в директории.
    """
    backups_dir = os.path.join(current_app.root_path, 'backups')
    backups_info = {
        'full': {'count': 0, 'total_size': 0, 'files': []},
        'incremental': {'count': 0, 'total_size': 0, 'files': []},
        'differential': {'count': 0, 'total_size': 0, 'files': []}
    }

    if not os.path.exists(backups_dir):
        return backups_info

    for backup_type in ['full', 'incremental', 'differential']:
        type_dir = os.path.join(backups_dir, backup_type)
        if os.path.exists(type_dir):
            for filename in os.listdir(type_dir):
                filepath = os.path.join(type_dir, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    backups_info[backup_type]['count'] += 1
                    backups_info[backup_type]['total_size'] += size
                    backups_info[backup_type]['files'].append({
                        'name': filename,
                        'path': filepath,
                        'size': size,
                        'size_mb': f"{size / (1024 * 1024):.2f} МБ",
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
                    })

    # Сортируем файлы по дате (новые сверху)
    for backup_type in backups_info:
        backups_info[backup_type]['files'].sort(
            key=lambda x: x['modified'], reverse=True
        )
        backups_info[backup_type]['total_size_mb'] = f"{backups_info[backup_type]['total_size'] / (1024 * 1024):.2f} МБ"

    return backups_info


def cleanup_old_backups(keep_count=10):
    """
    Удаляет старые резервные копии, оставляя только последние keep_count штук.
    Возвращает количество удалённых файлов.
    """
    backups_dir = os.path.join(current_app.root_path, 'backups')
    deleted_count = 0

    if not os.path.exists(backups_dir):
        return 0

    for backup_type in ['full', 'incremental', 'differential']:
        type_dir = os.path.join(backups_dir, backup_type)
        if os.path.exists(type_dir):
            # Получаем список файлов с их временем модификации
            files = []
            for filename in os.listdir(type_dir):
                filepath = os.path.join(type_dir, filename)
                if os.path.isfile(filepath):
                    files.append((filepath, os.path.getmtime(filepath)))

            # Сортируем по времени (старые в конце)
            files.sort(key=lambda x: x[1], reverse=True)

            # Удаляем старые файлы
            for filepath, _ in files[keep_count:]:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Ошибка удаления {filepath}: {e}")

    return deleted_count


def validate_backup_file(filename):
    """
    Проверяет, является ли файл корректной резервной копией.
    Возвращает (is_valid, message, filepath)
    """
    backups_dir = os.path.join(current_app.root_path, 'backups')

    # Ищем файл в поддиректориях
    for subdir in ['full', 'incremental', 'differential']:
        filepath = os.path.join(backups_dir, subdir, filename)
        if os.path.exists(filepath):
            # Проверяем расширение
            if not (filename.endswith('.db') or filename.endswith('.zip')):
                return False, "Некорректный формат файла. Ожидается .db или .zip", None

            # Проверяем размер (не должен быть 0)
            if os.path.getsize(filepath) == 0:
                return False, "Файл резервной копии повреждён (размер 0)", None

            # Для zip-файлов проверяем, что внутри есть .db
            if filename.endswith('.zip'):
                try:
                    with zipfile.ZipFile(filepath, 'r') as zipf:
                        has_db = any(f.endswith('.db') for f in zipf.namelist())
                        if not has_db:
                            return False, "Архив не содержит файла базы данных", None
                except zipfile.BadZipFile:
                    return False, "Архив повреждён", None

            return True, "Файл валиден", filepath

    return False, "Файл не найден", None


def get_system_stats():
    """
    Собирает общую статистику по системе.
    """
    from app.models import User, Building, Apartment, Owner, Request, Service, Charge, Payment, Expense

    stats = {
        'users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True, blocked=False).count(),
        'blocked_users': User.query.filter_by(blocked=True).count(),
        'admins': User.query.filter_by(is_admin=True).count(),
        'buildings': Building.query.count(),
        'apartments': Apartment.query.count(),
        'owners': Owner.query.count(),
        'requests': {
            'total': Request.query.count(),
            'new': Request.query.filter_by(status='new').count(),
            'in_progress': Request.query.filter_by(status='in_progress').count(),
            'completed': Request.query.filter_by(status='completed').count(),
            'rejected': Request.query.filter_by(status='rejected').count()
        },
        'services': Service.query.count(),
        'charges_total': db.session.query(db.func.sum(Charge.amount)).scalar() or 0,
        'payments_total': db.session.query(db.func.sum(Payment.paid_amount)).scalar() or 0,
        'expenses_total': db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    }

    # Вычисляем общую задолженность
    stats['debt_total'] = stats['charges_total'] - stats['payments_total']

    # Чистая прибыль
    stats['net_profit'] = stats['payments_total'] - stats['expenses_total']

    return stats


def get_recent_activity(limit=20):
    """
    Возвращает недавнюю активность в системе (логи действий администраторов и заявки).
    """
    from app.models import AdminActionLog, Request

    activities = []

    # Логи администраторов
    admin_logs = AdminActionLog.query.order_by(
        AdminActionLog.timestamp.desc()
    ).limit(limit).all()

    for log in admin_logs:
        activities.append({
            'timestamp': log.timestamp,
            'type': 'admin',
            'admin': log.admin.username if log.admin else 'Unknown',
            'action': log.action,
            'target': f"{log.target_type} #{log.target_id}" if log.target_id else None,
            'details': log.details
        })

    # Если логов меньше limit, добавляем последние заявки
    if len(activities) < limit:
        requests = Request.query.order_by(
            Request.created_at.desc()
        ).limit(limit - len(activities)).all()

        for req in requests:
            activities.append({
                'timestamp': req.created_at,
                'type': 'request',
                'title': req.title,
                'status': req.status,
                'priority': req.priority,
                'apartment_id': req.apartment_id
            })

    # Сортируем по времени
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return activities[:limit]


def export_users_to_csv():
    """
    Экспортирует список пользователей в CSV-формат.
    Возвращает строку CSV.
    """
    from app.models import User
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow(['ID', 'Имя пользователя', 'Email', 'Администратор', 'Активен', 'Заблокирован', 'Дата создания'])

    # Данные
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email or '',
            'Да' if user.is_admin else 'Нет',
            'Да' if user.is_active else 'Нет',
            'Да' if user.blocked else 'Нет',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
        ])

    return output.getvalue()


def export_financial_report(period=None):
    """
    Экспортирует финансовый отчёт по начислениям и платежам.
    period: строка формата 'YYYY-MM' или None для всего периода.
    """
    from app.models import Charge, Payment
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow([
        'Период', 'Тип операции', 'Услуга', 'Квартира', 'Сумма', 'Дата'
    ])

    # Запрос для начислений
    charges_query = Charge.query
    if period:
        charges_query = charges_query.filter(Charge.period == period)
    charges = charges_query.all()

    for charge in charges:
        writer.writerow([
            charge.period,
            'Начисление',
            charge.service.name if charge.service else 'Неизвестно',
            f"Кв.{charge.apartment.number} (Дом #{charge.apartment.building_id})" if charge.apartment else 'Неизвестно',
            charge.amount,
            charge.created_at.strftime('%Y-%m-%d %H:%M:%S') if charge.created_at else ''
        ])

    # Запрос для платежей
    payments_query = Payment.query
    if period:
        # Для платежей фильтр по дате платежа
        from datetime import datetime
        try:
            year, month = map(int, period.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            payments_query = payments_query.filter(
                Payment.payment_date >= start_date,
                Payment.payment_date < end_date
            )
        except:
            pass

    payments = payments_query.all()

    for payment in payments:
        writer.writerow([
            payment.payment_date.strftime('%Y-%m') if payment.payment_date else 'Неизвестно',
            'Платёж',
            payment.service.name if payment.service else 'Неизвестно',
            f"Кв.{payment.apartment.number} (Дом #{payment.apartment.building_id})" if payment.apartment else 'Неизвестно',
            payment.paid_amount,
            payment.payment_date.strftime('%Y-%m-%d %H:%M:%S') if payment.payment_date else ''
        ])

    return output.getvalue()