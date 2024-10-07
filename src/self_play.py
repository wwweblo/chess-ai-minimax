import chess
from chessbot import ChessBot

if __name__ == "__main__":
    board = chess.Board()
    bot = ChessBot(depth=3)

    while not board.is_game_over():
        print(board)
        if board.turn == chess.WHITE:
            # Ход бота за белых
            move = bot.find_best_move(board)
            board.push(move)
            print(f"Bot (White) move: {move}")
        else:
            # Ход бота за черных
            move = bot.find_best_move(board)
            board.push(move)
            print(f"Bot (Black) move: {move}")

    print("Game over!")
    if board.is_checkmate():
        print("Checkmate!")
    elif board.is_stalemate():
        print("Stalemate!")
    elif board.is_insufficient_material():
        print("Insufficient material!")
    else:
        print("Game drawn!")