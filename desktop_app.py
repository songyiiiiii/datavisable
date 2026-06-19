# -*- coding: utf-8 -*-
"""
Nyx Integrated Desktop — Logical Layout with Enriched Analytics
=================================================================
matplotlib TkAgg. Organized by analytical flow:
  Time context → 3D structure → Category evolution → Statistics → Particles

RUN: python desktop_app.py
"""

import numpy as np, matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button, SpanSelector
import os, sys, warnings, csv; warnings.filterwarnings('ignore')
sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_all_timesteps

# ============================================================================
print("Loading data...")
ALL = load_all_timesteps(verbose=True)

# Core stats
means=np.array([ALL[t].mean() for t in range(N_TIMESTEPS)])
stds=np.array([ALL[t].std() for t in range(N_TIMESTEPS)])
mins=np.array([ALL[t].min() for t in range(N_TIMESTEPS)])
maxs=np.array([ALL[t].max() for t in range(N_TIMESTEPS)])
iqrs=np.array([np.percentile(ALL[t],75)-np.percentile(ALL[t],25) for t in range(N_TIMESTEPS)])
p99p01s=np.array([np.percentile(ALL[t],99)-np.percentile(ALL[t],1) for t in range(N_TIMESTEPS)])

# Histograms
HIST={}
for t in range(N_TIMESTEPS):
    h,e=np.histogram(ALL[t].ravel(),bins=64,range=DENSITY_RANGE);HIST[t]={"c":h,"x":(e[:-1]+e[1:])/2}

# TimeWheel data
_TW=np.zeros((N_TIMESTEPS,10))
for t in range(N_TIMESTEPS):
    d=ALL[t].ravel()
    _TW[t]=[(d<8.5).sum()/d.size*100,(d>12.0).sum()/d.size*100,
            np.mean((d-d.mean())**4)/d.std()**4-3,np.mean((d-d.mean())**3)/d.std()**3,
            np.percentile(d,75)-np.percentile(d,25),d.std(),d.mean(),d.min(),d.max(),
            np.percentile(d,99)-np.percentile(d,1)]
vmn,vrng=_TW.min(axis=0),_TW.max(axis=0)-_TW.min(axis=0);vrng[vrng==0]=1
TW_N=(_TW-vmn)/vrng*8+1

# Category fractions from secondary data
CAT_NAMES=["deep_void","void","near_void","sub_filament","cool_filament",
           "warm_filament","proto_cluster","cluster_halo","cluster_core","extreme_peak"]
CAT_COLORS=['#071840',BLUE_700,BLUE_500,BLUE_300,'#8899aa','#aabbaa',RED_100,RED_300,RED_500,'#6b0015']
cat_data=np.zeros((N_TIMESTEPS,len(CAT_NAMES)))
with open(os.path.join(os.path.dirname(OUTPUT_DIR),'processed','category_fractions.csv')) as f:
    reader=csv.reader(f);next(reader)
    for row in reader:
        t=int(row[0]);cat_data[t]=[float(v) for v in row[1:]]

# Particles data
SS,SUB4=4,{}
for ts in REPRESENTATIVE_STEPS:
    d=ALL[ts][::SS,::SS,::SS];SUB4[ts]=np.ascontiguousarray(np.transpose(d,(2,1,0)))

# Key frames for center display
KEY_FRAMES=list(range(0,100,5));KEY_FRAMES.append(99);KEY_FRAMES=sorted(set(KEY_FRAMES))
MODEL={}
for ts in KEY_FRAMES:
    p=os.path.join(OUTPUT_DIR,"task1",f"layer_composite_t{ts:04d}.png")
    if os.path.exists(p):MODEL[ts]=plt.imread(p)

CUR,BLO,BHI,PLAY=0,None,None,False
METRICS=["Void%","Peak%","Kurt","Skew","IQR","Std","Mean","Min","Max","P99-P01"]
print(f"  {len(MODEL)} keyframes. Ready.\n")

