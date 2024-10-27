# Helper Python code for mapping from an FEN chessboard representation string, to a python dictionary formatted for rendering in a Django template, similar to Sudoku.
def fen_to_dict(fen_string):
    # Mapping of pieces to HTML entities
    piece_to_html = {
        'K': '&#9812;',  # White King
        'Q': '&#9813;',  # White Queen
        'R': '&#9814;',  # White Rook
        'B': '&#9815;',  # White Bishop
        'N': '&#9816;',  # White Knight
        'P': '&#9817;',  # White Pawn
        'k': '&#9818;',  # Black King
        'q': '&#9819;',  # Black Queen
        'r': '&#9820;',  # Black Rook
        'b': '&#9821;',  # Black Bishop
        'n': '&#9822;',  # Black Knight
        'p': '&#9823;',  # Black Pawn
    }

    # Get the position part of the FEN string
    position_part = fen_string.split(' ')[0]
    ranks = position_part.split('/')

    rows_list = []

    for rank_index, rank_str in enumerate(ranks):
        rank_number = 8 - rank_index  # Rank numbers from 8 to 1
        rank_dict = {}
        file_index = 0  # Files from 'a' to 'h'
        for c in rank_str:
            if c.isdigit():
                n = int(c)
                for _ in range(n):
                    if file_index >= 8:
                        break  # Safety check
                    file_letter = chr(ord('a') + file_index)
                    position = f"{file_letter}{rank_number}"
                    rank_dict[position] = '&nbsp;'
                    file_index += 1
            else:
                if file_index >= 8:
                    break  # Safety check
                file_letter = chr(ord('a') + file_index)
                position = f"{file_letter}{rank_number}"
                rank_dict[position] = piece_to_html.get(c, '&nbsp;')
                file_index += 1
        rows_list.append(rank_dict)

    return rows_list

# Example usage:
fen_string = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'
board_rows = fen_to_dict(fen_string)

