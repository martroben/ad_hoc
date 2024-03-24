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


class AsciiImage:
    BLANK_CHARACTER = " "
    NEWLINE_CHARACTER = "\n"

    def __init__(self, ascii_text: str) -> None:
        self.text = ascii_text

    def get_binary(self) -> list[list[bool]]:
        """
        Return a matrix (list or rows) where character locations are indicated by True values
        """
        binary_image = []
        for row in self.text.split(self.NEWLINE_CHARACTER):
            binary_row = [character != self.BLANK_CHARACTER for character in row]
            binary_image += [binary_row]
        return binary_image

    def get_scaled_matrix(self, n_rows: int, n_columns: int) -> list[list[bool]]:
        """
        Position binary image in the middle of a matrix of given dimensions. I.e. pad it with False cells.
        """
        binary = self.get_binary()
        n_rows_image = len(binary)
        n_columns_image = len(binary[0])

        if n_rows_image > n_rows or n_columns_image > n_columns:
            raise ValueError("Scaling dimensions are smaller than the input image. Function can only scale the number of rows and columns up, not down.")

        n_pad_rows_top = (n_rows - n_rows_image) // 2
        n_pad_rows_bottom = n_rows - n_pad_rows_top - n_rows_image
        n_pad_columns_left = (n_columns - n_columns_image) // 2
        n_pad_columns_right = n_columns - n_pad_columns_left - n_columns_image

        scaled_image_midpart = [n_pad_columns_left * [False] + row + n_pad_columns_right * [False] for row in binary]
        scaled_image = n_pad_rows_top * [n_columns * [False]] + scaled_image_midpart + n_pad_rows_bottom * [n_columns * [False]]

        return scaled_image


# self.position_in_drop -> self.drop

class Drop:
    def __init__(self, length: int) -> None:
        self.length = length
        self.step = 1           # Parameter for possible extension: could make drops that move two cells in a cycle
    
    def get_colour(self, position_in_drop: int, bright_colours: int, lit_colours: list[int], fading_colours: list[int]) -> int:
        if position_in_drop == 0:
            return random.choice(bright_colours)
        colour_sequence = lit_colours + fading_colours
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
    BRIGHT_COLOURS = [231]             # whites
    LIT_COLOURS = [48, 41, 35, 29]     # greens
    DIM_COLOURS = [29, 22]             # dark greens
    FADING_COLOURS = [238]             # grays
    INIVISIBLE_COLOUR = -1             # black (color code 0 doesn't look good on screen, so we return a blank character instead)

    def __init__(self, character: str) -> None:
        self.character: str = character
        self.override_character: str = None

        self.is_lit: bool = False
        self.default_colour: int = random.choice(self.LIT_COLOURS)
        self.override_colour: int = None

        self.position_in_drop: int = 0      # Position starting from drop head. 0-based indexing.
        self.drop: Drop = None

        self.is_ascii_image = False                # Cell is part of a 2d ascii "image"
        self.is_message = False             # Cell is part of a vertical text "message"

    def __str__(self) -> str:
        if self.is_lit:
            active_character = self.get_active_character()
            active_colour = self.get_active_colour()
            return AsciiTricks.get_coloured_character(active_character, active_colour)
        return AsciiTricks.blank_character

    def get_active_colour(self):
        if self.override_colour:
            return self.override_colour
        if self.drop:
            drop_colour = self.drop.get_colour(self.position_in_drop, self.BRIGHT_COLOURS, self.LIT_COLOURS, self.FADING_COLOURS)
            return drop_colour
        return self.default_colour

    def get_active_character(self):
        # black doesn't look good on screen, so we return a blank character instead
        if self.get_active_colour() == self.INIVISIBLE_COLOUR:
            return AsciiTricks.blank_character
        return self.override_character or self.character

    def set_drop_head(self, drop_length: int) -> None:
        self.position_in_drop = 0
        self.drop = Drop(drop_length)
        self.is_lit = True

    def move_drop(self, image_active: bool) -> None:
        if not self.drop:
            # Cell is not part of an active drop
            return
        if next_position := self.drop.get_next_position(self.position_in_drop):
            # If next_position is not none, the cell is part of drop body / tail
            self.position_in_drop = next_position
            return
        # Else, drop has passed the cell and it's set back to inactive stage
        self.drop = None
        # Set cell as not lit, unless it's part of an active ascii image
        self.is_lit = image_active and self.is_ascii_image


class Glitch:
    def __init__(self, cell: Cell) -> None:
        self.cell = cell
        self.action_sequence = []

        # Don't glitch messages
        if cell.is_message:
            return

        self.action_sequence += random.randint(0, 1) * [self.flash]
        self.action_sequence += random.randint(0, 5) * [self.keep_same_state]
        self.action_sequence += [self.invisible]
        self.action_sequence += random.randint(15, 20) * [self.keep_same_state]
        # self.action_sequence += random.randint(0, 5) * self.flicker_colour()
        # self.action_sequence += random.randint(0, 5) * self.flicker_character()
        self.action_sequence += [self.clear]
        # Reverse, so it can be applied by pop()
        self.action_sequence = list(reversed(self.action_sequence))
    
    def flash(self) -> None:
        self.cell.override_colour = random.choice(self.cell.BRIGHT_COLOURS)

    def invisible(self) -> None:
        self.cell.override_colour = self.cell.INIVISIBLE_COLOUR
    
    def dim(self) -> None:
        self.cell.override_colour = random.choice(self.cell.DIM_COLOURS)
    
    def keep_same_state(self) -> None:
        return

    def flicker_colour(self) -> list:
        # Dark period followed by a dim period
        return [self.invisible] + random.randint(0, 2) * [self.keep_same_state] + random.randint(1, 3) * [self.dim]
    
    def change_character(self) -> None:
        self.cell.character = random.choice(Matrix.AVAILABLE_CHARACTERS)
    
    def flicker_character(self) -> list:
        return [self.change_character] + random.randint(0, 2) * [self.keep_same_state]
    
    def clear(self) -> list:
        self.cell.override_colour = None
    
    def do_action(self) -> None:
        # Performs one action step and removes it from the sequence
        action = self.action_sequence.pop()
        action()


