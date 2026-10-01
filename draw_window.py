"""
The complete PyGame implementation of a drawing window for the game
"Sketchy Connections", containing complete class structure for
the Grid and GridCells to use the window independently, and a
DrawingWindow class that allows for this to be easily plopped into
a broader project engine if necessary.

Also includes code for a simple animation loop to display the history
of drawings made in the window, great little bonus feature for implementation
or for an aspiring pixel artist.

Authored by Mathew Neves with edits from Kent Schneider
Direct comments or bug reports to
Mathew Neves <mneves@uvm.edu>

Contains complete drawing window documentation that can be reused
and modified for without express consent of the authors.

We would love to hear from you or see your drawings
if you use this window!
"""

# pylint doesn't like pygame members
# pylint: disable=no-member

import math
import pygame

GRID_WIDTH = 325 # width of the grid used by engine.py
GRID_HEIGHT = 175 # height of the grid used by engine.py

# for debugging and basic usage purposes
COLORS = {
    'background': [240, 240, 240],
    'black_pen' : [0, 0, 0],
    'green_pen': [0, 255, 0],
    'blue_pen': [0, 0, 255],
    'purple_pen': [128, 0, 128],
    'red_pen': [255, 0, 0],
    'orange_pen': [255, 128, 0],
    'yellow_pen': [255, 255, 0],
    'grey_pen': [128, 128, 128],
    'sky_blue_pen': [135, 206, 235],
    'brown_pen': [139, 69, 19],
    'white_pen': [255, 255, 255],
    'eraser': [240, 240, 240]
}

class GridCell:
    """Represents a single cell in the drawing grid."""
    def __init__(self, row, col, cell_size, color = COLORS['background']):
        """Initialize a new instance of the GridCell class."""
        self.row = row
        self.col = col
        self.cell_size = cell_size
        self.x = col * cell_size
        self.y = row * cell_size
        self.color = color

    def get_position(self):
        """Return the row, col position of the cell.

        Returns:
            A tuple of the (row, col) position of the cell.
        """
        return self.row, self.col

    def drawing(self, color):
        """Update the cell's color.

        Args:
            color (tuple): RGB color to assign to the cell.
        """
        self.color = color


