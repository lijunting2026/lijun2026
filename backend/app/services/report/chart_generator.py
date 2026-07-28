import io, os, math
from PIL import Image, ImageDraw, ImageFont

# Find Chinese font
FONT_PATH = 'C:/Windows/Fonts/simsun.ttc'
if not os.path.exists(FONT_PATH):
    FONT_PATH = 'C:/Windows/Fonts/msyh.ttc'
    if not os.path.exists(FONT_PATH):
        FONT_PATH = 'C:/Windows/Fonts/simsun.ttc'
        if not os.path.exists(FONT_PATH):
            FONT_PATH = None

def _font(size=12):
    try:
        return ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default()
    except:
        return ImageFont.load_default()

CHART_COLORS = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#B37FEB', '#19CAAD', '#F8B500']

def draw_bar_chart(data, labels, title="", ylabel="", bar_colors=None, width=600, height=360):
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    margin_l, margin_r, margin_t, margin_b = 60, 20, 40, 50
    chart_w = width - margin_l - margin_r
    chart_h = height - margin_t - margin_b

    if title:
        tf = _font(14)
        draw.text(((width - draw.textlength(title, font=tf)) / 2, 8), title, fill='#333333', font=tf)

    if not data or not labels:
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf

    colors = bar_colors or CHART_COLORS
    max_val = max(max(d) if isinstance(d, (list, tuple)) else d for d in data)
    max_val = math.ceil(max_val * 1.15)
    if max_val <= 0: max_val = 10

    n_groups = len(labels)
    n_bars = max(len(d) if isinstance(d, (list, tuple)) else 1 for d in data)
    group_w = chart_w / n_groups
    bar_w = min(group_w * 0.7 / n_bars, 40)
    gap = (group_w - bar_w * n_bars) / 2

    n_grid = 5
    gf = _font(10)
    for i in range(n_grid + 1):
        y = margin_t + chart_h - chart_h * i / n_grid
        val = max_val * i / n_grid
        draw.line([(margin_l, y), (width - margin_r, y)], fill='#E8E8E8', width=1)
        draw.text((margin_l - draw.textlength(str(round(val, 1)), font=gf) - 4, y - 7),
                  str(round(val, 1)), fill='#666666', font=gf)
    draw.line([(margin_l, margin_t), (margin_l, margin_t + chart_h)], fill='#CCCCCC', width=1)
    draw.line([(margin_l, margin_t + chart_h), (width - margin_r, margin_t + chart_h)], fill='#CCCCCC', width=1)

    xf = _font(10)
    for gi, label in enumerate(labels):
        x0 = margin_l + gi * group_w + gap
        for bi in range(n_bars):
            val = data[gi] if n_bars == 1 else (data[gi][bi] if isinstance(data[gi], (list, tuple)) else data[gi])
            bar_h = chart_h * val / max_val if max_val > 0 else 0
            color = colors[bi % len(colors)]
            draw.rectangle([(x0 + bi * bar_w, margin_t + chart_h - bar_h),
                           (x0 + (bi + 1) * bar_w, margin_t + chart_h)], fill=color)
            if val > 0:
                vl = str(round(val, 1))
                draw.text((x0 + bi * bar_w + (bar_w - draw.textlength(vl, font=xf)) / 2,
                          margin_t + chart_h - bar_h - 16), vl, fill=color, font=xf)
        lw = draw.textlength(label, font=xf)
        draw.text((x0 + bar_w * n_bars / 2 - lw / 2, margin_t + chart_h + 6), label, fill='#333333', font=xf)

    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return buf


def draw_line_chart(series_list, x_labels, title="", ylabel="", width=640, height=360):
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    margin_l, margin_r, margin_t, margin_b = 60, 20, 40, 50
    chart_w = width - margin_l - margin_r
    chart_h = height - margin_t - margin_b

    if title:
        tf = _font(14)
        draw.text(((width - draw.textlength(title, font=tf)) / 2, 8), title, fill='#333333', font=tf)

    if not series_list or not x_labels:
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf

    all_vals = [v for s in series_list for v in (s.get('data', []) if isinstance(s, dict) else s) if v is not None]
    if not all_vals:
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf
    max_val = max(all_vals) * 1.15
    if max_val <= 0: max_val = 10

    n_points = len(x_labels)
    step_x = chart_w / (n_points - 1) if n_points > 1 else chart_w

    n_grid = 5
    gf = _font(10)
    for i in range(n_grid + 1):
        y = margin_t + chart_h - chart_h * i / n_grid
        val = max_val * i / n_grid
        draw.line([(margin_l, y), (width - margin_r, y)], fill='#E8E8E8', width=1)
        draw.text((margin_l - draw.textlength(str(round(val, 1)), font=gf) - 4, y - 7),
                  str(round(val, 1)), fill='#666666', font=gf)
    draw.line([(margin_l, margin_t), (margin_l, margin_t + chart_h)], fill='#CCCCCC', width=1)
    draw.line([(margin_l, margin_t + chart_h), (width - margin_r, margin_t + chart_h)], fill='#CCCCCC', width=1)

    xf = _font(9)
    for si, series in enumerate(series_list):
        data = series.get('data', []) if isinstance(series, dict) else series
        name = series.get('name', '') if isinstance(series, dict) else ''
        color = CHART_COLORS[si % len(CHART_COLORS)]

        points = []
        for pi, val in enumerate(data):
            if val is None: continue
            px = margin_l + pi * step_x
            py = margin_t + chart_h - chart_h * val / max_val
            points.append((px, py))
            draw.ellipse([(px - 3, py - 3), (px + 3, py + 3)], fill=color)
            vl = str(round(val, 1))
            draw.text((px - draw.textlength(vl, font=_font(9)) / 2, py - 16), vl, fill=color, font=_font(9))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=2)
        if name:
            lx = width - 120; ly = margin_t + 4 + si * 18
            draw.rectangle([(lx, ly + 2), (lx + 12, ly + 14)], fill=color)
            draw.text((lx + 16, ly + 1), name, fill='#333333', font=_font(10))

    for pi, label in enumerate(x_labels):
        px = margin_l + pi * step_x
        draw.text((px - draw.textlength(label, font=xf) / 2, margin_t + chart_h + 6), label, fill='#333333', font=xf)

    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return buf


