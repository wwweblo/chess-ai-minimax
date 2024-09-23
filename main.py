import chess
from chessbot import ChessBot
# Пример использования
if __name__ == "__main__":
    board = chess.Board()
    bot = ChessBot(depth=3)
    
    while not board.is_game_over():
        if board.turn:
            # Ход бота за белых
            move = bot.find_best_move(board)
            board.push(move)
            print(f"Bot move: {move}")
        else:
            # Ход бота за черных
            move = bot.find_best_move(board)
            board.push(move)
            print(f"Bot move: {move}")
        
        print(board)
