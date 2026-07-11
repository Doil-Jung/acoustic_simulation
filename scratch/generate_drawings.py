import math
import os

def create_svg(filename, cup_d, outer_d=358.0, pcd=240.0, sq=20.2):
    # Centered on a canvas that is outer_d + 42 (with 21mm margins)
    canvas_size = outer_d + 42
    cx, cy = canvas_size / 2.0, canvas_size / 2.0
    r_outer = outer_d / 2.0
    r_cup = cup_d / 2.0
    r_pcd = pcd / 2.0
    half_sq = sq / 2.0
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_size}mm" height="{canvas_size}mm" viewBox="0 0 {canvas_size} {canvas_size}">')
    svg.append(f'  <!-- Layer Info: OD={outer_d}mm, Cup Hole D={cup_d}mm, Center Square={sq}mm -->')
    # Outer circle
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="red" stroke-width="0.1" />')
    # Center square
    x1, y1 = cx - half_sq, cy - half_sq
    svg.append(f'  <rect x="{x1}" y="{y1}" width="{sq}" height="{sq}" fill="none" stroke="red" stroke-width="0.1" />')
    # 6 holes
    for i in range(6):
        angle = math.radians(i * 60.0)
        hx = cx + r_pcd * math.cos(angle)
        hy = cy + r_pcd * math.sin(angle)
        svg.append(f'  <circle cx="{hx}" cy="{hy}" r="{r_cup}" fill="none" stroke="red" stroke-width="0.1" />')
    svg.append('</svg>')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Generated SVG: {filename}")

def create_dxf(filename, cup_d, outer_d=358.0, pcd=240.0, sq=20.2):
    # Centered at (0, 0) for DXF
    r_outer = outer_d / 2.0
    r_cup = cup_d / 2.0
    r_pcd = pcd / 2.0
    half_sq = sq / 2.0
    
    entities = []
    
    # Outer circle
    entities.append(f"0\nCIRCLE\n8\n0\n10\n0.0\n20\n0.0\n30\n0.0\n40\n{r_outer:.3f}")
    
    # Center square (4 lines)
    x1, y1 = -half_sq, -half_sq
    x2, y2 = half_sq, -half_sq
    x3, y3 = half_sq, half_sq
    x4, y4 = -half_sq, half_sq
    
    coords = [(x1, y1, x2, y2), (x2, y2, x3, y3), (x3, y3, x4, y4), (x4, y4, x1, y1)]
    for sx, sy, ex, ey in coords:
        entities.append(f"0\nLINE\n8\n0\n10\n{sx:.3f}\n20\n{sy:.3f}\n30\n0.0\n11\n{ex:.3f}\n21\n{ey:.3f}\n31\n0.0")
        
    # 6 holes
    for i in range(6):
        angle = math.radians(i * 60.0)
        hx = r_pcd * math.cos(angle)
        hy = r_pcd * math.sin(angle)
        entities.append(f"0\nCIRCLE\n8\n0\n10\n{hx:.3f}\n20\n{hy:.3f}\n30\n0.0\n40\n{r_cup:.3f}")
        
    content = [
        "0", "SECTION",
        "2", "HEADER",
        "9", "$ACADVER",
        "1", "AC1015",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "ENTITIES"
    ]
    content.extend(entities)
    content.extend([
        "0", "ENDSEC",
        "0", "EOF"
    ])
    
    with open(filename, 'w', encoding='ascii') as f:
        f.write('\n'.join(content) + '\n')
    print(f"Generated DXF: {filename}")

if __name__ == "__main__":
    docs_dir = r"c:\Users\user\OneDrive - 충북과학고등학교\원드라이브 동기화 폴더\코딩 작업 폴더\acoustic_simulation\docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # Type 1: ø358 OD, ø100.5 Holes (for Upper Hub layers 2,3 and Lower Hub layers 1,2)
    create_svg(os.path.join(docs_dir, "hub_layer_100_5.svg"), cup_d=100.5, outer_d=358.0)
    create_dxf(os.path.join(docs_dir, "hub_layer_100_5.dxf"), cup_d=100.5, outer_d=358.0)
    
    # Type 2: ø358 OD, ø110.2 Holes (for Upper Hub layer 1, Lower Hub layer 3, and Middle Hub layers 1,2)
    create_svg(os.path.join(docs_dir, "hub_layer_110_2.svg"), cup_d=110.2, outer_d=358.0)
    create_dxf(os.path.join(docs_dir, "hub_layer_110_2.dxf"), cup_d=110.2, outer_d=358.0)
    
    # Type 3: ø361.3 OD, ø110.2 Holes (for Middle Hub layer 3 - Guide Flange)
    create_svg(os.path.join(docs_dir, "hub_middle_rim_110_2.svg"), cup_d=110.2, outer_d=361.3)
    create_dxf(os.path.join(docs_dir, "hub_middle_rim_110_2.dxf"), cup_d=110.2, outer_d=361.3)
