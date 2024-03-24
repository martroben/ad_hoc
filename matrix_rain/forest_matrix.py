import random
import time


#########################
# Functions and Classes #
#########################

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


class Logo:
    BLANK_CHARACTER = " "
    NEWLINE_CHARACTER = "\n"

    def __init__(self, logo_text: str) -> None:
        self.text = logo_text

    def get_binary(self) -> list[list[bool]]:
        """
        Return a matrix (list or rows) where character locations are indicated by True values
        """
        binary_logo = []
        for row in self.text.split(self.NEWLINE_CHARACTER):
            binary_row = [character != self.BLANK_CHARACTER for character in row]
            binary_logo += [binary_row]
        return binary_logo

    def get_scaled_matrix(self, n_rows: int, n_columns: int) -> list[list[bool]]:
        """
        Position binary logo in the middle of a matrix of given dimensions. I.e. pad it with False cells.
        """
        binary = self.get_binary()
        n_rows_logo = len(binary)
        n_columns_logo = len(binary[0])

        if n_rows_logo > n_rows or n_columns_logo > n_columns:
            raise ValueError("Scaling dimensions are smaller than the input logo. Function can only scale the number of rows and columns up, not down.")

        n_pad_rows_top = (n_rows - n_rows_logo) // 2
        n_pad_rows_bottom = n_rows - n_pad_rows_top - n_rows_logo
        n_pad_columns_left = (n_columns - n_columns_logo) // 2
        n_pad_columns_right = n_columns - n_pad_columns_left - n_columns_logo

        scaled_logo_midpart = [n_pad_columns_left * [False] + row + n_pad_columns_right * [False] for row in binary]
        scaled_logo = n_pad_rows_top * [n_columns * [False]] + scaled_logo_midpart + n_pad_rows_bottom * [n_columns * [False]]

        return scaled_logo


class Glitch:
    pass


# self.position_in_drop -> self.drop

