# recreate_tables.py
from database.db import engine, Base
from models import Tournament, TournamentParticipant, Match

def recreate_tournament_tables():
    # Удаляем существующие таблицы (если есть)
    Base.metadata.drop_all(bind=engine, tables=[
        Match.__table__,
        TournamentParticipant.__table__,
        Tournament.__table__
    ])

    # Создаём таблицы заново с новой структурой
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы турниров пересозданы")

if __name__ == "__main__":
    recreate_tournament_tables()