def draw_radar_chart(data, indicators, title="", width=360, height=360):
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    if title:
        tf = _font(14)
        draw.text(((width - draw.textlength(title, font=tf)) / 2, 4), title, fill='#333333', font=tf)

    if not data or not indicators:
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf

    cx, cy = width // 2, (height + 20) // 2
    r = min(cx, cy) - 40
    n = len(indicators)

    # Draw grid
    for ri in range(1, 5):
        radius = r * ri / 4
        poly = []
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2
            poly.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        draw.polygon(poly, outline='#E8E8E8', width=1)

    # Draw axis lines
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        draw.line([(cx, cy), (cx + r * math.cos(angle), cy + r * math.sin(angle))], fill='#E8E8E8', width=1)
        tx = cx + (r + 20) * math.cos(angle)
        ty = cy + (r + 20) * math.sin(angle)
        label = indicators[i] if isinstance(indicators[i], str) else indicators[i].get('name', '')
        lf = _font(10)
        lw = draw.textlength(label, font=lf)
        draw.text((tx - lw / 2, ty - 6), label, fill='#333333', font=lf)

    # Draw data polygons
    for di, dataset in enumerate(data if isinstance(data, list) else [data]):
        vals = dataset if isinstance(dataset, (list, tuple)) else dataset.get('value', [])
        name = dataset.get('name', '') if isinstance(dataset, dict) else ''
        color = CHART_COLORS[di % len(CHART_COLORS)]

        max_indicator = 100
        points = []
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2
            val = min(vals[i] if i < len(vals) else 0, max_indicator)
            radius = r * val / max_indicator
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

        # Fill
        draw.polygon(points, fill=color + '40' if len(color) == 7 else color)
        # Outline
        draw.line(points + [points[0]], fill=color, width=2)
        # Points
        for px, py in points:
            draw.ellipse([(px - 3, py - 3), (px + 3, py + 3)], fill=color)

    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return buf


def draw_table_image(headers, rows, title="", width=600):
    cell_h = 28
    col_ws = [max(draw.textlength(h, font=_font(11)), 80) for h in headers]
    for row in rows:
        for ci, val in enumerate(row):
            w = draw.textlength(str(val), font=_font(10)) + 16
            if w > col_ws[ci]: col_ws[ci] = w
    total_w = max(sum(col_ws) + 1, width)
    header_h = 32
    total_h = header_h + cell_h * len(rows) + 20

    img = Image.new('RGB', (total_w, total_h), 'white')
    draw = ImageDraw.Draw(img)

    y = 0
    if title:
        tf = _font(14)
        draw.text((4, 0), title, fill='#333333', font=tf)
        y = 22

    # Header
    x = 0
    for ci, h in enumerate(headers):
        draw.rectangle([(x, y), (x + col_ws[ci], y + header_h)], fill='#409EFF')
        lf = _font(11)
        draw.text((x + 6, y + (header_h - 12) / 2), h, fill='white', font=lf)
        x += col_ws[ci]
    y += header_h

    # Rows
    for ri, row in enumerate(rows):
        x = 0
        bg = '#F5F7FA' if ri % 2 == 0 else 'white'
        for ci, val in enumerate(row):
            draw.rectangle([(x, y), (x + col_ws[ci], y + cell_h)], fill=bg, outline='#E8E8E8')
            draw.text((x + 6, y + (cell_h - 12) / 2), str(val), fill='#333333', font=_font(10))
            x += col_ws[ci]
        y += cell_h

    # Crop to content
    img = img.crop((0, 0, total_w, y))
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return buf
