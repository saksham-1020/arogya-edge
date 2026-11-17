import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from simulator import BLOOD_GROUPS, ANTIGEN_MAP

def generate_well_texture(is_clumped: bool, size: int=120, hematocrit: float=42.0, is_weak: bool=False) -> Image.Image:
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
        num_clumps = np.random.randint(25, 45) if is_weak else np.random.randint(50, 80)
        for _ in range(num_clumps):
            r = np.random.uniform(0, radius - 8)
            theta = np.random.uniform(0, 2 * np.pi)
            cx = center + int(r * np.cos(theta))
            cy = center + int(r * np.sin(theta))
            clump_size = np.random.randint(3, 7) if is_weak else np.random.randint(4, 11)
            c_r = int(np.clip(base_r * 0.7 + np.random.randint(-15, 15), 50, 140))
            c_g = int(np.clip(base_g * 0.6 + np.random.randint(-5, 5), 5, 25))
            c_b = int(np.clip(base_b * 0.6 + np.random.randint(-5, 5), 5, 25))
            draw.ellipse([cx - clump_size, cy - clump_size, cx + clump_size, cy + clump_size], fill=(c_r, c_g, c_b, 245))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    return img

def render_strip(blood_group: str, hematocrit: float, is_weak: bool, strip_id: str) -> Image.Image:
    width, height = (500, 200)
    strip = Image.new('RGB', (width, height), (242, 243, 245))
    draw = ImageDraw.Draw(strip)
    draw.rounded_rectangle([10, 10, width - 10, height - 10], radius=15, fill=(250, 251, 252), outline=(210, 214, 219), width=2)
    draw.text((25, 20), 'AROGYA-EDGE PoC TEST CASSETTE', fill=(40, 50, 60))
    draw.text((25, 38), f'REF ID: {strip_id}', fill=(120, 130, 140))
    antigens = ANTIGEN_MAP[blood_group]
    well_labels = ['ANTI-A', 'ANTI-B', 'ANTI-D (Rh)']
    well_centers_x = [110, 250, 390]
    well_center_y = 120
    well_radius = 50
    for i in range(3):
        cx = well_centers_x[i]
        cy = well_center_y
        reacts = bool(antigens[i])
        weak_ch = is_weak and i in [0, 2] and reacts
        draw.ellipse([cx - well_radius - 2, cy - well_radius - 2, cx + well_radius + 2, cy + well_radius + 2], fill=(215, 218, 222), outline=(180, 185, 192), width=1)
        draw.ellipse([cx - well_radius, cy - well_radius, cx + well_radius, cy + well_radius], fill=(255, 255, 255))
        texture = generate_well_texture(is_clumped=reacts, size=well_radius * 2, hematocrit=hematocrit, is_weak=weak_ch)
        strip.paste(texture, (cx - well_radius, cy - well_radius), texture)
        draw.text((cx - 24, cy + well_radius + 6), well_labels[i], fill=(60, 70, 80))
    brightness_factor = np.random.uniform(0.85, 1.15)
    strip = ImageEnhance.Brightness(strip).enhance(brightness_factor)
    contrast_factor = np.random.uniform(0.9, 1.1)
    strip = ImageEnhance.Contrast(strip).enhance(contrast_factor)
    return strip

def build_split_dataset(total_images: int=1200):
    base_dir = os.path.join(os.path.dirname(__file__), 'dataset', 'vision_dataset')
    splits = {'train': int(total_images * 0.7), 'val': int(total_images * 0.15), 'test': int(total_images * 0.15)}
    print(f"[+] Creating Vision Dataset of {total_images} images (Train: {splits['train']}, Val: {splits['val']}, Test: {splits['test']})...")
    manifest = []
    for split_name, count in splits.items():
        split_dir = os.path.join(base_dir, split_name)
        os.makedirs(split_dir, exist_ok=True)
        for i in range(1, count + 1):
            bg = np.random.choice(BLOOD_GROUPS)
            hct = float(np.random.uniform(19.0, 58.0))
            weak = np.random.rand() < 0.15
            strip_id = f"{split_name}_{bg.replace('+', 'POS').replace('-', 'NEG')}_{i:04d}"
            img = render_strip(blood_group=bg, hematocrit=hct, is_weak=weak, strip_id=strip_id)
            img_path = os.path.join(split_dir, f'{strip_id}.png')
            img.save(img_path, 'PNG')
            manifest.append(f'{split_name},{strip_id}.png,{bg},{hct:.1f},{(1 if weak else 0)}\n')
        print(f'  -> Generated {split_name} split ({count} images)')
    manifest_file = os.path.join(base_dir, 'manifest.csv')
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write('split,filename,blood_group,hematocrit,is_weak\n')
        f.writelines(manifest)
    print(f'[+] Large-Scale Vision Dataset generated successfully at: {base_dir}')
if __name__ == '__main__':
    build_split_dataset(total_images=1200)