# ============================================================================
plt.rcParams.update({'font.size':7,'axes.titlesize':9.5,'axes.labelsize':7.5,
                     'figure.facecolor':WHITE,'axes.facecolor':WHITE})
fig=plt.figure(figsize=(23,14))
fig.patch.set_facecolor(WHITE)
fig.canvas.manager.set_window_title('Nyx Integrated Visual Analytics')

# Logical layout: 3 rows
# Row 1: TimeWheel(left) | 3D Render(center) | Sparklines(right)
# Row 2: Category Streamgraph (full width)
# Row 3: Histogram(left) | 3D Particles(right)
gs=GridSpec(3,3,fig,height_ratios=[2.0,1.0,1.5],width_ratios=[1.2,1.8,1.3],
            hspace=0.38,wspace=0.25,left=0.03,right=0.98,top=0.94,bottom=0.07)

ax_tw=fig.add_subplot(gs[0,0])
ax_model=fig.add_subplot(gs[0,1])
ax_spark=fig.add_subplot(gs[0,2])
ax_stream=fig.add_subplot(gs[1,:])
ax_hist=fig.add_subplot(gs[2,0:2])
ax_parts=fig.add_subplot(gs[2,2],projection='3d')

# Controls
ax_sl=fig.add_axes([0.12,0.02,0.55,0.022])
ax_play=fig.add_axes([0.69,0.013,0.04,0.033])
ax_rst=fig.add_axes([0.74,0.013,0.05,0.033])
ax_lbl=fig.add_axes([0.80,0.013,0.06,0.033])
ax_st=fig.add_axes([0.87,0.013,0.10,0.033])

for ax in[ax_tw,ax_hist,ax_spark,ax_stream]:ax.set_facecolor(WHITE);ax.tick_params(labelsize=6.5,colors=GRAY_400)
ax_model.axis('off')
ax_parts.set_facecolor(WHITE)
for p in[ax_parts.xaxis.pane,ax_parts.yaxis.pane,ax_parts.zaxis.pane]:p.fill=False;p.set_edgecolor(GRAY_200)
ax_st.axis('off');ax_lbl.axis('off')

slider=Slider(ax_sl,'Time Step',0,99,valinit=0,valstep=1,color=BLUE_500)
slider.label.set_color(GRAY_600);slider.valtext.set_color(GRAY_500)
btn_play=Button(ax_play,'Play',color=BLUE_500,hovercolor=BLUE_300)
btn_play.label.set_color('white');btn_play.label.set_fontweight('bold');btn_play.label.set_fontsize(8)
btn_rst=Button(ax_rst,'Reset',color=GRAY_400,hovercolor=GRAY_300)
btn_rst.label.set_color('white');btn_rst.label.set_fontsize(8)
step_txt=ax_lbl.text(0.5,0.5,"t=0",ha='center',va='center',fontsize=16,fontweight='bold',color=BLUE_700,transform=ax_lbl.transAxes)
stat_txt=ax_st.text(0,0.5,"",fontsize=7.5,color=GRAY_500,va='center')

def dcolor(v):
    t=np.clip((v-7.5)/7.5,0,1)
    if t<0.3:return(0.13+0.7*t,0.40+0.5*t,0.67-0.5*t)
    elif t<0.5:s=(t-0.3)/0.2;return(0.34+0.56*s,0.55+0.35*s,0.52+0.38*s)
    elif t<0.7:s=(t-0.5)/0.2;return(0.90+0.05*s,0.90-0.12*s,0.90-0.22*s)
    else:s=(t-0.7)/0.3;return(0.95-0.35*s,0.78-0.68*s,0.68-0.58*s)

