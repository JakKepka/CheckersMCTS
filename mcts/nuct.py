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
        self.nested_mcts_score = 0  # Store result from nested MCTS
        self.untried_moves = []
        self.player = None

    def add_child(self, child_node):
        self.children.append(child_node)
        if child_node.move in self.untried_moves:
            self.untried_moves.remove(child_node.move)

    def update(self, result, nested_score=0):
        self.visits += 1
        self.wins += result
        self.nested_mcts_score += nested_score  # Accumulate nested MCTS score

    def ucb1_nested(self, parent_visits, exploration_constant=math.sqrt(2), gamma=0.5):
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration = exploration_constant * math.sqrt(math.log(parent_visits) / self.visits)
        nested_term = gamma * (self.nested_mcts_score / self.visits if self.visits > 0 else 0)
        return exploitation + exploration + nested_term

class MCTSNESTED:
    def __init__(self, board, player, iterations=300, nested_iterations=50):
        self.root_board = board
        self.player = player
        self.opponent = BLUE if player == RED else RED
        self.iterations = iterations
        self.nested_iterations = nested_iterations  # Number of iterations for nested MCTS
        self.exploration_constant = math.sqrt(2)  # c in UCT formula
        self.gamma = 0.5  # Weight for nested MCTS term

    def search(self):
        root = Node(copy.deepcopy(self.root_board))
        root.player = self.player
        self._initialize_untried_moves(root)

        if not root.untried_moves:
            return None  # No valid moves available

        for _ in range(self.iterations):
            node = self._select(root)
            result, nested_score = self._simulate(node)
            self._backpropagate(node, result, nested_score)

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
                        temp_board = copy.deepcopy(node.board)
                        temp_piece = temp_board.get_piece(piece.row, piece.col)
                        valid, captured, _ = temp_board.valid_move(temp_piece, dest_row, dest_col)
                        if valid and captured:
                            capture_moves.append((piece, dest_row, dest_col))
                            has_captures = True
                        else:
                            moves.append((piece, dest_row, dest_col))

        node.untried_moves = capture_moves if has_captures else moves

    def _select(self, node):
        while node.children and not node.untried_moves:
            node = max(node.children, key=lambda c: c.ucb1_nested(node.visits, self.exploration_constant, self.gamma))
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
        # Instead of random simulation, run a nested MCTS
        nested_mcts = MCTS(copy.deepcopy(node.board), node.player, iterations=self.nested_iterations)
        nested_best_move = nested_mcts.search()
        
        # If no move is returned, evaluate the board directly
        if nested_best_move is None:
            score = self._evaluate_board(node.board)
            return score, score
        
        # Simulate one step with the best move from nested MCTS
        piece, dest_row, dest_col = nested_best_move
        sim_board = copy.deepcopy(node.board)
        sim_piece = sim_board.get_piece(piece.row, piece.col)
        
        if sim_piece == 0 or sim_piece.color != node.player:
            score = self._evaluate_board(node.board)
            return score, score
        
        result = sim_board.move(sim_piece, dest_row, dest_col)
        score = self._evaluate_board(sim_board)
        
        # Return both the simulation result and the nested MCTS score
        return score, score

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

    def _backpropagate(self, node, result, nested_score):
        while node is not None:
            node.update(result, nested_score)
            result = 1.0 - result
            nested_score = 1.0 - nested_score  # Invert for opponent
            node = node.parent