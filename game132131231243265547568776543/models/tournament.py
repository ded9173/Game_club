from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base
import enum


class TournamentStatus(str, enum.Enum):
    PLANNED = "Планируется"
    ACTIVE = "Активен"
    FINISHED = "Завершён"
    CANCELLED = "Отменён"


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    game_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    max_participants = Column(Integer, nullable=False, default=8)
    current_participants = Column(Integer, default=0)
    status = Column(SQLEnum(TournamentStatus), default=TournamentStatus.PLANNED)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Связи
    creator = relationship("User", foreign_keys=[created_by])
    participants = relationship("TournamentParticipant", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}')>"


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 - участвует, 0 - выбыл/отменил

    # Связи
    tournament = relationship("Tournament", back_populates="participants")
    user = relationship("User")

    # Уникальность: пользователь может зарегистрироваться на турнир только один раз
    __table_args__ = (UniqueConstraint("tournament_id", "user_id", name="unique_participant"),)


class MatchStatus(str, enum.Enum):
    SCHEDULED = "Запланирован"
    IN_PROGRESS = "В процессе"
    FINISHED = "Завершён"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    round_number = Column(Integer, nullable=False)  # Номер тура
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = бай (свободный)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = бай
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED)
    match_order = Column(Integer, default=0)  # Порядок матчей для отображения

    # Связи
    tournament = relationship("Tournament", back_populates="matches")
    player1 = relationship("User", foreign_keys=[player1_id])
    player2 = relationship("User", foreign_keys=[player2_id])
    winner = relationship("User", foreign_keys=[winner_id])

    def __repr__(self):
        p1 = self.player1.username if self.player1 else "БАЙ"
        p2 = self.player2.username if self.player2 else "БАЙ"
        return f"<Match(id={self.id}, {p1} vs {p2})>"