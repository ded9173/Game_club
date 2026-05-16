from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Building, Apartment, Owner, Service, Charge, Payment, Request, Staff, Expense, Resident
from app.forms import (
    RegistrationForm, LoginForm, ProfileForm, BuildingRegistrationForm,
    ApartmentRegistrationForm, OwnerRegistrationForm, ServiceSelectionForm,
    ChargeEntryForm, PaymentEntryForm, RequestForm, StaffForm, ExpenseForm, ResidentForm
)
from app.services import create_user
from app.utils import generate_puzzle

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(
            db.select(User).filter_by(username=form.username.data)
        ).scalar()

        if user and user.check_password(form.password.data) and not user.blocked:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Ошибка авторизации. Неправильное имя пользователя или пароль.', 'danger')

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.home'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()

    if request.method == 'GET':
        bg_img, piece_img, slice_w, max_w = generate_puzzle()
        return render_template('auth/register.html',
                             form=form,
                             bg_img=bg_img,
                             piece_img=piece_img,
                             slice_w=slice_w,
                             max_w=max_w)

    user_x = request.form.get('puzzle_x')
    correct_x = session.get('captcha_correct_x')

    if not session.get('captcha_shown') or not user_x or abs(int(user_x) - correct_x) > 5:
        flash('Капча решена неверно. Попробуйте снова.', 'danger')
        bg_img, piece_img, slice_w, max_w = generate_puzzle()
        return render_template('auth/register.html',
                             form=form,
                             bg_img=bg_img,
                             piece_img=piece_img,
                             slice_w=slice_w,
                             max_w=max_w)

    if form.validate_on_submit():
        existing_user = db.session.execute(
            db.select(User).filter_by(username=form.username.data)
        ).scalar()
        if existing_user:
            flash('Пользователь с таким именем уже существует.', 'danger')
            bg_img, piece_img, slice_w, max_w = generate_puzzle()
            return render_template('auth/register.html',
                                 form=form,
                                 bg_img=bg_img,
                                 piece_img=piece_img,
                                 slice_w=slice_w,
                                 max_w=max_w)

        user = create_user(form.username.data, form.password.data)
        flash('Регистрация прошла успешно! Войдите в систему.', 'success')
        return redirect(url_for('main.login'))

    bg_img, piece_img, slice_w, max_w = generate_puzzle()
    return render_template('auth/register.html',
                         form=form,
                         bg_img=bg_img,
                         piece_img=piece_img,
                         slice_w=slice_w,
                         max_w=max_w)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():

        other_user = db.session.execute(
            db.select(User).filter_by(username=form.username.data)
        ).scalar()
        if other_user and other_user.id != current_user.id:
            flash('Это имя пользователя уже занято.', 'danger')
        else:
            current_user.username = form.username.data
            db.session.commit()
            flash('Профиль обновлён!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html', form=form)


@bp.route('/building/register', methods=['GET', 'POST'])
@login_required
def register_building():
    form = BuildingRegistrationForm()
    if form.validate_on_submit():
        building = Building(
            address=form.address.data,
            floors=form.floors.data,
            year_built=form.year_built.data,
            total_area=form.total_area.data,
            city=form.city.data,
            street=form.street.data,
            house_number=form.house_number.data
        )
        db.session.add(building)
        db.session.commit()
        flash('Здание зарегистрировано!', 'success')
        return redirect(url_for('main.home'))
    return render_template('building_register.html', form=form)


