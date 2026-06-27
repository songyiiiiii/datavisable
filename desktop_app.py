# -*- coding: utf-8 -*-
"""
Nyx Desktop Dashboard — Manual Layout (add_axes positioning)
==============================================================
Every panel positioned by [left, bottom, width, height] coordinates.
Change the numbers in LAYOUT dict to reposition/resize panels.
Background: grayscale t=50 render at alpha=0.06.

RUN: python desktop_app.py
"""

import numpy as np, matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, SpanSelector
from matplotlib.patches import ConnectionPatch
import os, sys, warnings, csv
warnings.filterwarnings('ignore')
sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_all_timesteps

# ============================================================================
# ★ MANUAL LAYOUT CONFIG — edit these numbers to reposition/resize ★
#   Each entry: [left, bottom, width, height] in figure fraction (0-1)
# ============================================================================
LAYOUT = {
    "bg":          [0, 0, 1, 1],            # background image
    "model":       [0.20, 0.22, 0.60, 0.55], # ★ CENTER: 3D render (main visual)
    "timewheel":   [0.02, 0.58, 0.17, 0.38], # top-left: radial stats
    "sparklines":  [0.82, 0.58, 0.16, 0.38], # top-right: evolution
    "histogram":   [0.02, 0.22, 0.48, 0.33], # bottom-left: brush histogram
    "particles":   [0.52, 0.22, 0.46, 0.33], # bottom-right: 3D particles
    "streamgraph": [0.02, 0.02, 0.96, 0.18], # full-width bottom: timeline
    "slider":      [0.14, 0.005, 0.55, 0.02],
    "play_btn":    [0.71, 0.002, 0.04, 0.025],
    "reset_btn":   [0.76, 0.002, 0.05, 0.025],
    "step_label":  [0.82, 0.002, 0.06, 0.025],
    "status":      [0.89, 0.002, 0.09, 0.025],
}

# Color scheme
BG_C   = '#FAFBFC'; GRID_C = '#E5EAF0'; TEXT_C = '#1E293B'
TEXT_L  = '#64748B'; BLUE_M = '#274C77'; BLUE_S = '#8FA3B8'; RED_A = '#C44536'
CONN_C  = '#C8D2E0'

plt.rcParams.update({
    'font.size':7.5,'axes.titlesize':10,'axes.labelsize':8,
    'figure.facecolor':BG_C,'axes.facecolor':BG_C,
    'text.color':TEXT_L,'axes.edgecolor':GRID_C,'grid.color':GRID_C,
})

# ============================================================================
print("Loading data...")
ALL = load_all_timesteps(verbose=True)
means=np.array([ALL[t].mean() for t in range(N_TIMESTEPS)])
stds=np.array([ALL[t].std() for t in range(N_TIMESTEPS)])
HIST={}
for t in range(N_TIMESTEPS):
    h,e=np.histogram(ALL[t].ravel(),bins=64,range=DENSITY_RANGE);HIST[t]={"c":h,"x":(e[:-1]+e[1:])/2}

_TW=np.zeros((N_TIMESTEPS,10))
for t in range(N_TIMESTEPS):
    d=ALL[t].ravel()
    _TW[t]=[(d<8.5).sum()/d.size*100,(d>12.0).sum()/d.size*100,
            np.mean((d-d.mean())**4)/d.std()**4-3,np.mean((d-d.mean())**3)/d.std()**3,
            np.percentile(d,75)-np.percentile(d,25),d.std(),d.mean(),d.min(),d.max(),
            np.percentile(d,99)-np.percentile(d,1)]
vmn,vrng=_TW.min(axis=0),_TW.max(axis=0)-_TW.min(axis=0);vrng[vrng==0]=1
TW_N=(_TW-vmn)/vrng*8+1

CAT_NAMES=["deep_void","void","near_void","sub_filament","cool_filament",
           "warm_filament","proto_cluster","cluster_halo","cluster_core","extreme_peak"]
CAT_CLRS=['#071840','#1A4A7A','#2166AC','#4393C3','#8899AA','#AABBAA',
          '#F4A582','#D6604D','#B2182B','#6B0015']