class Grid:
    """Represents the drawable grid and handles drawing logic."""
    def __init__(self, pos, cell_size, cells = None, surface = None):
        """Initializes a new instance of the Grid class."""
        self.pos = pos
        self.cell_size = cell_size
        self.cells = self.create_cells(cells)

        # pre-calculating offset shapes
        self.brush_cache = {}
        for r in [1, 2, 4, 8]:
            self.brush_cache[r] = self.brush_offsets(r)

        surface_width = int(GRID_WIDTH * self.cell_size)
        surface_height = int(GRID_HEIGHT * self.cell_size)
        self.surface = pygame.Surface((surface_width, surface_height))
        if not cells:
            self.surface.fill(COLORS['background'])
        else:
            self.surface.blit(surface, (0,0))

    def get_cell_rect(self, row, col):
        """Calculate precise int bounds to prevent rounding gaps.

        Args:
            row (int): The row of the cell.
            col (int): The col of the cell.

        Returns:
            A tuple for a pygame rect.
        """

        x = int(col * self.cell_size)
        y = int(row * self.cell_size)

        next_x = int((col + 1) * self.cell_size)
        next_y = int((row + 1) * self.cell_size)

        return (x, y, next_x - x, next_y - y)


    def create_cells(self, cell_data):
        """Create the GridCell objects.

        Returns:
            List of the cells on the grid.
        """
        if cell_data:
            return [
                [GridCell(row, col, self.cell_size,
                          cell_data[row][col].color) for col in range(GRID_WIDTH)]
                for row in range(GRID_HEIGHT)
            ]
        return [
            [GridCell(row, col, self.cell_size) for col in range(GRID_WIDTH)]
            for row in range(GRID_HEIGHT)
        ]

    def get_cell(self, row, col):
        """Get a specific cell based on row and column.

        Args:
            row (int): The row of the cell.
            col (int): The column of the cell.

        Returns:
            The cell if in the boundary, none otherwise.
        """
        if 0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH:
            return self.cells[row][col]
        return None

    def set_pixel(self, row, col, color):
        """Set a single cell to a given color and updates surface.

        Args:
            row (int): The row of the cell
            col (int): The column of the cell.
            color (tuple): RGB color of the cell.
        """
        row, col = int(row), int(col)
        if 0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH:
            self.cells[row][col].color = color
            pygame.draw.rect(self.surface, color,
                             self.get_cell_rect(row, col))

    def brush_offsets(self, radius):
        """Generate relative offsets for a circular brush.

        Args:
            radius (int): The brush radius.

        Returns:
            A list of the relative offsets.
        """
        offsets = []
        for r in range(-radius, radius + 1):
            for c in range(-radius, radius + 1):
                if r * r + c * c <= radius * radius:
                    offsets.append((r, c))
        return offsets

    def draw_brush(self, row, col, color, radius=1):
        """Apply the drawing brush logic for the user's pointer.

        Args:
            row (float): The row of the cell to be drawn.
            col (float): The col of the cell to be drawn.
            color (tuple): The RGB color to be drawn into cell.
            radius (int): The radius of the brush.

        Returns:
            A list of modified pixels.
        """
        drawn_pixels =[]

        offsets = self.brush_cache[radius]

        for dr, dc in offsets:
            r = int(row + dr)
            c = int(col + dc)
            if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                self.cells[r][c].color = color
                pygame.draw.rect(self.surface, color,
                                self.get_cell_rect(r, c))
                drawn_pixels.append((r, c, color))

        return drawn_pixels

    def draw_line_cells(self, start, end, color, radius=2, normalized=False):
        """Create a smooth line between two pixel positions.

        Args:
            start (tuple): The starting row, col of the line.
            end (tuple): The end row, col of the line.
            color (tuple): The color of the line.
            radius (int): The brush radius of the line.

        Returns:
            A list of modified pixels
        """
        drawn_pixels = []
        x1, y1 = start
        x2, y2 = end

        # find the greatest diff, use as number of steps needed for line
        steps = max(abs(x1 - x2), abs(y1 - y2))
        steps = max(1, math.ceil(steps))
        if steps == 0:
            return self.draw_brush(y1 // self.cell_size, x1 // self.cell_size, color, radius)

        # draw between the start and end point
        for i in range(steps + 1):
            t = i / steps if steps != 0 else 0
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            if not normalized:
                y = y / self.cell_size
                x = x / self.cell_size
            drawn_pixels += self.draw_brush(y, x, color, radius)

        return drawn_pixels

    def fill_tool(self, start_row, start_col, new_color):
        """Perform a flood fill starting from a cell.

        Args:
            start_row (int): The starting row.
            start_col (int): The starting column.
            new_color (tuple): The new color to be filled.

        Returns:
            A list of modified pixels.
        """
        drawn_pixels = []
        visited = set()
        start_row, start_col = int(start_row), int(start_col)
        start_cell = self.get_cell(start_row, start_col)
        if not start_cell:
            return drawn_pixels

        target_color = start_cell.color

        if target_color == new_color:
            return drawn_pixels

        # DFS fill with stack instead of recursion
        update_stack = [(start_row, start_col)]
        while update_stack:
            row, col = update_stack.pop()

            if (row, col) in visited:
                continue
            visited.add((row, col))

            cell = self.get_cell(row, col)

            if cell and cell.color == target_color:
                self.set_pixel(row, col, new_color)

                drawn_pixels.append((row, col, tuple(new_color)))

                # add orthogonal neighbors to the stack
                update_stack.append((row + 1, col))
                update_stack.append((row - 1, col))
                update_stack.append((row, col + 1))
                update_stack.append((row, col - 1))

        return drawn_pixels

    def draw(self, window):
        """Render the grid surface onto given window.

        Args:
            window (pygame.Surface): The window to render on.
        """
        window.blit(self.surface, self.pos)


class DrawingWindow:
    """Handle user drawing input and records drawing operation."""
    def __init__(self, center_pos, size, draggable = False):
        """Initialize the drawing window."""
        self.center = center_pos
        self.init_pos = center_pos[2]
        self.init_size = size[2]
        self.draggable = draggable
        self.size = size[:2]
        self.z = 1

        self.cell_width = size[0] / GRID_WIDTH
        self.cell_height = size[1] / GRID_HEIGHT
        self.cell_size = min(self.cell_width, self.cell_height)

        self.pixel_width = int(self.cell_size * GRID_WIDTH)
        self.pixel_height = int(self.cell_size * GRID_HEIGHT)

        self.drawn_pixels = []

        self.pos = (
            self.center[0] - self.pixel_width / 2,
            self.center[1] - self.pixel_height / 2
        )
        self.init_y = center_pos[1]

        self.grid = Grid(self.pos, self.cell_size)
        self.brush_radius = 1
        self.current_color = COLORS['black_pen']
        self.current_tool = "brush"
        self.last_pos = None
        self.last_mouse = False
        self.font = pygame.font.SysFont("Consolas", 18)
        self.pen_colors = [
            ("Black", COLORS['black_pen']),
            ("Green", COLORS['green_pen']),
            ("Blue", COLORS['blue_pen']),
            ("Purple", COLORS['purple_pen']),
            ("Red", COLORS['red_pen']),
            ("Orange", COLORS['orange_pen']),
            ("Yellow", COLORS['yellow_pen']),
            ("Grey", COLORS['grey_pen']),
            ("Sky Blue", COLORS['sky_blue_pen']),
            ("Brown", COLORS['brown_pen']),
            ("White", COLORS['white_pen']),
            ("Erasing", COLORS['eraser'])
        ]
        self.color_index = 0

        # allows for storing last action, instead of sending it repeatedly
        self.color_state = None
        self.radius_state = None
        self.tool_state = None

    def convert_to_local(self, x, y):
        """Convert screen coordinates to local coordinates.

        Args:
            x (int): The screen x coordinate.
            y (int): The screen y coordinate.
        Returns:
            Tuple of the local coordinates.
        """
        return int(x / self.grid.cell_size), int(y / self.grid.cell_size)

    def update(self, mouse_pos, mouse_pressed, curr_color, brush_radius, current_tool):
        """Update the window based on user input.

        Args:
            mouse_pos (tuple): The row, col position of the mouse.
            mouse_pressed (bool): True if the user pressed the mouse.
            curr_color (tuple): Current user color.
            brush_radius (int): Radius of the brush.
            current_tool (string): Current user tool.
        """
        # mouse pos to grid pos
        this_x = mouse_pos[0] - self.pos[0]
        this_y = mouse_pos[1] - self.pos[1]

        #if this_x < 0 or this_x > self.size[0] or this_y < 0 or this_y > self.size[1]:
            #self.last_pos = None
            #return

        col, row = self.convert_to_local(this_x, this_y)

        # call drawing logic for all tools
        if mouse_pressed:
            if curr_color != self.color_state:
                self.drawn_pixels.append((-1, curr_color))
                self.color_state = curr_color

            if brush_radius != self.radius_state:
                self.drawn_pixels.append((0, brush_radius))
                self.radius_state = brush_radius

            if current_tool == "brush":
                # ensures no gaps in lines
                if self.last_pos and (col, row) != self.last_pos:
                    self.drawn_pixels.append((1,
                        self.convert_to_local(self.last_pos[0],
                                              self.last_pos[1]), (col, row)))
                    self.grid.draw_line_cells(
                        self.last_pos,
                        (this_x, this_y),
                        curr_color,
                        brush_radius)
                else:
                    # handle single click
                    self.drawn_pixels.append((1, (col, row),
                                              (col, row)))
                    self.grid.draw_brush(row, col, curr_color, brush_radius)
                self.last_pos = this_x, this_y
            elif current_tool == "fill":
                # ensures fill triggers once per click
                if not self.last_mouse:
                    self.drawn_pixels.append((2, (col, row)))
                    self.grid.fill_tool(row, col, curr_color)
        else:
            self.last_pos = None

        self.last_mouse = mouse_pressed

    def draw(self, screen, curr_color):
        """Render the drawing grid on the screen.

        Args:
            screen: (pygame.Surface): The screen being displayed.
            curr_color (tuple): Not used but needed to match game syntax.
        """
        self.grid.draw(screen)

    def color_switch(self, input_color=None):
        """Cycle through colors or set a specific color.

        Args:
            input_color (tuple, optional): Directly sets color.
        """
        if input_color:
            self.current_color = input_color
        self.color_index = (self.color_index +1) % len(self.pen_colors)
        name, color = self.pen_colors[self.color_index]
        self.current_color = color

    def handle_clicks(self, click):
        """Process keyboard events - for debugging.

        Args:
            click (pygame.event.Event): The incoming user action.
        """
        if click.type == pygame.KEYDOWN:
            if click.key == pygame.K_TAB:
                self.color_switch()
            elif click.key == pygame.K_1:
                self.brush_radius = 1
            elif click.key == pygame.K_2:
                self.brush_radius = 2
            elif click.key == pygame.K_3:
                self.brush_radius = 4
            elif click.key == pygame.K_f:
                self.current_tool = "fill"
            elif click.key == pygame.K_b:
                self.current_tool = "brush"

    def get_drawn_pixels(self):
        """Get the list of drawn pixels.

        Returns:
            A list of drawing actions.
        """
        return self.drawn_pixels

    def resize(self, wid, ht):
        """Resize the drawing window.

        Args:
            length (int): The length of the drawing window.
            ht (int): The height of the drawing window.
        """
        pos = [int(self.init_pos[0] * wid / 100), int(self.init_pos[1] * ht / 100)]
        size = (self.init_size[0] * wid / 1000.0,
                self.init_size[0] * wid / 1000.0 * 175 / 325.0)
        self.center = pos
        self.size = size

        self.cell_width = size[0] / GRID_WIDTH
        self.cell_height = size[1] / GRID_HEIGHT
        self.cell_size = min(self.cell_width, self.cell_height)

        self.pixel_width = int(self.cell_size * GRID_WIDTH)
        self.pixel_height = int(self.cell_size * GRID_HEIGHT)

        self.pos = (
            self.center[0] - self.pixel_width / 2,
            self.center[1] - self.pixel_height / 2
        )
        self.init_y = pos[1]
        self.grid.surface = pygame.transform.scale(self.grid.surface, self.size)
        self.grid = Grid(self.pos, self.cell_size, self.grid.cells, self.grid.surface)

    def get_color(self, mouse_pos):
        this_x = mouse_pos[0] - self.pos[0]
        this_y = mouse_pos[1] - self.pos[1]
        col, row = self.convert_to_local(this_x, this_y)
        if col < 0 or col >= GRID_WIDTH or row < 0 or row >= GRID_HEIGHT:
            return [240, 240, 240]
        return self.grid.cells[row][col].color


class AnimationWindow:
    """Replay drawing operations as an animation or display."""
    def __init__(self, center_pos, size, drawn_pixels, animated = False, draggable=False, z=1):
        """Initialize the animation window."""
        self.center = [center_pos[0], center_pos[1]]
        self.init_y = center_pos[1]
        self.init_y_norm = center_pos[2][1]
        self.size = size[:2]
        self.init_size = size[2]
        self.init_pos = center_pos[2]
        self.draggable = draggable
        self.z = z

        # needed with new drawn_pixels structure
        self.curr_color = COLORS['black_pen']
        self.curr_rad = 1

        self.cell_width = size[0] / GRID_WIDTH
        self.cell_height = size[1] / GRID_HEIGHT
        self.cell_size = min(self.cell_width, self.cell_height)

        self.pixel_width = int(self.cell_size * GRID_WIDTH)
        self.pixel_height = int(self.cell_size * GRID_HEIGHT)

        self.pos = [
            self.center[0] - self.pixel_width / 2,
            self.center[1] - self.pixel_height / 2
        ]

        self.grid = Grid(self.pos, self.cell_size)
        self.drawn_pixels = drawn_pixels
        self.index = 0
        self.fps = 24
        self.max_seconds = 5
        self.clock = pygame.time.Clock()

        self.total_pixels = len(drawn_pixels)

        # sets good pacing
        self.pixels_per_frame = max(20, self.total_pixels // (self.fps * self.max_seconds))
        self.done = False

        # should it be animated
        self.animated = animated

    def update(self):
        """Update the animation window by 'drawing' list of stored pixels"""
        if self.done:
            return

        actions_left = self.pixels_per_frame if self.animated \
            else len(self.drawn_pixels)

        for i in range(actions_left):
            if self.index >= len(self.drawn_pixels):
                self.done = True
                break

            action = self.drawn_pixels[self.index]
            op_code = action[0]

            if op_code == -1: # color change
                self.curr_color = action[1]

            elif op_code == 0: # radius change
                self.curr_rad = action[1]

            elif op_code == 1: # brush stroke
                self.grid.draw_line_cells(
                    action[1],
                    action[2],
                    self.curr_color,
                    self.curr_rad,
                    normalized=True
                )

            elif op_code == 2: # fill
                self.grid.fill_tool(
                    action[1][1],
                    action[1][0],
                    self.curr_color
                )

            self.index += 1

    def draw(self, screen, curr_color):
        """Render the animation window on the screen.

        Args:
            screen: (pygame.Surface): the screen being displayed.
            curr_color (tuple): Not used but needed to match game syntax.
        """
        self.grid.draw(screen)

    def resize(self, wid, ht):
        """resizes the animation window based on new dimensions
         Args:
            wid ,ht : New dimensions of screen for scaling
        """
        pos = [int(self.init_pos[0] * wid / 100),
               int(self.init_pos[1] * ht / 100)]
        size = [self.init_size[0] * wid / 1000.0,
                self.init_size[0] * wid / 1000.0 * 175 / 325.0]
        self.center = pos
        self.size = size

        self.cell_width = size[0] / GRID_WIDTH
        self.cell_height = size[1] / GRID_HEIGHT
        self.cell_size = min(self.cell_width, self.cell_height)

        self.pixel_width = int(self.cell_size * GRID_WIDTH)
        self.pixel_height = int(self.cell_size * GRID_HEIGHT)

        self.pos = [
            self.center[0] - self.pixel_width / 2,
            self.center[1] - self.pixel_height / 2
        ]
        self.init_y = pos[1]
        if self.draggable:
            self.init_y = self.init_y_norm * ht / 100
        self.grid.surface = pygame.transform.scale(self.grid.surface, self.size)
        self.grid = Grid(self.pos, self.cell_size, self.grid.cells, self.grid.surface)


def get_clicked_pos(position, cell_size):
    """Get the position of a user click

    Args:
        position (tuple): Row, col position on the grid.
        cell_size (int): Size of a cell on the grid.

    Returns:
        A tuple of row, col position.
    """
    x, y = position
    col = x // cell_size
    row = y // cell_size
    return row, col


def run_drawing(window):
    """Run the drawing window from this file for debugging purposes."""
    pygame.font.init()
    font = pygame.font.SysFont("Consolas", 18)

    draw_w = DrawingWindow((600, 400, (50, 50)), (845, 455, (70, 70)))

    run = True
    while run:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            draw_w.handle_clicks(event)

        draw_w.update(mouse_pos,
                        mouse_pressed,
                        draw_w.current_color,
                        draw_w.brush_radius,
                        draw_w.current_tool)

        window.fill(COLORS['background'])
        draw_w.draw(window, draw_w.current_color)


        # debugging text boxes
        text_surface = font.render(
            f"Brush size (press 1-4 to change): {draw_w.brush_radius}", True, (0, 0, 0))
        text_surface2 = font.render(
            f"Color (press TAB to cycle): {draw_w.current_color}", True, (0, 0, 0))
        text_surface3 = font.render(
            f"Brush type (press f or b to cycle): {draw_w.current_tool}", True, (0, 0, 0))

        window.blit(text_surface, (10, 10))
        window.blit(text_surface2, (10, 20))
        window.blit(text_surface3, (10, 30))

        pygame.display.update()
    return draw_w.get_drawn_pixels()

def run_animation(window, drawn_pixels):
    """Run the drawing window from this file for debugging purposes"""
    anim = AnimationWindow((600, 400, (50, 50)), (800, 600, (70, 70)),drawn_pixels, True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        anim.update()

        window.fill(COLORS['background'])
        anim.draw(window, (0,0,0))
        pygame.display.update()

if __name__ == '__main__':
    w = pygame.display.set_mode((1200, 800))
    try:
        pixels = run_drawing(w)
        run_animation(w, pixels)
    finally:
        pygame.quit()
