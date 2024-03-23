
import random
import time

LOG = ""

class AsciiTricks:
    escape = "\x1b"
    set_colour_command = "38;5;"
    setting_start = "["
    setting_end = "m"
    home = "H"
    blank_character = " "

    @staticmethod
    def get_coloured_character(character: str, colour256: int) -> str:
        return f"{AsciiTricks.escape}{AsciiTricks.setting_start}{AsciiTricks.set_colour_command}{colour256}{AsciiTricks.setting_end}{character}"
    
    @staticmethod
    def return_to_top() -> str:
        return f"{AsciiTricks.escape}{AsciiTricks.setting_start}{AsciiTricks.home}"


class Cell:
    # Colour codes in 256 colour system
    DROP_HEAD_COLOUR256 = 231               # white
    DROP_BODY_COLOURS256 = [48, 41, 35]     # greens
    DROP_TAIL_COLOUR256 = 238               # gray

    def __init__(self, character: str) -> None:
        self.character: str = character
        self.override_character: str = ""

        self.is_lit: bool = False
        self.default_colour: int = random.choice(self.DROP_BODY_COLOURS256)

        self.position_in_drop: int = -1      # Position starting from drop head. 0-based indexing. -1 means no active drop
        self.drop_length: int = -1

    def __str__(self) -> str:
        if not self.is_lit:
            return AsciiTricks.blank_character
        
        active_character = self.get_active_character()
        active_colour = self.get_active_colour()
        return AsciiTricks.get_coloured_character(active_character, active_colour)

    def get_active_colour(self):
        if self.position_in_drop == -1:
            return self.default_colour
        if self.position_in_drop == 0:
            return self.DROP_HEAD_COLOUR256
        colour_options = self.DROP_BODY_COLOURS256 + [self.DROP_TAIL_COLOUR256]
        i_colour = int(round((len(colour_options) - 1) * self.position_in_drop / self.drop_length, 0))
        return colour_options[i_colour]

    def get_active_character(self):
        return self.override_character or self.character

    def set_drop_head(self, drop_length: int) -> None:
        self.position_in_drop = 0
        self.drop_length = drop_length
        self.is_lit = True

    def move_drop(self) -> None:
        if self.position_in_drop == -1:
            # Cell is not part of an active drop
            return
        if (next_position := self.position_in_drop + 1) < self.drop_length:
            # Cell is part of drop body / tail
            self.position_in_drop = next_position
            return
        # Drop has passed the cell and it's set back to inactive stage
        self.position_in_drop = self.drop_length = -1
        self.is_lit = False


class Matrix:
    # 1920 x 1090 (full HD) is 56 rows x 209 columns
    # use os.get_terminal_size() to determine the matrix dimensions
    N_ROWS = 56
    N_COLUMNS = 209

    MIN_DROP_LENGTH = 5
    MAX_DROP_LENGTH = 12
    DROP_DENSITY = 0.1      # Proportion of screen covered by drops

    # Forestry related symbols, like ㅆ 🜎  ⍦ ⍋ ⚘ ⚶ 𐡷 𐡸 ♣ 🙖
    # Problematic characters: 12614, 1993, 67703, 67704
    CHARACTER_CODE_POINTS = [985, 1126, 9035, 9062, 9753, 9872, 9880, 9906, 9910, 10047, 10048, 10086, 10087, 11439, 11801, 128598, 128782, 129990]

    FRAME_CHANGE_SLEEP_PERIOD_SECOND = 0.06
    glitch_freq = 0.01
    drop_freq = 0.1

    def __init__(self) -> None:

        self.available_characters = [chr(x) for x in self.CHARACTER_CODE_POINTS]
        # populate the matrix
        self.rows = []
        for _ in range(self.N_ROWS):
            row = [Cell(character) for character in random.choices(self.available_characters, k=self.N_COLUMNS)]
            self.rows.append(row)

    def __str__(self) -> str:
        return "".join("".join(str(cell) for cell in row) for row in self.rows)
    
    def count_drops(self) -> int:
        # Count all drop heads in matrix
        return sum([sum([cell.position_in_drop == 0 for cell in row]) for row in self.rows])
    
    def next_frame(self) -> None:
        # Iterate through rows starting from the bottom
        for i_row, row in reversed(list(enumerate(self.rows[1:]))):
            # Iterate through cells in the row
            for i_column, current_cell in enumerate(row):
                # Advance frame of each cell
                current_cell.move_drop()
                # If cell one row above is drop head, set cell as drop head
                cell_above = self.rows[i_row-1][i_column]
                if cell_above.position_in_drop == 0:
                    current_cell.set_drop_head(drop_length=cell_above.drop_length)
        
        # Advance frame for cells in first row
        for first_row_cell in self.rows[0]:
            first_row_cell.move_drop()

    def spawn_new_drops(self, n: int) -> None:
        # Spawn necessary number of drops in random columns in the first row
        # Actual number of drops spawned can be smaller, since same column can be chosen several times
        for _ in range(n):
            i_drop_column = random.randint(0, self.N_COLUMNS - 1)
            drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
            self.rows[0][i_drop_column].set_drop_head(drop_length)

    def get_n_drops_missing(self) -> int:
        # Get the number of drops to be added to achieve the desired drop density
        n_active_drops = self.count_drops()
        mean_drop_length = (self.MIN_DROP_LENGTH + self.MAX_DROP_LENGTH) / 2
        current_drop_density = n_active_drops * mean_drop_length / (self.N_ROWS * self.N_COLUMNS)
        n_drops_missing = int(round((self.DROP_DENSITY - current_drop_density) * (self.N_ROWS * self.N_COLUMNS) / mean_drop_length, 0))
        return(n_drops_missing)

    def start(self) -> None:
        for _ in range(50):
            # Print frame
            print(AsciiTricks.return_to_top(), end="")
            print(self, end="", flush=True)

            # Advance frame
            self.next_frame()
            n_drops_missing = self.get_n_drops_missing()
            self.spawn_new_drops(n_drops_missing)

            # Sleep
            time.sleep(self.FRAME_CHANGE_SLEEP_PERIOD_SECOND)


