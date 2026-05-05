import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from controllers.user_controller import UserController
from database.db import SessionLocal
from models import User, AccessLevel


class TestUserController(unittest.TestCase):
    def setUp(self):
        self.session = SessionLocal()
        self.user_ctrl = UserController(session=self.session)

        self.session.query(User).filter(User.username == 'testuser2').delete()
        self.session.query(AccessLevel).filter(AccessLevel.name == 'Пользователь').delete()
        self.session.commit()

    def tearDown(self):
        self.session.query(User).filter(User.username == 'testuser2').delete()
        self.session.query(AccessLevel).filter(AccessLevel.name == 'Пользователь').delete()
        self.session.commit()
        self.session.close()

    def test_create_and_get_user(self):
        user = self.user_ctrl.create_user('testuser2', 'password123', 'Пользователь')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser2')

        fetched_user = self.user_ctrl.get_user('testuser2')
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.username, 'testuser2')


if __name__ == '__main__':
    unittest.main()