cat_data=np.zeros((N_TIMESTEPS,len(CAT_NAMES)))
with open(os.path.join(os.path.dirname(OUTPUT_DIR),'processed','category_fractions.csv')) as f:
    r=csv.reader(f);next(r)
    for row in r:t=int(row[0]);cat_data[t]=[float(v) for v in row[1:]]

SS,SUB4=4,{}
for ts in REPRESENTATIVE_STEPS:
    d=ALL[ts][::SS,::SS,::SS];SUB4[ts]=np.ascontiguousarray(np.transpose(d,(2,1,0)))

KF=list(range(0,100,5));KF.append(99);KF=sorted(set(KF))
MODEL={}
for ts in KF:
    p=os.path.join(OUTPUT_DIR,"task1",f"layer_composite_t{ts:04d}.png")
    if os.path.exists(p):MODEL[ts]=plt.imread(p)

CUR,BLO,BHI,PLAY=0,None,None,False
METRICS=["Void%","Peak%","Kurt","Skew","IQR","Std","Mean","Min","Max","P99-P01"]
print(f"  {len(MODEL)} keyframes. Ready.\n")

# ============================================================================
fig=plt.figure(figsize=(23,14))
fig.patch.set_facecolor(BG_C)

# Soft naming for the set of subplots
bg_axes = fig.add_axes(LAYOUT["bg"], zorder=-10)
bg_axes.axis('off')
g_axes = fig.add_axes(LAYOUT["bg"], zorder=-10)

BACKGROUND_FRAME = 0  # use t=0 as default background (most uniform)
# Background: grayscale render at low opacity
if BACKGROUND_FRAME in MODEL:
    from matplotlib.colors import rgb_to_hsv
    img_gray = np.mean(MODEL[BACKGROUND_FRAME][:,:,:3], axis=2)  # grayscale
    img_gray = np.stack([img_gray, img_gray, img_gray], axis=2)  # 3-channel gray
    bg_invert = 1.0 - img_gray * 0.08  # lighten
    bg_axes.imshow(np.clip(bg_invert, 0, 1), aspect='auto', extent=[0,1,0,1], alpha=0.5)

g_axes.patch.set_alpha(0)  # transparent

ax_model  = fig.add_axes(LAYOUT["model"])
ax_tw     = fig.add_axes(LAYOUT["timewheel"])
ax_spark  = fig.add_axes(LAYOUT["sparklines"])
ax_hist   = fig.add_axes(LAYOUT["histogram"])
ax_parts  = fig.add_axes(LAYOUT["particles"], projection='3d')
ax_stream = fig.add_axes(LAYOUT["streamgraph"])
ax_sl     = fig.add_axes(LAYOUT["slider"])
ax_play   = fig.add_axes(LAYOUT["play_btn"])
ax_rst    = fig.add_axes(LAYOUT["reset_btn"])
ax_lbl    = fig.add_axes(LAYOUT["step_label"])
ax_st     = fig.add_axes(LAYOUT["status"])

# ── Style ──
for ax in [ax_tw, ax_hist, ax_spark, ax_stream]:
    ax.set_facecolor('none'); ax.tick_params(labelsize=6.5, colors=TEXT_L)
    for s in ax.spines.values(): s.set_color(GRID_C)
ax_model.axis('off')
ax_parts.set_facecolor('none')
for p in [ax_parts.xaxis.pane, ax_parts.yaxis.pane, ax_parts.zaxis.pane]:
    p.fill=False; p.set_edgecolor(GRID_C)
ax_st.axis('off'); ax_lbl.axis('off')

slider=Slider(ax_sl,'Time Step',0,99,valinit=0,valstep=1,color=BLUE_M)
slider.label.set_color(TEXT_L);slider.valtext.set_color(TEXT_L)
btn_play=Button(ax_play,'Play',color=BLUE_M,hovercolor=BLUE_S)
btn_play.label.set_color('white');btn_play.label.set_fontweight('bold');btn_play.label.set_fontsize(8)
btn_rst=Button(ax_rst,'Reset',color=TEXT_L,hovercolor=GRID_C)
btn_rst.label.set_color('white');btn_rst.label.set_fontsize(8)
step_txt=ax_lbl.text(0.5,0.5,"t=0",ha='center',va='center',fontsize=18,fontweight='bold',color=BLUE_M,transform=ax_lbl.transAxes)
stat_txt=ax_st.text(0,0.5,"",fontsize=7.5,color=TEXT_L,va='center')

