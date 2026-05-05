from sqlalchemy.orm import joinedload
from database.db import SessionLocal
from models import User, AccessLevel


class UserController:
    def __init__(self, session=None):
        self.db_session = session or SessionLocal()

    def get_user(self, username):
        return self.db_session.query(User)\
            .options(joinedload(User.access_level))\
            .filter(User.username == username).first()

    def get_user_by_id(self, user_id):
        return self.db_session.query(User)\
            .options(joinedload(User.access_level))\
            .filter(User.id == user_id).first()

    def get_all_users(self):
        return self.db_session.query(User)\
            .options(joinedload(User.access_level))\
            .all()

    def get_access_level(self, level_name):
        return self.db_session.query(AccessLevel).filter(AccessLevel.name == level_name).first()

    def create_user(self, username, password, access_level='Пользователь', is_active=True):
        from utils.security import Security
        hashed_password = Security.hash_password(password)

        level = self.get_access_level(access_level)
        if not level:
            level = AccessLevel(name=access_level)
            self.db_session.add(level)
            self.db_session.commit()

        user = User(
            username=username,
            password=hashed_password,
            access_level_id=level.id,
            is_active=is_active
        )
        self.db_session.add(user)
        self.db_session.commit()
        return user

    def update_user(self, user_id, data):
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        for key, value in data.items():
            setattr(user, key, value)
        self.db_session.commit()
        return user

    def delete_user(self, user_id):
        user = self.get_user_by_id(user_id)
        if user:
            self.db_session.delete(user)
            self.db_session.commit()

    def close(self):
        if self.db_session:
            self.db_session.close()

    def __del__(self):
        self.close()