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
from mcts.hueristics import  MCTSHEURISTIC
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

def game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event):
    turn = BLUE
    ai_timeout = 3
    iterations = 30 if mode != 'aivai' else 15

    while not stop_event.is_set():
        winner = board.get_winner()
        if winner is not None:
            print(f"Game Over! Winner: {'RED' if winner == RED else 'BLUE'}")
            time.sleep(2)
            stop_event.set()
            break

        if mode == 'aivai':
            current_ai = ai_blue if turn == BLUE else ai_red
            print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) turn")
            start_time = time.time()
            try:
                mcts = current_ai(copy.deepcopy(board), turn, iterations=iterations)
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != turn:
                        print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
                        stop_event.set()
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) moved from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
                    turn = RED if turn == BLUE else BLUE
                else:
                    print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) found no valid moves")
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
                        print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) has no moves, {'RED' if turn == BLUE else 'BLUE'} wins")
                        stop_event.set()
                    else:
                        print("MCTS failed to find moves despite available options")
                        stop_event.set()

            except Exception as e:
                print(f"AI error: {e}")
                stop_event.set()
        elif ai_player and turn == ai_player:
            print(f"AI ({'RED' if ai_player == RED else 'BLUE'}) turn")
            start_time = time.time()
            try:
                if mode == 'mcts':
                    mcts = MCTS(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai2':
                    mcts = MCTSHEURISTIC(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai3':
                    mcts = MCTSPROGRESSIVE(copy.deepcopy(board), ai_player, iterations=iterations)
                else:
                    print(f"{mode} not implemented yet")
                    stop_event.set()
                    break
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != ai_player:
                        print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
                        stop_event.set()
                        break
                    result = board.move(new_piece, dest_row, dest_col)
                    print(f"AI moved from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
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
                        stop_event.set()
                    else:
                        print("MCTS failed to find moves despite available options")
                        stop_event.set()

            except Exception as e:
                print(f"AI error: {e}")
                stop_event.set()
        elif mode != 'aivai':
            # Wait for human move (signaled via move_queue)
            time.sleep(0.01)  # Avoid busy waiting
        else:
            time.sleep(0.01)

def main():
    if platform.system() == "Emscripten":
        print("Warning: Threading not supported in Pyodide. Running in single-threaded mode.")
        # Fallback to single-threaded async mode
        import asyncio
        async def async_main():
            buttons = [
                {'text': 'Player vs Player', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'pvp'},
                {'text': 'Player vs MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'mcts'},
                {'text': 'Player vs Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai2'},
                {'text': 'Player vs Progressive MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai3'},
                {'text': 'AI vs AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 520, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'aivai'},
            ]
            mode = None
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
                await asyncio.sleep(0.016)

            board = Board()
            selected_piece = None
            turn = BLUE
            valid_moves = set()
            ai_player = RED if mode != 'pvp' else None
            ai_red = MCTSHEURISTIC if mode == 'aivai' else None
            ai_blue = MCTSPROGRESSIVE if mode == 'aivai' else None
            FPS = 60
            ai_timeout = 3
            iterations = 30 if mode != 'aivai' else 15
            clock = pygame.time.Clock()

            while True:
                clock.tick(FPS)
                board.draw(WIN)
                if selected_piece and mode != 'aivai':
                    board.highlight_moves(WIN, valid_moves)
                pygame.display.update()

                winner = board.get_winner()
                if winner is not None:
                    print(f"Game Over! Winner: {'RED' if winner == RED else 'BLUE'}")
                    await asyncio.sleep(2)
                    break

                if mode == 'aivai':
                    current_ai = ai_blue if turn == BLUE else ai_red
                    print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) turn")
                    start_time = time.time()
                    try:
                        mcts = current_ai(copy.deepcopy(board), turn, iterations=iterations)
                        move = mcts.search()
                        if move:
                            piece, dest_row, dest_col = move
                            new_piece = board.get_piece(piece.row, piece.col)
                            if new_piece == 0 or new_piece.color != turn:
                                print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
                                break
                            result = board.move(new_piece, dest_row, dest_col)
                            print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) moved from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
                            board.draw(WIN)
                            board.highlight_moves(WIN, {(dest_row, dest_col)})
                            pygame.display.update()
                            await asyncio.sleep(0.5)
                            turn = RED if turn == BLUE else BLUE
                        else:
                            print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) found no valid moves")
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
                                print(f"AI ({'BLUE' if turn == BLUE else 'RED'}) has no moves, {'RED' if turn == BLUE else 'BLUE'} wins")
                                break
                            else:
                                print("MCTS failed to find moves despite available options")
                                break

                    except Exception as e:
                        print(f"AI error: {e}")
                        break
                elif ai_player and turn == ai_player:
                    print(f"AI ({'RED' if ai_player == RED else 'BLUE'}) turn")
                    start_time = time.time()
                    try:
                        if mode == 'mcts':
                            mcts = MCTS(copy.deepcopy(board), ai_player, iterations=iterations)
                        elif mode == 'ai2':
                            mcts = MCTSHEURISTIC(copy.deepcopy(board), ai_player, iterations=iterations)
                        elif mode == 'ai3':
                            mcts = MCTSPROGRESSIVE(copy.deepcopy(board), ai_player, iterations=iterations)
                        else:
                            print(f"{mode} not implemented yet")
                            break
                        move = mcts.search()
                        if move:
                            piece, dest_row, dest_col = move
                            new_piece = board.get_piece(piece.row, piece.col)
                            if new_piece == 0 or new_piece.color != ai_player:
                                print(f"AI selected invalid piece at ({piece.row}, {piece.col})")
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
                                break
                            else:
                                print("MCTS failed to find moves despite available options")
                                break

                    except Exception as e:
                        print(f"AI error: {e}")
                        break
                else:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return
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
            asyncio.run(async_main())
            return

    # Threaded mode for non-Emscripten platforms
    buttons = [
        {'text': 'Player vs Player', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'pvp'},
        {'text': 'Player vs MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'mcts'},
        {'text': 'Player vs Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai2'},
        {'text': 'Player vs Progressive MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai3'},
        {'text': 'AI vs AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 520, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'aivai'},
    ]
    mode = None
    clock = pygame.time.Clock()
    FPS = 60

    # Menu loop
    while mode is None:
        clock.tick(FPS)
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

    # Game setup
    board = Board()
    selected_piece = None
    turn = BLUE
    valid_moves = set()
    ai_player = RED if mode != 'pvp' else None
    ai_red = MCTSHEURISTIC if mode == 'aivai' else None
    ai_blue = MCTSPROGRESSIVE if mode == 'aivai' else None
    move_queue = queue.Queue()
    stop_event = threading.Event()

    # Start game logic thread
    game_thread = threading.Thread(target=game_logic, args=(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event))
    game_thread.daemon = True
    game_thread.start()

    # Main GUI loop
    highlighted_move = None
    while not stop_event.is_set():
        clock.tick(FPS)
        board.draw(WIN)
        if selected_piece and mode != 'aivai':
            board.highlight_moves(WIN, valid_moves)
        if highlighted_move:
            board.highlight_moves(WIN, {highlighted_move})
        pygame.display.update()

        # Process moves from game logic thread
        try:
            move = move_queue.get_nowait()
            highlighted_move = (move[2], move[3])  # Highlight destination
            time.sleep(0.5)  # Display move briefly
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
                            print(f"Player {'BLUE' if turn == BLUE else 'RED'} moved from ({selected_piece.row}, {selected_piece.col}) to ({row}, {col})")
                            move_queue.put((selected_piece.row, selected_piece.col, row, col))
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
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop_event.set()
                    pygame.quit()
                    return

    print("Game ended")
    game_thread.join(timeout=1)
    pygame.quit()

if __name__ == "__main__":
    main()