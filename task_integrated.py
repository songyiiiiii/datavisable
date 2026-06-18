# -*- coding: utf-8 -*-
"""
Nyx Integrated Explorer — All 5 Tasks, One Window
==================================================
matplotlib TkAgg window. All charts visible. Shared slider.
- Task 1: 3D model (pre-rendered image) + 3D Particle Scatter (interactive)
- Task 2: Evolution stats charts
- Task 3: Histogram tracking overlay
- Task 4: Interactive histogram with brushing -> 3D particle highlight
- Task 5: TimeWheel polar spiral
RUN: python task_integrated.py
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
p01s  = np.array([np.percentile(ALL[t],1) for t in range(N_TIMESTEPS)])
p99s  = np.array([np.percentile(ALL[t],99) for t in range(N_TIMESTEPS)])

HIST = {}
for t in range(N_TIMESTEPS):
    h, e = np.histogram(ALL[t].ravel(), bins=64, range=DENSITY_RANGE)
    HIST[t] = {"c": h, "x": (e[:-1]+e[1:])/2}

TW_TH = np.linspace(0, 10*np.pi, N_TIMESTEPS)
TW_R  = np.linspace(2, 10, N_TIMESTEPS)

SS = 4
SUB = {}
for ts in REPRESENTATIVE_STEPS:
    d = ALL[ts][::SS,::SS,::SS]
    SUB[ts] = np.ascontiguousarray(np.transpose(d,(2,1,0)))

# Pre-load model images as numpy arrays (avoids PIL import in draw loop)
MODEL_IMGS = {}
for ts in REPRESENTATIVE_STEPS:
    p = os.path.join(OUTPUT_DIR, "task1", f"layer_composite_t{ts:04d}.png")
    if os.path.exists(p):
        MODEL_IMGS[ts] = plt.imread(p)

CUR, PLAY, BLO, BHI = 0, False, None, None
_tid = None

print("Ready.\n")

# ============================================================================
# Color helper
# ============================================================================
def dcolor(v):
    t = np.clip((v-7.5)/7.5, 0, 1)
    if t<0.3: return (0.13+0.7*t, 0.40+0.5*t, 0.67-0.5*t)
    elif t<0.5: s=(t-0.3)/0.2; return (0.34+0.56*s, 0.55+0.35*s, 0.52+0.38*s)
    elif t<0.7: s=(t-0.5)/0.2; return (0.90+0.05*s, 0.90-0.12*s, 0.90-0.22*s)
    else: s=(t-0.7)/0.3; return (0.95-0.35*s, 0.78-0.68*s, 0.68-0.58*s)

# ============================================================================
# Figure
# ============================================================================
plt.rcParams.update({'font.size':7.5, 'axes.titlesize':10, 'axes.labelsize':8,
                     'figure.facecolor':WHITE, 'axes.facecolor':WHITE,
                     'text.color':GRAY_600, 'xtick.labelsize':6.5, 'ytick.labelsize':6.5})
fig = plt.figure(figsize=(20, 13))
fig.patch.set_facecolor(WHITE)
fig.canvas.manager.set_window_title('Nyx Integrated Explorer — Tasks 1-5')

gs = GridSpec(2, 4, fig, height_ratios=[2.5, 2], width_ratios=[2, 2.2, 1.6, 1.6],
              hspace=0.35, wspace=0.30, left=0.04, right=0.98, top=0.94, bottom=0.07)

# ── Row 1 ──
ax_model = fig.add_subplot(gs[0, 0])               # Task 1: 3D model image
ax_parts = fig.add_subplot(gs[0, 1], projection='3d')  # Task 1: 3D particles
ax_tw    = fig.add_subplot(gs[0, 2], projection='polar')  # Task 5: TimeWheel
ax_hist  = fig.add_subplot(gs[0, 3])               # Task 4: Brush histogram

# ── Row 2 ──
ax_evo   = fig.add_subplot(gs[1, 0:2])             # Task 2: Evolution stats
ax_ht    = fig.add_subplot(gs[1, 2:])              # Task 3: Histogram tracking

# ── 3D particle style ──
for ax in [ax_parts]:
    ax.set_facecolor(WHITE)
    for p in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        p.fill=False; p.set_edgecolor(GRAY_200)

# ── Slider ──
ax_sl = fig.add_axes([0.12, 0.02, 0.55, 0.022])
slider = Slider(ax_sl, 'Time Step', 0, 99, valinit=0, valstep=1, color=BLUE_500)
slider.label.set_color(GRAY_600); slider.valtext.set_color(GRAY_500)

# ── Buttons ──
ax_play = fig.add_axes([0.70, 0.015, 0.05, 0.032])
btn_play = Button(ax_play, 'Play', color=BLUE_500, hovercolor=BLUE_300)
btn_play.label.set_color('white'); btn_play.label.set_fontweight('bold'); btn_play.label.set_fontsize(9)

ax_rst = fig.add_axes([0.76, 0.015, 0.06, 0.032])
btn_rst = Button(ax_rst, 'Reset', color=GRAY_400, hovercolor=GRAY_300)
btn_rst.label.set_color('white'); btn_rst.label.set_fontsize(9)

# ── Step label ──
ax_lbl = fig.add_axes([0.83, 0.015, 0.05, 0.032]); ax_lbl.axis('off')
step_txt = ax_lbl.text(0.5, 0.5, "t=0", ha='center', va='center',
                       fontsize=15, fontweight='bold', color=BLUE_700, transform=ax_lbl.transAxes)

# ── Status ──
ax_st = fig.add_axes([0.89, 0.015, 0.10, 0.032]); ax_st.axis('off')
status_txt = ax_st.text(0, 0.5, "", fontsize=7, color=GRAY_500, va='center')

# ============================================================================
# Draw functions
# ============================================================================
def draw_model(step):
    ax_model.clear(); ax_model.set_facecolor(WHITE)
    ns = min(REPRESENTATIVE_STEPS, key=lambda x: abs(x-step))
    if ns in MODEL_IMGS:
        ax_model.imshow(MODEL_IMGS[ns])
    ax_model.axis('off')
    ax_model.set_title("Task 1: 3D Isosurface Model", fontweight='bold', color=BLACK, pad=4, fontsize=10)


def draw_particles(step):
    ax_parts.clear(); ax_parts.set_facecolor(WHITE)
    for p in [ax_parts.xaxis.pane, ax_parts.yaxis.pane, ax_parts.zaxis.pane]:
        p.fill=False; p.set_edgecolor(GRAY_200)
    ax_parts.set_title("Task 1+4: 3D Particles (brush-linked)", fontweight='bold', color=BLACK, pad=4, fontsize=10)
    ax_parts.set_xlabel('X'); ax_parts.set_ylabel('Y'); ax_parts.set_zlabel('Z')
    ax_parts.set_xlim(0,127); ax_parts.set_ylim(0,127); ax_parts.set_zlim(0,127)
    ax_parts.tick_params(colors=GRAY_400, labelsize=6)

    ns = min(REPRESENTATIVE_STEPS, key=lambda x: abs(x-step))
    if ns not in SUB:
        d = ALL[ns][::SS,::SS,::SS]; SUB[ns] = np.ascontiguousarray(np.transpose(d,(2,1,0)))
    d3 = SUB[ns]
    idx = np.argwhere(np.ones_like(d3,dtype=bool)); vals = d3.flatten()

    # Apply brush if active
    if BLO is not None:
        mask = (vals>=BLO)&(vals<=BHI); idx=idx[mask]; vals=vals[mask]

    n_total = len(vals)
    if n_total > 4000:
        rng = np.random.default_rng(42); si = rng.choice(n_total, size=4000, replace=False)
        idx=idx[si]; vals=vals[si]

    if len(vals) > 0:
        cols = [dcolor(v) for v in vals]
        ax_parts.scatter(idx[:,0]*SS, idx[:,1]*SS, idx[:,2]*SS, c=cols, s=4,
                        alpha=0.6, marker='.', linewidths=0)
    ax_parts.view_init(elev=25, azim=-60+step*1.5)

    # Show brush info in title
    if BLO is not None:
        ax_parts.set_title(f"Task 1+4: Particles [{BLO:.2f},{BHI:.2f}] n={n_total:,}",
                          fontweight='bold', color=RED_500, pad=4, fontsize=10)


def draw_timewheel(step):
    ax_tw.clear(); ax_tw.set_facecolor(WHITE)
    cols_tw = [get_time_color(t) for t in range(N_TIMESTEPS)]
    sizes = [14+stds[t]*40 for t in range(N_TIMESTEPS)]
    ax_tw.scatter(TW_TH, TW_R, c=cols_tw, s=sizes, alpha=0.5, edgecolors='white', linewidth=0.15)
    ax_tw.scatter([TW_TH[step]], [TW_R[step]], c=get_time_color(step), s=100,
                  edgecolors=BLACK, linewidth=2.5, zorder=10)
    ax_tw.set_xticklabels([]); ax_tw.set_yticklabels([])
    ax_tw.set_title("Task 5: TimeWheel", fontweight='bold', color=BLACK, pad=4, fontsize=10)


def draw_histogram(step):
    ax_hist.clear(); ax_hist.set_facecolor(WHITE)
    hc = HIST[step]; ctr, cnt = hc["x"], hc["c"]
    clrs = [RED_500 if (BLO and BLO<=c<=BHI) else GRAY_400 for c in ctr]
    ax_hist.bar(ctr, cnt, width=0.07, color=clrs, edgecolor='none', alpha=0.85)
    if BLO: ax_hist.axvspan(BLO, BHI, color=RED_500, alpha=0.12)
    ax_hist.set_xlabel("ln(rho)"); ax_hist.set_ylabel("Count")
    ax_hist.set_title("Task 4: Drag to Brush", fontweight='bold', color=BLACK, pad=4, fontsize=10)
    ax_hist.tick_params(labelsize=6.5)


def draw_evolution(step):
    ax_evo.clear(); ax_evo.set_facecolor(WHITE)
    ts = np.arange(N_TIMESTEPS)

    # Subplot 1: sigma
    ax1 = ax_evo
    ax1.plot(ts, stds, color=RED_500, lw=1.5, label='Std sigma')
    ax1.axvline(step, color=BLUE_500, lw=1.5, alpha=0.4, ls='--')
    ax1.set_ylabel("sigma", color=RED_500); ax1.tick_params(axis='y', colors=RED_500, labelsize=6.5)

    # Subplot 2: mean on twin axis
    ax2 = ax1.twinx()
    ax2.plot(ts, means, color=BLUE_500, lw=1.5, label='Mean')
    ax2.set_ylabel("mean", color=BLUE_500); ax2.tick_params(axis='y', colors=BLUE_500, labelsize=6.5)

    ax1.set_xlabel("Time Step")
    ax1.set_title(f"Task 2: Evolution (sigma={stds[step]:.4f}, mean={means[step]:.3f})",
                  fontweight='bold', color=BLACK, pad=4, fontsize=10)
    ax1.tick_params(labelsize=6.5)


def draw_hist_tracking(step):
    ax_ht.clear(); ax_ht.set_facecolor(WHITE)
    for ts in [0,20,40,60,80,99]:
        hc = HIST[ts]; c = get_time_color(ts)
        lw = 2.5 if ts == step else 0.5; al = 1.0 if ts == step else 0.3
        ax_ht.plot(hc["x"], hc["c"], color=c, lw=lw, alpha=al, label=f"t={ts}" if ts in [0,99] else "")
    ax_ht.set_xlabel("ln(rho)"); ax_ht.set_ylabel("Count")
    ax_ht.set_title(f"Task 3: Histogram Tracking (bold=t={step})",
                    fontweight='bold', color=BLACK, pad=4, fontsize=10)
    ax_ht.legend(fontsize=5.5, loc='upper right', frameon=True, facecolor='white', edgecolor=GRAY_200)
    ax_ht.tick_params(labelsize=6.5)


def draw_all(step):
    draw_model(step)
    draw_particles(step)
    draw_timewheel(step)
    draw_histogram(step)
    draw_evolution(step)
    draw_hist_tracking(step)
    step_txt.set_text(f"t={step}"); step_txt.set_color(get_time_color(step))
    if BLO: status_txt.set_text(f"Brush: [{BLO:.2f},{BHI:.2f}]")
    else: status_txt.set_text("Drag in histogram")
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
    global CUR, PLAY
    if not PLAY: return
    CUR = (CUR+1)%N_TIMESTEPS; slider.set_val(CUR)
    draw_all(CUR)
    fig.canvas.flush_events()
    if PLAY:
        fig.canvas.manager.window.after(150, anim)

def on_brush(vmin, vmax):
    global BLO, BHI
    if abs(vmin-vmax) < 0.01: return
    BLO, BHI = min(vmin,vmax), max(vmin,vmax); draw_all(CUR)

def on_reset(event):
    global BLO, BHI; BLO, BHI = None, None; draw_all(CUR)

slider.on_changed(on_slider)
btn_play.on_clicked(on_play)
btn_rst.on_clicked(on_reset)
SpanSelector(ax_hist, on_brush, 'horizontal', props=dict(facecolor=RED_500, alpha=0.2))

draw_all(0)

print("="*60)
print("CONTROLS: Slider=time | Play=animate | Histogram drag=brush")
print("          3D particles=rotate/zoom | Reset=clear brush")
print("="*60)

plt.show()
