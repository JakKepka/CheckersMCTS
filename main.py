import pygame
import asyncio
import platform
import time
import threading
import queue
import copy
import logging
import csv
import os
from checkers.board import Board
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, BLUE, ROWS, COLS
from mcts.mcts import MCTS
from mcts.hueristics import MCTSHEURISTIC  # Fixed typo from 'hueristics'
from mcts.progressive_widening import MCTSPROGRESSIVE
from mcts.heuristics_material import MCTSMaterialHeuristic

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def draw_win_summary(win, red_wins, blue_wins, red_ai_name, blue_ai_name, current_game, total_games, metrics):
    win.fill((0, 0, 0))
    summary_text = f"Game {current_game}/{total_games} Completed"
    red_text = f"RED ({red_ai_name}): {red_wins} wins"
    blue_text = f"BLUE ({blue_ai_name}): {blue_wins} wins"
    metrics_text = (
        f"Piece Diff: {metrics['piece_diff']:.1f}, King Diff: {metrics['king_diff']:.1f}, "
        f"Moves: {metrics['move_count']}, Captures (R/B): {metrics['captures_red']}/{metrics['captures_blue']}, "
        f"Promotions (R/B): {metrics['promotions_red']}/{metrics['promotions_blue']}"
    )
    
    summary_surface = FONT.render(summary_text, True, TEXT_COLOR)
    red_surface = FONT.render(red_text, True, TEXT_COLOR)
    blue_surface = FONT.render(blue_text, True, TEXT_COLOR)
    metrics_surface = FONT.render(metrics_text, True, TEXT_COLOR)
    
    win.blit(summary_surface, (WIDTH//2 - summary_surface.get_width()//2, 200))
    win.blit(red_surface, (WIDTH//2 - red_surface.get_width()//2, 280))
    win.blit(blue_surface, (WIDTH//2 - blue_surface.get_width()//2, 360))
    win.blit(metrics_surface, (WIDTH//2 - metrics_surface.get_width()//2, 440))
    pygame.display.update()

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn, metrics_queue):
    turn = initial_turn
    iterations = 30 if mode != 'aivai' else 15
    move_count = 0
    captures_red = 0
    captures_blue = 0
    promotions_red = 0
    promotions_blue = 0

    while not stop_event.is_set():
        winner = board.get_winner()
        if winner is not None:
            # Calculate piece and king differences
            red_pieces = 0
            blue_pieces = 0
            red_kings = 0
            blue_kings = 0
            for row in range(ROWS):
                for col in range(COLS):
                    piece = board.get_piece(row, col)
                    if piece != 0:
                        if piece.color == RED:
                            red_pieces += 1
                            if piece.king:
                                red_kings += 1
                        else:
                            blue_pieces += 1
                            if piece.king:
                                blue_kings += 1
            piece_diff = red_pieces - blue_pieces if winner == RED else blue_pieces - red_pieces
            king_diff = red_kings - blue_kings if winner == RED else blue_kings - red_kings
            
            # Generate outcome description
            outcome_desc = (
                f"{'RED' if winner == RED else 'BLUE'} won with {abs(piece_diff)} more piece{'s' if abs(piece_diff) != 1 else ''} "
                f"and {abs(king_diff)} more king{'s' if abs(king_diff) != 1 else ''} after {move_count} moves, "
                f"capturing {captures_red if winner == RED else captures_blue} piece{'s' if (captures_red if winner == RED else captures_blue) != 1 else ''} "
                f"and promoting {promotions_red if winner == RED else promotions_blue} pawn{'s' if (promotions_red if winner == RED else promotions_blue) != 1 else ''}"
            )
            
            metrics = {
                'winner': winner,
                'piece_diff': piece_diff,
                'king_diff': king_diff,
                'move_count': move_count,
                'captures_red': captures_red,
                'captures_blue': captures_blue,
                'promotions_red': promotions_red,
                'promotions_blue': promotions_blue,
                'outcome_desc': outcome_desc
            }
            metrics_queue.put(metrics)
            logging.debug(f"Game ended with winner: {'RED' if winner == RED else 'BLUE'}")
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
                        logging.error(f"Invalid AI move: {move} for player {'BLUE' if turn == BLUE else 'RED'}")
                        stop_event.set()
                        break
                    # Check for promotion and captures
                    was_king = new_piece.king
                    _, captured, _ = board.valid_move(new_piece, dest_row, dest_col)
                    result = board.move(new_piece, dest_row, dest_col)
                    move_count += 1
                    if captured:
                        if turn == RED:
                            captures_red += len(captured)
                        else:
                            captures_blue += len(captured)
                    if not was_king and new_piece.king:
                        if turn == RED:
                            promotions_red += 1
                        else:
                            promotions_blue += 1
                    logging.debug(f"AI move: {piece.row},{piece.col} to {dest_row},{dest_col}")
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
                    turn = RED if turn == BLUE else BLUE
                else:
                    has_moves = False
                    for row in range(ROWS):
                        for col in range(COLS):
                            piece = board.get_piece(row, col)
                            if piece != 0 and piece.color == turn:
                                if board.can_move(piece):
                                    has_moves = True
                                    break
                        if has_moves:
                            break
                    if not has_moves:
                        logging.info(f"No valid moves for {'BLUE' if turn == BLUE else 'RED'}")
                        winner = BLUE if turn == RED else RED
                        outcome_desc = (
                            f"No winner: {'BLUE' if turn == BLUE else 'RED'} had no valid moves after {move_count} moves, "
                            f"with RED capturing {captures_red} and BLUE capturing {captures_blue} pieces"
                        )
                        metrics = {
                            'winner': winner,
                            'piece_diff': 0,
                            'king_diff': 0,
                            'move_count': move_count,
                            'captures_red': captures_red,
                            'captures_blue': captures_blue,
                            'promotions_red': promotions_red,
                            'promotions_blue': promotions_blue,
                            'outcome_desc': outcome_desc
                        }
                        metrics_queue.put(metrics)
                        win_queue.put(winner)
                        stop_event.set()
                    else:
                        logging.error("AI returned None but valid moves exist")
                        stop_event.set()

            except Exception as e:
                logging.error(f"AI exception: {str(e)}")
                stop_event.set()
        elif ai_player and turn == ai_player:
            try:
                if mode == 'mcts':
                    mcts = MCTS(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai2':
                    mcts = MCTSHEURISTIC(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'ai3':
                    mcts = MCTSPROGRESSIVE(copy.deepcopy(board), ai_player, iterations=iterations)
                elif mode == 'material':
                    mcts = MCTSMaterialHeuristic(copy.deepcopy(board), ai_player, iterations=iterations)
                else:
                    logging.error(f"Invalid mode: {mode}")
                    stop_event.set()
                    break
                move = mcts.search()
                if move:
                    piece, dest_row, dest_col = move
                    new_piece = board.get_piece(piece.row, piece.col)
                    if new_piece == 0 or new_piece.color != ai_player:
                        logging.error(f"Invalid AI move: {move} for player {'RED' if ai_player == RED else 'BLUE'}")
                        stop_event.set()
                        break
                    was_king = new_piece.king
                    _, captured, _ = board.valid_move(new_piece, dest_row, dest_col)
                    result = board.move(new_piece, dest_row, dest_col)
                    move_count += 1
                    if captured:
                        captures_red += len(captured)
                    if not was_king and new_piece.king:
                        promotions_red += 1
                    logging.debug(f"AI move: {piece.row},{piece.col} to {dest_row},{dest_col}")
                    move_queue.put((piece.row, piece.col, dest_row, dest_col))
                    turn = BLUE
                else:
                    has_moves = False
                    for row in range(ROWS):
                        for col in range(COLS):
                            piece = board.get_piece(row, col)
                            if piece != 0 and piece.color == ai_player:
                                if board.can_move(piece):
                                    has_moves = True
                                    break
                        if has_moves:
                            break
                    if not has_moves:
                        logging.info(f"No valid moves for AI {'RED' if ai_player == RED else 'BLUE'}")
                        outcome_desc = (
                            f"BLUE won: RED had no valid moves after {move_count} moves, "
                            f"with RED capturing {captures_red} and BLUE capturing {captures_blue} pieces"
                        )
                        metrics = {
                            'winner': BLUE,
                            'piece_diff': 0,
                            'king_diff': 0,
                            'move_count': move_count,
                            'captures_red': captures_red,
                            'captures_blue': captures_blue,
                            'promotions_red': promotions_red,
                            'promotions_blue': promotions_blue,
                            'outcome_desc': outcome_desc
                        }
                        metrics_queue.put(metrics)
                        win_queue.put(BLUE)
                        stop_event.set()
                    else:
                        logging.error("AI returned None but valid moves exist")
                        stop_event.set()

            except Exception as e:
                logging.error(f"AI exception in Player vs AI: {str(e)}")
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
        {'text': 'Material Heuristic MCTS', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'ai_class': MCTSMaterialHeuristic},
    ]
    
    buttons = [
        {'text': 'Player vs Player', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 200, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'pvp'},
        {'text': 'Player vs MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 280, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'mcts'},
        {'text': 'Player vs Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 360, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai2'},
        {'text': 'Player vs Progressive MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 440, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'ai3'},
        {'text': 'Player vs Material Heuristic MCTS AI', 'rect': pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, 520, BUTTON_WIDTH, BUTTON_HEIGHT), 'hover': False, 'mode': 'material'},
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
            'material': 'Material Heuristic MCTS'
        }[mode]
        print(f"BLUE: Human, RED: {ai_name}")

    FPS = 60
    iterations = 30 if mode != 'aivai' else 15
    move_queue = queue.Queue()
    win_queue = queue.Queue()
    metrics_queue = queue.Queue()
    stop_event = threading.Event()

    # CSV fieldnames
    fieldnames = [
        'Game_Number', 'Winner', 'Starting_Player', 'Piece_Difference', 'King_Difference',
        'Move_Count', 'Captures_Red', 'Captures_Blue', 'Promotions_Red', 'Promotions_Blue',
        'Outcome_Description'
    ]

    if mode == 'aivai':
        red_wins = 0
        blue_wins = 0
        start_red_wins = 0
        start_blue_wins = 0
        game_metrics = []
        running_totals = {
            'piece_diff': 0,
            'king_diff': 0,
            'move_count': 0,
            'captures_red': 0,
            'captures_blue': 0,
            'promotions_red': 0,
            'promotions_blue': 0,
            'games': 0
        }

        # Define CSV filenames based on AI names
        metrics_csv = f"{red_ai_name.replace(' ', '_')}_vs_{blue_ai_name.replace(' ', '_')}_metrics.csv"
        averages_csv = f"{red_ai_name.replace(' ', '_')}_vs_{blue_ai_name.replace(' ', '_')}_averages.csv"

        # Initialize metrics CSV with headers if it doesn't exist
        if not os.path.exists(metrics_csv):
            with open(metrics_csv, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

        for game_num in range(1, num_games + 1):
            board = Board()
            initial_turn = BLUE if game_num % 2 == 1 else RED
            turn = initial_turn
            stop_event.clear()
            print(f"\nStarting Game {game_num}/{num_games} (First move: {'BLUE' if initial_turn == BLUE else 'RED'})")

            if platform.system() != "Emscripten":
                game_thread = threading.Thread(target=game_logic, args=(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn, metrics_queue))
                game_thread.daemon = True
                game_thread.start()
            else:
                async def async_game_logic():
                    await game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, initial_turn, metrics_queue)
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
                metrics = metrics_queue.get_nowait()
                if winner == RED:
                    red_wins += 1
                    if initial_turn == RED:
                        start_red_wins += 1
                elif winner == BLUE:
                    blue_wins += 1
                    if initial_turn == BLUE:
                        start_blue_wins += 1
                
                running_totals['piece_diff'] += metrics['piece_diff']
                running_totals['king_diff'] += metrics['king_diff']
                running_totals['move_count'] += metrics['move_count']
                running_totals['captures_red'] += metrics['captures_red']
                running_totals['captures_blue'] += metrics['captures_blue']
                running_totals['promotions_red'] += metrics['promotions_red']
                running_totals['promotions_blue'] += metrics['promotions_blue']
                running_totals['games'] += 1

                game_data = {
                    'game_num': game_num,
                    'winner': 'RED' if winner == RED else 'BLUE',
                    'starting_player': 'BLUE' if initial_turn == BLUE else 'RED',
                    'piece_diff': metrics['piece_diff'],
                    'king_diff': metrics['king_diff'],
                    'move_count': metrics['move_count'],
                    'captures_red': metrics['captures_red'],
                    'captures_blue': metrics['captures_blue'],
                    'promotions_red': metrics['promotions_red'],
                    'promotions_blue': metrics['promotions_blue'],
                    'outcome_desc': metrics['outcome_desc']
                }
                game_metrics.append(game_data)

                # Append to metrics CSV
                with open(metrics_csv, 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({
                        'Game_Number': game_data['game_num'],
                        'Winner': game_data['winner'],
                        'Starting_Player': game_data['starting_player'],
                        'Piece_Difference': game_data['piece_diff'],
                        'King_Difference': game_data['king_diff'],
                        'Move_Count': game_data['move_count'],
                        'Captures_Red': game_data['captures_red'],
                        'Captures_Blue': game_data['captures_blue'],
                        'Promotions_Red': game_data['promotions_red'],
                        'Promotions_Blue': game_data['promotions_blue'],
                        'Outcome_Description': game_data['outcome_desc']
                    })

                # Update averages CSV
                with open(averages_csv, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerow({
                        'Game_Number': 'AVERAGE',
                        'Winner': '',
                        'Starting_Player': '',
                        'Piece_Difference': running_totals['piece_diff'] / running_totals['games'] if running_totals['games'] else 0,
                        'King_Difference': running_totals['king_diff'] / running_totals['games'] if running_totals['games'] else 0,
                        'Move_Count': running_totals['move_count'] / running_totals['games'] if running_totals['games'] else 0,
                        'Captures_Red': running_totals['captures_red'] / running_totals['games'] if running_totals['games'] else 0,
                        'Captures_Blue': running_totals['captures_blue'] / running_totals['games'] if running_totals['games'] else 0,
                        'Promotions_Red': running_totals['promotions_red'] / running_totals['games'] if running_totals['games'] else 0,
                        'Promotions_Blue': running_totals['promotions_blue'] / running_totals['games'] if running_totals['games'] else 0,
                        'Outcome_Description': ''
                    })

                # Print intermediate statistics
                avg_piece_diff = running_totals['piece_diff'] / running_totals['games']
                avg_king_diff = running_totals['king_diff'] / running_totals['games']
                avg_move_count = running_totals['move_count'] / running_totals['games']
                avg_captures_red = running_totals['captures_red'] / running_totals['games']
                avg_captures_blue = running_totals['captures_blue'] / running_totals['games']
                avg_promotions_red = running_totals['promotions_red'] / running_totals['games']
                avg_promotions_blue = running_totals['promotions_blue'] / running_totals['games']
                start_win_rate = (
                    (start_blue_wins / (game_num // 2 + game_num % 2) * 100) if initial_turn == BLUE and game_num > 0
                    else (start_red_wins / (game_num // 2) * 100) if game_num > 1 else 0
                )

                print(f"Game {game_num} Over! Winner: {'RED' if winner == RED else 'BLUE'}")
                print(f"Game Metrics: Piece Diff: {metrics['piece_diff']}, King Diff: {metrics['king_diff']}, "
                      f"Moves: {metrics['move_count']}, Captures (R/B): {metrics['captures_red']}/{metrics['captures_blue']}, "
                      f"Promotions (R/B): {metrics['promotions_red']}/{metrics['promotions_blue']}")
                print(f"Outcome: {metrics['outcome_desc']}")
                print(f"Running Averages: Avg Piece Diff: {avg_piece_diff:.2f}, Avg King Diff: {avg_king_diff:.2f}, "
                      f"Avg Moves: {avg_move_count:.1f}, Avg Captures (R/B): {avg_captures_red:.1f}/{avg_captures_blue:.1f}, "
                      f"Avg Promotions (R/B): {avg_promotions_red:.2f}/{avg_promotions_blue:.2f}")
                print(f"Win Rate for Starting Player ({'BLUE' if initial_turn == BLUE else 'RED'}): {start_win_rate:.1f}%")
                print(f"Current Results: RED ({red_ai_name}): {red_wins} wins, BLUE ({blue_ai_name}): {blue_wins} wins")
                print(f"Updated '{metrics_csv}' and '{averages_csv}'")

                draw_win_summary(WIN, red_wins, blue_wins, red_ai_name, blue_ai_name, game_num, num_games, metrics)
                await asyncio.sleep(2)

            except queue.Empty:
                print(f"Game {game_num} ended with no winner")
                metrics = metrics_queue.get_nowait() if not metrics_queue.empty() else {
                    'winner': 'NONE',
                    'piece_diff': 0,
                    'king_diff': 0,
                    'move_count': move_count,
                    'captures_red': captures_red,
                    'captures_blue': captures_blue,
                    'promotions_red': promotions_red,
                    'promotions_blue': promotions_blue,
                    'outcome_desc': f"No winner: Game ended after {move_count} moves with RED capturing {captures_red} and BLUE capturing {captures_blue} pieces"
                }
                game_data = {
                    'game_num': game_num,
                    'winner': 'NONE',
                    'starting_player': 'BLUE' if initial_turn == BLUE else 'RED',
                    'piece_diff': metrics['piece_diff'],
                    'king_diff': metrics['king_diff'],
                    'move_count': metrics['move_count'],
                    'captures_red': metrics['captures_red'],
                    'captures_blue': metrics['captures_blue'],
                    'promotions_red': metrics['promotions_red'],
                    'promotions_blue': metrics['promotions_blue'],
                    'outcome_desc': metrics['outcome_desc']
                }
                game_metrics.append(game_data)
                running_totals['games'] += 1

                # Append to metrics CSV
                with open(metrics_csv, 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({
                        'Game_Number': game_data['game_num'],
                        'Winner': game_data['winner'],
                        'Starting_Player': game_data['starting_player'],
                        'Piece_Difference': game_data['piece_diff'],
                        'King_Difference': game_data['king_diff'],
                        'Move_Count': game_data['move_count'],
                        'Captures_Red': game_data['captures_red'],
                        'Captures_Blue': game_data['captures_blue'],
                        'Promotions_Red': game_data['promotions_red'],
                        'Promotions_Blue': game_data['promotions_blue'],
                        'Outcome_Description': game_data['outcome_desc']
                    })

                # Update averages CSV
                with open(averages_csv, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerow({
                        'Game_Number': 'AVERAGE',
                        'Winner': '',
                        'Starting_Player': '',
                        'Piece_Difference': running_totals['piece_diff'] / running_totals['games'] if running_totals['games'] else 0,
                        'King_Difference': running_totals['king_diff'] / running_totals['games'] if running_totals['games'] else 0,
                        'Move_Count': running_totals['move_count'] / running_totals['games'] if running_totals['games'] else 0,
                        'Captures_Red': running_totals['captures_red'] / running_totals['games'] if running_totals['games'] else 0,
                        'Captures_Blue': running_totals['captures_blue'] / running_totals['games'] if running_totals['games'] else 0,
                        'Promotions_Red': running_totals['promotions_red'] / running_totals['games'] if running_totals['games'] else 0,
                        'Promotions_Blue': running_totals['promotions_blue'] / running_totals['games'] if running_totals['games'] else 0,
                        'Outcome_Description': ''
                    })

                draw_win_summary(WIN, red_wins, blue_wins, red_ai_name, blue_ai_name, game_num, num_games, metrics)
                await asyncio.sleep(2)
                print(f"Updated '{metrics_csv}' and '{averages_csv}'")

            if platform.system() != "Emscripten":
                game_thread.join(timeout=1)

        print(f"\nCompleted all games. Final results in '{metrics_csv}' and '{averages_csv}'.")

    else:
        if platform.system() != "Emscripten":
            game_thread = threading.Thread(target=game_logic, args=(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, turn, metrics_queue))
            game_thread.daemon = True
            game_thread.start()
        else:
            async def async_game_logic():
                await game_logic(board, mode, ai_player, ai_red, ai_blue, move_queue, stop_event, win_queue, turn, metrics_queue)
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
                                logging.debug(f"Human move: {selected_piece.row},{selected_piece.col} to {row},{col}")
                                move_queue.put((selected_piece.row, selected_piece.col, row, col))
                                selected_piece = None
                                valid_moves = set()
                                turn = RED if turn == BLUE else BLUE
                            else:
                                logging.debug(f"Invalid human move attempted: {row},{col}")
                                selected_piece = None
                                valid_moves = set()
                        else:
                            if piece != 0 and piece.color == turn:
                                selected_piece = piece
                                valid_moves = board.get_valid_moves(piece)
                                logging.debug(f"Selected piece at {piece.row},{piece.col} with valid moves: {valid_moves}")
                            else:
                                logging.debug(f"Clicked on invalid piece or empty square at {row},{col}")

                if turn == BLUE and not selected_piece:
                    has_moves = False
                    for row in range(ROWS):
                        for col in range(COLS):
                            piece = board.get_piece(row, col)
                            if piece != 0 and piece.color == BLUE:
                                if board.can_move(piece):
                                    has_moves = True
                                    break
                        if has_moves:
                            break
                    if not has_moves:
                        logging.info("No valid moves for human (BLUE)")
                        outcome_desc = (
                            f"RED won: BLUE had no valid moves after {move_count} moves, "
                            f"with RED capturing {captures_red} and BLUE capturing {captures_blue} pieces"
                        )
                        metrics_queue.put({
                            'winner': RED,
                            'piece_diff': 0,
                            'king_diff': 0,
                            'move_count': move_count,
                            'captures_red': captures_red,
                            'captures_blue': captures_blue,
                            'promotions_red': promotions_red,
                            'promotions_blue': promotions_blue,
                            'outcome_desc': outcome_desc
                        })
                        win_queue.put(RED)
                        stop_event.set()
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stop_event.set()
                        pygame.quit()
                        return

            await asyncio.sleep(1.0 / FPS)

        if platform.system() != "Emscripten":
            game_thread.join(timeout=1)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())