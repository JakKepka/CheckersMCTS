# board.py
import pygame
from checkers.constants import *
from checkers.pieces import Piece

class Board:
    def __init__(self):
        self.board = []
        self.create_board()

    def draw_squares(self, win):
        win.fill(WHITE)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, GREY, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if row < 4 and (row + col) % 2 == 1:
                    self.board[row].append(Piece(row, col, RED))
                elif row > 5 and (row + col) % 2 == 1:
                    self.board[row].append(Piece(row, col, BLUE))
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def get_piece(self, row, col):
        return self.board[row][col]

    def valid_move(self, piece, dest_row, dest_col):
        print(1)
        # Sprawdź, czy pole docelowe jest puste
        if self.get_piece(dest_row, dest_col) != 0:
            return False

        print(2)
        row_diff = dest_row - piece.row
        col_diff = dest_col - piece.col

        # Ruchy pionka
        if not piece.king:
            direction = -1 if piece.color == BLUE else 1
            print(3)
            # Zwykły ruch o jedno pole
            if row_diff == direction and abs(col_diff) == 1:
                return True
            print(4)

            # Bicie
            if row_diff == 2 * direction and abs(col_diff) == 2:
                mid_row = piece.row + direction
                mid_col = piece.col + (col_diff // 2)
                print(5)
                mid_piece = self.get_piece(mid_row, mid_col)
                print(6)
                if mid_piece != 0 and mid_piece.color != piece.color:
                    return True

        # Ruchy damki
        else:
            if abs(row_diff) == abs(col_diff):
                step_row = 1 if row_diff > 0 else -1
                step_col = 1 if col_diff > 0 else -1
                row, col = piece.row + step_row, piece.col + step_col
                has_captured = False

                while row != dest_row and col != dest_col:
                    current_piece = self.get_piece(row, col)
                    if current_piece != 0:
                        if current_piece.color == piece.color:
                            return False
                        if has_captured:
                            return False
                        has_captured = True
                    row += step_row
                    col += step_col

                return True

        return False


    def move(self, piece, dest_row, dest_col):
        print(f"Attempting to move piece from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
        if self.valid_move(piece, dest_row, dest_col):
            # Sprawdzenie, czy ruch jest biciem
            row_diff = dest_row - piece.row
            col_diff = dest_col - piece.col

            if abs(row_diff) == 2 and abs(col_diff) == 2:
                # Obliczenie pozycji zbitego pionka
                mid_row = piece.row + row_diff // 2
                mid_col = piece.col + col_diff // 2
                captured_piece = self.get_piece(mid_row, mid_col)
                if captured_piece != 0 and captured_piece.color != piece.color:
                    # Usunięcie zbitego pionka
                    self.board[mid_row][mid_col] = 0

            # Przesunięcie pionka
            self.board[piece.row][piece.col], self.board[dest_row][dest_col] = 0, piece
            piece.move(dest_row, dest_col)

            # Promocja na damkę
            if (piece.color == 'red' and dest_row == 0) or (piece.color == 'blue' and dest_row == self.ROWS - 1):
                piece.make_king()

            return True
        return False


    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0

    def get_valid_moves(self, piece):
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == BLUE or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1

        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves
