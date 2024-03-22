
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
    def set_colour(character: str, colour256: int) -> str:
        return f"{AsciiTricks.escape}{AsciiTricks.setting_start}{AsciiTricks.set_colour_command}{colour256}{AsciiTricks.setting_end}{character}"
    
    @staticmethod
    def return_to_1_1() -> str:
        return f"{AsciiTricks.escape}{AsciiTricks.setting_start}{AsciiTricks.home}"


class Cell:
    # Colour codes in 256 colour system
    DROP_HEAD_COLOUR256 = 231
    DROP_TAIL_COLOURS256 = [48, 41, 35, 238]
    DROP_COLOURS256 = [DROP_HEAD_COLOUR256] + DROP_TAIL_COLOURS256

    def __init__(self, character: str) -> None:
        self.character: str = character
        self.subliminal_character: str = ""

        self.position_in_drop: int = -1      # Position starting from drop head. 0-based indexing. -1 means no active drop
        self.drop_length: int = -1

    def __str__(self) -> str:
        if self.position_in_drop == -1:
            return AsciiTricks.blank_character
        
        active_character = self.subliminal_character or self.character

        # and operator returns 0 iff position in drop is 0, i.e. first colour in drop colours list is used only for head of the drop
        colour_position = self.position_in_drop and int(self.position_in_drop / len(Cell.DROP_TAIL_COLOURS256) // 1 + 1)
        colour256 = Cell.DROP_COLOURS256[colour_position]
        return AsciiTricks.set_colour(active_character, colour256)

    def set_drop_head(self, drop_length: int) -> None:
        self.position_in_drop = 0
        self.drop_length = drop_length

    def next_frame(self) -> None:
        if self.position_in_drop == -1:
            # Cell is not part of an active drop
            return
        if (new_position_in_drop := self.position_in_drop + 1) < self.drop_length:
            # Cell is part of drop tail
            self.position_in_drop = new_position_in_drop
            return
        # Drop has passed the cell and it's set back to inactive stage
        self.position_in_drop = self.drop_length = -1


class Matrix:
    def __init__(self) -> None:
        # 1920 x 1090 (full HD) is 56 rows x 209 columns
        # use os.get_terminal_size() to determine the matrix dimensions
        self.n_rows = 56
        self.n_columns = 209

        # Forestry related symbols, like ㅆ 🜎  ⍦ ⍋ ⚘ ⚶ 𐡷 𐡸 ♣ 🙖
        forest_character_code_points = [985, 1126, 1993, 9035, 9062, 9753, 9872, 9880, 9906, 9910, 10047, 10048, 10086, 10087, 12614, 11439, 11801, 67703, 67704, 128598, 128782, 129990]
        self.available_characters = [chr(x) for x in forest_character_code_points]

        # populate the matrix
        self.rows = []
        for _ in range(self.n_rows):
            row = [Cell(character) for character in random.choices(self.available_characters, k=self.n_columns)]
            self.rows.append(row)

        self.wait = 0.06
        self.glitch_freq = 0.01
        self.drop_freq = 0.1

    def __str__(self) -> str:
        return "".join("".join(str(cell) for cell in row) for row in self.rows)
    
    def next_frame(self) -> None:
        # Iterate through rows starting from the bottom
        for i, row in reversed(list(enumerate(self.rows[-1:]))):
            # Iterate through cells in the row
            for j, current_cell in enumerate(row):
                # Advance frame of each cell
                current_cell.next_frame()
                # If cell one row above is drop head, set cell as drop head
                if (cell_above := self.rows[i-1][j]).position_in_drop == 0:
                    LOG += f"({i-1}, {j})"
                    current_cell.set_drop_head(drop_length=cell_above.drop_length)
        
        # Advance frame for cells in first row
        for first_row_cell in self.rows[0]:
            first_row_cell.next_frame()

# Cycle through rows from bottom to top, 2 at a time (this & preceeding).
# With first row just apply next_frame().
# Spawn new drops in first row.

    def start(self) -> None:
        self.rows[0][50].set_drop_head(10)
        for _ in range(1):
            print(AsciiTricks.return_to_1_1(), end="")
            print(self, end="", flush=True)
            self.next_frame()
            time.sleep(self.wait)


matrix = Matrix()
matrix.start()

matrix.next_frame()
matrix.rows[0][50].position_in_drop



#################################################################

# + MAX_LEN    # Add MAX_LEN rows so drops can nicely fall off the screen at the bottom

def unnest_list(x: list) -> list:
    unnested_list = []
    for element in x:
        if isinstance(element, list):
            unnested_list += unnest_list(element)
        else:
            unnested_list.append(element)
    return unnested_list


        text = ""

        for (c, s, l) in sum(self[MAX_LEN:], []):
            if s == STATE_NONE:
                text += BLANK_CHAR
            elif s == STATE_FRONT:
                text += f"{FRONT_CLR}{c}"
            else:
                text += f"{BODY_CLRS[l]}{c}"

        return text



    def update_cell(
        self,
        r: int,
        c: int,
        *,
        char: str = None,
        state: int = None,
        length: int = None,
    ):
        if char is not None:
            self[r][c][0] = char

        if state is not None:
            self[r][c][1] = state

        if length is not None:
            self[r][c][2] = length

    def fill(self):
        # [:] Notation: creates a shallow copy
        self[:] = [[[self.get_random_char(), STATE_NONE, 0] for _ in range(self.n_columns)] for _ in range(self.n_rows)]

    def apply_glitch(self):
        total = self.n_columns * self.n_rows * self.glitch_freq

        for _ in range(int(total)):
            c = random.randint(0, self.n_columns - 1)
            r = random.randint(0, self.n_rows - 1)

            self.update_cell(r, c, char=self.get_random_char())

    def drop_col(self, col: int):
        dropped = self[self.n_rows - 1][col] == STATE_FRONT

        for r in reversed(range(self.n_rows)):
            _, state, length = self[r][col]

            if state == STATE_NONE:
                continue

            if r != self.n_rows - 1:
                self.update_cell(r + 1, col, state=state, length=length)

            self.update_cell(r, col, state=STATE_NONE, length=0)

        return dropped

    def add_drop(self, row: int, col: int, length: int):
        for i in reversed(range(length)):
            r = row + (length - i)

            if i == 0:
                self.update_cell(r, col, state=STATE_FRONT, length=length)
            else:
                l = math.ceil((TOTAL_CLRS - 1) * i / length)

                self.update_cell(r, col, state=STATE_TAIL, length=l)

    def update(self):
        dropped = sum(self.drop_col(c) for c in range(self.n_columns))

        total = self.n_columns * self.n_rows * self.drop_freq
        missing = math.ceil((total - dropped) / self.n_columns)

        for _ in range(missing):
            # Set a non-random string with last section the same as beginning.
            col = random.randint(0, self.n_columns - 1)
            length = random.randint(MIN_LEN, MAX_LEN)

            self.add_drop(0, col, length)

    def start(self):
        self.fill()

        while True:
            print(CLEAR_CHAR, end="")
            print(self, end="", flush=True)

            # self.apply_glitch()
            self.update()

            time.sleep(self.wait)



matrix = Matrix()
matrix.start()
