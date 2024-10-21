import chess

def control_of_open_lines(board, piece_type, color):
        """Возвращает оценку контроля открытых линий (для ладей)."""
        open_lines = 0
        for file in range(8):
            if not any(board.piece_at(chess.square(file, rank)) for rank in range(8)):
                # Открытая линия, если нет пешек
                if any(board.piece_at(chess.square(file, rank)) and board.piece_at(chess.square(file, rank)).piece_type == piece_type and board.piece_at(chess.square(file, rank)).color == color for rank in range(8)):
                    open_lines += 1
        return open_lines

def evaluate_piece_safety(board):
        """Оценка защищенности фигур: штраф за незащищенные фигуры, которые могут быть атакованы"""
        safety_eval = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    if not board.is_attacked_by(chess.WHITE, square) and board.is_attacked_by(chess.BLACK, square):
                        safety_eval -= 50  # Белая фигура атакована, но не защищена
                else:
                    if not board.is_attacked_by(chess.BLACK, square) and board.is_attacked_by(chess.WHITE, square):
                        safety_eval += 50  # Черная фигура атакована, но не защищена
        return safety_eval

def is_kingside_safe(board, color):
        # Пример проверки безопасности рокировки на королевский фланг
        if color == chess.WHITE:
            return not board.is_attacked_by(chess.BLACK, chess.F1) and not board.is_attacked_by(chess.BLACK, chess.G1)
        else:
            return not board.is_attacked_by(chess.WHITE, chess.F8) and not board.is_attacked_by(chess.WHITE, chess.G8)

def is_queenside_safe(board, color):
        # Пример проверки безопасности рокировки на ферзевый фланг
        if color == chess.WHITE:
            return not board.is_attacked_by(chess.BLACK, chess.C1) and not board.is_attacked_by(chess.BLACK, chess.D1)
        else:
            return not board.is_attacked_by(chess.WHITE, chess.C8) and not board.is_attacked_by(chess.WHITE, chess.D8)

def spatial_advantage(board, color):
        """Оценка пространственного преимущества (число полей, контролируемых фигурами указанного цвета)."""
        control = 0
        for square in chess.SQUARES:
            attackers = board.attackers(color, square)
            if len(attackers) > 0:
                control += 1
        return control

def center_control(board, color):
    eval = 0
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    for square in center_squares:
        if board.piece_at(square):
            piece = board.piece_at(square)
            if piece.color == chess.WHITE:
                eval += 20
            else:
                eval -= 20
    return eval

def get_game_stage(board):

    if len(board.move_stack) < 15:  # Opening
        return 'opening'
    elif len(board.move_stack) < 30:  # Middle game
        return 'middle game'
    else:  # Endgame
        return 'endgame'