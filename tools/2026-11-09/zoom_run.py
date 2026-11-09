import sys; sys.path.insert(0,'/home/claude/w')
from run_c import *
W0,H0=2048,1152
def window(z,boxes,crit):
    w,h=W0/z,H0/z
    xs=[b[0] for b in boxes]+[b[2] for b in boxes]; cx=(min(xs)+max(xs))/2
    x0=min(max(cx-w/2,0),W0-w)
    cb=max(b[3] for b in crit); y1=min(H0,cb+90); y0=max(0,y1-h); y1=y0+h
    return x0,y0
def tf(b,x0,y0,z): return (round((b[0]-x0)*z),round((b[1]-y0)*z),round((b[2]-x0)*z),round((b[3]-y0)*z))
def zoomed(a,z,x0,y0):
    w,h=W0/z,H0/z
    return np.array(Image.fromarray(a).crop((round(x0),round(y0),round(x0+w),round(y0+h))).resize((W0,H0),Image.LANCZOS))
def run_panel(name,base,t1,cr,head,kind,lines,asset,tip=None,zs=(1.4,1.35,1.3,1.25,1.2,1.15,1.1,1.05,1.0),pitch=80,fc_fn=None):
    a0=np.array(Image.open(base).convert('RGB'))
    C.PITCH=pitch
    for z in zs:
        x0,y0=window(z,t1,cr); a=zoomed(a0,z,x0,y0)
        T=[tf(b,x0,y0,z) for b in t1]; R=[tf(b,x0,y0,z) for b in cr]; Hd=tf(head,x0,y0,z)
        if kind=='thought': r=C.compose(a,[P(b) for b in T],[P(b) for b in R],P(Hd),lines,asset)
        elif kind=='dream': r=C.compose(a,[P(b) for b in T],[P(b) for b in R],P(Hd),lines,None,fc=fc_fn())
        else:
            tp=(round((tip[0]-x0)*z),round((tip[1]-y0)*z))
            r=C.speech2(a,[P(b) for b in T],[P(b) for b in R],P(Hd),tp,lines,asset,stop=0,keep_head=True)
        if isinstance(r,tuple):
            res,o=r; res['zoom']=z; res['win']=(round(x0),round(y0)); print(name,res,flush=True)
            Image.fromarray(o).save('page/%s_final.png'%name); y=res['crop_start']
            Image.fromarray(o[y:y+1022]).resize((663,331),Image.LANCZOS).save('%s_cell2.png'%name)
            return res
    print(name,'FAILED',r); return None
