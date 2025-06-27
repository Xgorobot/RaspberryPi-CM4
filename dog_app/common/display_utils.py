from PIL import Image, ImageDraw, ImageFont
import os

# Attempt to import the new LCD module location
try:
    from .lcd_2inch import LCD_2inch
except ImportError:
    # Fallback for direct execution or if path issues occur during refactoring
    # This assumes lcd_2inch.py is in the same directory if run directly
    print("Warning: Could not import .lcd_2inch, trying lcd_2inch directly.")
    try:
        import lcd_2inch # For local testing if this file is run directly
        LCD_2inch = lcd_2inch.LCD_2inch
    except ImportError:
        print("Error: LCD_2inch module not found. Display functionalities will fail.")
        LCD_2inch = None # Placeholder if import fails

# Define Colors
BTN_SELECTED_COLOR = (24, 47, 223)
BTN_UNSELECTED_COLOR = (20, 30, 53)
TXT_SELECTED_COLOR = (255, 255, 255)
TXT_UNSELECTED_COLOR = (76, 86, 127)
SPLASH_THEME_COLOR = (15, 21, 46) # Used for background
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (238, 55, 59)

# Font Cache
_font_cache = {}

# Base path for assets within the dog_app project
# Assumes display_utils.py is in dog_app/common/
# So, ../assets/ would be dog_app/assets/
PROJECT_ROOT_GUESS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSET_BASE_PATH = os.path.join(PROJECT_ROOT_GUESS, "assets")

FONT_NAME = "msyh.ttc" # Default font file name
FONT_PATH = os.path.join(ASSET_BASE_PATH, "fonts", FONT_NAME)

def get_font(size):
    if size not in _font_cache:
        try:
            # print(f"Attempting to load font: {FONT_PATH}")
            _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
        except IOError:
            print(f"Warning: Font file not found at {FONT_PATH}. Using default font.")
            _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]

# Define Font Sizess
FONT_SIZE_SMALL = 15
FONT_SIZE_MEDIUM = 22
FONT_SIZE_LARGE = 30
FONT_SIZE_XLARGE = 40

font1 = get_font(FONT_SIZE_SMALL)
font2 = get_font(FONT_SIZE_MEDIUM)
font3 = get_font(FONT_SIZE_LARGE)
font4 = get_font(FONT_SIZE_XLARGE)

# --- Global Display Objects ---
# This section needs careful management in a larger application.
# Consider encapsulating into a DisplayManager class.
if LCD_2inch:
    display = LCD_2inch()
    display.Init()
    display.clear()
    splash = Image.new("RGB", (display.height, display.width), SPLASH_THEME_COLOR)
    draw = ImageDraw.Draw(splash) # Main drawing context
    display.ShowImage(splash) # Initial display of blank splash
else:
    display = None
    splash = None
    draw = None
    print("Error: Display not initialized.")

# BATTERY_ICON_NAME = "battery.png" # Removed
# BATTERY_ICON_PATH = os.path.join(ASSET_BASE_PATH, "images", BATTERY_ICON_NAME) # Removed

# try: # Removed
    # print(f"Attempting to load battery icon: {BATTERY_ICON_PATH}") # Removed
    # bat_icon = Image.open(BATTERY_ICON_PATH) # Removed
# except FileNotFoundError: # Removed
    # print(f"Warning: Battery icon not found at {BATTERY_ICON_PATH}") # Removed
bat_icon = None # Ensure bat_icon is None if other parts of the code might still reference it defensively

def lcd_draw_string(pil_draw_context, x, y, text, color=COLOR_WHITE, font_object=None):
    if font_object is None:
        font_object = font1 # Default to small font
    if pil_draw_context:
        pil_draw_context.text((x, y), text, fill=color, font=font_object)

def lcd_rect(pil_draw_context, x, y, w, h, color, thickness=-1): # thickness -1 for fill
    if pil_draw_context:
        pil_draw_context.rectangle([(x, y), (w, h)], fill=color, width=thickness)

