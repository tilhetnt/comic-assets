import sys; sys.path.insert(0,'/home/claude/w'); sys.path.insert(0,'/home/claude/w/th')
from zoom_run import *
from tb import mali
import numpy as np
from PIL import Image, ImageDraw
S=int(sys.argv[2]) if len(sys.argv)>2 else 60; PITCH=int(sys.argv[3]) if len(sys.argv)>3 else round(S*1.6)
def tm_th(lines,pitch=None):
    f=mali(S); bs=[f.getbbox(l,stroke_width=2) for l in lines]; tw=max(b[2]-b[0] for b in bs)
    top=min(b[1] for b in bs); bot=max(b[3] for b in bs[-1:])
    th=PITCH*(len(lines)-1)+(bs[-1][3]-top)+10
    m=Image.new('L',(tw+8,th+8),0); d=ImageDraw.Draw(m)
    for i,(l,b) in enumerate(zip(lines,bs)): d.text(((tw-(b[2]-b[0]))//2-b[0]+4,i*PITCH-top+4),l,font=f,fill=255,stroke_width=2,stroke_fill=255)
    return np.array(m)>127
C.text_mask=tm_th
SA=C.speech_asset('speech_empty.png'); SB=C.speech_asset('speech_empty_flip.png')
L={1:['ลูกค้าใหญ่','ออเดอร์ใหญ่ผ่าน Coke บัดดี้','ดีใจจังหู!'],2:['เดือนหนึ่งมาแค่สองครั้ง','ก็เลยต้องไปแม็คโคร'],3:['สั่งตรงนี้เลยครับ','เราส่งถึงร้าน ผมก็ได้ยอดขาย!'],
4:['ฝรั่งดื่มโค้กเหม็ดเลย! ขายหมดแล้ว!','สั่งผ่าน Coke บัดดี้เลยดีกว่า!'],5:['ได้ผลจริง!','ถูกใจพนักงานขายพรีเซลจังหู!'],6:['ยอดแบบนี้','ให้ตู้แช่ที่เธอขอได้แน่!']}
k=int(sys.argv[1]); out='th_p%d'%k
import shutil
def go(*a,**kw):
    r=run_panel(out,*a,**kw); return r
if k==1:
  for LL,sx in [(['ลูกค้าใหญ่ ออเดอร์ใหญ่','ผ่าน Coke บัดดี้ ดีใจจังหู!'],2.4),(['ลูกค้าใหญ่ ออเดอร์ใหญ่','ผ่าน Coke บัดดี้ ดีใจจังหู!'],2.8),(L[1],2.6)]:
   if go('p1_scr.png',[(460,490,720,770),(400,760,780,1152),(776,650,1000,1050),(1000,490,1240,760),(1040,720,1340,1152),(1352,424,1696,1152)],[(460,490,720,770),(776,650,1000,1050),(1000,490,1240,760),(1352,424,1696,960)],(1000,490,1240,760),'thought',LL,stretch(A20,sx),zs=(1.0,)): break
if k==2: go('p2_ext.png',[(600,445,770,640),(520,640,900,1152),(783,538,1025,1009),(1130,406,1340,1114)],[(600,445,770,640),(783,538,1025,1009),(1140,406,1330,600)],(600,445,770,640),'speech',L[2],SB,tip=(578,592),zs=(1.2,1.15,1.1))
if k==3: go('p3g3_scr.png',[(460,360,800,750),(400,700,860,1152),(836,530,1056,976),(1140,320,1500,560),(1185,560,1500,700),(1120,650,1580,1152)],[(460,360,800,750),(836,530,1056,976),(1140,320,1500,700)],(1140,320,1500,700),'speech',L[3],SA,tip=(1170,612),zs=(1.05,1.0))
if k==4:
    f=0.86; X,Y=143,161; T=lambda b:(round(X+b[0]*f),round(Y+b[1]*f),round(X+b[2]*f),round(Y+b[3]*f))
    go('p4_loc.png',[T(b) for b in [(1416,367,1807,925),(1160,428,1386,1000),(226,503,1084,1075)]],[T(b) for b in [(1416,367,1807,925),(1160,428,1386,1000),(226,503,1084,760)]],T((1490,380,1700,620)),'thought',L[4],stretch(A20,2.0),zs=(1.1,1.05,1.0))
if k==5: go('p5_base.png',[(286,464,1069,946),(964,660,1175,1051),(1295,614,1446,1021)],[(286,464,1069,946),(1295,614,1446,1021)],(1300,614,1440,760),'thought',L[5],stretch(A20,1.4),zs=(1.1,1.05,1.0))
if k==6: go('p6_base.png',[(623,526,818,1095),(990,580,2048,1152)],[(623,526,818,900),(1100,640,1500,700)],(638,526,810,659),'dream',None,None,zs=(1.15,1.1,1.05,1.0),fc_fn=lambda: C.dream_side('b6_rl.png',stretch(A20,1.2),L[6],0.34))