matrix = Matrix()
matrix.start()

# matrix.next_frame()
# matrix.rows[0][52].set_drop_head(10)
# matrix.get_current_drop_density()
# matrix.rows[0][50].position_in_drop



# #################################################################

# # + MAX_LEN    # Add MAX_LEN rows so drops can nicely fall off the screen at the bottom

# def unnest_list(x: list) -> list:
#     unnested_list = []
#     for element in x:
#         if isinstance(element, list):
#             unnested_list += unnest_list(element)
#         else:
#             unnested_list.append(element)
#     return unnested_list


#         text = ""

#         for (c, s, l) in sum(self[MAX_LEN:], []):
#             if s == STATE_NONE:
#                 text += BLANK_CHAR
#             elif s == STATE_FRONT:
#                 text += f"{FRONT_CLR}{c}"
#             else:
#                 text += f"{BODY_CLRS[l]}{c}"

#         return text



#     def update_cell(
#         self,
#         r: int,
#         c: int,
#         *,
#         char: str = None,
#         state: int = None,
#         length: int = None,
#     ):
#         if char is not None:
#             self[r][c][0] = char

#         if state is not None:
#             self[r][c][1] = state

#         if length is not None:
#             self[r][c][2] = length

#     def fill(self):
#         # [:] Notation: creates a shallow copy
#         self[:] = [[[self.get_random_char(), STATE_NONE, 0] for _ in range(self.n_columns)] for _ in range(self.n_rows)]

#     def apply_glitch(self):
#         total = self.n_columns * self.n_rows * self.glitch_freq

#         for _ in range(int(total)):
#             c = random.randint(0, self.n_columns - 1)
#             r = random.randint(0, self.n_rows - 1)

#             self.update_cell(r, c, char=self.get_random_char())

#     def drop_col(self, col: int):
#         dropped = self[self.n_rows - 1][col] == STATE_FRONT

#         for r in reversed(range(self.n_rows)):
#             _, state, length = self[r][col]

#             if state == STATE_NONE:
#                 continue

#             if r != self.n_rows - 1:
#                 self.update_cell(r + 1, col, state=state, length=length)

#             self.update_cell(r, col, state=STATE_NONE, length=0)

#         return dropped

#     def add_drop(self, row: int, col: int, length: int):
#         for i in reversed(range(length)):
#             r = row + (length - i)

#             if i == 0:
#                 self.update_cell(r, col, state=STATE_FRONT, length=length)
#             else:
#                 l = math.ceil((TOTAL_CLRS - 1) * i / length)

#                 self.update_cell(r, col, state=STATE_TAIL, length=l)

#     def update(self):
#         dropped = sum(self.drop_col(c) for c in range(self.n_columns))

#         total = self.n_columns * self.n_rows * self.drop_freq
#         missing = math.ceil((total - dropped) / self.n_columns)

#         for _ in range(missing):
#             # Set a non-random string with last section the same as beginning.
#             col = random.randint(0, self.n_columns - 1)
#             length = random.randint(MIN_LEN, MAX_LEN)

#             self.add_drop(0, col, length)

#     def start(self):
#         self.fill()

#         while True:
#             print(CLEAR_CHAR, end="")
#             print(self, end="", flush=True)

#             # self.apply_glitch()
#             self.update()

#             time.sleep(self.wait)



# matrix = Matrix()
# matrix.start()