@bp.route('/apartment/register', methods=['GET', 'POST'])
@login_required
def register_apartment():
    form = ApartmentRegistrationForm()
    buildings = db.session.execute(db.select(Building)).scalars().all()
    owners = db.session.execute(db.select(Owner)).scalars().all()

    form.building_id.choices = [(b.id, b.address) for b in buildings]
    form.owner_id.choices = [('', '— Не указан —')] + [(str(o.id), o.full_name) for o in owners]

    if form.validate_on_submit():
        building = db.session.get(Building, form.building_id.data)
        if not building:
            flash('Выбранное здание не найдено.', 'danger')
            return render_template('apartment_register.html', form=form)

        owner_id = form.owner_id.data
        owner_id = int(owner_id) if owner_id else None

        apartment = Apartment(
            number=form.number.data,
            area=form.area.data,
            building_id=form.building_id.data,
            owner_id=owner_id
        )
        db.session.add(apartment)
        db.session.commit()
        flash('Квартира зарегистрирована!', 'success')
        return redirect(url_for('main.home'))

    return render_template('apartment_register.html', form=form)


@bp.route('/owner/register', methods=['GET', 'POST'])
@login_required
def register_owner():
    form = OwnerRegistrationForm()
    if form.validate_on_submit():
        owner = Owner(
            full_name=form.full_name.data,
            phone=form.phone.data,
            email=form.email.data or None
        )
        db.session.add(owner)
        db.session.commit()
        flash('Владелец зарегистрирован!', 'success')
        return redirect(url_for('main.home'))
    return render_template('owner_register.html', form=form)


@bp.route('/service/register', methods=['GET', 'POST'])
@login_required
def register_service():
    form = ServiceSelectionForm()
    services = db.session.execute(db.select(Service)).scalars().all()
    form.service.choices = [(s.id, s.name) for s in services]
    form.service.choices.append(('new', '➕ Добавить новую услугу'))

    if form.validate_on_submit():
        if form.service.data == 'new':
            flash('Укажите название новой услуги.', 'info')
            return render_template('service_register.html', form=form)

        flash('Услуга уже доступна.', 'info')
        return redirect(url_for('main.home'))

    return render_template('service_register.html', form=form)


@bp.route('/service/new', methods=['GET', 'POST'])
@login_required
def add_new_service():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Название услуги обязательно.', 'danger')
            return redirect(url_for('main.register_service'))

        existing = db.session.execute(
            db.select(Service).filter_by(name=name)
        ).scalar()
        if existing:
            flash('Такая услуга уже существует.', 'warning')
        else:
            service = Service(name=name)
            db.session.add(service)
            db.session.commit()
            flash('Новая услуга добавлена!', 'success')

        return redirect(url_for('main.home'))

    return render_template('service_new.html')


@bp.route('/charge/register', methods=['GET', 'POST'])
@login_required
def register_charge():
    form = ChargeEntryForm()
    apartments = db.session.execute(db.select(Apartment)).scalars().all()
    services = db.session.execute(db.select(Service)).scalars().all()

    form.apartment_id.choices = [(a.id, f'{a.number}, {a.building.address}') for a in apartments]
    form.service_id.choices = [(s.id, s.name) for s in services]

    if form.validate_on_submit():
        apartment = db.session.get(Apartment, form.apartment_id.data)
        service = db.session.get(Service, form.service_id.data)
        if not apartment or not service:
            flash('Некорректная квартира или услуга.', 'danger')
            return render_template('charge_register.html', form=form)

        charge = Charge(
            apartment_id=form.apartment_id.data,
            service_id=form.service_id.data,
            period=form.period.data,
            amount=form.amount.data
        )
        db.session.add(charge)
        db.session.commit()
        flash('Начисление внесено!', 'success')
        return redirect(url_for('main.home'))

    return render_template('charge_register.html', form=form)


