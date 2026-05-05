from database.db import SessionLocal
from models import Tournament, TournamentParticipant, Match, User, TournamentStatus, MatchStatus
from sqlalchemy import and_
from datetime import datetime
import random


class TournamentController:
    def __init__(self, session=None):
        self.db_session = session or SessionLocal()

    # ---------- Управление турнирами ----------
    def create_tournament(self, name, game_name, start_date, max_participants, created_by, description=""):
        """Создать новый турнир."""
        tournament = Tournament(
            name=name,
            game_name=game_name,
            start_date=start_date,
            max_participants=max_participants,
            created_by=created_by,
            description=description,
            status=TournamentStatus.PLANNED
        )
        self.db_session.add(tournament)
        self.db_session.commit()
        return tournament

    def get_all_tournaments(self, include_finished=False):
        """Получить все турниры."""
        query = self.db_session.query(Tournament)
        if not include_finished:
            query = query.filter(Tournament.status != TournamentStatus.FINISHED)
        return query.order_by(Tournament.start_date).all()

    def get_tournament_by_id(self, tournament_id):
        """Получить турнир по ID."""
        return self.db_session.query(Tournament).filter(Tournament.id == tournament_id).first()

    def update_tournament(self, tournament_id, data):
        """Обновить данные турнира."""
        tournament = self.get_tournament_by_id(tournament_id)
        if not tournament:
            raise ValueError("Турнир не найден")

        for key, value in data.items():
            if hasattr(tournament, key):
                setattr(tournament, key, value)
        self.db_session.commit()
        return tournament

    def delete_tournament(self, tournament_id):
        """Удалить турнир."""
        tournament = self.get_tournament_by_id(tournament_id)
        if tournament:
            self.db_session.delete(tournament)
            self.db_session.commit()

    # ---------- Управление участниками ----------
    def register_participant(self, tournament_id, user_id):
        """Зарегистрировать пользователя на турнир."""
        tournament = self.get_tournament_by_id(tournament_id)

        if not tournament:
            raise ValueError("Турнир не найден")

        if tournament.status != TournamentStatus.PLANNED:
            raise ValueError("Регистрация на турнир закрыта")

        if tournament.current_participants >= tournament.max_participants:
            raise ValueError("Нет свободных мест")

        # Проверка, не зарегистрирован ли уже
        existing = self.db_session.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        ).first()

        if existing:
            raise ValueError("Вы уже зарегистрированы на этот турнир")

        participant = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=user_id
        )
        self.db_session.add(participant)
        tournament.current_participants += 1
        self.db_session.commit()
        return participant

    def unregister_participant(self, tournament_id, user_id):
        """Отменить регистрацию с турнира."""
        participant = self.db_session.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        ).first()

        if participant:
            tournament = self.get_tournament_by_id(tournament_id)
            tournament.current_participants -= 1
            self.db_session.delete(participant)

            # Удалить связанные матчи, где этот пользователь участвует
            matches = self.db_session.query(Match).filter(
                Match.tournament_id == tournament_id,
                (Match.player1_id == user_id) | (Match.player2_id == user_id)
            ).all()
            for match in matches:
                self.db_session.delete(match)

            self.db_session.commit()
            return True
        return False

    def get_tournament_participants(self, tournament_id):
        """Получить всех участников турнира."""
        participants = self.db_session.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.is_active == 1
        ).all()
        return [p.user for p in participants]

    def is_user_registered(self, tournament_id, user_id):
        """Проверить, зарегистрирован ли пользователь."""
        return self.db_session.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        ).first() is not None

    # ---------- Формирование пар ----------
    def generate_matches(self, tournament_id):
        """Сформировать пары для первого тура."""
        participants = self.get_tournament_participants(tournament_id)
        if len(participants) < 2:
            raise ValueError("Недостаточно участников для формирования пар")

        # Перемешиваем участников
        shuffled = participants.copy()
        random.shuffle(shuffled)

        # Удаляем старые матчи
        self.db_session.query(Match).filter(Match.tournament_id == tournament_id).delete()

        matches = []
        round_num = 1
        match_order = 0

        # Формируем пары
        i = 0
        while i < len(shuffled):
            if i + 1 < len(shuffled):
                # Обычная пара
                match = Match(
                    tournament_id=tournament_id,
                    round_number=round_num,
                    player1_id=shuffled[i].id,
                    player2_id=shuffled[i + 1].id,
                    match_order=match_order
                )
                matches.append(match)
                i += 2
            else:
                # Нечётное количество - бай (пропуск)
                match = Match(
                    tournament_id=tournament_id,
                    round_number=round_num,
                    player1_id=shuffled[i].id,
                    player2_id=None,  # БАЙ
                    match_order=match_order
                )
                # Победа автоматическая
                match.winner_id = shuffled[i].id
                match.status = MatchStatus.FINISHED
                matches.append(match)
                i += 1
            match_order += 1

        for match in matches:
            self.db_session.add(match)

        # Обновляем статус турнира
        tournament = self.get_tournament_by_id(tournament_id)
        tournament.status = TournamentStatus.ACTIVE

        self.db_session.commit()
        return matches

    def get_tournament_matches(self, tournament_id, round_number=None):
        """Получить матчи турнира (опционально по туру)."""
        query = self.db_session.query(Match).filter(Match.tournament_id == tournament_id)
        if round_number:
            query = query.filter(Match.round_number == round_number)
        return query.order_by(Match.match_order).all()

    def get_available_rounds(self, tournament_id):
        """Получить список доступных туров."""
        rounds = self.db_session.query(Match.round_number).filter(
            Match.tournament_id == tournament_id
        ).distinct().order_by(Match.round_number).all()
        return [r[0] for r in rounds]

    # ---------- Результаты ----------
    def set_match_result(self, match_id, winner_id, score1, score2):
        """Установить результат матча."""
        match = self.db_session.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("Матч не найден")

        match.winner_id = winner_id
        match.player1_score = score1
        match.player2_score = score2
        match.status = MatchStatus.FINISHED
        self.db_session.commit()

        # Проверяем, завершены ли все матчи текущего тура
        tournament = self.get_tournament_by_id(match.tournament_id)
        current_round = match.round_number
        all_finished = self.db_session.query(Match).filter(
            Match.tournament_id == match.tournament_id,
            Match.round_number == current_round,
            Match.status != MatchStatus.FINISHED
        ).count() == 0

        if all_finished:
            self._advance_to_next_round(match.tournament_id, current_round)

        return match

    def _advance_to_next_round(self, tournament_id, current_round):
        """Перейти к следующему раунду."""
        winners = self.db_session.query(Match).filter(
            Match.tournament_id == tournament_id,
            Match.round_number == current_round,
            Match.winner_id.isnot(None)
        ).all()

        if len(winners) <= 1:
            # Турнир завершён
            tournament = self.get_tournament_by_id(tournament_id)
            tournament.status = TournamentStatus.FINISHED
            self.db_session.commit()
            return

        # Формируем матчи следующего тура
        winner_ids = [m.winner_id for m in winners if m.winner_id]
        random.shuffle(winner_ids)

        next_round = current_round + 1
        match_order = 0

        i = 0
        while i < len(winner_ids):
            if i + 1 < len(winner_ids):
                match = Match(
                    tournament_id=tournament_id,
                    round_number=next_round,
                    player1_id=winner_ids[i],
                    player2_id=winner_ids[i + 1],
                    match_order=match_order
                )
                self.db_session.add(match)
                i += 2
            else:
                # Бай для следующего раунда
                match = Match(
                    tournament_id=tournament_id,
                    round_number=next_round,
                    player1_id=winner_ids[i],
                    player2_id=None,
                    match_order=match_order
                )
                match.winner_id = winner_ids[i]
                match.status = MatchStatus.FINISHED
                self.db_session.add(match)
                i += 1
            match_order += 1

        self.db_session.commit()

    def get_tournament_winner(self, tournament_id):
        """Получить победителя турнира."""
        # Ищем финальный матч (последний тур)
        last_round = self.db_session.query(Match.round_number).filter(
            Match.tournament_id == tournament_id
        ).order_by(Match.round_number.desc()).first()

        if last_round:
            final_match = self.db_session.query(Match).filter(
                Match.tournament_id == tournament_id,
                Match.round_number == last_round[0]
            ).first()
            if final_match and final_match.winner_id:
                return final_match.winner
        return None

    def close(self):
        """Закрыть сессию."""
        if self.db_session:
            self.db_session.close()

    def __del__(self):
        self.close()