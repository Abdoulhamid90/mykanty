from PIL import Image, ImageDraw, ImageFont
import os

def create_pwa_icons():
    os.makedirs('static/icons', exist_ok=True)
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Fond dégradé orange-vert
        for y in range(size):
            ratio = y / size
            r = int(255 * (1 - ratio))
            g = int(153 * (1 - ratio) + 107 * ratio)
            b = int(51 * (1 - ratio) + 63 * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b))
        
        # Texte "MK"
        try:
            font = ImageFont.truetype("arial.ttf", int(size * 0.5))
        except:
            font = ImageFont.load_default()
        
        text = "MK"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x+2, y+2), text, fill=(0,0,0,128), font=font)
        draw.text((x, y), text, fill='white', font=font)
        
        filename = f'static/icons/icon-{size}x{size}.png'
        img.save(filename, 'PNG')
        print(f'✅ {filename}')
    
    print(f"\n🎉 {len(sizes)} icônes créées!")

if __name__ == '__main__':
    create_pwa_icons()