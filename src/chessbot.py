import chess
import math
import time

class ChessBot:
    def __init__(self, depth=3):
        self.depth = depth
        self.position_history = set()  # Храним хэши позиций
        self.transposition_table = {}   # Добавляем таблицу транспозиции

    def evaluate_board(self, board):
        if board.is_checkmate():
            return -9999 if board.turn else 9999
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        eval = 0
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 10000
        }

        # Материальная оценка
        for piece in chess.PIECE_TYPES:
            eval += len(board.pieces(piece, chess.WHITE)) * piece_values[piece]
            eval -= len(board.pieces(piece, chess.BLACK)) * piece_values[piece]

        # Оценка уязвимости фигур (потеря темпа)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    if square in board.attacks(square):  # Если фигура под угрозой
                        eval -= 10  # Штраф за уязвимость
                else:
                    if square in board.attacks(square):
                        eval += 10  # Увеличение оценки, если фигура противника уязвима

        # Пешечная структура
        eval += 10 * len([square for square in board.pieces(chess.PAWN, chess.WHITE) if chess.square_rank(square) >= 4])
        eval -= 10 * len([square for square in board.pieces(chess.PAWN, chess.BLACK) if chess.square_rank(square) <= 3])

        # Контроль центра
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        for square in center_squares:
            if board.piece_at(square):
                piece = board.piece_at(square)
                if piece.color == chess.WHITE:
                    eval += 20
                else:
                    eval -= 20

        # Оценка активности фигур
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                if piece.piece_type == chess.KNIGHT:
                    eval += 10 if piece.color == chess.WHITE and chess.square_distance(square, chess.E4) <= 2 else 0
                    eval -= 10 if piece.color == chess.BLACK and chess.square_distance(square, chess.E5) <= 2 else 0
                if piece.piece_type == chess.BISHOP:
                    eval += 10 if piece.color == chess.WHITE and len(board.attacks(square)) > 0 else 0
                    eval -= 10 if piece.color == chess.BLACK and len(board.attacks(square)) > 0 else 0

        # Оценка безопасности короля (штраф за ненадёжную позицию)
        eval -= 50 if board.piece_at(chess.E1) and board.piece_at(chess.E1).piece_type == chess.KING and not board.has_castling_rights(chess.WHITE) else 0
        eval += 50 if board.piece_at(chess.E8) and board.piece_at(chess.E8).piece_type == chess.KING and not board.has_castling_rights(chess.BLACK) else 0

        return eval

    def evaluate_move(self, board, move):
        board.push(move)                    # Применяем ход
        score = self.evaluate_board(board)  # Оцениваем новую позицию
        board.pop()                         # Возвращаемся к исходной позиции
        return score

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        board_fen = board.fen()

        # Проверяем, есть ли уже рассчитанная оценка позиции в кэше
        if board_fen in self.transposition_table and self.transposition_table[board_fen]['depth'] >= depth:
            return self.transposition_table[board_fen]['eval'], None  # Убираем move, если он не нужен

        repetition_penalty = -50 if board_fen in self.position_history else 0

        if depth == 0 or board.is_game_over():
            eval = self.evaluate_board(board) + repetition_penalty
            self.transposition_table[board_fen] = {'eval': eval, 'depth': depth}  # Убираем 'move'
            return eval, None

        best_move = None
        if maximizing_player:
            max_eval = -math.inf
            sorted_moves = sorted(board.legal_moves, key=lambda move: self.evaluate_move(board, move), reverse=True)

            for move in sorted_moves:
                board.push(move)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                eval += repetition_penalty
            
                if eval > max_eval:
                    max_eval = eval
                    best_move = move

                alpha = max(alpha, eval)
                if eval >= beta:
                    break

            self.transposition_table[board_fen] = {'eval': max_eval, 'depth': depth}  # Убираем 'move'
            return max_eval, best_move
        else:
            min_eval = math.inf
            sorted_moves = sorted(board.legal_moves, key=lambda move: self.evaluate_move(board, move))

            for move in sorted_moves:
                board.push(move)
                eval, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                eval += repetition_penalty
            
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
            
                beta = min(beta, eval)
                if eval <= alpha:
                    break

            self.transposition_table[board_fen] = {'eval': min_eval, 'depth': depth}  # Убираем 'move'
            return min_eval, best_move

    def find_best_move(self, board, max_time=5):
    
        start_time = time.time()
        best_move = None

        for depth in range(1, self.depth + 1):
            if time.time() - start_time > max_time:
                break  # Прерываем, если время вышло
            _, move = self.minimax(board, depth, -math.inf, math.inf, board.turn)
            if move:
                best_move = move

        return best_move