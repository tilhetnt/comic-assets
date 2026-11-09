import io
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W_ = '/home/claude/w/'
FONT_BYTES = open(W_ + 'NotoSans.ttf', 'rb').read()
LOGO = Image.open(W_ + 'Coke_Buddy_Logo.png').convert('RGBA')
def font(s):
    f = ImageFont.truetype(io.BytesIO(FONT_BYTES), s)
    try: f.set_variation_by_name('Bold')
    except Exception: pass
    return f
def extract_grey(a):
    white = a.min(2) > 235; lab, n = ndimage.label(white); s = ndimage.sum(white, lab, range(1, n + 1))
    core = ndimage.binary_fill_holes(lab == (np.argmax(s) + 1)); dark = a.astype(int).sum(2) < 250
    full = ndimage.binary_fill_holes(core | (ndimage.binary_dilation(core, iterations=12) & dark))
    ys, xs = np.where(full); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return a[y0:y1, x0:x1], full[y0:y1, x0:x1]
def scaled(rgb, mask, f):
    H, W = mask.shape; nw, nh = round(W * f), round(H * f)
    r = np.array(Image.fromarray(rgb).resize((nw, nh), Image.LANCZOS))
    m = np.array(Image.fromarray((mask * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) > 127
    return r, m
def find_screen(a, box):
    x0, y0, x1, y1 = box; sub = a[y0:y1, x0:x1]
    white = sub.min(2) > 228; lab, n = ndimage.label(white); s = ndimage.sum(white, lab, range(1, n + 1))
    comp = ndimage.binary_fill_holes(lab == (np.argmax(s) + 1)).astype(np.uint8)
    cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea)
    q = cv2.boxPoints(cv2.minAreaRect(c)); q[:, 0] += x0; q[:, 1] += y0
    M = np.zeros(a.shape[:2], bool); M[y0:y1, x0:x1] = comp.astype(bool)
    return q, M
def order(q):
    s = q.sum(1); d = np.diff(q, axis=1).ravel()
    return np.float32([q[np.argmin(s)], q[np.argmin(d)], q[np.argmax(s)], q[np.argmax(d)]])
def size_of(q):
    qo = order(q); return int(round(np.linalg.norm(qo[1] - qo[0]))), int(round(np.linalg.norm(qo[3] - qo[0])))
def warp_paste(a, content, q, M):
    qo = order(q); h, w = content.shape[:2]
    T = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), qo)
    wc = cv2.warpPerspective(content, T, (a.shape[1], a.shape[0]), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    wm = cv2.warpPerspective(np.full((h, w), 255, np.uint8), T, (a.shape[1], a.shape[0])) > 127
    m = wm & ndimage.binary_erosion(M, iterations=2); o = a.copy(); o[m] = wc[m]; return o
def logo_top(im, w, h):
    L = round(min(w * 0.46, h * 0.24)); lg = LOGO.resize((L, L), Image.LANCZOS); top = round(h * 0.06)
    im.paste(lg, ((w - L) // 2, top), lg); return top + L
def bottle(d, cx, top, hgt, col):
    w = hgt * 0.32; neck = w * 0.38
    d.rounded_rectangle([cx - neck / 2, top, cx + neck / 2, top + hgt * 0.35], radius=4, fill=col)
    d.rounded_rectangle([cx - w / 2, top + hgt * 0.28, cx + w / 2, top + hgt], radius=round(w * 0.3), fill=col)
def app_content(w, h, cols):
    """Coke Buddy screen: logo, product tiles (plain bottle icons), green check. No text."""
    im = Image.new('RGB', (w, h), (255, 255, 255)); d = ImageDraw.Draw(im)
    top = logo_top(im, w, h) + round(h * 0.04)
    n = len(cols); gap = round(w * 0.06); tw = round((w - gap * (n + 1)) / n); th = round(min(tw * 1.15, h * 0.26))
    for i, c in enumerate(cols):
        x0 = gap + i * (tw + gap)
        d.rounded_rectangle([x0, top, x0 + tw, top + th], radius=round(tw * 0.12), fill=(242, 242, 242), outline=(205, 205, 205), width=3)
        if n == 1:
            for dx in (-0.26, 0, 0.26): bottle(d, x0 + tw / 2 + dx * tw, top + th * 0.12, th * 0.76, c)
        else: bottle(d, x0 + tw / 2, top + th * 0.12, th * 0.76, c)
    R = round(min(w * 0.2, h * 0.11)); cx = w // 2; cy = top + th + round(h * 0.05) + R
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(30, 170, 70)); t = round(R * 0.22)
    d.line([(cx - R * 0.5, cy + R * 0.02), (cx - R * 0.12, cy + R * 0.42), (cx + R * 0.55, cy - R * 0.38)], fill=(255, 255, 255), width=t, joint='curve')
    return np.array(im)
def screen_app(a, box, cols):
    q, M = find_screen(a, box); w, h = size_of(q)
    return warp_paste(a, app_content(w, h, cols), q, M), (w, h)
def relabel(a, box, text, thr=200, fill_frac=0.92):
    """Replace generator-drawn white script lettering on red with plain white lettering (Noto Sans Bold)."""
    x0, y0, x1, y1 = box; sub = a[y0:y1, x0:x1].astype(int)
    red = (sub[..., 0] > 140) & (sub[..., 1] < 110) & (sub[..., 2] < 110)
    lab, n = ndimage.label(red); sz = ndimage.sum(red, lab, range(1, n + 1)); reg = ndimage.binary_fill_holes(lab == (np.argmax(sz) + 1))
    reg = ndimage.binary_erosion(reg, iterations=2)
    wm = (sub.min(2) > thr) & reg; m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = ndimage.binary_dilation(wm, iterations=4)
    ys, xs = np.where(m > 0); bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    o = cv2.inpaint(a, m * 255, 9, cv2.INPAINT_TELEA)
    tw = (bx1 - bx0) * fill_frac
    s = 20
    while font(s + 1).getlength(text) <= tw and (font(s + 1).getbbox(text)[3] - font(s + 1).getbbox(text)[1]) <= (by1 - by0) * 0.9: s += 1
    f = font(s); b = f.getbbox(text)
    im = Image.fromarray(o); d = ImageDraw.Draw(im)
    d.text(((bx0 + bx1) / 2 - (b[2] - b[0]) / 2 - b[0], (by0 + by1) / 2 - (b[3] - b[1]) / 2 - b[1]), text, font=f, fill=(255, 255, 255))
    return np.array(im), (int(bx0), int(by0), int(bx1), int(by1)), s
