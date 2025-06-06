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

        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                current_row = piece.row + dr
                current_col = piece.col + dc
                found_piece = False
                
                while 0 <= current_row < ROWS and 0 <= current_col < COLS:
                    current_piece = self.get_piece(current_row, current_col)
                    if current_piece != 0:
                        if current_piece.color == piece.color:
                            break
                        if found_piece:  # Już znaleźliśmy jeden pionek
                            break
                        found_piece = True
                    elif found_piece:  # Znaleźliśmy pionek i puste pole za nim
                        return True
                    current_row += dr
                    current_col += dc
            return False

        # Dla zwykłych pionków
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            mid_row = piece.row + dr
            mid_col = piece.col + dc
            end_row = piece.row + 2 * dr
            end_col = piece.col + 2 * dc

            if 0 <= end_row < ROWS and 0 <= end_col < COLS:
                mid_piece = self.get_piece(mid_row, mid_col)
                end_piece = self.get_piece(end_row, end_col)
                # Usunięto sprawdzanie czy zbijany pionek jest damką
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

        # Damka moves
        if piece.king:
            # Musi się poruszać po przekątnej
            if abs(row_diff) != abs(col_diff):
                return False, [], set()

            # Dla damki używamy _check_capture_path tak samo jak dla zwykłych pionków
            result, captured, visited = self._check_capture_path(piece, piece.row, piece.col, dest_row, dest_col, [], set())
            if result:
                return result, captured, visited

            # Jeśli nie ma bicia, sprawdź zwykły ruch
            if not self.can_capture(piece):
                # Sprawdź czy na drodze nie ma żadnych pionków
                step_row = 1 if row_diff > 0 else -1
                step_col = 1 if col_diff > 0 else -1
                current_row = piece.row + step_row
                current_col = piece.col + step_col

                while current_row != dest_row and current_col != dest_col:
                    if self.get_piece(current_row, current_col) != 0:
                        return False, [], set()
                    current_row += step_row
                    current_col += step_col

                return True, [], {(dest_row, dest_col)}

            return False, [], set()
        # Jeśli żaden warunek nie został spełniony
        return False, [], set()

    def _check_capture_path(self, piece, current_row, current_col, dest_row, dest_col, captured_pieces, visited):
        # Jeśli dotarliśmy do celu
        if current_row == dest_row and current_col == dest_col:
            return len(captured_pieces) > 0, captured_pieces, visited

        # Sprawdź wszystkie możliwe kierunki bicia
        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Damka może iść w każdym kierunku
        else:
            directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]  # Zwykły pionek tylko o 2 pola
        
        for dr, dc in directions:
            if piece.king:
                # Dla damki - szukamy pionków do zbicia w danym kierunku
                new_row = current_row + dr
                new_col = current_col + dc
                found_piece = False
                
                # Sprawdzaj daną przekątną
                while 0 <= new_row < ROWS and 0 <= new_col < COLS:
                    current_piece = self.get_piece(new_row, new_col)
                    
                    if current_piece != 0:
                        if current_piece.color == piece.color:
                            break  # Własny pionek - nie możemy go przeskoczyć
                        if (new_row, new_col) in captured_pieces:
                            break  # Ten pionek już został zbity
                        # Znaleźliśmy pionek do zbicia
                        found_piece = True
                        capture_pos = (new_row, new_col)
                        
                        # Sprawdź pola za znalezionym pionkiem
                        next_row = new_row + dr
                        next_col = new_col + dc
                        
                        while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                            if self.get_piece(next_row, next_col) != 0:
                                break  # Napotkaliśmy inny pionek
                                
                            if (next_row, next_col) not in visited:
                                # Próbujemy wykonać bicie i szukać kolejnych
                                new_captured = captured_pieces + [capture_pos]
                                new_visited = visited | {(next_row, next_col)}
                                
                                result, final_captured, final_visited = self._check_capture_path(
                                    piece, next_row, next_col, dest_row, dest_col,
                                    new_captured, new_visited)
                                    
                                if result:
                                    return True, final_captured, final_visited
                                    
                            next_row += dr
                            next_col += dc
                        break  # Kończymy sprawdzanie tego kierunku po znalezieniu pionka
                    
                    new_row += dr
                    new_col += dc
            else:
                # Dla zwykłego pionka - istniejąca logika
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
                new_visited = visited | {(new_row, new_col)}
                
                if (new_row, new_col) not in visited:
                    result, final_captured, final_visited = self._check_capture_path(
                        piece, new_row, new_col, dest_row, dest_col, new_captured, new_visited)
                    if result:
                        return True, final_captured, final_visited
                        
        return False, captured_pieces, visited

    def get_valid_moves(self, piece):
        valid_moves = set()  # Używamy set() aby uniknąć duplikatów
        
        if piece.king:
            # Sprawdź ruchy damki w każdym kierunku
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                current_row = piece.row + dr
                current_col = piece.col + dc
                
                # Sprawdź zwykłe ruchy (bez bicia)
                while (0 <= current_row < ROWS and 0 <= current_col < COLS and 
                    self.get_piece(current_row, current_col) == 0 and
                    not self.can_capture(piece)):
                    valid_moves.add((current_row, current_col))
                    current_row += dr
                    current_col += dc
        else:
            # Dla zwykłego pionka
            direction = -1 if piece.color == BLUE else 1
            moves = [(direction, -1), (direction, 1)]
            
            # Sprawdź zwykłe ruchy (bez bicia)
            for dr, dc in moves:
                new_row = piece.row + dr
                new_col = piece.col + dc
                if (0 <= new_row < ROWS and 0 <= new_col < COLS and 
                    self.get_piece(new_row, new_col) == 0 and
                    not self.can_capture(piece)):
                    valid_moves.add((new_row, new_col))
        
        # Sprawdź możliwe bicia (dla obu typów pionków)
        self._add_capture_moves(piece, piece.row, piece.col, set(), valid_moves)
        
        return valid_moves

    def _add_capture_moves(self, piece, row, col, captured, valid_moves):
        if piece.king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            current_row = row + dr
            current_col = col + dc
            
            while 0 <= current_row < ROWS and 0 <= current_col < COLS:
                current_piece = self.get_piece(current_row, current_col)
                if current_piece == 0:
                    if not piece.king:
                        break
                    current_row += dr
                    current_col += dc
                    continue
                    
                if current_piece.color == piece.color:
                    break
                    
                # Znaleziono pionek przeciwnika
                if (current_row, current_col) not in captured:
                    next_row = current_row + dr
                    next_col = current_col + dc
                    
                    while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                        if self.get_piece(next_row, next_col) != 0:
                            break
                        valid_moves.add((next_row, next_col))
                        if not piece.king:
                            break
                        next_row += dr
                        next_col += dc
                break
                
                current_row += dr
                current_col += dc

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
                            15)  # Zielone kółka pokazujące możliwe ruchy
            
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

            # Promocja na damkę według zasad warcabów polskich:
            # - Czerwony pionek dociera do rzędu 0
            # - Niebieski pionek dociera do rzędu 9 (ROWS-1)
            # - Pionek kończy ruch na linii promocji
            if not piece.king:  # Sprawdzamy tylko dla zwykłych pionków
                if (piece.color == BLUE and dest_row == 0) or (piece.color == RED and dest_row == ROWS - 1):
                    piece.make_king()
                    print(f"Piece promoted to king at position ({dest_row}, {dest_col})")
                    # Po promocji na damkę, nie można już wykonać kolejnego bicia w tym samym ruchu
                    return True
                
            # Sprawdź czy gra się zakończyła
            winner = self.get_winner()
            if winner is not None:
                print(f"Gra zakończona! Wygrał {'CZERWONY' if winner == RED else 'NIEBIESKI'}")
                return True
            
            # Sprawdzenie możliwości kolejnego bicia
            if self.can_capture(piece):
                print("Możliwe kolejne bicie. Gracz musi kontynuować.")
                return "CONTINUE"

            return True
        return False

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0

    def can_move(self, piece):
        # Sprawdź możliwość bicia
        if self.can_capture(piece):
            return True
            
        # Sprawdź możliwe zwykłe ruchy
        if not piece.king:
            # Dla zwykłych pionków sprawdź ruchy do przodu
            direction = -1 if piece.color == BLUE else 1
            moves = [(direction, -1), (direction, 1)]
        else:
            # Dla damki sprawdź wszystkie kierunki
            moves = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Sprawdź każdy możliwy ruch
        for dr, dc in moves:
            new_row = piece.row + dr
            new_col = piece.col + dc
            if 0 <= new_row < ROWS and 0 <= new_col < COLS:
                if self.get_piece(new_row, new_col) == 0:
                    return True
                    
        return False

    def get_winner(self):
        red_pieces = 0
        blue_pieces = 0
        red_can_move = False
        blue_can_move = False

        # Sprawdź wszystkie pionki na planszy
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.get_piece(row, col)
                if piece != 0:
                    # Zlicz pionki każdego koloru i sprawdź możliwość ruchu
                    if piece.color == RED:
                        red_pieces += 1
                        if not red_can_move and self.can_move(piece):
                            red_can_move = True
                    else:  # BLUE
                        blue_pieces += 1
                        if not blue_can_move and self.can_move(piece):
                            blue_can_move = True

        # Sprawdź warunki końca gry
        if red_pieces == 0:
            return BLUE  # Niebieski wygrał
        elif blue_pieces == 0:
            return RED   # Czerwony wygrał
        elif not red_can_move:
            return BLUE  # Czerwony jest zablokowany, niebieski wygrał
        elif not blue_can_move:
            return RED   # Niebieski jest zablokowany, czerwony wygrał
        else:
            return None  # Gra trwa nadal