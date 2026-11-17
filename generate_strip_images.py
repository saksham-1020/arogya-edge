import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from simulator import BLOOD_GROUPS, ANTIGEN_MAP

def generate_well_texture(is_clumped: bool, size: int=120, hematocrit: float=42.0) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    radius = size // 2 - 6
    hct_norm = np.clip(hematocrit / 45.0, 0.4, 1.4)
    base_r = int(np.clip(160 * hct_norm, 110, 200))
    base_g = int(np.clip(25 * hct_norm, 10, 40))
    base_b = int(np.clip(30 * hct_norm, 15, 45))
    if not is_clumped:
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=(base_r, base_g, base_b, 250))
        draw.ellipse([center - radius // 2, center - radius // 2 - 4, center, center - 6], fill=(base_r + 45, base_g + 20, base_b + 20, 140))
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    else:
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=(235, 220, 190, 230))
        num_clumps = np.random.randint(45, 75)
        for _ in range(num_clumps):
            r = np.random.uniform(0, radius - 8)
            theta = np.random.uniform(0, 2 * np.pi)
            cx = center + int(r * np.cos(theta))
            cy = center + int(r * np.sin(theta))
            clump_size = np.random.randint(4, 11)
            c_r = int(np.clip(base_r * 0.7 + np.random.randint(-15, 15), 50, 140))
            c_g = int(np.clip(base_g * 0.6 + np.random.randint(-5, 5), 5, 25))
            c_b = int(np.clip(base_b * 0.6 + np.random.randint(-5, 5), 5, 25))
            draw.ellipse([cx - clump_size, cy - clump_size, cx + clump_size, cy + clump_size], fill=(c_r, c_g, c_b, 245))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    return img

def render_strip_image(blood_group: str, hematocrit: float=42.0, strip_id: str='STRIP_001') -> Image.Image:
    width, height = (500, 200)
    strip = Image.new('RGB', (width, height), (242, 243, 245))
    draw = ImageDraw.Draw(strip)
    draw.rounded_rectangle([10, 10, width - 10, height - 10], radius=15, fill=(250, 251, 252), outline=(210, 214, 219), width=2)
    draw.text((25, 20), 'AROGYA-EDGE PoC TEST CASSETTE', fill=(40, 50, 60))
    draw.text((25, 38), f'REF ID: {strip_id}  |  ABO/Rh TYPING', fill=(120, 130, 140))
    antigens = ANTIGEN_MAP[blood_group]
    well_labels = ['ANTI-A', 'ANTI-B', 'ANTI-D (Rh)']
    well_centers_x = [110, 250, 390]
    well_center_y = 120
    well_radius = 50
    for i in range(3):
        cx = well_centers_x[i]
        cy = well_center_y
        reacts = bool(antigens[i])
        draw.ellipse([cx - well_radius - 2, cy - well_radius - 2, cx + well_radius + 2, cy + well_radius + 2], fill=(215, 218, 222), outline=(180, 185, 192), width=1)
        draw.ellipse([cx - well_radius, cy - well_radius, cx + well_radius, cy + well_radius], fill=(255, 255, 255))
        texture = generate_well_texture(is_clumped=reacts, size=well_radius * 2, hematocrit=hematocrit)
        strip.paste(texture, (cx - well_radius, cy - well_radius), texture)
        label = well_labels[i]
        draw.text((cx - 24, cy + well_radius + 6), label, fill=(60, 70, 80))
    return strip

def generate_image_dataset(n_images: int=50):
    output_dir = os.path.join(os.path.dirname(__file__), 'dataset', 'images')
    os.makedirs(output_dir, exist_ok=True)
    print(f'[+] Generating {n_images} Realistic Photographic Blood Strip Images...')
    for i in range(1, n_images + 1):
        bg = np.random.choice(BLOOD_GROUPS)
        hct = float(np.random.uniform(22.0, 52.0))
        strip_id = f"STRIP_{bg.replace('+', 'POS').replace('-', 'NEG')}_{i:03d}"
        img = render_strip_image(blood_group=bg, hematocrit=hct, strip_id=strip_id)
        file_path = os.path.join(output_dir, f'{strip_id}.png')
        img.save(file_path, 'PNG')
        if i % 10 == 0 or i == n_images:
            print(f'  -> Generated {i}/{n_images} images (Saved: {os.path.basename(file_path)})')
    print(f'[+] Images saved successfully in: {output_dir}')
if __name__ == '__main__':
    generate_image_dataset(n_images=30)
