# -*- coding: utf-8 -*-
"""
Nyx Integrated Desktop — All Tasks, One Window
================================================
Single matplotlib TkAgg window. No PyVista, no browser, no server.
All 5 tasks in one unified layout with shared slider.

RUN: python desktop_app.py
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button, SpanSelector
import os, sys, warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_all_timesteps

# ============================================================================
print("Loading 100 steps...")
ALL = load_all_timesteps(verbose=True)

means = np.array([ALL[t].mean() for t in range(N_TIMESTEPS)])
stds  = np.array([ALL[t].std()  for t in range(N_TIMESTEPS)])
mins  = np.array([ALL[t].min()  for t in range(N_TIMESTEPS)])
maxs  = np.array([ALL[t].max()  for t in range(N_TIMESTEPS)])

HIST = {}
for t in range(N_TIMESTEPS):
    h, e = np.histogram(ALL[t].ravel(), bins=64, range=DENSITY_RANGE)
    HIST[t] = {"c": h, "x": (e[:-1]+e[1:])/2}

# Radial stats
_TW = np.zeros((N_TIMESTEPS, 10))
for t in range(N_TIMESTEPS):
    d = ALL[t].ravel()
    _TW[t] = [(d<8.5).sum()/d.size*100,(d>12.0).sum()/d.size*100,
              np.mean((d-d.mean())**4)/d.std()**4-3,np.mean((d-d.mean())**3)/d.std()**3,
              np.percentile(d,75)-np.percentile(d,25),d.std(),d.mean(),d.min(),d.max(),
              np.percentile(d,99)-np.percentile(d,1)]
vmn = _TW.min(axis=0); vmx = _TW.max(axis=0); vr = vmx-vmn; vr[vr==0]=1
TW_N = (_TW-vmn)/vr*8+1

SS = 4; SUB = {}
for ts in REPRESENTATIVE_STEPS:
    d = ALL[ts][::SS,::SS,::SS]
    SUB[ts] = np.ascontiguousarray(np.transpose(d,(2,1,0)))

# Pre-load model images
MODEL = {}
for ts in REPRESENTATIVE_STEPS:
    p = os.path.join(OUTPUT_DIR,"task1",f"layer_composite_t{ts:04d}.png")
    if os.path.exists(p): MODEL[ts] = plt.imread(p)

CUR, PLAY, BLO, BHI = 0, False, None, None
METRICS = ["Void%","Peak%","Kurt","Skew","IQR","Std","Mean","Min","Max","P99-P01"]
print("Ready.\n")

# ============================================================================
# Figure
# ============================================================================
plt.rcParams.update({'font.size':7,'axes.titlesize':9.5,'axes.labelsize':7.5,
                     'figure.facecolor':WHITE,'axes.facecolor':WHITE,'text.color':GRAY_600})
fig = plt.figure(figsize=(20, 12.5))
fig.patch.set_facecolor(WHITE)
fig.canvas.manager.set_window_title('Nyx Integrated Explorer — Tasks 1-5')

gs = GridSpec(3, 4, fig, height_ratios=[2, 1.8, 0.25],
              width_ratios=[2.2, 2, 1.6, 1.6],
              hspace=0.42, wspace=0.32, left=0.03, right=0.98, top=0.94, bottom=0.06)

# ── Row 1 ──
ax_model  = fig.add_subplot(gs[0, 0])                # Task 1: 3D model image
ax_parts  = fig.add_subplot(gs[0, 1], projection='3d') # Task 1+4: 3D particles
ax_tw     = fig.add_subplot(gs[0, 2:])                # Task 5: Radial stats
# ── Row 2 ──
ax_hist   = fig.add_subplot(gs[1, 0])                # Task 4: Brush histogram
ax_evo    = fig.add_subplot(gs[1, 1])                # Task 2: Evolution
ax_ht     = fig.add_subplot(gs[1, 2:])               # Task 3: Histogram tracking
# ── Row 3 ──
ax_sl     = fig.add_axes([0.12, 0.018, 0.50, 0.022])# Slider
ax_play   = fig.add_axes([0.65, 0.012, 0.04, 0.032])# Play btn
ax_rst    = fig.add_axes([0.70, 0.012, 0.05, 0.032])# Reset btn
ax_lbl    = fig.add_axes([0.76, 0.012, 0.06, 0.032])# Step label
ax_st     = fig.add_axes([0.83, 0.012, 0.15, 0.032])# Status

for ax in [ax_model, ax_tw, ax_hist, ax_evo, ax_ht]: ax.set_facecolor(WHITE)
ax_parts.set_facecolor(WHITE)
for p in [ax_parts.xaxis.pane, ax_parts.yaxis.pane, ax_parts.zaxis.pane]:
    p.fill = False; p.set_edgecolor(GRAY_200)
ax_model.axis('off'); ax_st.axis('off'); ax_lbl.axis('off')

slider  = Slider(ax_sl, 'Time Step', 0, 99, valinit=0, valstep=1, color=BLUE_500)
slider.label.set_color(GRAY_600); slider.valtext.set_color(GRAY_500)
btn_play = Button(ax_play, 'Play', color=BLUE_500, hovercolor=BLUE_300)
btn_play.label.set_color('white'); btn_play.label.set_fontweight('bold'); btn_play.label.set_fontsize(8)
btn_rst  = Button(ax_rst, 'Reset', color=GRAY_400, hovercolor=GRAY_300)
btn_rst.label.set_color('white'); btn_rst.label.set_fontsize(8)
step_txt = ax_lbl.text(0.5,0.5,"t=0",ha='center',va='center',fontsize=15,fontweight='bold',color=BLUE_700,transform=ax_lbl.transAxes)
stat_txt = ax_st.text(0,0.5,"",fontsize=7,color=GRAY_500,va='center')

# ============================================================================
# Draw functions
# ============================================================================
def dcolor(v):
    t = np.clip((v-7.5)/7.5,0,1)
    if t<0.3: return (0.13+0.7*t,0.40+0.5*t,0.67-0.5*t)
    elif t<0.5: s=(t-0.3)/0.2; return (0.34+0.56*s,0.55+0.35*s,0.52+0.38*s)
    elif t<0.7: s=(t-0.5)/0.2; return (0.90+0.05*s,0.90-0.12*s,0.90-0.22*s)
    else: s=(t-0.7)/0.3; return (0.95-0.35*s,0.78-0.68*s,0.68-0.58*s)

def draw_model(step):
    ax_model.clear(); ax_model.axis('off')
    ns = min(REPRESENTATIVE_STEPS, key=lambda x: abs(x-step))
    if ns in MODEL: ax_model.imshow(MODEL[ns])
    ax_model.set_title("Task 1: 3D Isosurface Model", fontweight='bold', color=BLACK, pad=3)

def draw_parts(step):
    ax_parts.clear(); ax_parts.set_facecolor(WHITE)
    for p in [ax_parts.xaxis.pane, ax_parts.yaxis.pane, ax_parts.zaxis.pane]:
        p.fill = False; p.set_edgecolor(GRAY_200)
    ax_parts.set_xlim(0,127); ax_parts.set_ylim(0,127); ax_parts.set_zlim(0,127)
    ax_parts.tick_params(labelsize=5.5, colors=GRAY_400)

    ns = min(REPRESENTATIVE_STEPS, key=lambda x: abs(x-step))
    if ns not in SUB:
        d = ALL[ns][::SS,::SS,::SS]; SUB[ns] = np.ascontiguousarray(np.transpose(d,(2,1,0)))
    d3 = SUB[ns]; idx = np.argwhere(np.ones_like(d3,dtype=bool)); vals = d3.flatten()
    n_all = len(vals)
    if BLO is not None: mask = (vals>=BLO)&(vals<=BHI); idx=idx[mask]; vals=vals[mask]
    n_show = len(vals)
    if n_show > 4000:
        rng = np.random.default_rng(42); si = rng.choice(n_show,size=4000,replace=False)
        idx=idx[si]; vals=vals[si]
    if len(vals) > 0:
        cols = [dcolor(v) for v in vals]
        ax_parts.scatter(idx[:,0]*SS, idx[:,1]*SS, idx[:,2]*SS, c=cols, s=4, alpha=0.55, marker='.', linewidths=0)
    ax_parts.view_init(elev=25, azim=-60+step*1.5)
    t = "Task 1+4: 3D Particles"
    if BLO: t += f" [{BLO:.2f},{BHI:.2f}] n={n_show}"
    ax_parts.set_title(t, fontweight='bold', color=RED_500 if BLO else BLACK, pad=3)

def draw_tw(step):
    ax_tw.clear(); ax_tw.set_facecolor(WHITE)
    rot = 0  # could be interactive
    for t in range(N_TIMESTEPS):
        alpha_val = 0.28 if t != step else 1.0; lw = 1.8 if t != step else 4.0
        px, py = [], []
        for i in range(10):
            angle = 2*np.pi*i/10; r = TW_N[t,i]
            px.append(r*np.cos(angle)); py.append(r*np.sin(angle))
        px.append(px[0]); py.append(py[0])
        ax_tw.plot(px, py, color=get_time_color(t), lw=lw, alpha=alpha_val)
    # Axes
    for i in range(10):
        angle = 2*np.pi*i/10
        ax_tw.plot([0,10*np.cos(angle)],[0,10*np.sin(angle)],color=GRAY_400,lw=2.5)
        ax_tw.text(11*np.cos(angle),11*np.sin(angle),METRICS[i],ha='center',va='center',fontsize=6.5,color=BLACK,fontweight='bold')
    # Decagon frame
    fx,fy=[],[]
    for i in range(11):
        a=2*np.pi*(i%10)/10; fx.append(10*np.cos(a)); fy.append(10*np.sin(a))
    ax_tw.plot(fx,fy,color=GRAY_300,lw=1,ls='--')
    ax_tw.set_xlim(-13,13); ax_tw.set_ylim(-13,13); ax_tw.set_aspect('equal')
    ax_tw.axis('off')
    ax_tw.set_title(f"Task 5: Radial Stats (bold=t={step})", fontweight='bold', color=BLACK, pad=3)

def draw_hist(step):
    ax_hist.clear(); ax_hist.set_facecolor(WHITE)
    hc = HIST[step]; ctr, cnt = hc["x"], hc["c"]
    clrs = [RED_500 if (BLO and BLO<=c<=BHI) else GRAY_400 for c in ctr]
    ax_hist.bar(ctr, cnt, width=0.07, color=clrs, edgecolor='none', alpha=0.85)
    if BLO: ax_hist.axvspan(BLO, BHI, color=RED_500, alpha=0.12)
    ax_hist.set_xlabel("ln(rho)"); ax_hist.set_ylabel("Count")
    ax_hist.set_title("Task 4: Drag to Brush", fontweight='bold', color=BLACK, pad=3)
    ax_hist.tick_params(labelsize=6.5)

def draw_evo(step):
    ax_evo.clear(); ax_evo.set_facecolor(WHITE)
    ts = np.arange(N_TIMESTEPS)
    ax_evo.plot(ts, stds, color=RED_500, lw=1.8); ax_evo.axvline(step, color=BLUE_500, ls='--', lw=1.5)
    ax2 = ax_evo.twinx(); ax2.plot(ts, means, color=BLUE_500, lw=1.5)
    ax_evo.set_xlabel("Time"); ax_evo.set_ylabel("sigma",color=RED_500); ax2.set_ylabel("mean",color=BLUE_500)
    ax_evo.set_title(f"Task 2: sigma={stds[step]:.4f} mean={means[step]:.3f}", fontweight='bold', color=BLACK, pad=3)
    ax_evo.tick_params(labelsize=6); ax2.tick_params(labelsize=6,colors=BLUE_500)

def draw_ht(step):
    ax_ht.clear(); ax_ht.set_facecolor(WHITE)
    for ts in [0,20,40,60,80,99]:
        hc = HIST[ts]; c = get_time_color(ts)
        lw = 2.5 if ts==step else 0.5; al = 1.0 if ts==step else 0.25
        ax_ht.plot(hc["x"], hc["c"], color=c, lw=lw, alpha=al, label=f"t={ts}"if ts in[0,99]else"")
    ax_ht.set_xlabel("ln(rho)"); ax_ht.set_ylabel("Count")
    ax_ht.set_title(f"Task 3: Histogram Tracking", fontweight='bold', color=BLACK, pad=3)
    ax_ht.legend(fontsize=5, loc='upper right', frameon=True, ncol=3); ax_ht.tick_params(labelsize=6.5)

def draw_all(step):
    draw_model(step); draw_parts(step); draw_tw(step)
    draw_hist(step); draw_evo(step); draw_ht(step)
    step_txt.set_text(f"t={step}"); step_txt.set_color(get_time_color(step))
    if BLO: stat_txt.set_text(f"Brush:[{BLO:.2f},{BHI:.2f}]")
    else: stat_txt.set_text("Drag in histogram")
    fig.canvas.draw_idle()

# ============================================================================
# Callbacks
# ============================================================================
def on_slider(val):
    global CUR; CUR = int(round(val)); draw_all(CUR)

def on_play(event):
    global PLAY; PLAY = not PLAY
    btn_play.label.set_text('Pause' if PLAY else 'Play')
    if PLAY: anim()

def anim():
    global CUR
    if not PLAY: return
    CUR = (CUR+1)%N_TIMESTEPS; slider.set_val(CUR); draw_all(CUR)
    fig.canvas.manager.window.after(150, anim)

def on_brush(vmin, vmax):
    global BLO, BHI
    if abs(vmin-vmax)<0.01: return
    BLO, BHI = min(vmin,vmax), max(vmin,vmax); draw_all(CUR)

def on_reset(event):
    global BLO, BHI; BLO, BHI = None, None; draw_all(CUR)

slider.on_changed(on_slider)
btn_play.on_clicked(on_play)
btn_rst.on_clicked(on_reset)
SpanSelector(ax_hist, on_brush, 'horizontal', props=dict(facecolor=RED_500, alpha=0.2))

draw_all(0)

print("="*60)
print("INTEGRATED DESKTOP — All 5 Tasks, One Window")
print("  Slider: time | Histogram: drag to brush | 3D: drag to rotate")
print("="*60)

plt.show()