@bp.route('/payment/register', methods=['GET', 'POST'])
@login_required
def register_payment():
    form = PaymentEntryForm()
    apartments = db.session.execute(db.select(Apartment)).scalars().all()
    services = db.session.execute(db.select(Service)).scalars().all()

    form.apartment_id.choices = [(a.id, f'{a.number}, {a.building.address}') for a in apartments]
    form.service_id.choices = [(s.id, s.name) for s in services]

    if form.validate_on_submit():
        apartment = db.session.get(Apartment, form.apartment_id.data)
        service = db.session.get(Service, form.service_id.data)
        if not apartment or not service:
            flash('Некорректная квартира или услуга.', 'danger')
            return render_template('payment_register.html', form=form)

        payment = Payment(
            apartment_id=form.apartment_id.data,
            service_id=form.service_id.data,
            paid_amount=form.paid_amount.data,
            payment_date=form.payment_date.data or None
        )
        db.session.add(payment)
        db.session.commit()
        flash('Оплата внесена!', 'success')
        return redirect(url_for('main.home'))

    return render_template('payment_register.html', form=form)


@bp.route('/request/register', methods=['GET', 'POST'])
@login_required
def register_request():
    form = RequestForm()
    apartments = db.session.execute(db.select(Apartment)).scalars().all()
    form.apartment_id.choices = [(a.id, f'{a.number}, {a.building.address}') for a in apartments]

    if form.validate_on_submit():
        apartment = db.session.get(Apartment, form.apartment_id.data)
        if not apartment:
            flash('Квартира не найдена.', 'danger')
            return render_template('request_register.html', form=form)

        req = Request(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            apartment_id=form.apartment_id.data
        )
        db.session.add(req)
        db.session.commit()
        flash('Обращение зарегистрировано!', 'success')
        return redirect(url_for('main.home'))

    return render_template('request_register.html', form=form)


@bp.route('/staff/register', methods=['GET', 'POST'])
@login_required
def register_staff():
    form = StaffForm()
    if form.validate_on_submit():
        staff = Staff(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            position=form.position.data,
            phone=form.phone.data,
            email=form.email.data
        )
        db.session.add(staff)
        db.session.commit()
        flash('Сотрудник зарегистрирован!', 'success')
        return redirect(url_for('main.home'))
    return render_template('staff_register.html', form=form)


@bp.route('/expense/register', methods=['GET', 'POST'])
@login_required
def register_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            date=form.date.data,
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data
        )
        db.session.add(expense)
        db.session.commit()
        flash('Расход зарегистрирован!', 'success')
        return redirect(url_for('main.home'))
    return render_template('expense_register.html', form=form)


@bp.route('/resident/register', methods=['GET', 'POST'])
@login_required
def register_resident():
    form = ResidentForm()
    apartments = db.session.execute(db.select(Apartment)).scalars().all()
    form.apartment_id.choices = [(a.id, f'{a.number}, {a.building.address}') for a in apartments]

    if form.validate_on_submit():
        apartment = db.session.get(Apartment, form.apartment_id.data)
        if not apartment:
            flash('Квартира не найдена.', 'danger')
            return render_template('resident_register.html', form=form)

        resident = Resident(
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data or None,
            relation_to_owner=form.relation_to_owner.data,
            apartment_id=form.apartment_id.data
        )
        db.session.add(resident)
        db.session.commit()
        flash('Житель зарегистрирован!', 'success')
        return redirect(url_for('main.home'))

    return render_template('resident_register.html', form=form)


@bp.route('/api/buildings', methods=['GET'])
def api_get_buildings():
    try:
        buildings = db.session.execute(db.select(Building)).scalars().all()
        results = [
            {
                'id': b.id,
                'address': b.address,
                'floors': b.floors,
                'year_built': b.year_built,
                'total_area': float(b.total_area) if b.total_area else None
            }
            for b in buildings
        ]
        return jsonify(results), 200
    except Exception as e:
        from app import app
        app.logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/admin/dashboard')
@bp.route('/admin/settings')
@bp.route('/admin/settings/change-password')
@bp.route('/admin/settings/backup')
@bp.route('/admin/settings/restore')
@bp.route('/admin/users')
@bp.route('/admin/users/create')
@bp.route('/admin/users/<int:user_id>/edit')
@bp.route('/admin/users/<int:user_id>/block')
@bp.route('/admin/users/<int:user_id>/delete')


@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500