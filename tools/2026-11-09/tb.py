import sys, itertools, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from pythainlp import word_tokenize
MALI='/home/claude/w/Mali-Bold.ttf'; NOTO='/home/claude/w/NotoSansThai.ttf'
FC={}
def mali(s):
    if s not in FC: FC[s]=ImageFont.truetype(MALI,s)
    return FC[s]
def noto(s):
    f=ImageFont.truetype(NOTO,s); f.set_variation_by_axes([700,100]); return f
KEEP=['Coke บัดดี้','ร้านก๋วยเตี๋ยว','นักท่องเที่ยวต่างชาติ','เดือนละ','ออเดอร์เต็ม','พนักงานขายพรีเซล','พนักงานขาย','แม็คโคร','2,000 บาท','3,700 บาท','ก๋วยเตี๋ยว','ตู้แช่','ออเดอร์แรก','วันรุ่งขึ้น','ร้านเล็ก','ร้านใหญ่']
def toks(t):
    out=[];i=0
    while i<len(t):
        k=next((k for k in KEEP if t.startswith(k,i)),None)
        if k: out.append(k); i+=len(k); continue
        j=i
        while j<len(t) and not any(t.startswith(k,j) for k in KEEP): j+=1
        out+=word_tokenize(t[i:j],keep_whitespace=True); i=j
    m=[]
    for x in out:
        if m and (x.strip()=='' or all(c in '?!.,' for c in x.strip())): m[-1]+=x
        else: m.append(x)
    return m
def partitions(tk,kmax=4):
    n=len(tk)
    for k in range(0,kmax):
        for br in itertools.combinations(range(1,n),k):
            idx=(0,)+br+(n,); lines=[''.join(tk[idx[j]:idx[j+1]]).strip() for j in range(len(idx)-1)]
            if all(lines): yield lines
def cloud(a,seed,clip=None):
    white=a.min(2)>235
    if clip is not None:
        cm=np.zeros(white.shape,bool); x0,y0,x1,y1=clip; cm[y0:y1,x0:x1]=True; white&=cm
    lab,n=ndimage.label(white); cid=lab[seed[1],seed[0]]
    if cid==0:
        ys,xs=np.nonzero(lab[seed[1]-60:seed[1]+60,seed[0]-60:seed[0]+60]); cid=lab[seed[1]-60+ys[0],seed[0]-60+xs[0]]
    core=ndimage.binary_fill_holes(lab==cid)
    txt=core&~(a.min(2)>235); txt=ndimage.binary_opening(txt,iterations=1)
    ys,xs=np.where(txt); cx=(xs.min()+xs.max())/2; cy=(ys.min()+ys.max())/2
    col=np.median(a[core&(a.min(2)>235)],0).astype(np.uint8)
    return core,(cx,cy),col
def prep(a,seed,clip=None,margin=12):
    core,(cx,cy),col=cloud(a,seed,clip)
    inner=ndimage.binary_erosion(core,iterations=margin); bad=(~inner).astype(np.int64)
    ii=np.zeros((bad.shape[0]+1,bad.shape[1]+1),np.int64); ii[1:,1:]=bad.cumsum(0).cumsum(1)
    return core,(cx,cy),col,ii
def fits(ii,shape,cx,cy,lines,s,pitch):
    f=mali(s); P=round(s*pitch); H=P*len(lines); y0=round(cy-H/2)
    for i,l in enumerate(lines):
        b=f.getbbox(l,stroke_width=2); w=b[2]-b[0]; x=round(cx-w/2)-b[0]; ly=y0+i*P
        t,bo,le,r=ly+b[1],ly+b[3],x+b[0],x+b[2]
        if t<0 or le<0 or bo>=shape[0] or r>=shape[1]: return False
        if ii[bo,r]-ii[t,r]-ii[bo,le]+ii[t,le]>0: return False
    return True
def gaps(lines,s,pitch):
    P=round(s*pitch); f=mali(s); W=2600; masks=[]
    for i,l in enumerate(lines):
        m=Image.new('L',(W,P*len(lines)+400),0); d=ImageDraw.Draw(m); b=f.getbbox(l,stroke_width=2); w=b[2]-b[0]
        d.text((round(W/2-w/2)-b[0],150+i*P),l,font=f,fill=255,stroke_width=2,stroke_fill=255); masks.append(np.array(m)>0)
    out=[]
    for i in range(len(masks)-1):
        A,B=masks[i],masks[i+1]; g=[]
        for x in np.where(A.any(0)&B.any(0))[0]:
            g.append(np.where(B[:,x])[0].min()-np.where(A[:,x])[0].max())
        out.append(int(min(g)) if g else 999)
    return out
def render(a,core,cx,cy,col,lines,s,pitch):
    o=a.copy(); o[core]=col
    f=mali(s); m=Image.new('L',(a.shape[1],a.shape[0]),0); d=ImageDraw.Draw(m)
    P=round(s*pitch); H=P*len(lines); y0=round(cy-H/2)
    for i,l in enumerate(lines):
        b=f.getbbox(l,stroke_width=2); w=b[2]-b[0]
        d.text((round(cx-w/2)-b[0],y0+i*P),l,font=f,fill=255,stroke_width=2,stroke_fill=255)
    mm=np.array(m).astype(np.int32)[...,None]
    return ((o.astype(np.int32)*(255-mm))//255).astype(np.uint8)
NOBREAK_AFTER={'ของ','ที่','จาก','ใน','ใส่','กับ','ผ่าน','ใต้','เจอ','หา','ให้','ละ'}
def card_balanced(t,box=555,size=30):
    f=noto(size); tk=toks(t); best=None
    if f.getlength(t)<=box: return [t],[round(f.getlength(t))]
    sp=[i for i in range(1,len(tk)) if tk[i-1].endswith(' ')]
    for i in (sp if any(noto(size).getlength(''.join(tk[:i]).strip())<=box and noto(size).getlength(''.join(tk[i:]).strip())<=box for i in sp) else range(1,len(tk))):
        prev=tk[i-1].strip()
        if prev.replace('.','').replace(',','').isdigit() or prev in NOBREAK_AFTER: continue
        a=''.join(tk[:i]).strip(); b=''.join(tk[i:]).strip()
        wa,wb=f.getlength(a),f.getlength(b)
        if wa<=box and wb<=box:
            sc=max(wa,wb)
            if best is None or sc<best[0]: best=(sc,[a,b],[round(wa),round(wb)])
    return (best[1],best[2]) if best else (None,None)
