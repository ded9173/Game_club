import os
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user

from app import db
from app.models import User, AdminActionLog, Backup
from app.forms import (
    AdminChangePasswordForm, AdminCreateUserForm, AdminEditUserForm,
    AdminChangeUserPasswordForm, AdminBlockUserForm, BackupCreateForm,
    RestoreForm, FilterUsersForm
)
from app.decorators import admin_required
from backup_system import log_backup
from app.services import (
    create_user_with_email, get_user_by_username, get_user_by_email,
    update_user, change_user_password, block_user, unblock_user,
    soft_delete_user, hard_delete_user, get_all_users, get_user_stats
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================

def log_admin_action(admin_id, action, target_type=None, target_id=None, details=None, ip_address=None):
    """Логирование действий администратора"""
    log = AdminActionLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()


def get_backups_dir():
    """Получить путь к директории с бэкапами"""
    return os.path.join(current_app.root_path, 'backups')


def create_full_backup():
    """Создание полной резервной копии БД"""
    backups_dir = get_backups_dir()
    full_dir = os.path.join(backups_dir, 'full')
    os.makedirs(full_dir, exist_ok=True)

    db_path = os.path.join(current_app.root_path, 'app.db')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'full_backup_{timestamp}.db'
    backup_path = os.path.join(full_dir, backup_filename)

    shutil.copy2(db_path, backup_path)

    zip_filename = f'full_backup_{timestamp}.zip'
    zip_path = os.path.join(full_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(backup_path, os.path.basename(backup_path))

    os.remove(backup_path)

    backup_record = Backup(
        backup_type='full',
        filename=zip_filename,
        filepath=zip_path,
        filesize=os.path.getsize(zip_path),
        created_by=current_user.id if current_user.is_authenticated else None,
        description=f'Полная резервная копия от {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )
    db.session.add(backup_record)
    db.session.commit()

    log_backup('full', zip_filename, zip_path)

    return zip_path, zip_filename


def create_incremental_backup():
    """Создание инкрементной резервной копии"""
    backups_dir = get_backups_dir()
    inc_dir = os.path.join(backups_dir, 'incremental')
    os.makedirs(inc_dir, exist_ok=True)

    last_full = Backup.query.filter_by(backup_type='full').order_by(Backup.created_at.desc()).first()
    last_backup = Backup.query.filter(
        Backup.backup_type.in_(['full', 'incremental'])
    ).order_by(Backup.created_at.desc()).first()

    db_path = os.path.join(current_app.root_path, 'app.db')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'incremental_backup_{timestamp}.db'
    backup_path = os.path.join(inc_dir, backup_filename)

    shutil.copy2(db_path, backup_path)

    backup_record = Backup(
        backup_type='incremental',
        filename=backup_filename,
        filepath=backup_path,
        filesize=os.path.getsize(backup_path),
        created_by=current_user.id if current_user.is_authenticated else None,
        based_on=last_full.id if last_full else None,
        last_backup_time=last_backup.created_at if last_backup else None,
        description=f'Инкрементная резервная копия от {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )
    db.session.add(backup_record)
    db.session.commit()

    log_backup('incremental', backup_filename, backup_path)

    return backup_path, backup_filename


def create_differential_backup():
    """Создание дифференциальной резервной копии"""
    backups_dir = get_backups_dir()
    diff_dir = os.path.join(backups_dir, 'differential')
    os.makedirs(diff_dir, exist_ok=True)

    last_full = Backup.query.filter_by(backup_type='full').order_by(Backup.created_at.desc()).first()

    db_path = os.path.join(current_app.root_path, 'app.db')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'differential_backup_{timestamp}.db'
    backup_path = os.path.join(diff_dir, backup_filename)

    shutil.copy2(db_path, backup_path)

    backup_record = Backup(
        backup_type='differential',
        filename=backup_filename,
        filepath=backup_path,
        filesize=os.path.getsize(backup_path),
        created_by=current_user.id if current_user.is_authenticated else None,
        based_on=last_full.id if last_full else None,
        description=f'Дифференциальная резервная копия от {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )
    db.session.add(backup_record)
    db.session.commit()

    log_backup('differential', backup_filename, backup_path)

    return backup_path, backup_filename


def restore_from_backup(backup_filename):
    """Восстановление системы из резервной копии"""
    backups_dir = get_backups_dir()
    db_path = os.path.join(current_app.root_path, 'app.db')

    backup_path = None
    for subdir in ['full', 'incremental', 'differential']:
        candidate = os.path.join(backups_dir, subdir, backup_filename)
        if os.path.exists(candidate):
            backup_path = candidate
            break

    if not backup_path:
        return False, "Файл резервной копии не найден"

    rollback_path = os.path.join(backups_dir, 'rollback_backup.db')
    shutil.copy2(db_path, rollback_path)

    try:
        if backup_filename.endswith('.zip'):
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                for file in zipf.namelist():
                    if file.endswith('.db'):
                        zipf.extract(file, os.path.dirname(backup_path))
                        restored_db = os.path.join(os.path.dirname(backup_path), file)
                        shutil.copy2(restored_db, db_path)
                        os.remove(restored_db)
                        break
        else:
            shutil.copy2(backup_path, db_path)

        return True, "Система успешно восстановлена"
    except Exception as e:
        shutil.copy2(rollback_path, db_path)
        return False, f"Ошибка восстановления: {str(e)}"


# ======================
# АДМИН-МАРШРУТЫ
# ======================

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Панель администратора"""
    stats = get_user_stats()

    recent_actions = AdminActionLog.query.order_by(AdminActionLog.timestamp.desc()).limit(10).all()
    recent_backups = Backup.query.order_by(Backup.created_at.desc()).limit(5).all()
    last_full_backup = Backup.query.filter_by(backup_type='full').order_by(Backup.created_at.desc()).first()

    return render_template('admin/dashboard.html',
                           total_users=stats['total'],
                           active_users=stats['active'],
                           blocked_users=stats['blocked'],
                           admin_users=stats['admin'],
                           recent_actions=recent_actions,
                           recent_backups=recent_backups,
                           last_full_backup=last_full_backup)


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Настройки системы"""
    return render_template('admin/settings.html')


@admin_bp.route('/settings/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password():
    """Смена пароля администратора"""
    form = AdminChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Неверный текущий пароль.', 'danger')
        else:
            change_user_password(current_user.id, form.new_password.data)

            log_admin_action(
                admin_id=current_user.id,
                action='change_password',
                target_type='User',
                target_id=current_user.id,
                details={'ip': request.remote_addr},
                ip_address=request.remote_addr
            )

            flash('Пароль успешно изменён!', 'success')
            return redirect(url_for('admin.settings'))

    return render_template('admin/change_password.html', form=form)


@admin_bp.route('/settings/backup', methods=['GET', 'POST'])
@login_required
@admin_required
def backup():
    """Управление резервными копиями"""
    form = BackupCreateForm()
    backups = Backup.query.order_by(Backup.created_at.desc()).all()

    if form.validate_on_submit():
        backup_type = form.backup_type.data
        description = form.description.data

        try:
            if backup_type == 'full':
                backup_path, filename = create_full_backup()
                flash(f'Полная резервная копия создана: {filename}', 'success')
            elif backup_type == 'incremental':
                backup_path, filename = create_incremental_backup()
                flash(f'Инкрементная резервная копия создана: {filename}', 'success')
            elif backup_type == 'differential':
                backup_path, filename = create_differential_backup()
                flash(f'Дифференциальная резервная копия создана: {filename}', 'success')

            log_admin_action(
                admin_id=current_user.id,
                action='create_backup',
                target_type='Backup',
                details={'type': backup_type, 'description': description},
                ip_address=request.remote_addr
            )
        except Exception as e:
            flash(f'Ошибка создания резервной копии: {str(e)}', 'danger')

        return redirect(url_for('admin.backup'))

    return render_template('admin/backup.html', form=form, backups=backups)


@admin_bp.route('/settings/backup/download/<int:backup_id>')
@login_required
@admin_required
def download_backup(backup_id):
    """Скачивание файла резервной копии"""
    backup = Backup.query.get_or_404(backup_id)

    if not os.path.exists(backup.filepath):
        flash('Файл резервной копии не найден.', 'danger')
        return redirect(url_for('admin.backup'))

    log_admin_action(
        admin_id=current_user.id,
        action='download_backup',
        target_type='Backup',
        target_id=backup_id,
        ip_address=request.remote_addr
    )

    return send_file(backup.filepath, as_attachment=True, download_name=backup.filename)


@admin_bp.route('/settings/restore', methods=['GET', 'POST'])
@login_required
@admin_required
def restore():
    """Восстановление системы"""
    form = RestoreForm()

    if form.validate_on_submit():
        backup_file = form.backup_file.data

        success, message = restore_from_backup(backup_file)

        if success:
            log_admin_action(
                admin_id=current_user.id,
                action='restore_system',
                details={'backup_file': backup_file},
                ip_address=request.remote_addr
            )
            flash(message, 'success')
        else:
            flash(message, 'danger')

        return redirect(url_for('admin.settings'))

    return render_template('admin/restore.html', form=form)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Список пользователей"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', 'all')
    status = request.args.get('status', 'all')

    pagination = get_all_users(page=page, per_page=20, search=search, role=role, status=status)
    users = pagination.items
    stats = get_user_stats()

    return render_template('admin/users.html', users=users, pagination=pagination, stats=stats,
                           search=search, role=role, status=status)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Создание нового пользователя"""
    form = AdminCreateUserForm()

    if form.validate_on_submit():
        # Проверка уникальности
        if get_user_by_username(form.username.data):
            flash('Пользователь с таким именем уже существует.', 'danger')
            return render_template('admin/create_user.html', form=form)

        if form.email.data and get_user_by_email(form.email.data):
            flash('Пользователь с таким email уже существует.', 'danger')
            return render_template('admin/create_user.html', form=form)

        user = create_user_with_email(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data or None,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )

        log_admin_action(
            admin_id=current_user.id,
            action='create_user',
            target_type='User',
            target_id=user.id,
            details={'username': user.username, 'email': user.email, 'is_admin': user.is_admin},
            ip_address=request.remote_addr
        )

        flash(f'Пользователь {user.username} успешно создан!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html', form=form)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Редактирование пользователя"""
    user = get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('admin.users'))

    form = AdminEditUserForm(
        original_username=user.username,
        original_email=user.email,
        obj=user
    )

    if form.validate_on_submit():
        changes = {}

        if user.username != form.username.data:
            changes['username'] = {'old': user.username, 'new': form.username.data}
            user.username = form.username.data

        if user.email != form.email.data:
            changes['email'] = {'old': user.email, 'new': form.email.data}
            user.email = form.email.data

        if user.is_admin != form.is_admin.data:
            changes['is_admin'] = {'old': user.is_admin, 'new': form.is_admin.data}
            user.is_admin = form.is_admin.data

        if user.is_active != form.is_active.data:
            changes['is_active'] = {'old': user.is_active, 'new': form.is_active.data}
            user.is_active = form.is_active.data

        user.updated_at = datetime.utcnow()
        db.session.commit()

        if changes:
            log_admin_action(
                admin_id=current_user.id,
                action='edit_user',
                target_type='User',
                target_id=user.id,
                details=changes,
                ip_address=request.remote_addr
            )

        flash(f'Пользователь {user.username} успешно обновлён!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_password(user_id):
    """Смена пароля пользователя администратором"""
    user = get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('admin.users'))

    form = AdminChangeUserPasswordForm()

    if form.validate_on_submit():
        change_user_password(user_id, form.new_password.data)

        log_admin_action(
            admin_id=current_user.id,
            action='change_user_password',
            target_type='User',
            target_id=user.id,
            details={'username': user.username},
            ip_address=request.remote_addr
        )

        flash(f'Пароль пользователя {user.username} успешно изменён!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/change_user_password.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/block', methods=['GET', 'POST'])
@login_required
@admin_required
def block_user_route(user_id):
    """Блокировка пользователя"""
    user = get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('Вы не можете заблокировать самого себя.', 'danger')
        return redirect(url_for('admin.users'))

    form = AdminBlockUserForm()

    if form.validate_on_submit():
        block_user(user_id, form.block_reason.data, form.block_days.data)

        log_admin_action(
            admin_id=current_user.id,
            action='block_user',
            target_type='User',
            target_id=user.id,
            details={
                'username': user.username,
                'reason': form.block_reason.data,
                'block_days': form.block_days.data
            },
            ip_address=request.remote_addr
        )

        flash(f'Пользователь {user.username} заблокирован!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/block_user.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/unblock')
@login_required
@admin_required
def unblock_user_route(user_id):
    """Разблокировка пользователя"""
    user = get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('admin.users'))

    unblock_user(user_id)

    log_admin_action(
        admin_id=current_user.id,
        action='unblock_user',
        target_type='User',
        target_id=user.id,
        details={'username': user.username},
        ip_address=request.remote_addr
    )

    flash(f'Пользователь {user.username} разблокирован!', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_route(user_id):
    """Удаление пользователя"""
    user = get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('Вы не можете удалить самого себя.', 'danger')
        return redirect(url_for('admin.users'))

    username = user.username

    if request.form.get('delete_type') == 'soft':
        soft_delete_user(user_id)
        flash(f'Пользователь {username} деактивирован (мягкое удаление).', 'info')
    else:
        hard_delete_user(user_id)
        flash(f'Пользователь {username} полностью удалён из базы данных.', 'warning')

    log_admin_action(
        admin_id=current_user.id,
        action='delete_user',
        target_type='User',
        target_id=user_id,
        details={'username': username, 'delete_type': request.form.get('delete_type')},
        ip_address=request.remote_addr
    )

    return redirect(url_for('admin.users'))

@admin_bp.route('/export')
@login_required
@admin_required
def export_dashboard():
    """Дашборд экспорта данных"""
    from app.utils import get_system_stats
    stats = get_system_stats()
    return render_template('admin/export.html', stats=stats)


@admin_bp.route('/export/users')
@login_required
@admin_required
def export_users():
    """Экспорт пользователей в CSV"""
    from app.utils import export_users_to_csv
    import io
    from flask import Response

    csv_data = export_users_to_csv()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users_export.csv'}
    )


@admin_bp.route('/export/financial', methods=['POST'])
@login_required
@admin_required
def export_financial():
    """Экспорт финансового отчёта в CSV"""
    from app.utils import export_financial_report
    from flask import Response

    period = request.form.get('period', None)
    csv_data = export_financial_report(period)

    filename = f'financial_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    if period:
        filename = f'financial_report_{period}.csv'

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )