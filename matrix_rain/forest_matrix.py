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
        i_colour = int(((len(colour_options) - 1) * self.position_in_drop / self.drop_length - 0.1) // 1 + 1)
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
    N_ROWS: int = 56
    N_COLUMNS: int = 209

    MIN_DROP_LENGTH: int = 4
    MAX_DROP_LENGTH: int = 12
    DROP_DENSITY: float = 0.2      # Proportion of screen filled by drops

    # Forestry related symbols ϙ Ѧ ⍋ ⍦ ☙ ⚐ ⚘ ⚲ ⚶ ✿ ❀ ❦ ❧ ⲯ ⸙ 🙖 🜎 🯆
    CHARACTER_CODE_POINTS = [985, 1126, 9035, 9062, 9753, 9872, 9880, 9906, 9910, 10047, 10048, 10086, 10087, 11439, 11801, 128598, 128782, 129990]

    FRAME_SLEEP_PERIOD_SECONDS = 0.06

    def __init__(self) -> None:

        self.available_characters = [chr(x) for x in self.CHARACTER_CODE_POINTS]
        # populate the matrix
        self.rows = []
        for _ in range(self.N_ROWS):
            row = [Cell(character) for character in random.choices(self.available_characters, k=self.N_COLUMNS)]
            self.rows.append(row)
        
        self.active_drop_density = self.DROP_DENSITY
        self.rain_active = True

    def __str__(self) -> str:
        return "".join("".join(str(cell) for cell in row) for row in self.rows)
    
    def count_drops(self) -> int:
        # Count all drop heads in matrix
        return sum([sum([cell.position_in_drop == 0 for cell in row]) for row in self.rows])
    
    def move_drops(self) -> None:
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

    def spawn_new_drops(self) -> None:
        # Spawn drops in random columns in the first row
        mean_drop_length = (self.MIN_DROP_LENGTH + self.MAX_DROP_LENGTH) / 2
        for cell in self.rows[0]:
            # scale drop density by mean drop length to get screen fill density
            if random.random() < self.active_drop_density / mean_drop_length:
                drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
                cell.set_drop_head(drop_length)

    def print_frame(self) -> None:
        print(AsciiTricks.return_to_top(), end="")
        print(self, end="", flush=True)
        time.sleep(self.FRAME_SLEEP_PERIOD_SECONDS)

    def start(self) -> None:
        start_timestamp = time.time()
        run_time_seconds = 20
        while True:
            self.print_frame()

            # Advance frame
            self.move_drops()
            self.spawn_new_drops()

            # Stop rain mechanism
            if (time.time() - start_timestamp) > run_time_seconds:
                self.rain_active = False
            
            if not self.rain_active:
                # Stop rain within N_ROWS steps
                self.active_drop_density = max(0, self.active_drop_density - self.DROP_DENSITY / self.N_ROWS)


#######
# Run #
#######
matrix = Matrix()
matrix.start()
