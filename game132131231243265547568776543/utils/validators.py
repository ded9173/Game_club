import re


def validate_phone(phone):
    pattern = r'^(\+\d{1,3}|\d)?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
    return re.match(pattern, phone.strip()) is not None


def validate_inn(inn):
    return bool(re.fullmatch(r'\d{10}|\d{12}', inn))


def validate_name(name):
    if not name or not name.strip():
        return False
    return bool(re.match(r'^[а-яА-ЯёЁ][а-яА-ЯёЁ\s\-]+[а-яА-ЯёЁ]$', name.strip()))


def validate_address(address):
    return bool(address and len(address.strip()) >= 5)


def is_valid_customer_data(name, inn, address, phone):
    return all([
        validate_name(name),
        validate_inn(inn),
        validate_address(address),
        validate_phone(phone)
    ])

def validate_full_name(full_name):
    """
    Проверяет ФИО на:
    1. Наличие только кириллических букв, пробелов, дефисов и амперсанда (&)
    2. Отсутствие цифр и специальных символов (!, @, # и т.д.)

    :param full_name: str
    :return: list of str — список ошибок
    """
    errors = []

    allowed_pattern = r'^[А-Яа-яЁё&\-\s]+$'
    if not re.match(allowed_pattern, full_name):
        errors.append("Недопустимые символы: разрешены только кириллица, &, пробел, дефис")

    if re.search(r'\d', full_name):
        errors.append("ФИО содержит цифры")

    return errors

def validate_username(username):
    import re
    return bool(re.fullmatch(r'[a-zA-Z0-9_]{3,20}', username))