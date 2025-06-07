import pygame
import asyncio
import platform
import time
from checkers.board import Board
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, BLUE, ROWS, COLS
from mcts.mcts import MCTS
from mcts.hueristics import MCTSHEURISTIC
from mcts.progressive_widening import MCTSPROGRESSIVE

pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Polish Draughts')

# Menu button properties
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 60
BUTTON_SPACING = 20
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)
TEXT_COLOR = (255, 255, 255)
FONT = pygame.font.SysFont('arial', 30)

def draw_menu(win, buttons):
    win.fill((0, 0, 0))  # Black background
    for button in buttons:
        color = BUTTON_HOVER_COLOR if button['hover'] else BUTTON_COLOR
        pygame.draw.rect(win, color, button['rect'])
        text = FONT.render(button['text'], True, TEXT_COLOR)
        text_rect = text.get_rect(center=button['rect'].center)
        win.blit(text, text_rect)
    pygame.display.update()

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

async def main():
    # Menu setup
    buttons = [
        {'text': 'Player vs Player', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'pvp'},
        {'text': 'Player vs MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'mcts'},
        {'text': 'Player vs Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai2'},
        {'text': 'Player vs Progressive MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai3'},
    ]
    mode = None

    # Menu loop
    while mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEMOTION:
                for button in buttons:
                    button['hover'] = button['rect'].collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button['rect'].collidepoint(event.pos):
                        mode = button['mode']
                        break
        draw_menu(WIN, buttons)
        await asyncio.sleep(0.016)  # ~60 FPS

    # Game setup
    run = True
    clock = pygame.time.Clock()
    board = Board()
    selected_piece = None
    turn = BLUE  # Human player starts as BLUE
    valid_moves = set()
    ai_player = RED if mode != 'pvp' else None  # AI controls RED if not PvP
    FPS = 60
    ai_timeout = 3  # Timeout for AI moves

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

        if ai_player and turn == ai_player:
            print(f"AI ({'RED' if ai_player == RED else 'BLUE'}) turn")
            start_time = time.time()
            try:
                if mode == 'mcts':
                    mcts = MCTS(board, ai_player, iterations=30)
                    move = mcts.search()
                elif mode == 'ai2':
                    mcts = MCTSHEURISTIC(board, ai_player, iterations=30)
                    move = mcts.search()
                elif mode == 'ai3':
                    mcts = MCTSPROGRESSIVE(board, ai_player, iterations=30)
                    move = mcts.search()
                else:
                    print(f"{mode} not implemented yet")
                    run = False
                    break

                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != ai_player:
                        print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
                        run = False
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    print(f"AI moved from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
                    board.draw(WIN)
                    board.highlight_moves(WIN, {(dest_row, dest_col)})
                    pygame.display.update()
                    await asyncio.sleep(0.5)
                    turn = BLUE
                else:
                    print("AI found no valid moves")
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

            except Exception as e:
                print(f"AI error: {e}")
                run = False
        else:
            # Human player's turn (BLUE or RED)
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
                            print(f"Player {'BLUE' if turn == BLUE else 'RED'} moved from ({selected_piece.row}, {selected_piece.col}) to ({row}, {col})")
                            selected_piece = None
                            valid_moves = set()
                            turn = RED if turn == BLUE else BLUE
                        else:
                            selected_piece = None
                            valid_moves = set()
                            print("Invalid move, piece deselected")
                    else:
                        if piece != 0 and piece.color == turn:
                            selected_piece = piece
                            valid_moves = board.get_valid_moves(piece)
                            print(f"Player {'BLUE' if turn == BLUE else 'RED'} selected piece at ({piece.row}, {piece.col})")
        
        await asyncio.sleep(1.0 / FPS)

    print("Game ended")
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())