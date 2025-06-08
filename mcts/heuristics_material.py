import random
import copy
import math
from checkers.board import Board
from checkers.constants import RED, BLUE, ROWS, COLS

class Node:
    def __init__(self, board, move=None, parent=None, player=None):
        self.board = board
        self.move = move  # Tuple (piece, dest_row, dest_col)
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = []
        self.player = player

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

class MCTSMaterialHeuristic:
    def __init__(self, board, player, iterations=30):
        self.root_board = board
        self.player = player
        self.opponent = BLUE if player == RED else RED
        self.iterations = iterations
        self.material_weight = 0.5  # Weight for material heuristic
        self.sigmoid_k = 1.0  # Sigmoid steepness for normalization
        self.pawn_value = 1.0  # Value of a regular pawn
        self.king_value = 10.0  # Very high value for a king

    def search(self):
        root = Node(copy.deepcopy(self.root_board), player=self.player)
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
        max_captures = node.board.get_max_captures(node.player)

        for row in range(ROWS):
            for col in range(COLS):
                piece = node.board.get_piece(row, col)
                if piece != 0 and piece.color == node.player:
                    valid_moves = node.board.get_valid_moves(piece)
                    for dest_row, dest_col in valid_moves:
                        temp_board = copy.deepcopy(node.board)
                        temp_piece = temp_board.get_piece(piece.row, piece.col)
                        valid, captured, _ = temp_board.valid_move(temp_piece, dest_row, dest_col)
                        if valid and captured and len(captured) == max_captures:
                            capture_moves.append((piece, dest_row, dest_col))
                            has_captures = True
                        elif valid and not has_captures:
                            moves.append((piece, dest_row, dest_col))

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

        new_board.move(new_piece, dest_row, dest_col)
        new_node = Node(new_board, move, node, player=self.opponent)
        self._initialize_untried_moves(new_node)
        node.add_child(new_node)
        return new_node

    def _simulate(self, node):
        current_board = copy.deepcopy(node.board)
        current_player = node.player
        max_simulation_steps = 30
        seen_states = set()

        for step in range(max_simulation_steps):
            winner = current_board.get_winner()
            if winner is not None:
                return 1.0 if winner == self.player else 0.0

            board_state = tuple(
                tuple(current_board.get_piece(row, col).color if current_board.get_piece(row, col) != 0 else 0
                      for col in range(COLS))
                for row in range(ROWS)
            )
            if board_state in seen_states:
                return 0.5
            seen_states.add(board_state)

            capture_moves = []
            normal_moves = []
            max_captures = current_board.get_max_captures(current_player)

            for row in range(ROWS):
                for col in range(COLS):
                    piece = current_board.get_piece(row, col)
                    if piece != 0 and piece.color == current_player:
                        valid_moves = current_board.get_valid_moves(piece)
                        for dest_row, dest_col in valid_moves:
                            temp_board = copy.deepcopy(current_board)
                            temp_piece = temp_board.get_piece(piece.row, piece.col)
                            valid, captured, _ = temp_board.valid_move(temp_piece, dest_row, dest_col)
                            if valid and captured and len(captured) == max_captures:
                                capture_moves.append((piece, dest_row, dest_col))
                            elif valid and not max_captures:
                                normal_moves.append((piece, dest_row, dest_col))

            moves = capture_moves if capture_moves else normal_moves
            if not moves:
                return 0.0 if current_player == self.player else 1.0

            piece, dest_row, dest_col = random.choice(moves)
            current_board.move(piece, dest_row, dest_col)
            current_player = BLUE if current_player == RED else RED

        return self._evaluate_board(current_board)

    def _evaluate_board(self, board):
        """Evaluate board using material advantage heuristic, with high value for kings."""
        player_material = 0.0
        opponent_material = 0.0

        for row in range(ROWS):
            for col in range(COLS):
                piece = board.get_piece(row, col)
                if piece != 0:
                    value = self.king_value if piece.king else self.pawn_value
                    if piece.color == self.player:
                        player_material += value
                    else:
                        opponent_material += value

        # Material heuristic: (player_pawns + 10*player_kings) - (opponent_pawns + 10*opponent_kings)
        material_score = player_material - opponent_material
        # Normalize material score (max ~20 pawns + 20 kings*10 = 220 per player, total diff ~440)
        material_max = 440.0
        material_normalized = material_score / material_max if material_max != 0 else 0.0

        # Apply sigmoid to map to [0, 1]
        score = 1.0 / (1.0 + math.exp(-self.sigmoid_k * self.material_weight * material_normalized))
        return score

    def _backpropagate(self, node, result):
        while node is not None:
            node.update(result if node.player == self.player else 1.0 - result)
            node = node.parent