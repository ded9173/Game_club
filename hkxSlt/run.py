from app import create_app, db
import os

app = create_app()

session_dir = os.path.join(app.root_path, 'flask_session')
os.makedirs(session_dir, exist_ok=True)

with app.app_context():
    db_path = os.path.join(app.root_path, 'app.db')
    if not os.path.exists(db_path):
        db.create_all()
        print("✅ Таблицы успешно созданы в app.db")
    else:
        print("ℹ️  База данных уже существует, таблицы не создаются повторно")


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)