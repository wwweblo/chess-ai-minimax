import chess
from ai.evaluate.evaluator_utils import *

def evaluate_board(board):
    # Проверка окончания игры
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
    white_material = 0
    black_material = 0
    for piece in chess.PIECE_TYPES:
        white_pieces = len(board.pieces(piece, chess.WHITE))
        black_pieces = len(board.pieces(piece, chess.BLACK))
        white_material += white_pieces * piece_values[piece]
        black_material += black_pieces * piece_values[piece]
        eval += white_pieces * piece_values[piece]
        eval -= black_pieces * piece_values[piece]

    # Разница в материале
    material_difference = white_material - black_material

    # Штраф за размены при меньшем материале
    if material_difference < 0 and board.turn == chess.WHITE:
        eval -= abs(material_difference) * 0.05  # Белые хотят избежать разменов
    elif material_difference > 0 and board.turn == chess.BLACK:
        eval += abs(material_difference) * 0.05  # Черные хотят избежать разменов

    # Оценка защищенности фигур
    eval += evaluate_piece_safety(board)

    # Контроль центра
    eval += center_control(board, chess.WHITE)

    # Пространственное преимущество
    eval += spatial_advantage(board, chess.WHITE) * 15
    eval -= spatial_advantage(board, chess.BLACK) * 15

    # Мобильность (количество возможных ходов)
    mobility_bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        for square in board.piece_map():
            piece = board.piece_at(square)
            if piece.color == color:
                mobility_bonus += len(list(board.attacks(square)))

    eval += mobility_bonus if board.turn == chess.WHITE else -mobility_bonus

    stage = get_game_stage(board)

    # Фазы игры
    if stage == 'opening':
        eval += evaluate_opening(board)
    elif stage == 'middle game':
        eval += evaluate_middle_game(board)
    else:
        eval += evaluate_endgame(board)

    return eval

