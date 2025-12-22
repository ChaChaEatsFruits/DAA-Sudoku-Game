# A priority-queue-based greedy approach to Sudoku works by always selecting the next cell to fill based on how constrained it is,
# which is determined dynamically as the puzzle evolves.
# At the start, every empty cell is analyzed to compute the number of possible candidate digits it can take,
# and each cell is inserted into a min-heap (priority queue) keyed by its candidate count,
# so the most constrained cell (the one with the fewest legal values) is always extracted first.
# The algorithm repeatedly pops the top cell from the priority queue, assigns one of its valid digits (often chosen with an additional heuristic such as least-constraining value),
# updates the Sudoku board, and then recalculates candidate sets for all affected neighboring cells in the same row, column, and subgrid.
# Those neighbors have their priority values updated in the queue, ensuring the queue always reflects the current state of constraints.
# This greedy process continues, filling the most restricted cell at every step.
# While this does not guarantee a complete solution without fallback search,
# the priority queue efficiently enforces the heuristic that making the tightest forced decisions first reduces branching and dramatically improves solver performance.



import tkinter as tk
from tkinter import messagebox
import heapq
import random
import copy

class SudokuDuel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Duel — User vs Greedy AI")
        self.root.geometry("600x700")
        self.root.configure(bg="#ffffff")
        
        # Game state
        self.board = [[0]*9 for _ in range(9)]
        self.initial_board = [[0]*9 for _ in range(9)]
        self.current_turn = "user"
        self.cells = [[None]*9 for _ in range(9)]
        self.cell_colors = [[None]*9 for _ in range(9)]
        
        # Create GUI
        self.create_widgets()
        self.new_game()

        #initialise priority queue
        self.pq=[]
    
    def create_widgets(self):
        # Status bar
        self.status_label = tk.Label(self.root, text="User's Turn", 
                                     font=("Helvetica", 14, "bold"),
                                     bg="#ffffff", fg="black")
        self.status_label.pack(pady=10)
        
        # Board frame
        board_frame = tk.Frame(self.root, bg="#d0d0d0", bd=4, relief=tk.SUNKEN)
        board_frame.pack(pady=10)
        
        # Create 9x9 grid
        for i in range(9):
            for j in range(9):
                # Determine border thickness
                borderwidth = 1
                if i % 3 == 0 and i != 0:
                    pady_top = 2
                else:
                    pady_top = 0
                if j % 3 == 0 and j != 0:
                    padx_left = 2
                else:
                    padx_left = 0
                
                cell = tk.Entry(board_frame, width=3, font=("Helvetica", 20, "bold"),
                               justify="center", bd=1, relief=tk.SOLID,
                               bg="white", disabledbackground="white",
                               disabledforeground="black")
                cell.grid(row=i, column=j, padx=(padx_left, 0), pady=(pady_top, 0))
                cell.bind("<KeyRelease>", lambda e, r=i, c=j: self.on_cell_edit(r, c))
                self.cells[i][j] = cell
        
        # Button frame
        button_frame = tk.Frame(self.root, bg="#ffffff")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="New Game", command=self.new_game,
                 font=("Helvetica", 12), bg="#4CAF50", fg="white",
                 padx=10, pady=5).grid(row=0, column=0, padx=5)
        
        tk.Button(button_frame, text="Hint", command=self.show_hint,
                 font=("Helvetica", 12), bg="#2196F3", fg="white",
                 padx=10, pady=5).grid(row=0, column=1, padx=5)
        
        tk.Button(button_frame, text="AI Play", command=self.ai_play,
                 font=("Helvetica", 12), bg="#f44336", fg="white",
                 padx=10, pady=5).grid(row=0, column=2, padx=5)
        
        tk.Button(button_frame, text="Reset", command=self.reset_board,
                 font=("Helvetica", 12), bg="#FF9800", fg="white",
                 padx=10, pady=5).grid(row=0, column=3, padx=5)
    
    def generate_puzzle(self):
        """Generate a simple Sudoku puzzle"""
       # Step 1: Generate a fully solved valid board instantly
        full_board = self.get_base_pattern()
        
        # Step 2: Shuffle it to create a unique game
        full_board = self.shuffle_board(full_board)
        
        # Save this as the solution
        self.board = copy.deepcopy(full_board)
        
        # Remove numbers to create puzzle
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        
        # Remove about 40-45 cells
        remove_count = random.randint(40, 45)
        for i in range(remove_count):
            r, c = cells[i]
            self.board[r][c] = 0
        
        return self.board
    
    def get_base_pattern(self):
        """
        Generates a static valid Sudoku board using a mathematical pattern.
        Formula: (i * 3 + i // 3 + j) % 9 + 1
        This creates a valid board by shifting rows.
        """
        def pattern(r, c): return (3 * (r % 3) + r // 3 + c) % 9
        
        # Randomize the mapping of numbers (e.g. 1->7, 2->4)
        # This is the "Relabel Numbers" transformation
        nums = list(range(1, 10))
        random.shuffle(nums)
        
        # Build the board
        board = [[nums[pattern(r, c)] for c in range(9)] for r in range(9)]
        return board

    def shuffle_board(self, board):
        """
        Apply valid transformations to randomize the board while keeping it solved.
        """
        # 1. Shuffle Rows within each "Band" of 3 rows
        # Band 0: Rows 0,1,2 | Band 1: Rows 3,4,5 | Band 2: Rows 6,7,8
        for i in range(0, 9, 3):
            # Get the three rows in this band
            block = board[i:i+3]
            random.shuffle(block)
            board[i:i+3] = block
            
        # 2. Shuffle Columns within each "Stack" of 3 columns
        # To do this easily, we transpose the matrix (rows become cols), 
        # shuffle rows (which are effectively cols), then transpose back.
        board = list(map(list, zip(*board))) # Transpose
        for i in range(0, 9, 3):
            block = board[i:i+3]
            random.shuffle(block)
            board[i:i+3] = block
        board = list(map(list, zip(*board))) # Transpose back

        # 3. Shuffle "Row Bands" (Swap rows 0-2 with rows 3-5, etc.)
        # Groups of 3 rows
        bands = [board[i:i+3] for i in range(0, 9, 3)]
        random.shuffle(bands)
        # Flatten back into a 9x9 board
        board = [row for band in bands for row in band]
        
        # 4. Shuffle "Column Stacks" (Swap cols 0-2 with cols 3-5, etc.)
        # Transpose, shuffle bands, transpose back
        board = list(map(list, zip(*board))) 
        stacks = [board[i:i+3] for i in range(0, 9, 3)]
        random.shuffle(stacks)
        board = [row for stack in stacks for row in stack]
        board = list(map(list, zip(*board)))
        
        return board




    
    # def solve_greedy(self, board):
    #     """
    #     Fill board using a greedy heuristic (no backtracking).
    #     Chooses the empty cell with the fewest valid options and fills it.
    #     """
    #     """At each step, fill the empty cell that has the fewest valid choices (MRV heuristic), and pick one valid number immediately."""

    #     while True:
    #         best_cell = None
    #         best_candidates = None

    #         # Find the empty cell with minimum remaining values (MRV)
    #         for row in range(9):
    #             for col in range(9):
    #                 if board[row][col] == 0:
    #                     candidates = [
    #                         num for num in range(1, 10)
    #                         if self.is_valid(board, row, col, num)
    #                     ]

    #                     if not candidates:
    #                         return False  # Greedy choice failed

    #                     if best_cell is None or len(candidates) < len(best_candidates):
    #                         best_cell = (row, col)
    #                         best_candidates = candidates

    #         # No empty cells left → solved
    #         if best_cell is None:
    #             return True

    #         row, col = best_cell

    #         # Greedy choice: pick the first (or random) valid number
    #         board[row][col] = best_candidates[0]
    
    def find_empty(self, board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None
    
    def is_valid(self, board, row, col, num):
        # Check row
        if num in board[row]:
            return False
        
        # Check column
        if num in [board[i][col] for i in range(9)]:
            return False
        
        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False
        
        return True
    
    def get_candidates(self, board, row, col):
        """Get all valid candidates for a cell"""
        if board[row][col] != 0:
            return set()
        
        candidates = set(range(1, 10))
        
        # Remove row conflicts
        candidates -= set(board[row])
        
        # Remove column conflicts
        candidates -= set(board[i][col] for i in range(9))
        
        # Remove box conflicts
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                candidates.discard(board[i][j])
        
        return candidates
    
    def build_priority_queue(self):
        """Build priority queue of cells by constraint"""
        pq = []
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    candidates = self.get_candidates(self.board, i, j)
                    if candidates:
                        # Priority: fewer candidates = higher priority (lower number)
                        heapq.heappush(pq, (len(candidates), i, j, candidates))
        return pq
    
    def initialize_priority_queue(self):
        self.pq=[]
        for i in range(9):
            for j in range(9):
                if self.board[i][j]==0:
                    candidates=self.get_candidates(self.board,i,j)
                    if candidates:
                        heapq.heappush(self.pq,(len(candidates),i,j,candidates))

    
    def update_neighbors(self,row,col):
        neighbours=set()
        for i in range(9):
            neighbours.add((row,i))
            neighbours.add((i,col))

        box_row,box_col=3*(row//3),3*(col//3)
        for i in range(box_row,box_row+3):
            for j in range(box_col,box_col+3):
                neighbours.add((i,j))

        for row,col in neighbours:
            candidates=self.get_candidates(self.board,row,col)
            # Just push the new state. The old state stays in the heap 
            # but will be ignored later (Lazy Deletion).
            heapq.heappush(self.pq,(len(candidates),row,col,candidates))

    
    def ai_make_move(self):
        # Loop until we find a valid move or run out of options
        while self.pq:
            # Pop the best option
            count, row, col, candidates = heapq.heappop(self.pq)
            
            # LAZY DELETION CHECK:
            # If board[row][col] is not 0, it means this cell was already filled 
            # by a previous update. Ignore this stale entry.
            if self.board[row][col] != 0:
                continue
                
            # Optional: Re-check candidates 
            current_candidates = self.get_candidates(self.board, row, col)
            if not current_candidates:
                return False
                
            # Greedy Choice
            value = random.choice(list(current_candidates))
            
            # Make the move
            self.board[row][col] = value
            
            # --- GUI Updates (Copy your existing GUI code here) ---
            self.cells[row][col].config(state="normal")
            self.cells[row][col].delete(0, tk.END)
            self.cells[row][col].insert(0, str(value))
            self.cells[row][col].config(fg="red", state="disabled")
            self.cell_colors[row][col] = "ai"
            

            # Update the neighbors so the PQ is ready for the next turn
            self.update_neighbors(row, col)
            
            return True
            
        return False
    
    def on_cell_edit(self, row, col):
        """Handle user input"""
        if self.current_turn != "user":
            return
        
        # Check if cell is initial (locked)
        if self.initial_board[row][col] != 0:
            return
        
        cell = self.cells[row][col]
        value = cell.get().strip()
        
        if value == "":
            self.board[row][col] = 0
            self.cell_colors[row][col] = None
            return
        
        try:
            num = int(value)
            if num < 1 or num > 9:
                raise ValueError
            
            # Validate move
            temp = self.board[row][col]
            self.board[row][col] = 0
            
            if self.is_valid(self.board, row, col, num):
                self.board[row][col] = num

                self.update_neighbors(row, col)

                cell.config(fg="blue")
                self.cell_colors[row][col] = "user"
                
                # Check if puzzle is complete
                if self.is_complete():
                    messagebox.showinfo("Game Over", "Puzzle Complete!")
                    return
                
                # Switch to AI turn
                self.current_turn = "ai"
                self.status_label.config(text="AI is Thinking...")
                self.root.after(500, self.ai_turn)
            else:
                self.board[row][col] = temp
                cell.delete(0, tk.END)
                if temp != 0:
                    cell.insert(0, str(temp))
                messagebox.showerror("Invalid Move", "This number conflicts with Sudoku rules!")
        except ValueError:
            cell.delete(0, tk.END)
            self.board[row][col] = 0
    
    def ai_turn(self):
        """Execute AI turn"""
        success = self.ai_make_move()
        
        if not success:
            messagebox.showinfo("Game Over", "AI cannot make a move!")
            return
        
        # Check if puzzle is complete
        if self.is_complete():
            messagebox.showinfo("Game Over", "Puzzle Complete!")
            return
        
        # Switch back to user
        self.current_turn = "user"
        self.status_label.config(text="User's Turn")
    
    def is_complete(self):
        """Check if puzzle is solved"""
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return False
        return True
    
    def new_game(self):
        """Start a new game"""
        self.board = self.generate_puzzle()
        
        self.initial_board = copy.deepcopy(self.board)
        self.current_turn = "user"
        self.cell_colors = [[None]*9 for _ in range(9)]
        
        self.initialize_priority_queue()

        self.render_board()
        self.status_label.config(text="User's Turn")
    
    def render_board(self):
        """Render the board to GUI"""
        for i in range(9):
            for j in range(9):
                cell = self.cells[i][j]
                cell.config(state="normal")
                cell.delete(0, tk.END)
                
                if self.board[i][j] != 0:
                    cell.insert(0, str(self.board[i][j]))
                    
                    if self.initial_board[i][j] != 0:
                        cell.config(fg="black", state="disabled")
                    else:
                        cell.config(fg="blue")
                else:
                    cell.config(fg="black")
    
    def show_hint(self):
        """Highlight most constrained empty cell"""
        if not self.pq:
            messagebox.showinfo("Hint", "No empty cells remaining!")
            return
            
        # Clean the top of the heap (remove stale entries)
        while self.pq and self.board[self.pq[0][1]][self.pq[0][2]] != 0:
            heapq.heappop(self.pq)
            
        if not self.pq:
            messagebox.showinfo("Hint", "No empty cells remaining!")
            return

        
        _, row, col, candidates = self.pq[0]
        
        # Clear previous highlights
        for i in range(9):
            for j in range(9):
                self.cells[i][j].config(bg="white")
        
        self.cells[row][col].config(bg="#ffeb3b")
        
        # Re-calculate exact candidates for the display message to be 100% accurate
        
        real_candidates = self.get_candidates(self.board, row, col)
        messagebox.showinfo("Hint", f"Most constrained cell: Row {row+1}, Col {col+1}\nCandidates: {sorted(real_candidates)}")
    
    def ai_play(self):
        """Force AI to play regardless of turn"""
        success = self.ai_make_move()
        if not success:
            messagebox.showinfo("AI Play", "AI cannot make a move!")
        elif self.is_complete():
            messagebox.showinfo("Game Over", "Puzzle Complete!")
    
    def reset_board(self):
        """Reset to initial puzzle state"""
        self.board = copy.deepcopy(self.initial_board)
        self.current_turn = "user"
        self.cell_colors = [[None]*9 for _ in range(9)]
        self.render_board()
        self.status_label.config(text="User's Turn")

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuDuel(root)
    root.mainloop()
