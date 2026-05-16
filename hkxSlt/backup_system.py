import os
import json
from datetime import datetime

LOG_FILE = 'backup_log.json'

def log_backup(backup_type, filename, path):
    """Запись информации о бэкапе в лог-файл"""
    log_entry = {
        "type": backup_type,
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "path": path
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append(log_entry)

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"Лог: {backup_type} - {filename}")


def get_last_full_backup_time():
    """Возвращает время последнего полного бэкапа из лога"""
    try:
        if not os.path.exists(LOG_FILE):
            return None

        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        full_backups = [log for log in logs if log['type'] == 'full']

        if not full_backups:
            return None

        latest_full = sorted(full_backups, key=lambda x: x['timestamp'], reverse=True)[0]
        return datetime.fromisoformat(latest_full['timestamp']).timestamp()

    except:
        return None


def print_backup_history():
    """Выводит историю всех бэкапов"""
    if not os.path.exists(LOG_FILE):
        print("\nИстория бэкапов пуста")
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    print("\n" + "="*60)
    print("ИСТОРИЯ РЕЗЕРВНЫХ КОПИЙ")
    print("="*60)
    print(f"{'Тип':<15} {'Дата и время':<25} {'Имя файла'}")
    print("-"*60)

    for log in logs:
        log_type = log['type'].upper()
        timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{log_type:<15} {timestamp:<25} {log['filename']}")

    print("="*60)


if __name__ == "__main__":
    log_backup("full", "full_20260212_120000.db", "backups/full/full_20260212_120000.db")
    log_backup("incremental", "incremental_20260212_130000.db", "backups/incremental/incremental_20260212_130000.db")

    last_full = get_last_full_backup_time()
    if last_full:
        print(f"\nПоследний полный: {datetime.fromtimestamp(last_full)}")

    print_backup_history()