def evaluate_opening(board):
    eval = 0

    # Кешируем расположение фигур для ускорения
    piece_locations = {square: board.piece_at(square) for square in chess.SQUARES}

    # Штраф за повторные ходы одной и той же фигурой
    piece_move_count = {}
    repeated_moves_penalty = 0

    # Флаг рокировки для каждого цвета
    white_castled = board.has_castling_rights(chess.WHITE)
    black_castled = board.has_castling_rights(chess.BLACK)

    # Штраф за ходы королем до рокировки
    king_moves_penalty = 0

    # Проходим по последним ходам
    for move in board.move_stack:
        piece = piece_locations[move.from_square]

        if piece:
            # Увеличиваем счетчик ходов для каждой фигуры
            piece_key = (piece.piece_type, piece.color)
            if piece_key not in piece_move_count:
                piece_move_count[piece_key] = 1
            else:
                piece_move_count[piece_key] += 1

            # Если фигура ходила более одного раза, начисляем штраф
            if piece_move_count[piece_key] > 1:
                repeated_moves_penalty -= 60  # Уменьшаем оценку за каждый повторный ход

            # Проверка на ходы королем
            if piece.piece_type == chess.KING:
                if piece.color == chess.WHITE and not white_castled:
                    king_moves_penalty -= 30  # Штраф за ходы королем белых до рокировки
                elif piece.color == chess.BLACK and not black_castled:
                    king_moves_penalty -= 30  # Штраф за ходы королем черных до рокировки

    eval += repeated_moves_penalty
    eval += king_moves_penalty

    # Вознаграждение за рокировку в безопасную сторону
    if not white_castled:
        if is_kingside_safe(board, chess.WHITE):
            eval += 50  # Рокировка на королевский фланг
        elif is_queenside_safe(board, chess.WHITE):
            eval += 30  # Рокировка на ферзевый фланг
        else:
            eval -= 20  # Штраф за отсутствие рокировки

    if not black_castled:
        if is_kingside_safe(board, chess.BLACK):
            eval += 50  # Рокировка на королевский фланг
        elif is_queenside_safe(board, chess.BLACK):
            eval += 30  # Рокировка на ферзевый фланг
        else:
            eval -= 20  # Штраф за отсутствие рокировки

    # Применение штрафа за задержку рокировки
    if len(board.move_stack) > 10:
        if not white_castled:
            eval -= 15  # Штраф за задержку рокировки белыми
        if not black_castled:
            eval -= 15  # Штраф за задержку рокировки черными

    # Приоритеты развития фигур
    piece_priority = {
        chess.KNIGHT: 30,  # Очень высокий приоритет для коней
        chess.BISHOP: 25,  # Высокий приоритет для слонов
        chess.QUEEN: 10,   # Низкий приоритет для ферзя, чтобы не развивать его слишком рано
        chess.ROOK: 5      # Минимальный приоритет для ладей, чтобы дать возможность рокировки
    }

    piece_priority_bonus = 0

    # Проходим по последним ходам и начисляем бонусы за развитие фигур
    for move in board.move_stack[-10:]:  # Расширяем диапазон до 10 ходов для большего влияния
        piece = board.piece_at(move.from_square)  # Получаем фигуру, которая делала ход
        if piece and piece.piece_type in piece_priority:
            piece_priority_bonus += piece_priority[piece.piece_type] * 5 # Увеличиваем вес приоритета на 50%

    # Добавляем к оценке бонус за развитие
    eval += piece_priority_bonus

    # Контроль центра фигурами
    center_control_bonus = 0
    central_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    for square in central_squares:
        piece = piece_locations.get(square)
        if piece and piece.color == chess.WHITE:
            center_control_bonus += 20 if piece.piece_type == chess.PAWN else 10
        elif piece and piece.color == chess.BLACK:
            center_control_bonus -= 20 if piece.piece_type == chess.PAWN else 10
    eval += center_control_bonus

    # Развитие фигур
    piece_development = 0
    for piece in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
        piece_development += len(board.pieces(piece, chess.WHITE))
    eval += piece_development * 5

    # Штраф за фигуры на начальных позициях соперника и за наши фигуры на начальных позициях
    minor_pieces = [chess.KNIGHT, chess.BISHOP]  # Легкие фигуры: кони и слоны

    # Белые фигуры
    for piece in minor_pieces:
        for square in board.pieces(piece, chess.WHITE):
            if square in [chess.B1, chess.G1, chess.C1, chess.F1]:
                eval -= 50  # Штраф за белые легкие фигуры на начальных позициях

    # Черные фигуры
    for piece in minor_pieces:
        for square in board.pieces(piece, chess.BLACK):
            if square in [chess.B8, chess.G8, chess.C8, chess.F8]:
                eval += 50  # Положительная оценка за черные легкие фигуры на начальных позициях

    # Центральные пешки
    central_pawns = [chess.D4, chess.E4, chess.D5, chess.E5]
    pawn_position_bonus = 0

    for square in central_pawns:
        piece = piece_locations.get(square)
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == chess.WHITE:
                pawn_position_bonus += 40  # Поощрение за сохранение центральных пешек белых
            elif piece.color == chess.BLACK:
                pawn_position_bonus -= 40  # Штраф за центральные пешки черных

            # Поощрение за атаку центральных пешек соперника, чтобы они уходили в сторону
            if piece.color == chess.BLACK and board.is_attacked_by(chess.WHITE, square):
                pawn_position_bonus += 20  # Поощрение за давление на центральные пешки черных
            elif piece.color == chess.WHITE and board.is_attacked_by(chess.BLACK, square):
                pawn_position_bonus -= 20  # Поощрение за давление на центральные пешки белых

    eval += pawn_position_bonus

    return eval

def evaluate_middle_game(board):
        eval = 0

        # Piece coordination and harmony
        piece_coordination = 0
        for piece in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
            piece_coordination += len(board.pieces(piece, chess.WHITE)) * 5
            piece_coordination -= len(board.pieces(piece, chess.BLACK)) * 5
        eval += piece_coordination

        # Pawn chain evaluation
        pawn_chain_eval = 0
        for file in range(8):
            pawn_chain = 0
            for rank in range(8):
                if board.piece_at(file * 8 + rank) and board.piece_at(file * 8 + rank).piece_type == chess.PAWN:
                    pawn_chain += 1
            pawn_chain_eval += pawn_chain * 10
        eval += pawn_chain_eval

        # Open lines and files
        open_lines = 0
        for file in range(8):
            if not any(board.piece_at(file * 8 + rank) for rank in range(8)):
                open_lines += 10
        eval += open_lines

        # Piece mobility and activity
        piece_mobility = 0
        for piece in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
            piece_mobility += len(board.pieces(piece, chess.WHITE)) * 5
            piece_mobility -= len(board.pieces(piece, chess.BLACK)) * 5
        eval += piece_mobility

        # Attacking chances
        attacking_chances = 0
        for piece in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
            attacking_chances += len(board.pieces(piece, chess.WHITE)) * 10
            attacking_chances -= len(board.pieces(piece, chess.BLACK)) * 10
        eval += attacking_chances

        # King safety
        king_safety = 0
        king_proximity = 0
        for square in [chess.E1, chess.E8]:
            if board.piece_at(square) and board.piece_at(square).piece_type == chess.KING:
                king_proximity += 1
        king_safety += king_proximity * 10
        eval += king_safety

        return eval

def evaluate_endgame(board):
        # Additional evaluation methods for the endgame
        return 0
