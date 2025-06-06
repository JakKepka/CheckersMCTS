import pygame
from checkers.board import Board
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE
from checkers.constants import RED, BLUE

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Polish Draughts')

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def main():
    run = True
    clock = pygame.time.Clock()
    board = Board()
    selected_piece = None
    turn = BLUE
    valid_moves = set()  # Dodajemy zmienną do przechowywania możliwych ruchów

    while run:
        clock.tick(60)
        board.draw(WIN)
        if selected_piece:
            board.highlight_moves(WIN, valid_moves)  # Pokazujemy możliwe ruchy
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                piece = board.get_piece(row, col)
                
                if selected_piece:
                    if (row, col) in valid_moves:  # Sprawdzamy czy ruch jest dozwolony
                        if board.move(selected_piece, row, col):
                            selected_piece = None
                            valid_moves = set()  # Czyścimy możliwe ruchy
                            turn = BLUE if turn == RED else RED
                    else:
                        selected_piece = None
                        valid_moves = set()  # Czyścimy możliwe ruchy
                else:
                    if piece != 0 and piece.color == turn:
                        selected_piece = piece
                        valid_moves = board.get_valid_moves(piece)  # Pobieramy możliwe ruchy
if __name__ == "__main__":
    main()
