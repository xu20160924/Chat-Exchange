"""Simple image CAPTCHA generator for registration"""
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def generate_captcha_text(length=4):
    """Generate random CAPTCHA text (numbers and uppercase letters)"""
    # Exclude confusing characters like 0, O, I, 1
    characters = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    return ''.join(random.choice(characters) for _ in range(length))


def create_captcha_image(text, width=120, height=40):
    """
    Create a CAPTCHA image with the given text
    
    Args:
        text: The CAPTCHA text to display
        width: Image width in pixels
        height: Image height in pixels
    
    Returns:
        BytesIO object containing the PNG image
    """
    # Create image with background
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Add background noise (dots)
    for _ in range(random.randint(50, 100)):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(
            random.randint(150, 200),
            random.randint(150, 200),
            random.randint(150, 200)
        ))
    
    # Add background lines
    for _ in range(random.randint(2, 4)):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(
            random.randint(180, 220),
            random.randint(180, 220),
            random.randint(180, 220)
        ), width=1)
    
    # Calculate text positioning
    char_width = width // len(text)
    
    # Draw each character with random positioning and rotation
    for i, char in enumerate(text):
        # Random color for each character
        color = (
            random.randint(0, 100),
            random.randint(0, 100),
            random.randint(0, 100)
        )
        
        # Create a temporary image for this character
        char_image = Image.new('RGBA', (char_width, height), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_image)
        
        # Try to use a font, fall back to default if not available
        # Use MASSIVE font size to make characters fill 80% of 40px height = 32px font
        font_size = 32
        font = None
        
        # Try multiple font paths (macOS + CentOS 7 compatible)
        font_paths = [
            # CentOS 7 / RHEL fonts
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
            # Debian/Ubuntu fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            # macOS fonts
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            # Windows fonts
            "C:\\Windows\\Fonts\\arial.ttf",
            "arial.ttf"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        # If no TrueType font found, use default
        if font is None:
            font = ImageFont.load_default()
            # Draw text only twice for slight boldness, avoid fuzziness
            char_draw.text((5, 12), char, fill=color, font=font)
            char_draw.text((6, 12), char, fill=color, font=font)
        else:
            # Draw the character with TrueType font centered in the space
            char_draw.text((1, 2), char, fill=color, font=font)
        
        # Random rotation (reduced for better readability)
        rotated = char_image.rotate(random.randint(-20, 20), expand=False, fillcolor=(255, 255, 255, 0))
        
        # Paste onto main image
        image.paste(rotated, (i * char_width + random.randint(-5, 5), random.randint(-5, 5)), rotated)
    
    # Skip blur filter to keep characters sharp
    # image = image.filter(ImageFilter.SMOOTH)
    
    # Convert to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def verify_captcha(user_input, stored_captcha):
    """
    Verify user's CAPTCHA input
    
    Args:
        user_input: The text entered by user
        stored_captcha: The correct CAPTCHA text from session
    
    Returns:
        Boolean indicating if CAPTCHA is correct
    """
    if not user_input or not stored_captcha:
        return False
    
    # Case-insensitive comparison
    return user_input.strip().upper() == stored_captcha.upper()

