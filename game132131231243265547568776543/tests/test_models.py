import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Base
from models import User, AccessLevel

engine = create_engine("sqlite:///:memory:", echo=False)
Session = sessionmaker(bind=engine)


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def setUp(self):
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def test_create_access_level(self):
        level = AccessLevel(name='Тестовый уровень')
        self.session.add(level)
        self.session.commit()
        self.assertIsNotNone(level.id)
        self.assertGreater(level.id, 0)

    def test_create_user(self):
        level = AccessLevel(name='Пользователь')
        self.session.add(level)
        self.session.commit()

        user = User(
            username='testuser',
            password='$2b$12$abcde...dummyhash',
            access_level_id=level.id,
            is_active=True
        )
        self.session.add(user)
        self.session.commit()

        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.access_level_id, level.id)

    def test_unique_username_constraint(self):
        level = AccessLevel(name='Менеджер')
        self.session.add(level)
        self.session.commit()

        user1 = User(username='uniqueuser', password='pass', access_level_id=level.id)
        self.session.add(user1)
        self.session.commit()

        user2 = User(username='uniqueuser', password='pass', access_level_id=level.id)
        self.session.add(user2)
        with self.assertRaises(Exception):
            self.session.commit()
        self.session.rollback()


if __name__ == '__main__':
    unittest.main()