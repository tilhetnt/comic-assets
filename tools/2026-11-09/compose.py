import time, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
sys.path.insert(0,'/home/claude/w')
import afterlib as L
W,H=2048,1152; KEEP=1022; M=20; GAP=40
def pct(b): return (round(W*b[0]/100),round(H*b[1]/100),round(W*b[2]/100),round(H*b[3]/100))
def fred(s):
    f=ImageFont.truetype('/home/claude/w/fredoka.ttf',s); f.set_variation_by_axes([500,85]); return f
S=next(s for s in range(40,160) if (lambda b:b[3]-b[1])(fred(s).getbbox('H'))>=67); F=fred(S)
PITCH=80
def text_mask(lines,pitch=None):
    pitch=pitch or PITCH
    lines=[l.replace("'","’") for l in lines]
    hb=F.getbbox('H'); ws=[F.getbbox(l) for l in lines]; tw=max(b[2]-b[0] for b in ws)
    th=pitch*(len(lines)-1)+ (F.getbbox('g')[3]-hb[1])
    m=Image.new('L',(tw+4,th+4),0); d=ImageDraw.Draw(m)
    for i,(l,b) in enumerate(zip(lines,ws)): d.text(((tw-(b[2]-b[0]))//2-b[0]+2,i*pitch-hb[1]+2),l,font=F,fill=255)
    return np.array(m)>127
def cloud_asset(path):
    a=np.array(Image.open(path).convert('RGB')); rgb,mask=L.extract_grey(a)
    white=rgb.min(2)>235; core=ndimage.binary_fill_holes(mask&white) & mask
    return rgb,mask,core
def fit_cloud(asset,tm,margin=12,center=None):
    rgb,mask,core=asset; th,tw=tm.shape
    for f in np.arange(0.25,1.6,0.01):
        r,m=L.scaled(rgb,mask,f); c=np.array(Image.fromarray((core*255).astype(np.uint8)).resize((m.shape[1],m.shape[0])))>127
        inner=ndimage.binary_erosion(c,iterations=margin)
        if center is None: cy,cx=np.array(ndimage.center_of_mass(c)).round().astype(int)
        else: cx,cy=round(center[0]*m.shape[1]),round(center[1]*m.shape[0])
        y0,x0=cy-th//2,cx-tw//2
        if y0<0 or x0<0 or y0+th>c.shape[0] or x0+tw>c.shape[1]: continue
        if not (tm & ~inner[y0:y0+th,x0:x0+tw]).any():
            out=r.copy(); sub=out[y0:y0+th,x0:x0+tw]; sub[tm]=(20,20,20)
            grow=max(0,round(7-7*f/0.64))
            if grow:
                m2=ndimage.binary_dilation(m,iterations=grow); ring=m2&~m; out[ring]=(20,20,20); m=m2
            return out,m,round(f,2)
    return None
def trail_plan(bx,by,x,y,dtT,head_box,radii=(25,19,13)):
    x0,y0,x1,y1=pct(head_box)
    xs=bx+x; ys=by+y
    for fy in (0.0,0.08,0.16,0.3):
        for fx in (0.0,0.15,0.3,0.45,0.6,0.85,1.0):
            E=(x1-(x1-x0)*fx, y0+(y1-y0)*fy)
            order=np.argsort(np.hypot(xs-E[0],ys-E[1]))[:400:8]
            for k in order:
                sx,sy=float(xs[k]),float(ys[k]); Lg=float(np.hypot(E[0]-sx,E[1]-sy))
                if Lg<60: continue
                ux,uy=(E[0]-sx)/Lg,(E[1]-sy)/Lg
                pts=[(sx+ux*Lg*t,sy+uy*Lg*t,r) for r,t in zip(radii,(0.15,0.45,0.72))]
                if all(dtT[int(np.clip(cy,0,H-1)),int(np.clip(cx,0,W-1))]>r+8 for cx,cy,r in pts[:-1]) and all(cy-r>2 for cx,cy,r in pts):
                    return pts
    return None
def draw_trail(o,pts,outline=5):
    im=Image.fromarray(o); dr=ImageDraw.Draw(im)
    for cx,cy,r in pts: dr.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(252,252,252),outline=(20,20,20),width=outline)
    return np.array(im)
def compose(a,tier1,crit_boxes,head,lines,asset,center=None,fc=None):
    t0=time.time()
    T=np.zeros((H,W),bool)
    for b in tier1: x0,y0,x1,y1=pct(b); T[max(y0,0):min(y1,H),max(x0,0):min(x1,W)]=True
    crit=[pct(b) for b in crit_boxes]
    ylo=max(0,max(b[3] for b in crit)+M-KEEP); yhi=min(H-KEEP,min(b[1] for b in crit)-M)
    if ylo>yhi: return {'ok':False,'why':'tier-1 does not fit the crop window','span':(min(b[1] for b in crit),max(b[3] for b in crit))}
    if fc is None:
        tm=text_mask(lines); fc=fit_cloud(asset,tm,center=center)
    rgb,m,f=fc; bh,bw=m.shape
    dt=ndimage.distance_transform_edt(~T)
    hx,hy=[(pct(head)[0]+pct(head)[2])//2,(pct(head)[1]+pct(head)[3])//2]
    cand=[]
    for y in range(M,H-bh-M,8):
        for x in range(M,W-bw-M,8):
            if not (max(ylo,y+bh+M-KEEP)<=min(yhi,y-M)): continue
            if dt[y:y+bh,x:x+bw][m].min()<GAP: continue
            cand.append((np.hypot(x+bw/2-hx,y+bh/2-hy),x,y))
    if not cand: return {'ok':False,'why':'no free space for the balloon at %d x %d px'%(bw,bh)}
    cand.sort(); o=None
    bd=ndimage.binary_dilation(np.pad(m,3),iterations=2)[3:-3,3:-3]&~m; by,bx=np.where(bd)
    for _,x,y in cand:
        pts=trail_plan(bx,by,x,y,dt,head)
        if pts:
            o=a.copy(); sub=o[y:y+bh,x:x+bw]; sub[m]=rgb[m]; o=draw_trail(o,pts); break
    if o is None: return {'ok':False,'why':'no clear trail (%d positions)'%len(cand)}
    y0=min(max(ylo,y+bh+M-KEEP),min(yhi,y-M)); y0=max(ylo,min(y0,yhi))
    return {'ok':True,'balloon_xy':(x,y),'balloon_px':(bw,bh),'scale':f,'min_gap_px':round(float(dt[y:y+bh,x:x+bw][m].min()),1),'crop_start':y0,'crop_Y%':round(100*y0/130,2)},o

def content_block(lines, vign=None, vw=0, gap=24, pitch=80):
    """returns (rgb, mask) of text block, optionally with a picture above it"""
    tm = text_mask(lines, pitch)
    th, tw = tm.shape
    if vign is None:
        rgb = np.full((th, tw, 3), 255, np.uint8); rgb[tm] = (20, 20, 20); return rgb, tm
    vh = round(vign.shape[0] * vw / vign.shape[1])
    v = np.array(Image.fromarray(vign).resize((vw, vh), Image.LANCZOS))
    Wd = max(vw, tw); Hd = vh + gap + th
    rgb = np.full((Hd, Wd, 3), 255, np.uint8); m = np.zeros((Hd, Wd), bool)
    x = (Wd - vw) // 2; rgb[:vh, x:x + vw] = v; m[:vh, x:x + vw] = True
    x = (Wd - tw) // 2; sub = rgb[vh + gap:, x:x + tw]; sub[tm] = (20, 20, 20); m[vh + gap:, x:x + tw] |= tm
    # the text area must be inside too
    m[vh + gap:, x:x + tw] = True
    return rgb, m
def fit_content(asset, crgb, cmask, margin=14, center=None):
    rgb, mask, core = asset; th, tw = cmask.shape
    for f in np.arange(0.25, 2.5, 0.01):
        r, m = L.scaled(rgb, mask, f); c = np.array(Image.fromarray((core * 255).astype(np.uint8)).resize((m.shape[1], m.shape[0]))) > 127
        inner = ndimage.binary_erosion(c, iterations=margin)
        if center is None: cy, cx = np.array(ndimage.center_of_mass(c)).round().astype(int)
        else: cx, cy = round(center[0] * m.shape[1]), round(center[1] * m.shape[0])
        y0, x0 = cy - th // 2, cx - tw // 2
        if y0 < 0 or x0 < 0 or y0 + th > c.shape[0] or x0 + tw > c.shape[1]: continue
        if not (cmask & ~inner[y0:y0 + th, x0:x0 + tw]).any():
            out = r.copy(); sub = out[y0:y0 + th, x0:x0 + tw]
            tx = crgb.min(2) < 250
            sub[cmask & tx] = crgb[cmask & tx]
            grow = max(0, round(7 - 7 * f / 0.64))
            if grow:
                m2 = ndimage.binary_dilation(m, iterations=grow); ring = m2 & ~m; out[ring] = (20, 20, 20); m = m2
            return out, m, round(f, 2)
    return None
def speech(a, tier1_other, crit_boxes, mouth, lines, asset_path, flip=False, gap=GAP, xshift=0):
    """speech balloon: tail tip placed at the speaker's mouth; returns res, image"""
    s = np.array(Image.open(asset_path).convert('RGB'))
    if flip: s = s[:, ::-1].copy()
    rgb, mask = L.extract_grey(s); white = rgb.min(2) > 235
    core = ndimage.binary_fill_holes(mask & white) & mask
    body = ndimage.binary_opening(mask, structure=np.ones((3, 3)), iterations=25)
    asset = (rgb, mask, core)
    tm = text_mask(lines)
    # fit text using body center
    bc = ndimage.center_of_mass(body); center = (bc[1] / mask.shape[1], bc[0] / mask.shape[0])
    fc = fit_cloud(asset, tm, center=center)
    r, m, f = fc
    ys, xs = np.where(m); k = np.argmax(ys); tip = (xs[k], ys[k])
    x = mouth[0] - tip[0] + xshift; y = mouth[1] - tip[1]
    bh, bw = m.shape
    T = np.zeros((H, W), bool)
    for b in tier1_other: x0, y0, x1, y1 = pct(b); T[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)] = True
    dt = ndimage.distance_transform_edt(~T)
    bodyS = np.array(Image.fromarray((ndimage.binary_opening(m, structure=np.ones((3, 3)), iterations=int(25 * f) + 2) * 255).astype(np.uint8))) > 127
    if x < M or y < M or x + bw > W - M: return {'ok': False, 'why': 'balloon off frame', 'xy': (x, y), 'size': (bw, bh)}, None
    g = float(dt[y:y + bh, x:x + bw][bodyS].min())
    crit = [pct(b) for b in crit_boxes]
    ylo = max(0, max(max(b[3] for b in crit), y + bh) + M - KEEP); yhi = min(H - KEEP, min(min(b[1] for b in crit), y) - M)
    o = a.copy(); sub = o[y:y + bh, x:x + bw]; sub[m] = r[m]
    y0 = max(ylo, min(yhi, 0)) if ylo <= yhi else None
    return {'ok': g >= gap and ylo <= yhi, 'balloon_xy': (int(x), int(y)), 'balloon_px': (bw, bh), 'scale': f, 'min_gap_px': round(g, 1), 'crop_start': y0, 'crop_window': (ylo, yhi)}, o

def speech_asset(path):
    s = np.array(Image.open(path).convert('RGB')); rgb, mask = L.extract_grey(s)
    body = ndimage.binary_opening(mask, structure=np.ones((3, 3)), iterations=60)
    lab, n = ndimage.label(body); sz = ndimage.sum(body, lab, range(1, n + 1)); body = lab == (np.argmax(sz) + 1)
    ys, xs = np.where(body); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgb[y0:y1, x0:x1].copy(); body = body[y0:y1, x0:x1]
    white = rgb.min(2) > 235; core = ndimage.binary_fill_holes(body & white) & body
    full = mask[y0:, x0:x1]; bb = np.zeros_like(full); bb[:y1 - y0] = body
    tail = full & ~ndimage.binary_dilation(bb, iterations=3)
    ty, tx = np.where(tail); k = ty <= ty.min() + 6; gx = float(tx[k].mean())
    col = body[:, int(gx)]; gy = float(np.where(col)[0].max())
    rgb[~body] = (128, 128, 128)
    return rgb, body, core, (gx, gy)
def speech2(a, tier1, crit_boxes, speaker_head, mouth, lines, asset, tail_w=56, stop=22, keep_head=False):
    T = np.zeros((H, W), bool)
    for b in tier1: x0, y0, x1, y1 = pct(b); T[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)] = True
    crit = [pct(b) for b in crit_boxes]
    ylo = max(0, max(b[3] for b in crit) + M - KEEP); yhi = min(H - KEEP, min(b[1] for b in crit) - M)
    gap_pt = asset[3]; asset = asset[:3]
    tm = text_mask(lines); r, m, f = fit_cloud(asset, tm)
    bh, bw = m.shape; dt = ndimage.distance_transform_edt(~T)
    sxr = m.shape[1] / asset[1].shape[1]; syr = m.shape[0] / asset[1].shape[0]
    G = (gap_pt[0] * sxr, gap_pt[1] * syr)
    hb = pct(speaker_head)
    Th = T.copy()
    if not keep_head: Th[hb[1]:hb[3], hb[0]:hb[2]] = False
    dth = ndimage.distance_transform_edt(~Th)
    cand = []
    for y in range(M, H - bh - M, 8):
        for x in range(M, W - bw - M, 8):
            if not (max(ylo, y + bh + M - KEEP) <= min(yhi, y - M)): continue
            if dt[y:y + bh, x:x + bw][m].min() < GAP: continue
            cand.append((np.hypot(x + bw / 2 - mouth[0], y + bh - mouth[1]), x, y))
    cand.sort()
    for _, x, y in cand:
        B = np.array([x + G[0], y + G[1] - 4], float)
        Mo = np.array(mouth, float); v = Mo - B; Ln = np.linalg.norm(v)
        if Ln < 40: continue
        u = v / Ln; tip = Mo - u * stop
        # tail must not cross other tier-1 elements
        ok = all(dth[int(p[1]), int(p[0])] > 10 for p in [B + (tip - B) * t for t in np.linspace(0.05, 0.85, 30)])
        if not ok: continue
        o = a.copy()
        im = Image.fromarray(o); d = ImageDraw.Draw(im)
        nrm = np.array([-u[1], u[0]]); c = B - u * 30
        p1 = c + nrm * tail_w / 2; p2 = c - nrm * tail_w / 2
        d.polygon([tuple(p1), tuple(tip), tuple(p2)], fill=(252, 252, 252), outline=(20, 20, 20), width=7)
        o = np.array(im)
        sub = o[y:y + bh, x:x + bw]; sub[m] = r[m]
        # reopen the seam: interior of balloon near the tail base stays white
        im = Image.fromarray(o); d = ImageDraw.Draw(im)
        q1 = c + nrm * (tail_w / 2 - 7) + u * 2; q2 = c - nrm * (tail_w / 2 - 7) + u * 2
        ins = [tuple(q1), tuple(tip - u * 14), tuple(q2)]
        d.polygon(ins, fill=(252, 252, 252))
        o = np.array(im)
        sub = o[y:y + bh, x:x + bw]; inner = ndimage.binary_erosion(m, iterations=10)
        txt = (r.min(2) < 120) & inner; sub[txt] = r[txt]
        y0 = min(max(ylo, y + bh + M - KEEP), min(yhi, y - M)); y0 = max(ylo, min(y0, yhi))
        return {'ok': True, 'balloon_xy': (x, y), 'balloon_px': (bw, bh), 'scale': f, 'min_gap_px': round(float(dt[y:y + bh, x:x + bw][m].min()), 1), 'crop_start': int(y0), 'tail_len': round(Ln)}, o
    return {'ok': False, 'why': 'no position (%d tried)' % len(cand)}

def dream_cluster(dream_path, text_asset, lines, fd, overlap=0.62, dx=0):
    d = np.array(Image.open(dream_path).convert('RGB')); rgb, mask = L.extract_grey(d)
    rd, md = L.scaled(rgb, mask, fd)
    tm = text_mask(lines); rt, mt, ft = fit_cloud(text_asset, tm)
    hd, wd = md.shape; ht, wt = mt.shape
    off = round(dx * wt); xd0 = 0; xt0 = (wd - wt) // 2 + off
    mn = min(xd0, xt0); xd0 -= mn; xt0 -= mn
    Wc = max(xd0 + wd, xt0 + wt); oy = round(hd * overlap); Hc = max(hd, oy + ht)
    out = np.full((Hc, Wc, 3), 128, np.uint8); m = np.zeros((Hc, Wc), bool)
    xd = xd0; sub = out[:hd, xd:xd + wd]; sub[md] = rd[md]; m[:hd, xd:xd + wd] |= md
    xt = xt0; sub = out[oy:oy + ht, xt:xt + wt]; sub[mt] = rt[mt]; m[oy:oy + ht, xt:xt + wt] |= mt
    return out, m, (fd, ft)
