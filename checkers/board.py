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
                        
                    # Znaleziono pionek przeciwnika, sprawdź czy jest pole za nim
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if 0 <= next_row < ROWS and 0 <= next_col < COLS:
                        if self.get_piece(next_row, next_col) == 0:
                            return True
                    break
                    
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
        # Pobierz wszystkie możliwe ruchy dla danego pionka
        valid_moves = self.get_valid_moves(piece)
        
        # Jeśli punkt docelowy jest w zbiorze możliwych ruchów
        if (dest_row, dest_col) in valid_moves:
            # Znajdź captured_pieces dla tego ruchu
            captured = []
            if self.can_capture(piece):
                # Jeśli to bicie, znajdź zbite pionki
                current_row, current_col = piece.row, piece.col
                # Użyj _check_capture_path do znalezienia zbitych pionków
                _, captured, visited = self._check_capture_path(
                    piece, current_row, current_col, dest_row, dest_col, [], set())
            else:
                # Jeśli to zwykły ruch, nie ma zbitych pionków
                visited = {(dest_row, dest_col)}
                
            return True, captured, visited
            
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
                        # Znaleziono pionek do zbicia, sprawdź pola za nim
                        next_row = new_row + dr
                        next_col = new_col + dc
                        
                        # Sprawdź wszystkie pola za zbitym pionkiem
                        while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                            if self.get_piece(next_row, next_col) != 0:
                                break
                                
                            if (next_row, next_col) not in visited:
                                new_captured = captured_pieces + [(new_row, new_col)]
                                new_visited = visited | {(next_row, next_col)}
                                
                                result, final_captured, final_visited = self._check_capture_path(
                                    piece, next_row, next_col, dest_row, dest_col,
                                    new_captured, new_visited)
                                    
                                if result:
                                    return True, final_captured, final_visited
                                    
                            next_row += dr
                            next_col += dc
                    break
                    
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
        # Sprawdzamy wszystkie możliwe kierunki
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Dla każdego kierunku
        for dr, dc in directions:
            if piece.king:
                next_row = row + dr
                next_col = col + dc
                
                # Sprawdzaj całą przekątną
                while 0 <= next_row < ROWS and 0 <= next_col < COLS:
                    next_piece = self.get_piece(next_row, next_col)
                    
                    if next_piece == 0:
                        next_row += dr
                        next_col += dc
                        continue
                        
                    if next_piece.color == piece.color:
                        break
                        
                    if (next_row, next_col) not in captured:
                        # Znaleziono pionek do zbicia, sprawdź pola za nim
                        jump_row = next_row + dr
                        jump_col = next_col + dc
                        
                        while 0 <= jump_row < ROWS and 0 <= jump_col < COLS:
                            if self.get_piece(jump_row, jump_col) != 0:
                                break
                                
                            # Znaleziono pole do lądowania
                            new_captured = captured | {(next_row, next_col)}
                            
                            # Rekurencyjnie sprawdź możliwość kolejnych bić z nowej pozycji
                            self._add_capture_moves(piece, jump_row, jump_col, new_captured, valid_moves)
                            
                            # Jeśli nie ma więcej bić, dodaj tę pozycję
                            if not any(self._can_capture_from(piece, jump_row, jump_col, new_captured)):
                                valid_moves.add((jump_row, jump_col))
                                
                            if not piece.king:
                                break
                            jump_row += dr
                            jump_col += dc
                    break
                    
                    next_row += dr
                    next_col += dc
            else:
                # Dla zwykłego pionka - sprawdzamy bicie o 2 pola
                next_row = row + (2 * dr)
                next_col = col + (2 * dc)
                mid_row = row + dr
                mid_col = col + dc
                
                if (0 <= next_row < ROWS and 0 <= next_col < COLS and
                    self.get_piece(next_row, next_col) == 0):
                    
                    piece_to_capture = self.get_piece(mid_row, mid_col)
                    if (piece_to_capture != 0 and 
                        piece_to_capture.color != piece.color and 
                        (mid_row, mid_col) not in captured):
                        
                        # Znaleziono możliwe bicie
                        new_captured = captured | {(mid_row, mid_col)}
                        
                        # Rekurencyjnie sprawdź kolejne bicia
                        self._add_capture_moves(piece, next_row, next_col, new_captured, valid_moves)
                        
                        # Jeśli nie ma więcej bić, dodaj tę pozycję
                        if not any(self._can_capture_from(piece, next_row, next_col, new_captured)):
                            valid_moves.add((next_row, next_col))

    def _can_capture_from(self, piece, row, col, captured):
        """Pomocnicza funkcja sprawdzająca możliwość bicia z danej pozycji"""
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
                        if (0 <= jump_row < ROWS and 0 <= jump_col < COLS and 
                            self.get_piece(jump_row, jump_col) == 0):
                            yield True
                    break
                    next_row += dr
                    next_col += dc
            else:
                next_row = row + (2 * dr)
                next_col = col + (2 * dc)
                mid_row = row + dr
                mid_col = col + dc
                
                if (0 <= next_row < ROWS and 0 <= next_col < COLS and
                    self.get_piece(next_row, next_col) == 0):
                    piece_to_capture = self.get_piece(mid_row, mid_col)
                    if (piece_to_capture != 0 and 
                        piece_to_capture.color != piece.color and 
                        (mid_row, mid_col) not in captured):
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
                            15)  # Zielone kółka pokazujące możliwe ruchy
            
    def move(self, piece, dest_row, dest_col):
        print(f"Attempting to move piece from ({piece.row}, {piece.col}) to ({dest_row}, {dest_col})")
        valid, captured_pieces, visited = self.valid_move(piece, dest_row, dest_col)
        
        if valid:
            # Zamień koordynaty zbitych pionków na obiekty Piece
            pieces_to_remove = []
            for mid_row, mid_col in captured_pieces:
                piece_to_remove = self.get_piece(mid_row, mid_col)
                if piece_to_remove != 0:
                    pieces_to_remove.append(piece_to_remove)
            
            print(f"Captured pieces to remove: {[(p.row, p.col) for p in pieces_to_remove]}")
            # Usuń zbite pionki
            self.remove(pieces_to_remove)

            # Przesunięcie pionka na końcową pozycję
            self.board[piece.row][piece.col] = 0
            self.board[dest_row][dest_col] = piece
            piece.move(dest_row, dest_col)

            # Promocja na damkę według zasad warcabów polskich:
            # - Czerwony pionek dociera do rzędu 0
            # - Niebieski pionek dociera do rzędu 9 (ROWS-1)
            # - Pionek kończy ruch na linii promocji
            if not piece.king:  
                if (piece.color == BLUE and dest_row == 0) or (piece.color == RED and dest_row == ROWS - 1):
                    piece.make_king()
                    print(f"Piece promoted to king at position ({dest_row}, {dest_col})")
                    return True
                    
            winner = self.get_winner()
            if winner is not None:
                print(f"Gra zakończona! Wygrał {'CZERWONY' if winner == RED else 'NIEBIESKI'}")
                return True
                
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