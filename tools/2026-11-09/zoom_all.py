import sys; sys.path.insert(0,'/home/claude/w')
from zoom_run import *
import json
SA=C.speech_asset('speech_empty.png'); SB=C.speech_asset('speech_empty_flip.png')
R={}
which=sys.argv[1:]
if 'p1' in which: R['p1']=run_panel('p1','p1_scr.png',[(460,490,720,770),(400,760,780,1152),(776,650,1000,1050),(1000,490,1240,760),(1040,720,1340,1152),(1352,424,1696,1152)],[(460,490,720,770),(776,650,1000,1050),(1000,490,1240,760),(1352,424,1696,960)],(1000,490,1240,760),'thought',["Big customer,","big order on Coke Buddy.","I'm happy!"],stretch(A20,2.2),pitch=85)
if 'p2' in which: R['p2']=run_panel('p2','p2_ext.png',[(600,445,770,640),(520,640,900,1152),(783,538,1025,1009),(1130,406,1340,1114)],[(600,445,770,640),(783,538,1025,1009),(1140,406,1330,600)],(600,445,770,640),'speech',["You come only twice","a month. So I go to Makro."],SB,tip=(578,592))
if 'p3' in which: R['p3']=run_panel('p3','p3g3_scr.png',[(460,360,800,750),(400,700,860,1152),(836,530,1056,976),(1140,320,1500,560),(1185,560,1500,700),(1120,650,1580,1152)],[(460,360,800,750),(836,530,1056,976),(1140,320,1500,700)],(1140,320,1500,700),'speech',["Order here. We deliver","to you, and I get the sale!"],SA,tip=(1170,612))
if 'p4' in which: R['p4']=run_panel('p4','p4_ext.png',[(1416,367,1807,925),(1160,428,1386,1000),(226,503,1084,1075)],[(1416,367,1807,925),(1160,428,1386,1000),(226,503,1084,760)],(1476,367,1717,560),'thought',["Farangs drank all my","Coke and Fanta!"],stretch(A20,1.5))
if 'p5' in which: R['p5']=run_panel('p5','p5_base.png',[(286,464,1069,946),(964,660,1175,1051),(1295,614,1446,1021)],[(286,464,1069,946),(1295,614,1446,1021)],(1300,614,1440,760),'thought',["It works! And I love","my preseller!"],stretch(A20,1.4))
if 'p6' in which: R['p6']=run_panel('p6','p6_base.png',[(623,526,818,1095),(1278,744,1356,885)],[(638,526,810,659)],(638,526,810,659),'dream',None,None,fc_fn=lambda: C.dream_cluster('b6_rl.png',stretch(A20,1.4),["At this rate, I can","offer her the cooler","she asked for!"],0.42))
json.dump({k:(v and {kk:(str(vv)) for kk,vv in v.items()}) for k,v in R.items()},open('zoom_%s.json'%'_'.join(which),'w'))
