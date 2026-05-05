from datetime import datetime
from config import LOGS_DIR
import logging

LOGS_DIR.mkdir(exist_ok=True)
log_file = LOGS_DIR / f'app_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8'
)


def log_action(user: str, action: str):
    logging.info(f"Пользователь: {user} | Действие: {action}")