import pygame
import asyncio
import platform
import time
from checkers.board import Board
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, BLUE, ROWS, COLS
from mcts.mcts import MCTS

pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Polish Draughts')

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

async def main():
    run = True
    clock = pygame.time.Clock()
    board = Board()
    selected_piece = None
    turn = BLUE  # Human player starts as BLUE
    valid_moves = set()
    ai_player = RED  # AI controls RED
    FPS = 60
    ai_timeout = 3  # Reduced timeout to 3 seconds

    while run:
        clock.tick(FPS)
        board.draw(WIN)
        if selected_piece:
            board.highlight_moves(WIN, valid_moves)
        pygame.display.update()

        # Check for game end
        winner = board.get_winner()
        if winner is not None:
            print(f"Game Over! Winner: {'RED' if winner == RED else 'BLUE'}")
            await asyncio.sleep(2)
            run = False
            break

        if turn == ai_player:
            print(f"AI ({'RED' if ai_player == RED else 'BLUE'}) turn")
            start_time = time.time()
            try:
                mcts = MCTS(board, ai_player, iterations=30)  # Further reduced for responsiveness
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != ai_player:
                        print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
                        run = False
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    print(f"AI moved from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col}), result: {result}")
                    # Highlight AI move briefly
                    board.highlight_moves(WIN, {(dest_row, dest_col)})
                    pygame.display.update()
                    await asyncio.sleep(0.5)
                    board.draw(WIN)
                    if result != "CONTINUE":
                        turn = BLUE
                    else:
                        print("AI must continue capturing")
                else:
                    print("AI found no valid moves")
                    # Check if AI has any moves
                    has_moves = False
                    for row in range(ROWS):
                        for col in range(COLS):
                            piece = board.get_piece(row, col)
                            if piece != 0 and piece.color == ai_player and board.can_move(piece):
                                has_moves = True
                                break
                        if has_moves:
                            break
                    if not has_moves:
                        print("AI has no moves, human wins")
                        run = False
                    else:
                        print("MCTS failed to find moves despite available options")
                        run = False
                    break
                # if time.time() - start_time > ai_timeout:
                #     print("AI move timed out")
                #     run = False
                #     break
            except Exception as e:
                print(f"AI error: {e}")
                run = False
                break
        else:
            # Human player's turn
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = get_row_col_from_mouse(pos)
                    piece = board.get_piece(row, col)
                    
                    if selected_piece:
                        if (row, col) in valid_moves:
                            result = board.move(selected_piece, row, col)
                            print(f"Human moved from ({selected_piece.row}, {selected_piece.col}) to ({row}, {col}), result: {result}")
                            if result == True or result is None:
                                selected_piece = None
                                valid_moves = set()
                                turn = ai_player
                            elif result == "CONTINUE":
                                valid_moves = board.get_valid_moves(selected_piece)
                                print("Human must continue capturing")
                        else:
                            selected_piece = None
                            valid_moves = set()
                            print("Invalid move, piece deselected")
                    else:
                        if piece != 0 and piece.color == turn:
                            selected_piece = piece
                            valid_moves = board.get_valid_moves(piece)
                            print(f"Human selected piece at ({piece.row}, {piece.col})")
        
        await asyncio.sleep(1.0 / FPS)

    print("Game ended")
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())