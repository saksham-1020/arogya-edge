import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def extract_micro_clumps(crop_bgr):
    h, w, _ = crop_bgr.shape
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Background subtraction via morphological opening (top-hat transform)
    # Extracts bright or dark granular micro-clumps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    texture = cv2.add(tophat, blackhat)
    
    # 2. Local adaptive thresholding to isolate micro-clump granules
    norm_texture = cv2.normalize(texture, None, 0, 255, cv2.NORM_MINMAX)
    _, binary = cv2.threshold(norm_texture, 40, 255, cv2.THRESH_BINARY)
    
    # 3. Find individual micro-clump contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    clump_details = []
    total_clump_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if 2 <= area <= (h * w * 0.4): # filter tiny noise and whole-drop borders
            total_clump_area += area
            x, y, bw, bh = cv2.boundingRect(c)
            clump_details.append({
                'contour': c,
                'area': area,
                'center': (x + bw // 2, y + bh // 2),
                'bbox': (x, y, bw, bh)
            })
            
    total_well_area = np.pi * ((min(h, w) // 2) ** 2)
    area_coverage_pct = (total_clump_area / max(1, total_well_area)) * 100.0
    num_clumps = len(clump_details)
    
    # Clinical Agglutination Grading (0+ to 4+)
    if area_coverage_pct < 2.0 and num_clumps < 5:
        grade = "0+ (Negative / Smooth)"
    elif area_coverage_pct < 8.0:
        grade = "1+ (Weak / Fine Granules)"
    elif area_coverage_pct < 18.0:
        grade = "2+ (Moderate / Small Clumps)"
    elif area_coverage_pct < 35.0:
        grade = "3+ (Strong / Large Clumps)"
    else:
        grade = "4+ (Very Strong / Solid Agglutinate)"
        
    # Generate Clump Overlay
    overlay = crop_bgr.copy()
    cv2.drawContours(overlay, [cd['contour'] for cd in clump_details], -1, (0, 255, 0), 1) # Green outlines
    
    # Generate Heatmap
    heatmap = cv2.applyColorMap(norm_texture, cv2.COLORMAP_JET)
    heatmap_blended = cv2.addWeighted(crop_bgr, 0.4, heatmap, 0.6, 0)
    
    return {
        'num_clumps': num_clumps,
        'area_coverage_pct': area_coverage_pct,
        'grade': grade,
        'overlay': overlay,
        'heatmap': heatmap_blended,
        'norm_texture': norm_texture,
        'contours': [cd['contour'] for cd in clump_details]
    }

def visualize_slide_micro_clumps(image_path: str, output_path: str = "micro_clumps_visualization.png"):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading {image_path}")
        return
        
    from predict_from_image import detect_3_drops
    peaks, cy, ir = detect_3_drops(img)
    
    h, w, _ = img.shape
    well_names = ['Well-A (Anti-A)', 'Well-B (Anti-B)', 'Well-D (Anti-D / Rh)']
    
    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    fig.patch.set_facecolor('#0f172a')
    
    col_titles = ['Original Well (Zoom)', 'Micro-Clump Texture Filter', 'Granule Segmentation Mask', 'Agglutination Density Heatmap']
    for j, col_title in enumerate(col_titles):
        axes[0, j].set_title(col_title, color='#38bdf8', fontsize=12, fontweight='bold', pad=10)
        
    for i, cx in enumerate(peaks):
        crop = img[max(0, cy - ir):min(h, cy + ir), max(0, cx - ir):min(w, cx + ir)]
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        
        res = extract_micro_clumps(crop)
        
        # 1. Original RGB
        axes[i, 0].imshow(crop_rgb)
        axes[i, 0].set_ylabel(f"{well_names[i]}\nGrade: {res['grade']}", color='#f8fafc', fontsize=10, fontweight='bold')
        axes[i, 0].axis('off')
        
        # 2. Micro-clump texture filter
        axes[i, 1].imshow(res['norm_texture'], cmap='magma')
        axes[i, 1].axis('off')
        
        # 3. Granule Segmentation Mask with green contours
        overlay_rgb = cv2.cvtColor(res['overlay'], cv2.COLOR_BGR2RGB)
        axes[i, 2].imshow(overlay_rgb)
        axes[i, 2].axis('off')
        axes[i, 2].text(5, crop.shape[0] - 8, f"Clumps: {res['num_clumps']} | Area: {res['area_coverage_pct']:.1f}%", 
                        color='#4ade80', fontsize=9, fontweight='bold', bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))
        
        # 4. Agglutination Density Heatmap
        heatmap_rgb = cv2.cvtColor(res['heatmap'], cv2.COLOR_BGR2RGB)
        axes[i, 3].imshow(heatmap_rgb)
        axes[i, 3].axis('off')
        
    plt.suptitle(f"CLINICAL MICRO-CLUMP MULTI-SPECTRAL GRANULARITY ANALYSIS\nSource: {os.path.basename(image_path)}", 
                 color='#ffffff', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[+] Micro-clump visualization saved to: {output_path}")

if __name__ == "__main__":
    sample_img = r'C:/Users/Saksham Tomar/.gemini/antigravity/brain/566d1ef6-9c6a-4f6b-91f4-28f7bdeff862/.user_uploaded/media_1794909291235_ec529c94.jpg'
    visualize_slide_micro_clumps(sample_img, "micro_clumps_visualization.png")
