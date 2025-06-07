import random
import copy
from checkers.board import Board
from checkers.constants import RED, BLUE, ROWS, COLS
import math

class Node:
    def __init__(self, board, move=None, parent=None):
        self.board = board
        self.move = move  # Tuple (piece, dest_row, dest_col)
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = []
        self.player = None

    def add_child(self, child_node):
        self.children.append(child_node)
        if child_node.move in self.untried_moves:
            self.untried_moves.remove(child_node.move)

    def update(self, result):
        self.visits += 1
        self.wins += result

    def ucb1(self, parent_visits):
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + math.sqrt(2 * math.log(parent_visits) / self.visits)

class MCTS:
    def __init__(self, board, player, iterations=300):
        self.root_board = board
        self.player = player
        self.opponent = BLUE if player == RED else RED
        self.iterations = iterations

    def search(self):
        root = Node(copy.deepcopy(self.root_board))
        root.player = self.player
        self._initialize_untried_moves(root)

        if not root.untried_moves:
            return None  # No valid moves available

        for _ in range(self.iterations):
            node = self._select(root)
            result = self._simulate(node)
            self._backpropagate(node, result)

        best_child = max(root.children, key=lambda c: c.visits) if root.children else None
        return best_child.move if best_child else None

    def _initialize_untried_moves(self, node):
        """Initialize all possible moves for the current player, prioritizing captures."""
        moves = []
        capture_moves = []
        has_captures = False

        for row in range(ROWS):
            for col in range(COLS):
                piece = node.board.get_piece(row, col)
                if piece != 0 and piece.color == self.player:
                    valid_moves = node.board.get_valid_moves(piece)
                    for dest_row, dest_col in valid_moves:
                        # Check if move is a capture
                        temp_board = copy.deepcopy(node.board)
                        temp_piece = temp_board.get_piece(piece.row, piece.col)
                        valid, captured, _ = temp_board.valid_move(temp_piece, dest_row, dest_col)
                        if valid and captured:
                            capture_moves.append((piece, dest_row, dest_col))
                            has_captures = True
                        else:
                            moves.append((piece, dest_row, dest_col))

        # If captures exist, only include capture moves (Polish Checkers rule)
        node.untried_moves = capture_moves if has_captures else moves

    def _select(self, node):
        while node.children and not node.untried_moves:
            node = max(node.children, key=lambda c: c.ucb1(node.visits))
        return self._expand(node) if node.untried_moves else node

    def _expand(self, node):
        if not node.untried_moves:
            return node
        move = random.choice(node.untried_moves)
        piece, dest_row, dest_col = move
        new_board = copy.deepcopy(node.board)
        new_piece = new_board.get_piece(piece.row, piece.col)
        
        if new_piece == 0 or new_piece.color != node.player:
            node.untried_moves.remove(move)
            return node

        result = new_board.move(new_piece, dest_row, dest_col)
        new_node = Node(new_board, move, node)
        if result == "CONTINUE":
            new_node.player = node.player
        else:
            new_node.player = self.opponent
        self._initialize_untried_moves(new_node)
        node.add_child(new_node)
        return new_node

    def _simulate(self, node):
        current_board = copy.deepcopy(node.board)
        current_player = node.player
        max_simulation_steps = 30  # Further reduced to prevent loops
        seen_states = set()

        for step in range(max_simulation_steps):
            winner = current_board.get_winner()
            if winner is not None:
                return 1.0 if winner == self.player else 0.0

            # Serialize board state
            board_state = tuple(
                tuple(current_board.get_piece(row, col).color if current_board.get_piece(row, col) != 0 else 0
                      for col in range(COLS))
                for row in range(ROWS)
            )
            if board_state in seen_states:
                return 0.5
            seen_states.add(board_state)

            # Get moves, prioritizing captures
            capture_moves = []
            normal_moves = []
            for row in range(ROWS):
                for col in range(COLS):
                    piece = current_board.get_piece(row, col)
                    if piece != 0 and piece.color == current_player:
                        valid_moves = current_board.get_valid_moves(piece)
                        for dest_row, dest_col in valid_moves:
                            temp_board = copy.deepcopy(current_board)
                            temp_piece = temp_board.get_piece(piece.row, piece.col)
                            valid, captured, _ = temp_board.valid_move(temp_piece, dest_row, dest_col)
                            if valid and captured:
                                capture_moves.append((piece, dest_row, dest_col))
                            else:
                                normal_moves.append((piece, dest_row, dest_col))

            moves = capture_moves if capture_moves else normal_moves
            if not moves:
                return 0.0 if current_player == self.player else 1.0

            piece, dest_row, dest_col = random.choice(moves)
            new_piece = current_board.get_piece(piece.row, piece.col)
            result = current_board.move(new_piece, dest_row, dest_col)

            if result != "CONTINUE":
                current_player = BLUE if current_player == RED else RED

        return self._evaluate_board(current_board)

    def _evaluate_board(self, board):
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

        player_score = (red_pieces + 2 * red_kings) if self.player == RED else (blue_pieces + 2 * blue_kings)
        opponent_score = (blue_pieces + 2 * blue_kings) if self.player == RED else (red_pieces + 2 * red_kings)
        total = player_score + opponent_score

        return 0.5 if total == 0 else player_score / total

    def _backpropagate(self, node, result):
        while node is not None:
            node.update(result)
            result = 1.0 - result
            node = node.parent