class Drop:
    def __init__(self, length: int) -> None:
        self.length = length
        self.step = 1           # Parameter for possible extension: could make drops that move two cells in a cycle
    
    def get_colour(self, position_in_drop: int, bright_colour: int, lit_colours: list[int], dim_colours: list[int]) -> int:
        if position_in_drop == 0:
            return bright_colour
        colour_sequence = lit_colours + dim_colours
        # Selection formula prioritises colours in the tail end (rounds index up)
        i_colour = int(((len(colour_sequence) - 1) * position_in_drop / self.length - 0.1) // 1 + 1)
        return colour_sequence[i_colour]
    
    def get_next_position(self, position_in_drop: int) -> int:
        next_position = position_in_drop + self.step
        if next_position < self.length:
            return next_position
        return None


class Cell:
    # Colour codes in 256 colour system
    CELL_BRIGHT_COLOUR = 231                # white
    CELL_LIT_COLOURS = [48, 41, 35, 29]     # greens
    CELL_TAIL_COLOURS = [238]               # darks and grays

    def __init__(self, character: str) -> None:
        self.character: str = character
        self.override_character: str = ""

        self.is_lit: bool = False
        self.default_colour: int = random.choice(self.CELL_LIT_COLOURS)

        self.position_in_drop: int = 0      # Position starting from drop head. 0-based indexing.
        self.drop: Drop = None

        self.is_logo = False

    def __str__(self) -> str:
        if not self.is_lit:
            return AsciiTricks.blank_character
        
        active_character = self.get_active_character()
        active_colour = self.get_active_colour()
        return AsciiTricks.get_coloured_character(active_character, active_colour)

    def get_active_colour(self):
        if not self.drop:
            return self.default_colour
        drop_colour = self.drop.get_colour(self.position_in_drop, self.CELL_BRIGHT_COLOUR, self.CELL_LIT_COLOURS, self.CELL_TAIL_COLOURS)
        return drop_colour

    def get_active_character(self):
        return self.override_character or self.character

    def set_drop_head(self, drop_length: int) -> None:
        self.position_in_drop = 0
        self.drop = Drop(drop_length)
        self.is_lit = True

    def move_drop(self, logo_active: bool) -> None:
        if not self.drop:
            # Cell is not part of an active drop
            return
        if next_position := self.drop.get_next_position(self.position_in_drop):
            # If next_position is not none, the cell is part of drop body / tail
            self.position_in_drop = next_position
            return
        # Else, drop has passed the cell and it's set back to inactive stage
        self.drop = None
        # Set cell as not lit, unless it's part of an active logo
        self.is_lit = logo_active and self.is_logo


class Matrix:
    # 1920 x 1090 (full HD): 56 rows x 209 columns
    # use python3 -c import os; os.get_terminal_size() in full screen terminal to get matrix dimensions
    N_ROWS: int = 56
    N_COLUMNS: int = 209

    MIN_DROP_LENGTH: int = 4
    MAX_DROP_LENGTH: int = 12
    DROP_PROBABLITY: float = 0.02

    # Forestry related symbols: ϙ Ѧ ⍋ ⍦ ☙ ⚐ ⚘ ⚲ ⚶ ✿ ❀ ❦ ❧ ⲯ ⸙ 🙖 🜎 🯆
    CHARACTER_CODE_POINTS = [985, 1126, 9035, 9062, 9753, 9872, 9880, 9906, 9910, 10047, 10048, 10086, 10087, 11439, 11801, 128598, 128782, 129990]
    AVAILABLE_CHARACTERS = [chr(x) for x in CHARACTER_CODE_POINTS]

    FRAME_SLEEP_PERIOD_SECONDS = 0.07

    def __init__(self) -> None:
        # populate the matrix
        self.rows = []
        for _ in range(self.N_ROWS):
            row = [Cell(character) for character in random.choices(self.AVAILABLE_CHARACTERS, k=self.N_COLUMNS)]
            self.rows.append(row)
        
        # Duplicated instance variable is set, because it changes when "stopping" the rain
        self.active_drop_probability = self.DROP_PROBABLITY
        self.rain_active = True

    def __str__(self) -> str:
        return "".join("".join(str(cell) for cell in row) for row in self.rows)
    
    def set_logo(self, logo: Logo) -> None:
        logo_matrix = logo.get_scaled_matrix(self.N_ROWS, self.N_COLUMNS)
        for i_row, logo_row in enumerate(logo_matrix):
            for i_column, is_logo in enumerate(logo_row):
                self.rows[i_row][i_column].is_logo = is_logo
        
        # Make a register of logo top edge cells to be used when "washing" away the logo
        self.logo_top_cells = []
        for i_column in range(len(self.rows[0])):
            for i_row, row in enumerate(self.rows):
                cell = row[i_column]
                if cell.is_logo:
                    self.logo_top_cells += [cell]
                    continue

        self.logo_active = False
    
    def move_drops(self) -> None:
        # Iterate through rows starting from the bottom
        for i_row, row in reversed(list(enumerate(self.rows[1:]))):
            # Iterate through cells in the row
            for i_column, current_cell in enumerate(row):
                # Advance frame of each cell
                current_cell.move_drop(logo_active = self.logo_active)
                # If cell one row above is drop head, set cell as drop head
                cell_above = self.rows[i_row-1][i_column]
                if cell_above.drop and cell_above.position_in_drop == 0:
                    current_cell.set_drop_head(drop_length=cell_above.drop.length)
        
        # Advance frame for cells in first row
        for first_row_cell in self.rows[0]:
            first_row_cell.move_drop(logo_active = self.logo_active)

    def spawn_new_drops(self) -> None:
        for cell in self.rows[0]:
            if random.random() > self.active_drop_probability:
                continue

            drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
            cell.set_drop_head(drop_length)

    def spawn_logo_washing_drops(self) -> None:
        if self.logo_active:
            return
        
        # Only initiate drops in currently lit non-drop cells
        active_logo_top_cells = [cell for cell in self.logo_top_cells if cell.is_lit and not cell.drop]
        
        # Increase drop probablity as less cells remain in logo (for better visual)
        max_probablity = 0.1
        drop_probablity = Matrix.DROP_PROBABLITY + (max_probablity - Matrix.DROP_PROBABLITY) * (len(self.logo_top_cells) - len(active_logo_top_cells)) / len(self.logo_top_cells)
        for cell in active_logo_top_cells:
            if random.random() > drop_probablity:
                continue

            drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
            cell.set_drop_head(drop_length)

    def print_frame(self) -> None:
        print(AsciiTricks.return_to_top(), end="")
        print(self, end="", flush=True)
        time.sleep(self.FRAME_SLEEP_PERIOD_SECONDS)

    def run(self) -> None:

        start_timestamp = time.time()
        start_logo_seconds = 20
        stop_rain_seconds = 24
        wash_logo_seconds = 35
        cycle_end_seconds = 50

        while (time.time() - start_timestamp) < cycle_end_seconds:
            self.print_frame()

            # Advance frame
            self.move_drops()
            self.spawn_new_drops()

            if (time.time() - start_timestamp) > start_logo_seconds:
                self.logo_active = True

            if (time.time() - start_timestamp) > stop_rain_seconds:
                self.rain_active = False

            if (time.time() - start_timestamp) > wash_logo_seconds:
                self.logo_active = False
                self.spawn_logo_washing_drops()
            
            if not self.rain_active:
                # Stop rain within N_ROWS steps
                self.active_drop_probability = max(0, self.active_drop_probability - self.DROP_PROBABLITY / self.N_ROWS)



#######
# Run #
#######

while True:
    matrix = Matrix()

    # Ascii logo generated by https://seotoolbelt.co/tools/ascii-art-generator/#text-list-tab
    with open("ascii_logo.txt") as logo_file:
        logo_text = logo_file.read()

    logo = Logo(logo_text)
    matrix.set_logo(logo)

    matrix.run()
