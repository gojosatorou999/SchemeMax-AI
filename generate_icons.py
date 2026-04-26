import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color='#2C7BE5')
    draw = ImageDraw.Draw(img)
    text = "SM"
    
    # Very basic font loading, falling back to default if unavailable
    try:
        font = ImageFont.truetype("arial.ttf", size=int(size*0.4))
    except:
        font = ImageFont.load_default()
        
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    # Centered text
    draw.text(((size-w)/2, (size-h)/2), text, font=font, fill='white')
    
    os.makedirs('static/icons', exist_ok=True)
    img.save(f'static/icons/{filename}')
    print(f"Created {filename}")

if __name__ == "__main__":
    create_icon(192, 'icon-192.png')
    create_icon(512, 'icon-512.png')
