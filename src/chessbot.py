import chess
import math
import time

class ChessBot:
    def __init__(self, depth=3):
        self.depth = depth
        self.position_history = set()  # Храним хэши позиций
        self.transposition_table = {}  # Таблица транспозиции
        self.killer_moves = {}         # Сохраняем хорошие ходы для каждой глубины

    def calculate_pawn_islands(self, board, color):
        """Возвращает количество пешечных островов для указанного цвета."""
        files_with_pawns = set(chess.square_file(square) for square in board.pieces(chess.PAWN, color))
        islands = 0
        last_file = -2
        for file in sorted(files_with_pawns):
            if file > last_file + 1:
                islands += 1
            last_file = file
        return islands

    def calculate_isolated_pawns(self, board, color):
        """Возвращает количество изолированных пешек."""
        isolated_pawns = 0
        for square in board.pieces(chess.PAWN, color):
            file = chess.square_file(square)
            left_adjacent_file = file - 1 if file > 0 else None
            right_adjacent_file = file + 1 if file < 7 else None

            # Проверяем пешки на соседних вертикалях (файлах)
            has_left_pawn = any(board.piece_at(chess.square(left_adjacent_file, rank)) == chess.PAWN for rank in range(8)) if left_adjacent_file is not None else False
            has_right_pawn = any(board.piece_at(chess.square(right_adjacent_file, rank)) == chess.PAWN for rank in range(8)) if right_adjacent_file is not None else False

            if not has_left_pawn and not has_right_pawn:
                isolated_pawns += 1

        return isolated_pawns

    def calculate_doubled_pawns(self, board, color):
        """Возвращает количество удвоенных пешек."""
        doubled_pawns = 0
        for file in chess.FILE_NAMES:
            pawns_in_file = board.pieces(chess.PAWN, color) & chess.BB_FILES[chess.FILE_NAMES.index(file)]
            if len(pawns_in_file) > 1:
                doubled_pawns += 1
        return doubled_pawns

    def control_of_open_lines(self, board, piece_type, color):
        """Возвращает оценку контроля открытых линий (для ладей)."""
        open_lines = 0
        for file in range(8):
            if not any(board.piece_at(chess.square(file, rank)) for rank in range(8)):
                # Открытая линия, если нет пешек
                if any(board.piece_at(chess.square(file, rank)) and board.piece_at(chess.square(file, rank)).piece_type == piece_type and board.piece_at(chess.square(file, rank)).color == color for rank in range(8)):
                    open_lines += 1
        return open_lines

    def spatial_advantage(self, board, color):
        """Оценка пространственного преимущества (число полей, контролируемых фигурами указанного цвета)."""
        control = 0
        for square in chess.SQUARES:
            attackers = board.attackers(color, square)
            if len(attackers) > 0:
                control += 1
        return control

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

        # Пешечные структуры
        eval -= 20 * self.calculate_pawn_islands(board, chess.WHITE)
        eval += 20 * self.calculate_pawn_islands(board, chess.BLACK)

        eval -= 15 * self.calculate_isolated_pawns(board, chess.WHITE)
        eval += 15 * self.calculate_isolated_pawns(board, chess.BLACK)

        eval -= 10 * self.calculate_doubled_pawns(board, chess.WHITE)
        eval += 10 * self.calculate_doubled_pawns(board, chess.BLACK)

        # Контроль центра
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        for square in center_squares:
            if board.piece_at(square):
                piece = board.piece_at(square)
                if piece.color == chess.WHITE:
                    eval += 20
                else:
                    eval -= 20

        # Пространственное преимущество
        eval += self.spatial_advantage(board, chess.WHITE) * 15
        eval -= self.spatial_advantage(board, chess.BLACK) * 15

        return eval

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
            eval = self.evaluate_board(board) + repetition_penalty
            self.transposition_table[board_fen] = {'eval': eval, 'depth': depth}
            return eval, previous_best_move

        best_move = None
        killer_moves_at_depth = self.killer_moves.get(depth, [])
        moves = list(board.legal_moves)

        # Сортируем ходы с учетом захватов, угроз и предыдущих лучших ходов
        if previous_best_move:
            moves.insert(0, previous_best_move)  # Проверяем лучший ход первым
        moves = self.sort_moves(board, moves, self.killer_moves, depth)

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