# ============================================================================
def draw_all(step):
    # ── CENTER: 3D Render ──
    ax_model.clear();ax_model.axis('off')
    ns=min(KEY_FRAMES,key=lambda x:abs(x-step))
    if ns in MODEL:ax_model.imshow(MODEL[ns])
    ax_model.set_title("Task 1 — 3D Isosurface Render",fontweight='bold',color=BLACK,pad=3)

    # ── LEFT: TimeWheel ──
    ax_tw.clear();ax_tw.set_facecolor(WHITE)
    for t in range(0,N_TIMESTEPS,3):
        al=0.20 if t!=step else 1.0;lw=1.0 if t!=step else 3.0
        px,py=[],[]
        for i in range(10):a=2*np.pi*i/10;r=TW_N[t,i];px.append(r*np.cos(a));py.append(r*np.sin(a))
        px.append(px[0]);py.append(py[0]);ax_tw.plot(px,py,color=get_time_color(t),lw=lw,alpha=al)
    for i in range(10):
        a=2*np.pi*i/10;ax_tw.plot([0,10*np.cos(a)],[0,10*np.sin(a)],color=GRAY_400,lw=1.5)
        ax_tw.text(11*np.cos(a),11*np.sin(a),METRICS[i],ha='center',va='center',fontsize=5.5,color=BLACK,fontweight='bold')
    ax_tw.set_xlim(-13,13);ax_tw.set_ylim(-13,13);ax_tw.set_aspect('equal');ax_tw.axis('off')
    ax_tw.set_title("TimeWheel — Radial Stats",fontweight='bold',color=BLACK,pad=3)

    # ── RIGHT: Sparklines ──
    ax_spark.clear();ax_spark.set_facecolor(WHITE);ts=np.arange(N_TIMESTEPS)
    ax_spark.plot(ts,stds,color=RED_500,lw=1.5);ax_spark.scatter([step],[stds[step]],color=BLUE_500,s=35,zorder=10)
    a2=ax_spark.twinx();a2.plot(ts,means,color=BLUE_500,lw=1.5);a2.scatter([step],[means[step]],color=RED_500,s=35,zorder=10)
    ax_spark.set_xlabel("Time");ax_spark.set_ylabel("sigma",color=RED_500);a2.set_ylabel("mean",color=BLUE_500)
    ax_spark.set_title(f"Evolution — sigma={stds[step]:.4f}  mean={means[step]:.3f}",fontweight='bold',color=BLACK,pad=3)
    ax_spark.tick_params(labelsize=6,colors=GRAY_400);a2.tick_params(labelsize=6,colors=BLUE_500)

    # ── MIDDLE ROW: Category Streamgraph ──
    ax_stream.clear();ax_stream.set_facecolor(WHITE)
    ts_arr=np.arange(N_TIMESTEPS)
    # Stack categories bottom-up
    cumsum=np.zeros(N_TIMESTEPS)
    for j in range(len(CAT_NAMES)):
        ax_stream.fill_between(ts_arr,cumsum,cumsum+cat_data[:,j],
                               color=CAT_COLORS[j],alpha=0.8,linewidth=0.3,edgecolor='white')
        cumsum+=cat_data[:,j]
    ax_stream.axvline(x=step,color=BLACK,lw=2,alpha=0.5,ls='--')
    ax_stream.set_xlabel("Time Step");ax_stream.set_ylabel("Volume Fraction %")
    ax_stream.set_title("Density Category Streamgraph — Composition Evolution (dashed=current step)",fontweight='bold',color=BLACK,pad=3)
    ax_stream.set_xlim(0,99);ax_stream.set_ylim(0,100)
    # Mini legend
    for j in[0,3,6,9]:
        ax_stream.text(2+j*25,102,CAT_NAMES[j].replace('_',' '),fontsize=6,color=CAT_COLORS[j],fontweight='bold')

    # ── BOTTOM-LEFT: Brush Histogram ──
    ax_hist.clear();ax_hist.set_facecolor(WHITE)
    hc=HIST[step];ctr,cnt=hc["x"],hc["c"]
    clrs=[RED_500 if(BLO and BLO<=c<=BHI)else GRAY_400 for c in ctr]
    ax_hist.bar(ctr,cnt,width=0.07,color=clrs,edgecolor='none',alpha=0.85)
    if BLO:ax_hist.axvspan(BLO,BHI,color=RED_500,alpha=0.12)
    ax_hist.set_xlabel("ln(rho)");ax_hist.set_ylabel("Count")
    ax_hist.set_title("Brush Histogram (drag to select) → linked to 3D particles →",fontweight='bold',color=BLACK,pad=3)

    # ── BOTTOM-RIGHT: 3D Particles ──
    ax_parts.clear();ax_parts.set_facecolor(WHITE)
    for p in[ax_parts.xaxis.pane,ax_parts.yaxis.pane,ax_parts.zaxis.pane]:p.fill=False;p.set_edgecolor(GRAY_200)
    ns=min(REPRESENTATIVE_STEPS,key=lambda x:abs(x-step))
    if ns not in SUB4:d=ALL[ns][::SS,::SS,::SS];SUB4[ns]=np.ascontiguousarray(np.transpose(d,(2,1,0)))
    d3=SUB4[ns];idx=np.argwhere(np.ones_like(d3,dtype=bool));vals=d3.flatten()
    if BLO is not None:mask=(vals>=BLO)&(vals<=BHI);idx=idx[mask];vals=vals[mask]
    n_show=len(vals)
    if n_show>2000:rng=np.random.default_rng(42);si=rng.choice(n_show,size=2000,replace=False);idx=idx[si];vals=vals[si]
    if len(vals)>0:
        cols=[dcolor(v) for v in vals]
        ax_parts.scatter(idx[:,0]*SS,idx[:,1]*SS,idx[:,2]*SS,c=cols,s=4,alpha=0.6,marker='.',linewidths=0)
    ax_parts.set_xlim(0,127);ax_parts.set_ylim(0,127);ax_parts.set_zlim(0,127)
    t="3D Particles"+(" (all)" if not BLO else f" [{BLO:.2f},{BHI:.2f}] n={n_show}")
    ax_parts.set_title(t,fontweight='bold',color=RED_500 if BLO else BLACK,pad=3)
    ax_parts.tick_params(labelsize=5,colors=GRAY_400);ax_parts.view_init(elev=25,azim=-60+step*1.5)

    step_txt.set_text(f"t={step}");step_txt.set_color(get_time_color(step))
    d=ALL[step];vfrac=(d<8.5).sum()/d.size*100;pfrac=(d>12).sum()/d.size*100
    stat_txt.set_text(f"Void:{vfrac:.1f}% Peak:{pfrac:.2f}%"+(f" Brush:[{BLO:.2f},{BHI:.2f}]" if BLO else ""))
    fig.canvas.draw_idle()

# ============================================================================
def on_slider(v):global CUR;CUR=int(round(v));draw_all(CUR)
def on_play(event):
    global PLAY;PLAY=not PLAY
    btn_play.label.set_text('Pause' if PLAY else 'Play')
    if PLAY:anim()
def anim():
    global CUR
    if not PLAY:return
    CUR=(CUR+1)%N_TIMESTEPS;slider.set_val(CUR);draw_all(CUR)
    fig.canvas.manager.window.after(120,anim)
def on_brush(vmin,vmax):
    global BLO,BHI
    if abs(vmin-vmax)<0.01:return
    BLO,BHI=min(vmin,vmax),max(vmin,vmax);draw_all(CUR)
def on_reset(event):
    global BLO,BHI;BLO,BHI=None,None;draw_all(CUR)

slider.on_changed(on_slider);btn_play.on_clicked(on_play);btn_rst.on_clicked(on_reset)
SpanSelector(ax_hist,on_brush,'horizontal',props=dict(facecolor=RED_500,alpha=0.2))

draw_all(0)
plt.show()
