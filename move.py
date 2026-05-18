class Move:
    def __init__(self, start_sq, end_sq, board, is_en_passant=False, is_castle=False, promotion=None):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.promotion = promotion
        
        if self.is_en_passant:
            self.piece_captured = 'bp' if self.piece_moved == 'wp' else 'wp'
            
        promo_code = 0
        if self.promotion:
            promo_code = (ord(self.promotion[0]) * 10 + ord(self.promotion[1])) * 100000
        self.move_id = (
            self.start_row * 10000000
            + self.start_col * 1000000
            + self.end_row * 100000
            + self.end_col * 10000
            + (1000 if self.is_en_passant else 0)
            + (100 if self.is_castle else 0)
            + promo_code
        )
            
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id and self.promotion == other.promotion
        return False

    def get_chess_notation(self):
        cols_to_files = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        start_sq = cols_to_files[self.start_col] + str(8 - self.start_row)
        end_sq = cols_to_files[self.end_col] + str(8 - self.end_row)
        
        if self.is_castle:
            return "O-O" if self.end_col == 6 else "O-O-O"
            
        s = ""
        if self.piece_moved[1] != 'p':
            s += self.piece_moved[1].upper()
        elif self.piece_captured:
            s += cols_to_files[self.start_col]
            
        if self.piece_captured:
            s += "x"
            
        s += end_sq
        
        if self.promotion:
            s += "=" + self.promotion[1].upper()
            
        return s

    def __str__(self):
        return self.get_chess_notation()
