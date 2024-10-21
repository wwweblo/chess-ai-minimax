import chess
from chessbot import ChessBot

def get_player_move(board):
    while True:
        try:
            move_input = input("Your move: ")
            move = chess.Move.from_uci(move_input)
            if move in board.legal_moves:
                return move
            else:
                print("Illegal move. Try again.")
        except ValueError:
            print("Invalid move format. Please use UCI format (e.g., 'e2e4').")

if __name__ == "__main__":
    board = chess.Board()
    bot = ChessBot(depth=3)

    # Выбор стороны игрока
    player_color = input("Do you want to play as white (w) or black (b)? ").strip().lower()

    while not board.is_game_over():
        print(board)
        
        if (board.turn == chess.WHITE and player_color == 'w') or (board.turn == chess.BLACK and player_color == 'b'):
            # Ход игрока
            move = get_player_move(board)
            board.push(move)
        else:
            # Ход бота
            move = bot.find_best_move(board)
            board.push(move)
            print(f"Bot move: {move}")
        
    print("Game over!")
    if board.is_checkmate():
        print("Checkmate!")
    elif board.is_stalemate():
        print("Stalemate!")
    elif board.is_insufficient_material():
        print("Insufficient material!")
    else:
        print("Game drawn!")
