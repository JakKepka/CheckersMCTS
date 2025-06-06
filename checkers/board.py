# board.py
import pygame
from checkers.constants import *
from checkers.pieces import Piece


# Warcaby polskie (wariant znany także jako warcaby międzynarodowe) to gra
#planszowa dla dwóch graczy na planszy 10×10 polach, po 20 pionków każ-
#dego koloru na starcie. Pionki poruszają się po przekątnych, zwykłe pionki
#mogą skakać przez figury przeciwnika zarówno do przodu, jak i do tyłu, a po
#zdobyciu drugiego końca planszy stają się damkami, które mogą poruszać się
#na wiele pól (tzw. „króle”). Zwycięża gracz, który zbije lub zablokuje wszyst-
#kie figury przeciwnika. Ponadto zwykłe pionki nie mogą bić króli/damki.


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

    def can_capture(self, piece):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            mid_row = piece.row + dr
            mid_col = piece.col + dc
            end_row = piece.row + 2 * dr
            end_col = piece.col + 2 * dc

            if 0 <= end_row < ROWS and 0 <= end_col < COLS:
                mid_piece = self.get_piece(mid_row, mid_col)
                end_piece = self.get_piece(end_row, end_col)
                if mid_piece != 0 and mid_piece.color != piece.color and end_piece == 0:
                    return True
        return False

    def valid_move(self, piece, dest_row, dest_col):
        # Check if destination is within board bounds
        if not (0 <= dest_row < ROWS and 0 <= dest_col < COLS):
            return False, [], set()  # Zwracamy krotkę zamiast samego False

        # Check if destination square is empty
        if self.get_piece(dest_row, dest_col) != 0:
            return False, [], set()  # Zwracamy krotkę zamiast samego False

        row_diff = dest_row - piece.row
        col_diff = dest_col - piece.col

        # Regular piece moves
        if not piece.king:
            direction = -1 if piece.color == BLUE else 1
            
            # Normal one square move
            if row_diff == direction and abs(col_diff) == 1:
                if self.can_capture(piece):
                    return False, [], set()
                return True, [], set()

            # Capture moves
            if abs(row_diff) % 2 == 0 and abs(col_diff) % 2 == 0:
                # Sprawdzamy wszystkie możliwe ścieżki bicia
                result, captured, visited = self._check_capture_path(piece, piece.row, piece.col, dest_row, dest_col, [], set())
                return result, captured, visited

        # Jeśli żaden warunek nie został spełniony
        return False, [], set()

    def _check_capture_path(self, piece, current_row, current_col, dest_row, dest_col, captured_pieces, visited):
        # Jeśli dotarliśmy do celu
        if current_row == dest_row and current_col == dest_col:
            return len(captured_pieces) > 0, captured_pieces, visited

        # Sprawdź wszystkie możliwe kierunki bicia
        directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        
        for dr, dc in directions:
            new_row = current_row + dr
            new_col = current_col + dc
            
            # Sprawdź czy nowa pozycja jest w granicach planszy
            if not (0 <= new_row < ROWS and 0 <= new_col < COLS):
                continue
                
            mid_row = current_row + dr//2
            mid_col = current_col + dc//2
            
            if self.get_piece(new_row, new_col) != 0:
                continue
            
            piece_to_capture = self.get_piece(mid_row, mid_col)
            if (piece_to_capture == 0 or 
                piece_to_capture.color == piece.color or 
                (piece_to_capture.king and not piece.king) or
                (mid_row, mid_col) in captured_pieces):
                continue
                
            new_captured = captured_pieces + [(mid_row, mid_col)]
            new_visited = visited | {(new_row, new_col)}
            
            if (new_row, new_col) not in visited:
                result, final_captured, final_visited = self._check_capture_path(
                    piece, new_row, new_col, dest_row, dest_col, new_captured, new_visited)
                if result:
                    return True, final_captured, final_visited
                    
        return False, captured_pieces, visited

    def move(self, piece, dest_row, dest_col):
        print(f"Attempting to move piece from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
        valid, captured_pieces, visited = self.valid_move(piece, dest_row, dest_col)
        
        if valid:
            # Usuwamy wszystkie zbite pionki
            for mid_row, mid_col in captured_pieces:
                self.board[mid_row][mid_col] = 0

            # Przesunięcie pionka na końcową pozycję
            self.board[piece.row][piece.col] = 0
            self.board[dest_row][dest_col] = piece
            piece.move(dest_row, dest_col)

            # Promocja na damkę
            if (piece.color == RED and dest_row == 0) or (piece.color == BLUE and dest_row == ROWS - 1):
                piece.make_king()

            # Sprawdzenie możliwości kolejnego bicia
            if self.can_capture(piece):
                print("Możliwe kolejne bicie. Gracz musi kontynuować.")
                return "CONTINUE"

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
