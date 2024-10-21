import math
import time
from tabulate import tabulate
from ai.evaluate.evaluator import evaluate_board

class ChessBot:
    def __init__(self, depth=3):
        self.depth = depth
        self.position_history = set()  # Храним хэши позиций
        self.transposition_table = {}  # Таблица транспозиции
        self.killer_moves = {}         # Сохраняем хорошие ходы для каждой глубины

    def sort_moves(self, board, moves, killer_moves, depth):
        """Сортируем ходы с учетом предыдущего лучшего хода и "убийственных" ходов."""
        def move_priority(move):
            # Присваиваем высокий приоритет захватам и угрозам
            score = 0
            if board.is_capture(move):
                score += 1000
            if board.gives_check(move):
                score += 500
            if move in killer_moves.get(depth, []):
                score += 2000  # "Убийственные" ходы
            return score

        return sorted(moves, key=lambda move: move_priority(move), reverse=True)

    def minimax(self, board, depth, alpha, beta, maximizing_player, previous_best_move=None):
        board_fen = board.fen()

        if board_fen in self.transposition_table and self.transposition_table[board_fen]['depth'] >= depth:
            return self.transposition_table[board_fen]['eval'], previous_best_move

        repetition_penalty = -50 if board_fen in self.position_history else 0

        if depth == 0 or board.is_game_over():
            eval = evaluate_board(board) + repetition_penalty
            self.transposition_table[board_fen] = {'eval': eval, 'depth': depth}
            return eval, previous_best_move

        best_move = None
        killer_moves_at_depth = self.killer_moves.get(depth, [])
        moves = list(board.legal_moves)

        # Сортируем ходы с учетом захватов, угроз и предыдущих лучших ходов
        if previous_best_move:
            moves.insert(0, previous_best_move)  # Проверяем лучший ход первым
        moves = self.sort_moves(board, moves, self.killer_moves, depth)

        # # Выводим таблицу оценок для текущего уровня глубины
        # self.print_board_evaluation(board, moves)

        if maximizing_player:
            max_eval = -math.inf

            for move in moves:
                board.push(move)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                eval += repetition_penalty

                if eval > max_eval:
                    max_eval = eval
                    best_move = move

                alpha = max(alpha, eval)
                if eval >= beta:
                    # Сохраняем убийственные ходы
                    self.killer_moves.setdefault(depth, []).append(move)
                    break

            self.transposition_table[board_fen] = {'eval': max_eval, 'depth': depth}
            return max_eval, best_move
        else:
            min_eval = math.inf

            for move in moves:
                board.push(move)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                eval += repetition_penalty

                if eval < min_eval:
                    min_eval = eval
                    best_move = move

                beta = min(beta, eval)
                if eval <= alpha:
                    self.killer_moves.setdefault(depth, []).append(move)
                    break

            self.transposition_table[board_fen] = {'eval': min_eval, 'depth': depth}
            return min_eval, best_move

    def print_board_evaluation(self, board, moves):
        """Выводит таблицу с ходами и их оценками."""
        table = []
        for move in moves:
            board.push(move)
            eval = evaluate_board(board)
            table.append([move, eval])
            board.pop()
        print(tabulate(table, headers=['Ход', 'Оценка'], tablefmt='orgtbl'))

    def find_best_move(self, board, max_time=5):
        start_time = time.time()
        best_move = None

        for depth in range(1, self.depth + 1):
            if time.time() - start_time > max_time:
                break  # Прерываем, если время вышло
            _, move = self.minimax(board, depth, -math.inf, math.inf, board.turn, best_move)
            if move:
                best_move = move

        return best_move
