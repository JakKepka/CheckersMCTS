import pygame
import asyncio
import platform
import time
import threading
import queue
import copy
from checkers.board import Board
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, BLUE, ROWS, COLS
from mcts.mcts import MCTS
from mcts.hueristics import MCTSHEURISTIC
from mcts.progressive_widening import MCTSPROGRESSIVE
from mcts.nuct import MCTSNESTED

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
    win.fill((0, 0, 0))
    for button in buttons:
        color = BUTTON_HOVER_COLOR if button['hover'] else BUTTON_COLOR
        pygame.draw.rect(win, color, button['rect'])
        text = FONT.render(button['text'], True, TEXT_COLOR)
        text_rect = text.get_rect(center=button['rect'].center)
        win.blit(text, text_rect)
    pygame.display.update()

def draw_ai_selection_menu(win, buttons, title):
    win.fill((0, 0, 0))
    title_text = FONT.render(title, True, TEXT_COLOR)
    title_rect = title_text.get_rect(center=(WIDTH//2, 100))
    win.blit(title_text, title_rect)
    for button in buttons:
        color = BUTTON_HOVER_COLOR if button['hover'] else BUTTON_COLOR
        pygame.draw.rect(win, color, button['rect'])
        text = FONT.render(button['text'], True, TEXT_COLOR)
        text_rect = text.get_rect(center=button['rect'].center)
        win.blit(text, text_rect)
    pygame.display.update()

def draw_game_count_menu(win, buttons):
    win.fill((0, 0, 0))
    title_text = FONT.render("Select Number of Games", True, TEXT_COLOR)
    title_rect = title_text.get_rect(center=(WIDTH//2, 100))
    win.blit(title_text, title_rect)
    for button in buttons:
        color = BUTTON_HOVER_COLOR if button['hover'] else BUTTON_COLOR
        pygame.draw.rect(win, color, button['rect'])
        text = FONT.render(button['text'], True, TEXT_COLOR)
        text_rect = text.get_rect(center=button['rect'].center)
        win.blit(text, text_rect)
    pygame.display.update()

def draw_win_summary(win, red_wins, blue_wins, red_ai_name, blue_ai_name, current_game, total_games):
    win.fill((0, 0, 0))
    summary_text = f"Game {current_game}/{total_games} Completed"
    red_text = f"RED ({red_ai_name}): {red_wins} wins"
    blue_text = f"BLUE ({blue_ai_name}): {blue_wins} wins"
    
    summary_surface = FONT.render(summary_text, True, TEXT_COLOR)
    red_surface = FONT.render(red_text, True, TEXT_COLOR)
    blue_surface = FONT.render(blue_text, True, TEXT_COLOR)
    
    win.blit(summary_surface, (WIDTH//2 - summary_surface.get_width()//2, 200))
    win.blit(red_surface, (WIDTH//2 - red_surface.get_width()//2, 280))
    win.blit(blue_surface, (WIDTH//2 - blue_surface.get_width()//2, 360))
    pygame.display.update()

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn):
    turn = initial_turn
    iterations = 30 if mode != 'aivai' else 15

    while not stop_event.is_set():
        winner = board.get_winner()
        if winner is not None:
            win_queue.put(winner)
            stop_event.set()
            break

        if mode == 'aivai':
            current_ai = ai_blue if turn == BLUE else ai_red
            try:
                mcts = current_ai(copy.deepcopy(board), turn, iterations=iterations)
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != turn:
                        stop_event.set()
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
                    turn = RED if turn == BLUE else BLUE
                else:
                    has_moves = False
                    for row in range(ROWS):
                        for col in range(COLS):
                            piece = board.get_piece(row, col)
                            if piece != 0 and piece.color == turn and board.can_move(piece):
                                has_moves = True
                                break
                        if has_moves:
                            break
                    if not has_moves:
                        stop_event.set()
                    else:
                        stop_event.set()

            except Exception:
                stop_event.set()
        elif ai_player and turn == ai_player:
            try:
                if mode == 'mcts':
                    mcts = MCTS(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai2':
                    mcts = MCTSHEURISTIC(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai3':
                    mcts = MCTSPROGRESSIVE(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'nested':
                    mcts = MCTSNESTED(copy.deepcopy(board), ai_player, iterations=iterations)
                else:
                    stop_event.set()
                    break
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != ai_player:
                        stop_event.set()
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
                    turn = BLUE
                else:
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
                        stop_event.set()
                    else:
                        stop_event.set()

            except Exception:
                stop_event.set()
        elif mode != 'aivai':
            time.sleep(0.01)
        else:
            time.sleep(0.01)

async def main():
    ai_options = [
        {'text': 'MCTS', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'ai_class': MCTS},
        {'text': 'Heuristic MCTS', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'ai_class': MCTSHEURISTIC},
        {'text': 'Progressive MCTS', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'ai_class': MCTSPROGRESSIVE},
        {'text': 'Nested MCTS', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'ai_class': MCTSNESTED},
    ]
    
    buttons = [
        {'text': 'Player vs Player', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'pvp'},
        {'text': 'Player vs MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'mcts'},
        {'text': 'Player vs Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai2'},
        {'text': 'Player vs Progressive MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai3'},
        {'text': 'Player vs Nested MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 520, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'nested'},
        {'text': 'AI vs AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 600, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'aivai'},
    ]

    game_count_options = [
        {'text': '1 Game', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'count': 1},
        {'text': '5 Games', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'count': 5},
        {'text': '10 Games', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'count': 10},
        {'text': '20 Games', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'count': 20},
        {'text': '100 Games', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 520, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'count': 100},
    ]

    mode = None
    ai_red = None
    ai_blue = None
    num_games = 1
    selecting_red = False
    selecting_blue = False
    selecting_game_count = False
    clock = pygame.time.Clock()
    FPS = 60

    while mode is None:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEMOTION:
                if selecting_red or selecting_blue:
                    for button in ai_options:
                        button['hover'] = button['rect'].collidepoint(event.pos)
                elif selecting_game_count:
                    for button in game_count_options:
                        button['hover'] = button['rect'].collidepoint(event.pos)
                else:
                    for button in buttons:
                        button['hover'] = button['rect'].collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if selecting_red:
                    for button in ai_options:
                        if button['rect'].collidepoint(pos):
                            ai_red = button['ai_class']
                            selecting_red = False
                            selecting_blue = True
                            break
                elif selecting_blue:
                    for button in ai_options:
                        if button['rect'].collidepoint(pos):
                            ai_blue = button['ai_class']
                            selecting_blue = False
                            selecting_game_count = True
                            break
                elif selecting_game_count:
                    for button in game_count_options:
                        if button['rect'].collidepoint(pos):
                            num_games = button['count']
                            selecting_game_count = False
                            mode = 'aivai'
                            break
                else:
                    for button in buttons:
                        if button['rect'].collidepoint(pos):
                            if button['mode'] == 'aivai':
                                selecting_red = True
                            else:
                                mode = button['mode']
                            break

        if selecting_red:
            draw_ai_selection_menu(WIN, ai_options, "Select AI for RED")
        elif selecting_blue:
            draw_ai_selection_menu(WIN, ai_options, "Select AI for BLUE")
        elif selecting_game_count:
            draw_game_count_menu(WIN, game_count_options)
        else:
            draw_menu(WIN, buttons)
        await asyncio.sleep(0.016)

    board = Board()
    selected_piece = None
    turn = BLUE
    valid_moves = set()
    ai_player = RED if mode != 'pvp' else None

    # Print player types at the start
    if mode == 'pvp':
        print("BLUE: Human, RED: Human")
    elif mode == 'aivai':
        red_ai_name = next(opt['text'] for opt in ai_options if opt['ai_class'] == ai_red)
        blue_ai_name = next(opt['text'] for opt in ai_options if opt['ai_class'] == ai_blue)
        print(f"BLUE: {blue_ai_name}, RED: {red_ai_name}")
    else:
        ai_name = {
            'mcts': 'MCTS',
            'ai2': 'Heuristic MCTS',
            'ai3': 'Progressive MCTS',
            'nested': 'Nested MCTS'
        }[mode]
        print(f"BLUE: Human, RED: {ai_name}")

    FPS = 60
    iterations = 30 if mode != 'aivai' else 15
    move_queue = queue.Queue()
    win_queue = queue.Queue()
    stop_event = threading.Event()

    if mode == 'aivai':
        red_wins = 0
        blue_wins = 0
        for game_num in range(1, num_games + 1):
            board = Board()  # Reset board for new game
            # Alternate starting player: BLUE for odd games, RED for even games
            initial_turn = BLUE if game_num % 2 == 1 else RED
            turn = initial_turn
            stop_event.clear()
            print(f"Starting Game {game_num}/{num_games} (First move: {'BLUE' if initial_turn == BLUE else 'RED'})")

            if platform.system() != "Emscripten":
                game_thread = threading.Thread(target=game_logic, args=(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn))
                game_thread.daemon = True
                game_thread.start()
            else:
                async def async_game_logic():
                    await game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn)
                asyncio.create_task(async_game_logic())

            highlighted_move = None
            while not stop_event.is_set():
                clock.tick(FPS)
                board.draw(WIN)
                if highlighted_move:
                    board.highlight_moves(WIN, {highlighted_move})
                pygame.display.update()

                try:
                    move = move_queue.get_nowait()
                    highlighted_move = (move[2], move[3])
                    time.sleep(0.5)
                    highlighted_move = None
                except queue.Empty:
                    pass

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stop_event.set()
                        pygame.quit()
                        return

                await asyncio.sleep(1.0 / FPS)

            try:
                winner = win_queue.get_nowait()
                if winner == RED:
                    red_wins += 1
                elif winner == BLUE:
                    blue_wins += 1
                print(f"Game {game_num} Over! Winner: {'RED' if winner == RED else 'BLUE'}")
                print(f"Current Results: RED ({red_ai_name}): {red_wins} wins, BLUE ({blue_ai_name}): {blue_wins} wins")
            except queue.Empty:
                print(f"Game {game_num} ended with no winner")
                print(f"Current Results: RED ({red_ai_name}): {red_wins} wins, BLUE ({blue_ai_name}): {blue_wins} wins")

            if platform.system() != "Emscripten":
                game_thread.join(timeout=1)

            # Show win summary and wait automatically
            draw_win_summary(WIN, red_wins, blue_wins, red_ai_name, blue_ai_name, game_num, num_games)
            await asyncio.sleep(2)  # 2-second pause

        # Final summary shown above, exits automatically
    else:
        if platform.system() != "Emscripten":
            game_thread = threading.Thread(target=game_logic, args=(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, turn))
            game_thread.daemon = True
            game_thread.start()
        else:
            async def async_game_logic():
                await game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, turn)
            asyncio.create_task(async_game_logic())

        highlighted_move = None
        while not stop_event.is_set():
            clock.tick(FPS)
            board.draw(WIN)
            if selected_piece and mode != 'aivai':
                board.highlight_moves(WIN, valid_moves)
            if highlighted_move:
                board.highlight_moves(WIN, {highlighted_move})
            pygame.display.update()

            try:
                move = move_queue.get_nowait()
                highlighted_move = (move[2], move[3])
                time.sleep(0.5)
                highlighted_move = None
            except queue.Empty:
                pass

            if mode != 'aivai':
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stop_event.set()
                        pygame.quit()
                        return
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        row, col = get_row_col_from_mouse(pos)
                        piece = board.get_piece(row, col)
                        if selected_piece:
                            if (row, col) in valid_moves:
                                result = board.move(selected_piece, row, col)
                                move_queue.put((selected_piece.row, selected_piece.col, row, col))
                                selected_piece = None
                                valid_moves = set()
                                turn = RED if turn == BLUE else BLUE
                            else:
                                selected_piece = None
                                valid_moves = set()
                        else:
                            if piece != 0 and piece.color == turn:
                                selected_piece = (piece, row, col)
                                valid_moves = board.get_valid_moves(piece)
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stop_event.set()
                        pygame.quit()
                        return

            await asyncio.sleep(1.0 / FPS)

        if platform.system() != 'Emscripten':
            game_thread.join(timeout=1)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())