def show_battery_info(pil_draw_context, current_display, battery_level, dog_instance=None):
    """
    Displays the battery level on the screen.
    Needs a PIL draw context, the display object to show the image, and battery level.
    dog_instance is for compatibility, ideally battery_level is passed directly.
    """
    if not pil_draw_context or not current_display:
        print("Error: Draw context or display not available for show_battery_info.")
        return

    # Clear area for battery info
    lcd_rect(pil_draw_context, 200, 0, 320, 25, SPLASH_THEME_COLOR, -1) # x,y,w,h

    # if bat_icon: # Removed block for drawing battery icon
        # pil_draw_context.bitmap((270, 4), bat_icon, fill=COLOR_WHITE) # Assuming icon is black/transparent

    actual_battery_level = battery_level
    if dog_instance and battery_level is None: # Fallback to reading from dog if not provided
        try:
            actual_battery_level = dog_instance.read_battery()
        except Exception as e:
            print(f"Error reading battery from dog_instance: {e}")
            actual_battery_level = "N/A"

    if actual_battery_level is None: # If still None
        actual_battery_level = "N/A"

    level_str = str(actual_battery_level)
    if level_str == "0": # Original code had specific check for "0" implying error
        level_str = "N/A"
        print("Warning: Battery level reported as 0, possibly an error.")

    # Adjust text position based on length
    if level_str == "100": # Max length assumed
        lcd_draw_string(pil_draw_context, 274, 4, level_str, COLOR_WHITE, font1)
    elif len(level_str) == 2:
        lcd_draw_string(pil_draw_context, 280, 4, level_str, COLOR_WHITE, font1)
    elif len(level_str) == 1 and level_str != "0": # For single digit that's not "0"
        lcd_draw_string(pil_draw_context, 286, 4, level_str, COLOR_WHITE, font1)
    else: # For "N/A" or other cases
        lcd_draw_string(pil_draw_context, 274, 4, level_str, COLOR_WHITE, font1)

    # After drawing, the image needs to be shown on the display
    # current_display.ShowImage(pil_draw_context._image if hasattr(pil_draw_context, '_image') else splash)


# Placeholder for draw_cir and draw_wave, as they might be more specific to demos
# Or they can be utility functions if generic enough.
# For now, let's include them but acknowledge they use the global `draw`.

def draw_cir(pil_draw_context, ch):
    """Draws circles, assumes pil_draw_context is the global `draw`."""
    if not pil_draw_context: return
    # Clear area
    pil_draw_context.rectangle([(55, 40), (120, 100)], fill=SPLASH_THEME_COLOR)
    pil_draw_context.rectangle([(205, 40), (270, 100)], fill=SPLASH_THEME_COLOR)
    radius = 4
    cy = 70
    centers = [(62, cy), (87, cy), (112, cy), (210, cy), (235, cy), (260, cy)]
    for center_x, center_y in centers:
        random_offset = ch # ch seems to be an offset value
        new_y1 = center_y + random_offset
        new_y2 = center_y - random_offset
        pil_draw_context.line([(center_x, new_y2), (center_x, new_y1)], fill=COLOR_WHITE, width=11)
        pil_draw_context.ellipse([(center_x - radius, new_y1 - radius), (center_x + radius, new_y1 + radius)], fill=COLOR_WHITE)
        pil_draw_context.ellipse([(center_x - radius, new_y2 - radius), (center_x + radius, new_y2 + radius)], fill=COLOR_WHITE)

def draw_wave(pil_draw_context, ch):
    """Draws waves, assumes pil_draw_context is the global `draw`."""
    if not pil_draw_context: return
    # This function is quite complex and might be demo-specific.
    # For now, copying structure.
    # First wave
    start_x, start_y, width, height = 40, 42, 80, 50
    pil_draw_context.rectangle([(start_x - 1, start_y), (start_x + width, start_y + height)], fill=SPLASH_THEME_COLOR)
    # ... (implementation of wave drawing logic) ...

    # Second wave
    start_x, start_y, width, height = 210, 42, 80, 50
    pil_draw_context.rectangle([(start_x - 1, start_y), (start_x + width, start_y + height)], fill=SPLASH_THEME_COLOR)
    # ... (implementation of wave drawing logic) ...
    # Note: The actual wave drawing logic from uiutils.py is omitted for brevity here
    # but should be included if these functions are to be kept.
    # It involves random segment lengths and gaps.

def get_main_draw_context():
    """Returns the global PIL ImageDraw object."""
    return draw

def get_main_splash_image():
    """Returns the global PIL Image object (the splash screen)."""
    return splash

def get_display_manager():
    """Returns the global display hardware interface object."""
    return display

if __name__ == '__main__':
    print("Display Utils Test")
    if display and draw and splash:
        lcd_rect(draw, 10, 10, 310, 230, COLOR_BLACK, -1)
        lcd_draw_string(draw, 20, 20, "Hello from Display Utils!", COLOR_WHITE, font2)

        # Test battery display (passing None for dog_instance, providing level directly)
        show_battery_info(draw, display, 75)
        display.ShowImage(splash) # Update the physical display
        print("Drew test string and battery info. Check LCD.")
        time.sleep(5)

        # Test draw_cir (passing global draw context and a dummy offset)
        # draw_cir(draw, 5)
        # display.ShowImage(splash)
        # print("Drew circles. Check LCD.")
        # time.sleep(3)

        # Clear screen to theme color
        lcd_rect(draw, 0,0, display.height, display.width, SPLASH_THEME_COLOR, -1)
        display.ShowImage(splash)
        print("Screen cleared.")
    else:
        print("Display objects not initialized. Cannot run test.")

    print("Test complete.")
