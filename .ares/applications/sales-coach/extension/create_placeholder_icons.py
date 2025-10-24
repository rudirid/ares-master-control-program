#!/usr/bin/env python3
"""
Create placeholder icons for Sales Coach extension.
Uses PIL/Pillow to generate simple green icons with "SC" text.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL/Pillow not installed. Install with: pip install Pillow")
    print("\nAlternatively, create icons manually using the instructions in ICON_INSTRUCTIONS.txt")
    exit(1)

import os

# Icon sizes required
SIZES = [16, 48, 128]
COLOR = '#4CAF50'  # Green
TEXT = 'SC'

# Get icons directory
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
os.makedirs(icons_dir, exist_ok=True)

for size in SIZES:
    # Create image
    img = Image.new('RGB', (size, size), color=COLOR)
    draw = ImageDraw.Draw(img)

    # Try to use a font, fall back to default if not available
    try:
        # Adjust font size based on icon size
        font_size = int(size * 0.5)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw text in center
    text_bbox = draw.textbbox((0, 0), TEXT, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2

    draw.text((x, y), TEXT, fill='white', font=font)

    # Save
    filename = os.path.join(icons_dir, f'icon{size}.png')
    img.save(filename)
    print(f"Created: {filename}")

print("\nPlaceholder icons created successfully!")
print("These are simple temporary icons. Replace with professional designs later.")
