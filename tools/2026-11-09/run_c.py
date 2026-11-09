import sys; sys.path.insert(0,'/home/claude/w')
import numpy as np; from PIL import Image
import compose as C
def P(b): return [100*b[0]/2048,100*b[1]/1152,100*b[2]/2048,100*b[3]/1152]
def stretch(asset,sx):
    rgb,mask,core=asset; h,w=mask.shape; nw=round(w*sx)
    r=np.array(Image.fromarray(rgb).resize((nw,h),Image.LANCZOS))
    m=np.array(Image.fromarray((mask*255).astype(np.uint8)).resize((nw,h)))>127
    c=np.array(Image.fromarray((core*255).astype(np.uint8)).resize((nw,h)))>127
    return r,m,c
A13=C.cloud_asset('/home/claude/w/cloud_wide13.png'); A20=C.cloud_asset('/home/claude/w/cloud_wide20.png')
def run(name,img,tier1,crit,head,lines,asset):
    a=np.array(Image.open(img).convert('RGB'))
    r=C.compose(a,[P(b) for b in tier1],[P(b) for b in crit],P(head),lines,asset)
    if isinstance(r,tuple):
        res,o=r; Image.fromarray(o).save(name+'_c.png'); y0=res['crop_start']
        Image.fromarray(o[y0:y0+1022]).resize((663,331),Image.LANCZOS).save(name+'_cell.png')
    else: res=r
    print(name,res,flush=True); return res