def dcolor(v):
    t=np.clip((v-7.5)/7.5,0,1)
    if t<0.3:return(0.13+0.7*t,0.40+0.5*t,0.67-0.5*t)
    elif t<0.5:s=(t-0.3)/0.2;return(0.34+0.56*s,0.55+0.35*s,0.52+0.38*s)
    elif t<0.7:s=(t-0.5)/0.2;return(0.90+0.05*s,0.90-0.12*s,0.90-0.22*s)
    else:s=(t-0.7)/0.3;return(0.95-0.35*s,0.78-0.68*s,0.68-0.58*s)

# ============================================================================
def draw_all(step):
    # CENTER: 3D Render
    ax_model.clear();ax_model.axis('off')
    ns=min(KF,key=lambda x:abs(x-step))
    if ns in MODEL:ax_model.imshow(MODEL[ns])
    ax_model.set_title("Cosmic Web Structure — 3D Isosurface",fontweight='bold',
                       color=TEXT_C,pad=2,fontsize=11)

    # TL: TimeWheel
    ax_tw.clear()
    for t in range(0,N_TIMESTEPS,4):
        al=0.15 if t!=step else 1.0;lw=0.4 if t!=step else 2.8
        px,py=[],[]
        for i in range(10):a=2*np.pi*i/10;r=TW_N[t,i];px.append(r*np.cos(a));py.append(r*np.sin(a))
        px.append(px[0]);py.append(py[0]);ax_tw.plot(px,py,color=get_time_color(t),lw=lw,alpha=al)
    for i in range(10):
        a=2*np.pi*i/10;ax_tw.plot([0,10*np.cos(a)],[0,10*np.sin(a)],color=GRID_C,lw=1.2)
        ax_tw.text(11*np.cos(a),11*np.sin(a),METRICS[i],ha='center',va='center',fontsize=5,color=TEXT_C,fontweight='bold')
    ax_tw.set_xlim(-13,13);ax_tw.set_ylim(-13,13);ax_tw.set_aspect('equal');ax_tw.axis('off')
    ax_tw.set_title("Statistical Signature",fontweight='bold',color=TEXT_L,pad=2,fontsize=8)

    # TR: Sparklines
    ax_spark.clear();ts=np.arange(N_TIMESTEPS)
    ax_spark.plot(ts,stds,color=RED_A,lw=1.8);ax_spark.scatter([step],[stds[step]],color=RED_A,s=60,zorder=10,edgecolors='white',lw=1.5)
    a2=ax_spark.twinx();a2.plot(ts,means,color=BLUE_M,lw=1.8);a2.scatter([step],[means[step]],color=BLUE_M,s=60,zorder=10,edgecolors='white',lw=1.5)
    ax_spark.set_xlabel("Time");ax_spark.set_ylabel("sigma",color=RED_A);a2.set_ylabel("mean",color=BLUE_M)
    ax_spark.set_title("Temporal Metrics",fontweight='bold',color=TEXT_L,pad=2,fontsize=8)
    ax_spark.tick_params(labelsize=6,colors=TEXT_L);a2.tick_params(labelsize=6,colors=BLUE_M)
    ax_spark.text(0.95,0.92,f"t={step}",transform=ax_spark.transAxes,fontsize=11,fontweight='bold',color=TEXT_C,ha='right',
                  bbox=dict(boxstyle='round,pad=0.3',facecolor=BG_C,edgecolor=GRID_C,alpha=0.9))

    # BL: Histogram
    ax_hist.clear();hc=HIST[step];ctr,cnt=hc["x"],hc["c"]
    clrs=[RED_A if(BLO and BLO<=c<=BHI)else BLUE_S for c in ctr]
    ax_hist.bar(ctr,cnt,width=0.07,color=clrs,edgecolor='none',alpha=0.75)
    if BLO:ax_hist.axvspan(BLO,BHI,color=RED_A,alpha=0.10,lw=0)
    ax_hist.set_xlabel("ln(rho)");ax_hist.set_ylabel("Count")
    ax_hist.set_title("Density Distribution (drag to brush ->)",fontweight='bold',color=TEXT_C,pad=2,fontsize=9)

    # BR: Particles
    ax_parts.clear()
    for p in[ax_parts.xaxis.pane,ax_parts.yaxis.pane,ax_parts.zaxis.pane]:p.fill=False;p.set_edgecolor(GRID_C)
    ns=min(REPRESENTATIVE_STEPS,key=lambda x:abs(x-step))
    if ns not in SUB4:d=ALL[ns][::SS,::SS,::SS];SUB4[ns]=np.ascontiguousarray(np.transpose(d,(2,1,0)))
    d3=SUB4[ns];idx=np.argwhere(np.ones_like(d3,dtype=bool));vals=d3.flatten()
    if BLO is not None:mask=(vals>=BLO)&(vals<=BHI);idx=idx[mask];vals=vals[mask]
    n_show=len(vals)
    if n_show>1800:rng=np.random.default_rng(42);si=rng.choice(n_show,size=1800,replace=False);idx=idx[si];vals=vals[si]
    if len(vals)>0:
        cols=[dcolor(v) for v in vals]
        ax_parts.scatter(idx[:,0]*SS,idx[:,1]*SS,idx[:,2]*SS,c=cols,s=3.5,alpha=0.55,marker='.',linewidths=0)
    ax_parts.set_xlim(0,127);ax_parts.set_ylim(0,127);ax_parts.set_zlim(0,127)
    t="Linked Particles"+("" if not BLO else f" [{BLO:.2f},{BHI:.2f}] n={n_show}")
    ax_parts.set_title(t,fontweight='bold',color=RED_A if BLO else TEXT_C,pad=2,fontsize=8)
    ax_parts.tick_params(labelsize=5,colors=TEXT_L);ax_parts.view_init(elev=25,azim=-60+step*1.5)

    # Bottom: Streamgraph
    ax_stream.clear();ts_arr=np.arange(N_TIMESTEPS);cumsum=np.zeros(N_TIMESTEPS)
    for j in range(len(CAT_NAMES)):
        ax_stream.fill_between(ts_arr,cumsum,cumsum+cat_data[:,j],color=CAT_CLRS[j],alpha=0.78,linewidth=0.2,edgecolor='white')
        cumsum+=cat_data[:,j]
    ax_stream.axvline(x=step,color=TEXT_C,lw=2.5,alpha=0.6,ls='--')
    ax_stream.set_xlabel("Time Step",color=TEXT_L);ax_stream.set_ylabel("Volume %",color=TEXT_L)
    ax_stream.set_title("Density Composition Timeline",fontweight='bold',color=TEXT_L,pad=2,fontsize=8)
    ax_stream.set_xlim(0,99);ax_stream.set_ylim(0,100)

    # Status
    step_txt.set_text(f"t={step}");step_txt.set_color(get_time_color(step))
    d=ALL[step];vfrac=(d<8.5).sum()/d.size*100;pfrac=(d>12).sum()/d.size*100
    stat_txt.set_text(f"Void:{vfrac:.1f}%  Peak:{pfrac:.2f}%"+(f"  Brush:[{BLO:.2f},{BHI:.2f}]"if BLO else""))

    fig.canvas.draw_idle()

# ============================================================================
def on_slider(v):global CUR;CUR=int(round(v));draw_all(CUR)
def on_play(event):
    global PLAY;PLAY=not PLAY;btn_play.label.set_text('Pause'if PLAY else'Play')
    if PLAY:anim()
def anim():
    global CUR
    if not PLAY:return
    CUR=(CUR+1)%N_TIMESTEPS;slider.set_val(CUR);draw_all(CUR);fig.canvas.manager.window.after(120,anim)
def on_brush(vmin,vmax):
    global BLO,BHI
    if abs(vmin-vmax)<0.01:return
    BLO,BHI=min(vmin,vmax),max(vmin,vmax);draw_all(CUR)
def on_reset(event):
    global BLO,BHI;BLO,BHI=None,None;draw_all(CUR)

slider.on_changed(on_slider);btn_play.on_clicked(on_play);btn_rst.on_clicked(on_reset)
SpanSelector(ax_hist,on_brush,'horizontal',props=dict(facecolor=RED_A,alpha=0.15))

draw_all(0)
plt.show()
