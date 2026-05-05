from database.db import engine, Base
from models import Tournament, TournamentParticipant, Match

def migrate():
    print("Создание таблиц турниров...")
    Base.metadata.create_all(bind=engine)
    print("Готово!")

if __name__ == "__main__":
    migrate()