class Matrix:
    # 1920 x 1090 (full HD): 56 rows x 209 columns
    # use python3 -c import os; os.get_terminal_size() in full screen terminal to get matrix dimensions
    N_ROWS: int = 56
    N_COLUMNS: int = 209

    MIN_DROP_LENGTH: int = 4
    MAX_DROP_LENGTH: int = 12
    DROP_PROBABLITY: float = 0.02       # Drop probablity per column per step
    GLITCH_PROBABILITY: float = 0.01    # Glitch probability per cell per step

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
        self.glitches = []

    def __str__(self) -> str:
        return "".join("".join(str(cell) for cell in row) for row in self.rows)
    
    def set_ascii_image(self, ascii_image: AsciiImage) -> None:
        ascii_image_matrix = ascii_image.get_scaled_matrix(self.N_ROWS, self.N_COLUMNS)
        for i_row, image_row in enumerate(ascii_image_matrix):
            for i_column, is_ascii_image in enumerate(image_row):
                self.rows[i_row][i_column].is_ascii_image = is_ascii_image
        
        # Make a register of ascii image top edge cells to be used when "washing" away the image
        self.image_top_cells = []
        for i_column in range(len(self.rows[0])):
            for i_row, row in enumerate(self.rows):
                cell = row[i_column]
                if cell.is_ascii_image:
                    self.image_top_cells += [cell]
                    continue

        self.ascii_image_active = False
    
    def move_drops(self) -> None:
        # Iterate through rows starting from the bottom
        for i_row, row in reversed(list(enumerate(self.rows[1:]))):
            # Iterate through cells in the row
            for i_column, current_cell in enumerate(row):
                # Advance frame of each cell
                current_cell.move_drop(image_active = self.ascii_image_active)
                # If cell one row above is drop head, set cell as drop head
                cell_above = self.rows[i_row-1][i_column]
                if cell_above.drop and cell_above.position_in_drop == 0:
                    current_cell.set_drop_head(drop_length=cell_above.drop.length)
        
        # Advance frame for cells in first row
        for first_row_cell in self.rows[0]:
            first_row_cell.move_drop(image_active = self.ascii_image_active)

    def spawn_new_drops(self) -> None:
        for cell in self.rows[0]:
            if random.random() > self.active_drop_probability:
                continue

            drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
            cell.set_drop_head(drop_length)

    def spawn_ascii_image_washing_drops(self) -> None:
        if self.ascii_image_active:
            return
        
        # Only initiate drops in currently lit non-drop cells
        image_top_cells_active = [cell for cell in self.image_top_cells if cell.is_lit and not cell.drop]
        
        # Increase drop probablity as less cells remain in image (for better visual)
        max_probablity = 0.1
        drop_probablity = Matrix.DROP_PROBABLITY + (max_probablity - Matrix.DROP_PROBABLITY) * (len(self.image_top_cells) - len(image_top_cells_active)) / len(self.image_top_cells)
        for cell in image_top_cells_active:
            if random.random() > drop_probablity:
                continue

            drop_length = random.randint(self.MIN_DROP_LENGTH, self.MAX_DROP_LENGTH)
            cell.set_drop_head(drop_length)

    def spawn_new_glitches(self) -> None:
        cells_to_glitch = []
        # Choose random cells to glitch
        for row in self.rows:
            for cell in row:
                if random.random() < self.GLITCH_PROBABILITY:
                    cells_to_glitch += [cell]

        self.glitches += [Glitch(cell) for cell in cells_to_glitch]
    
    def apply_glitches(self) -> None:
        # Remove glitches that have ran out of actions
        self.glitches = [glitch for glitch in self.glitches if glitch.action_sequence]
        for glitch in self.glitches:
            glitch.do_action()

    def print_frame(self) -> None:
        print(AsciiTricks.return_to_top(), end="")
        print(self, end="", flush=True)
        time.sleep(self.FRAME_SLEEP_PERIOD_SECONDS)

    def run(self) -> None:

        start_timestamp = time.time()
        start_ascii_image_seconds = 20
        stop_rain_seconds = 24
        wash_ascii_image_seconds = 70
        cycle_end_seconds = 80

        while (time.time() - start_timestamp) < cycle_end_seconds:
            self.print_frame()

            # Advance frame
            self.move_drops()
            self.spawn_new_drops()
            self.apply_glitches()
            self.spawn_new_glitches()

            if (time.time() - start_timestamp) > start_ascii_image_seconds:
                self.ascii_image_active = True

            if (time.time() - start_timestamp) > stop_rain_seconds:
                self.rain_active = False

            if (time.time() - start_timestamp) > wash_ascii_image_seconds:
                self.ascii_image_active = False
                self.spawn_ascii_image_washing_drops()
            
            if not self.rain_active:
                # Stop rain within N_ROWS steps
                self.active_drop_probability = max(0, self.active_drop_probability - self.DROP_PROBABLITY / self.N_ROWS)



#######
# Run #
#######

while True:
    matrix = Matrix()

    # Ascii image generated by https://seotoolbelt.co/tools/ascii-art-generator/#text-list-tab
    with open("ascii_logo.txt") as logo_file:
        ascii_text = logo_file.read()

    ascii_image = AsciiImage(ascii_text)
    matrix.set_ascii_image(ascii_image)

    matrix.run()
