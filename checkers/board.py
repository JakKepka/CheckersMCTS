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
                    self.board[row].append(Piece(row, col, BLUE))  # BLUE starts at rows 0–3
                elif row > 5 and (row + col) % 2 == 1:
                    self.board[row].append(Piece(row, col, RED))   # RED starts at rows 6–9
                else:
                    self.board[row].append(0)

    def get_piece(self, row, col):
        return self.board[row][col]

    def can_capture(self, piece):
        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                current_row = piece.row + dr
                current_col = piece.col + dc
                while 0 <= current_row < ROWS and 0 <= current_col < COLS:
                    current_piece = self.get_piece(current_row, current_col)
                    if current_piece == 0:
                        current_row += dr
                        current_col += dc
                        continue
                    if current_piece.color == piece.color:
                        break
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if 0 <= next_row < ROWS and 0 <= next_col < COLS and self.get_piece(next_row, next_col) == 0:
                        return True
                    break
            return False

        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            mid_row = piece.row + dr
            mid_col = piece.col + dc
            end_row = piece.row + 2 * dr
            end_col = piece.col + 2 * dc
            if (0 <= mid_row < ROWS and 0 <= mid_col < COLS and
                0 <= end_row < ROWS and 0 <= end_col < COLS):
                mid_piece = self.get_piece(mid_row, mid_col)
                end_piece = self.get_piece(end_row, end_col)
                if mid_piece != 0 and mid_piece.color != piece.color and end_piece == 0:
                    return True
        return False

    def any_piece_can_capture(self, color):
        """Check if any piece of the given color can capture."""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.get_piece(row, col)
                if piece != 0 and piece.color == color and self.can_capture(piece):
                    return True
        return False

    def get_max_captures(self, color):
        """Find the maximum number of captures possible for any piece of the given color."""
        max_captures = 0
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.get_piece(row, col)
                if piece != 0 and piece.color == color:
                    sequences = self._get_all_capture_sequences(piece, piece.row, piece.col, set(), set())
                    if sequences:
                        max_captures = max(max_captures, max(len(seq[1]) for seq in sequences))
        return max_captures

    def valid_move(self, piece, dest_row, dest_col):
        valid_moves = self.get_valid_moves(piece)
        if (dest_row, dest_col) in valid_moves:
            captured = []
            visited = [(dest_row, dest_col)]  # List to store path
            if self.any_piece_can_capture(piece.color):
                _, captured, visited = self._check_capture_path(
                    piece, piece.row, piece.col, dest_row, dest_col, [], [])
            return True, captured, visited
        return False, [], []

    def _check_capture_path(self, piece, current_row, current_col, dest_row, dest_col, captured_pieces, visited):
        if current_row == dest_row and current_col == dest_col:
            return len(captured_pieces) > 0, captured_pieces, visited + [(current_row, current_col)]

        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

        for dr, dc in directions:
            if piece.king:
                new_row = current_row + dr
                new_col = current_col + dc
                while 0 <= new_row < ROWS and 0 <= new_col < COLS:
                    current_piece = self.get_piece(new_row, new_col)
                    if current_piece == 0:
                        new_row += dr
                        new_col += dc
                        continue
                    if current_piece.color == piece.color:
                        break
                    if (new_row, new_col) not in captured_pieces:
                        next_row = new_row + dr
                        next_col = new_col + dc
                        while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                            if self.get_piece(next_row, next_col) != 0:
                                break
                            if (next_row, next_col) not in visited:
                                new_captured = captured_pieces + [(new_row, new_col)]
                                new_visited = visited + [(next_row, next_col)]
                                result, final_captured, final_visited = self._check_capture_path(
                                    piece, next_row, next_col, dest_row, dest_col,
                                    new_captured, new_visited)
                                if result:
                                    return True, final_captured, final_visited
                            next_row += dr
                            next_col += dc
                    break
            else:
                new_row = current_row + dr
                new_col = current_col + dc
                if not (0 <= new_row < ROWS and 0 <= new_col < COLS):
                    continue
                mid_row = current_row + dr//2
                mid_col = current_col + dc//2
                if self.get_piece(new_row, new_col) != 0:
                    continue
                piece_to_capture = self.get_piece(mid_row, mid_col)
                if (piece_to_capture == 0 or 
                    piece_to_capture.color == piece.color or 
                    (mid_row, mid_col) in captured_pieces):
                    continue
                new_captured = captured_pieces + [(mid_row, mid_col)]
                new_visited = visited + [(new_row, new_col)]
                result, final_captured, final_visited = self._check_capture_path(
                    piece, new_row, new_col, dest_row, dest_col, new_captured, new_visited)
                if result:
                    return True, final_captured, final_visited
        return False, captured_pieces, visited

    def get_valid_moves(self, piece):
        if self.any_piece_can_capture(piece.color):
            if not self.can_capture(piece):
                return set()  # Block moves for pieces that cannot capture
            # Get all capture sequences and filter for maximum captures
            sequences = self._get_all_capture_sequences(piece, piece.row, piece.col, set(), set())
            if not sequences:
                return set()
            max_captures = self.get_max_captures(piece.color)
            valid_moves = set()
            for dest, captured, _ in sequences:
                if len(captured) == max_captures:
                    valid_moves.add(dest)
            return valid_moves
        # No captures available, allow simple moves
        valid_moves = set()
        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                row, col = piece.row + dr, piece.col + dc
                while 0 <= row < ROWS and 0 <= col < COLS:
                    if self.get_piece(row, col) == 0:
                        valid_moves.add((row, col))
                        row += dr
                        col += dc
                    else:
                        break
        else:
            # Restrict non-king moves: RED moves up (dr=-1), BLUE moves down (dr=1)
            directions = [(-1, -1), (-1, 1)] if piece.color == RED else [(1, -1), (1, 1)]
            for dr, dc in directions:
                row, col = piece.row + dr, piece.col + dc
                if 0 <= row < ROWS and 0 <= col < COLS and self.get_piece(row, col) == 0:
                    valid_moves.add((row, col))
        return valid_moves

    def _get_all_capture_sequences(self, piece, row, col, captured, visited):
        """Return list of (destination, captured_pieces, visited_squares) for all capture sequences."""
        sequences = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        found_capture = False

        for dr, dc in directions:
            if piece.king:
                r, c = row + dr, col + dc
                while 0 <= r < ROWS and 0 <= c < COLS and self.get_piece(r, c) == 0:
                    r += dr
                    c += dc
                if 0 <= r < ROWS and 0 <= c < COLS:
                    mid = self.get_piece(r, c)
                    if mid != 0 and mid.color != piece.color and (r, c) not in captured:
                        jump_r, jump_c = r + dr, c + dc
                        while 0 <= jump_r < ROWS and 0 <= jump_c < COLS and self.get_piece(jump_r, jump_c) == 0:
                            if (jump_r, jump_c) not in visited:
                                new_captured = captured | {(r, c)}
                                new_visited = visited | {(jump_r, jump_c)}
                                further_sequences = self._get_all_capture_sequences(
                                    piece, jump_r, jump_c, new_captured, new_visited)
                                if further_sequences:
                                    sequences.extend(further_sequences)
                                else:
                                    sequences.append(((jump_r, jump_c), new_captured, new_visited))
                                found_capture = True
                            jump_r += dr
                            jump_c += dc
            else:
                mid_r, mid_c = row + dr, col + dc
                jump_r, jump_c = row + 2 * dr, col + 2 * dc
                if 0 <= mid_r < ROWS and 0 <= mid_c < COLS and 0 <= jump_r < ROWS and 0 <= jump_c < COLS:
                    mid = self.get_piece(mid_r, mid_c)
                    if mid != 0 and mid.color != piece.color and (mid_r, mid_c) not in captured:
                        if self.get_piece(jump_r, jump_c) == 0 and (jump_r, jump_c) not in visited:
                            new_captured = captured | {(mid_r, mid_c)}
                            new_visited = visited | {(jump_r, jump_c)}
                            further_sequences = self._get_all_capture_sequences(
                                piece, jump_r, jump_c, new_captured, new_visited)
                            if further_sequences:
                                sequences.extend(further_sequences)
                            else:
                                sequences.append(((jump_r, jump_c), new_captured, new_visited))
                            found_capture = True

        return sequences

    def _can_capture_from(self, piece, row, col, captured):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            if piece.king:
                next_row = row + dr
                next_col = col + dc
                while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                    next_piece = self.get_piece(next_row, next_col)
                    if next_piece == 0:
                        next_row += dr
                        next_col += dc
                        continue
                    if next_piece.color == piece.color:
                        break
                    if (next_row, next_col) not in captured:
                        jump_row = next_row + dr
                        jump_col = next_col + dc
                        if 0 <= jump_row < ROWS and 0 <= jump_col < COLS and self.get_piece(jump_row, jump_col) == 0:
                            yield True
                    break
            else:
                next_row = row + (2 * dr)
                next_col = col + (2 * dc)
                mid_row = row + dr
                mid_col = col + dc
                if 0 <= next_row < ROWS and 0 <= next_col < COLS and self.get_piece(next_row, next_col) == 0:
                    piece_to_capture = self.get_piece(mid_row, mid_col)
                    if piece_to_capture != 0 and piece_to_capture.color != piece.color and (mid_row, mid_col) not in captured:
                        yield True

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def highlight_moves(self, win, valid_moves):
        for row, col in valid_moves:
            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE
            pygame.draw.circle(win, (0, 255, 0), 
                               (x + SQUARE_SIZE//2, y + SQUARE_SIZE//2), 
                               15)

    def move(self, piece, dest_row, dest_col):
        print(f"Attempting to move piece from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
        valid, captured_pieces, visited = self.valid_move(piece, dest_row, dest_col)
        
        if valid:
            pieces_to_remove = []
            for mid_row, mid_col in captured_pieces:
                piece_to_remove = self.get_piece(mid_row, mid_col)
                if piece_to_remove != 0:
                    pieces_to_remove.append(piece_to_remove)
            
            print(f"Removing captured pieces: {[(p.row, p.col) for p in pieces_to_remove]}")
            self.remove(pieces_to_remove)

            # Move through the capture path if it's a capture move
            if captured_pieces:
                for row, col in visited[:-1]:  # Exclude final destination
                    self.board[piece.row][piece.col] = 0
                    self.board[row][col] = piece
                    piece.move(row, col)
                # Final move
                self.board[piece.row][piece.col] = 0
                self.board[dest_row][dest_col] = piece
                piece.move(dest_row, dest_col)
            else:
                # Non-capture move
                self.board[piece.row][piece.col] = 0
                self.board[dest_row][dest_col] = piece
                piece.move(dest_row, dest_col)

            if not piece.king:
                if (piece.color == BLUE and dest_row == ROWS - 1) or (piece.color == RED and dest_row == 0):
                    piece.make_king()
                    print(f"Piece promoted to king at position ({dest_row}, {dest_col})")

            winner = self.get_winner()
            if winner is not None:
                print(f"Gra zakończona! Wygrał {'RED' if winner == RED else 'BLUE'}")
                return True

            return True  # Turn ends after move

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0

    def can_move(self, piece):
        return bool(self.get_valid_moves(piece))

    def get_winner(self):
        red_pieces = 0
        blue_pieces = 0
        red_can_move = False
        blue_can_move = False

        for row in range(ROWS):
            for col in range(COLS):
                piece = self.get_piece(row, col)
                if piece != 0:
                    if piece.color == RED:
                        red_pieces += 1
                        if not red_can_move and self.can_move(piece):
                            red_can_move = True
                    else:
                        blue_pieces += 1
                        if not blue_can_move and self.can_move(piece):
                            blue_can_move = True

        if red_pieces == 0:
            return BLUE
        elif blue_pieces == 0:
            return RED
        elif not red_can_move:
            return BLUE
        elif not blue_can_move:
            return RED
        return None

    def print_board(self):
        for row in range(ROWS):
            print([self.get_piece(row, col).color if self.get_piece(row, col) != 0 else 0 for col in range(COLS)])