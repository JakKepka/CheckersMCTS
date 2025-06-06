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

    while run:
        clock.tick(60)
        board.draw(WIN)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                print("Mouse clicked")
                print(f' Pre selecteing: {selected_piece}')
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                piece = board.get_piece(row, col)
                print(f"Clicked on row: {row}, col: {col}, piece: {piece}")
                if selected_piece:
                    print(f"Selected piece: {selected_piece}, trying to move to row: {row}, col: {col}")
                    if board.move(selected_piece, row, col):
                        selected_piece = None
                        turn = BLUE if turn == RED else RED
                    else:
                        selected_piece = None
                else:
                    print("Selecting piece")
                    if piece != 0 and piece.color == turn:
                        print(f"Piece selected: {piece}")
                        selected_piece = piece
                print(f"Selected piece: {selected_piece}")

    pygame.quit()

if __name__ == "__main__":
    main()
