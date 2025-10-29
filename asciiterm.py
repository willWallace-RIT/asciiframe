import sys
from PIL import Image
import io


# --- Configuration ---
# Target size for the ASCII art output (Terminal dimensions)
TERM_WIDTH = 50
TERM_HEIGHT = 50

#DIFIED ASCII_CHARS ---
# The last four characters (%B@$) have been replaced with the Unicode block shading characters
# \u2591 (Light Shade), \u2592 (Medium Shade), \u2593 (Dark Shade), and \u2588 (Full Block),
# which correspond to finer resolution for the darker pixel values.
# The original list had 69 characters. The new list also has 69 characters.
ASCII_CHARS = "`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8\u2591\u2592\u2593\u2588"

# --- Hardcode the target size ---
TARGET_WIDTH = 50
TARGET_HEIGHT = 50
# --------------------------------

def convert_to_ascii(image):
    # Resize the image to the fixed target size
    width, height = TARGET_WIDTH, TARGET_HEIGHT
    image = image.resize((width, height))
   
    # Convert image to grayscale
    image = image.convert('L')
   
    pixels = image.getdata()
    ascii_str = ""
    
    # Calculate the max index for the ASCII_CHARS string
    max_index = len(ASCII_CHARS) - 1
   
    for pixel_value in pixels:
        # Map pixel value (0-255) to an index (0-max_index)
        ascii_str += ASCII_CHARS[int(pixel_value / 255 * max_index)]
   
    return [ascii_str[i:i+width] for i in range(0, len(ascii_str), width)]



# ANSI color codes for 8-bit terminal colors (closest to standard desktop colors)
# Format: (R, G, B) -> ANSI Code
# We use the 'filled block' character: '\u2588'
ANSI_COLOR_MAP = {
    (0, 0, 0): '\033[30m',      # Black
    (128, 0, 0): '\033[31m',    # Red
    (0, 128, 0): '\033[32m',    # Green
    (128, 128, 0): '\033[33m',  # Yellow
    (0, 0, 128): '\033[34m',    # Blue
    (128, 0, 128): '\033[35m',  # Magenta
    (0, 128, 128): '\033[36m',  # Cyan
    (192, 192, 192): '\033[37m',# White/Light Gray
    # Bright colors for better fidelity
    (255, 0, 0): '\033[91m',    # Bright Red
    (0, 255, 0): '\033[92m',    # Bright Green
    (255, 255, 0): '\033[93m',  # Bright Yellow
    (0, 0, 255): '\033[94m',    # Bright Blue
    (255, 0, 255): '\033[95m',  # Bright Magenta
    (0, 255, 255): '\033[96m',  # Bright Cyan
    (255, 255, 255): '\033[97m',# Bright White
}
RESET_COLOR = '\033[0m'


def get_closest_ansi_color(r, g, b):
    """Finds the closest ANSI color code for a given RGB color."""
    min_dist = float('inf')
    closest_color_code = ANSI_COLOR_MAP[(0, 0, 0)] # Default to Black


    for (map_r, map_g, map_b), code in ANSI_COLOR_MAP.items():
        # Calculate Euclidean distance in RGB space
        dist = (r - map_r)**2 + (g - map_g)**2 + (b - map_b)**2
        if dist < min_dist:
            min_dist = dist
            closest_color_code = code
    return closest_color_code


def process_frame(image_bytes):
    """Processes a single image frame (PNG data) to produce ASCII output."""
    try:
        # Open image from bytes piped by ffmpeg
        image = Image.open(io.BytesIO(image_bytes))
        imargestr=convert_to_ascii(image)
        # Resize image to match terminal dimensions for block characters
        img_resized = image.resize((TERM_WIDTH, TERM_HEIGHT))
       
        # Convert to RGB if not already
        img_rgb = img_resized.convert("RGB")
       
        output_frame = []
        for y in range(TERM_HEIGHT):
            line = []
            for x in range(TERM_WIDTH):
                # Get the color of the "pixel" (which will be one block character)
                r, g, b = img_rgb.getpixel((x, y))
               
                # Determine the best terminal color
                color_code = get_closest_ansi_color(r, g, b)
                asciichar=imargestr[y][x]
                # Append the color code, the filled block character, and the reset code
                # Note: We append the RESET_COLOR at the end of the line, or before the next color change
                # For simplicity, we just set the foreground color and rely on the terminal to handle it.
                line.append(f"{color_code}\u2588")

            # Reset color at the end of the line
            output_frame.append("".join(line) + RESET_COLOR)


        print("\n".join(output_frame))


    except Exception as e:
        # This catches EOF/pipe close and other errors gracefully
        # print(f"Error processing frame: {e}", file=sys.stderr)
        pass


def main():
    # Loop continuously to read image data from standard input (the pipe)
    # The 'ffmpeg' command pipes *multiple* PNG images consecutively.
    image_data = b''
    while True:
        # Read a chunk of data
        chunk = sys.stdin.buffer.read(4096)
        if not chunk:
            break
        image_data += chunk
       # PNG files start with b'\x89PNG'
        # We search for the start of the next PNG to delimit the current frame.
        # Note: This is a simplified frame delimiter and may break with corrupted data.
        while True:
            png_header = b'\x89PNG'
            start_index = image_data.find(png_header, 1) # Start search after the very first byte
           
            if start_index != -1:
                # Found the start of the next frame
                frame_data = image_data[:start_index]
                image_data = image_data[start_index:]
               
                # Process the isolated frame
                process_frame(frame_data)
            else:
                # No more complete frames in the buffer, wait for more data
                break


if __name__ == '__main__':
    # Flush stdout to ensure frames are displayed immediately
    sys.stdout.reconfigure(encoding='utf-8')
    main()
