# -*- coding: utf-8 -*-
"""Generate ALL table images from all report/*.md files."""
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, r'e:\数据可视化')
from config import *

OUT = os.path.join(OUTPUT_DIR, "report_tables")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({'font.size': 10, 'text.color': GRAY_700,
                     'figure.facecolor': WHITE, 'axes.facecolor': WHITE})

def tab(headers, rows, filename, title="", hc=None):
    """Render a clean table as PNG. hc=highlight column index for red/blue text."""
    nr, nc = len(rows)+1, len(headers)
    fig, ax = plt.subplots(figsize=(max(nc*2.0+1, 8), nr*0.42+1.0))
    fig.patch.set_facecolor(WHITE); ax.set_facecolor(WHITE); ax.axis('off')
    if title: ax.set_title(title, fontsize=12, fontweight='bold', color=BLACK, pad=10)
    tbl = ax.table(cellText=rows, colLabels=headers, cellLoc='center', loc='center', edges='horizontal')
    tbl.auto_set_font_size(False); tbl.set_fontsize(8.5); tbl.scale(1, 1.45)
    for (r,c), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRAY_200); cell.set_linewidth(0.5)
        if r == 0: cell.set_facecolor(GRAY_100); cell.set_text_props(weight='bold', color=BLACK, fontsize=9)
        else: cell.set_facecolor(WHITE); cell.set_text_props(color=GRAY_700)
        if hc is not None and c == hc and r > 0:
            txt = cell.get_text().get_text()
            cell.set_text_props(weight='bold')
            if txt.startswith('+') or '↑' in txt or 'growth' in txt.lower(): cell.get_text().set_color(RED_500)
            elif txt.startswith('-') or '↓' in txt: cell.get_text().set_color(BLUE_500)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), facecolor=WHITE, dpi=200, bbox_inches='tight')
    plt.close(fig)

# ========================================================================
# data_description.md tables
# ========================================================================
tab(["Property","Value"],
    [["File count","100 (0000.dat - 0099.dat)"],["Single file size","8,388,608 bytes (8 MiB)"],
     ["Total data volume","~800 MiB"],["Naming","%04d.dat (4-digit zero-padded)"]],
    "table_file_org.png","Nyx Dataset — File Organization")

tab(["Property","Value"],
    [["Data type","float32 (IEEE 754 single precision)"],["Byte order","Little-endian"],
     ["Physical quantity","Gas density (natural log scale, ln rho)"],
     ["Value range","~7.75 - 14.45 (~3 orders of magnitude linear)"]],
    "table_binary_encoding.png","Nyx Dataset — Binary Encoding")

tab(["Item","Specification"],
    [["OS","Windows 11 Home China 10.0.26100"],["CPU","Intel Core i7 (13th Gen)"],
     ["GPU","NVIDIA GeForce RTX 4060 Laptop (8GB VRAM), driver 560.94"],
     ["Python","3.11"],["NumPy","1.26"],["PyVista","0.48.4"],["VTK","9.6.2"],
     ["Matplotlib","3.8"],["Plotly","5.24"],["Dash","2.18"],["SciPy","1.11"]],
    "table_platform.png","Processing Platform Specification")

tab(["Metric","t=0","t=25","t=50","t=75","t=99"],
    [["Min","7.984","7.916","7.860","7.806","7.753"],
     ["Max","13.843","14.051","14.327","14.354","14.449"],
     ["Mean","9.485","9.437","9.395","9.356","9.319"],
     ["Std","0.432","0.453","0.469","0.485","0.498"],
     ["Median","9.450","9.399","9.355","9.313","9.275"],
     ["P1","8.628","8.543","8.473","8.407","8.346"],
     ["P99","10.725","10.740","10.751","10.755","10.760"]],
    "table_rep_stats.png","Representative Time Step — Density Statistics")

tab(["Metric","t=0 -> t=99","Change"],
    [["Std dev (sigma)","0.432 -> 0.498","+15.4%"],
     ["IQR","0.535 -> 0.625","+16.7%"],
     ["P99-P01 spread","2.098 -> 2.414","+15.1%"],
     ["Min (voids deepen)","7.984 -> 7.753","-0.231"],
     ["Max (peaks grow)","13.843 -> 14.449","+0.606"],
     ["Void frac (ln<8.5)","0.31% -> 2.99%","~10x growth"]],
    "table_evolution.png","Density Evolution Trends (t=0 to t=99)", hc=2)

tab(["Category","ln(rho) Range","Color","Physical Meaning"],
    [["Deep Void","7.5 - 7.8","#071840","Extreme low density"],
     ["Void","7.8 - 8.2","#1A4A7A","Cosmic void body"],
     ["Near-Void","8.2 - 8.6","#2166AC","Void boundary transition"],
     ["Sub-Filament","8.6 - 9.2","#4393C3","Filament-void interface"],
     ["Cool Filament","9.2 - 9.8","#8899AA","Filament web backbone"],
     ["Warm Filament","9.8 - 10.5","#AABBAA","Filament-cluster transition"],
     ["Proto-Cluster","10.5 - 11.2","#F4A582","Gravitational collapse zone"],
     ["Cluster Halo","11.2 - 12.0","#D6604D","Dark matter halo periphery"],
     ["Cluster Core","12.0 - 13.0","#B2182B","Dense gas node"],
     ["Extreme Peak","13.0 - 15.0","#6B0015","Most compact structure"]],
    "table_classification.png","Unified Density Classification System (10 Categories)")

# ========================================================================
# task1_report.md tables
# ========================================================================
tab(["Method","Advantage","Disadvantage","Verdict"],
    [["VTK GPU Ray Casting","True volume rendering, composite blending","Offscreen unstable; interactive needs GPU context","Backup"],
     ["Plotly WebGL (go.Volume)","Browser-native, cross-platform","Rendered nothing visible on this machine","Unusable"],
     ["PyVista Multi-Layer Isosurface","Verified mesh rendering, Blinn-Phong, per-layer control","Isosurface not volume integral","SELECTED"]],
    "table_t1_methods.png","Task 1 — Technical Approach Comparison")

tab(["Level","ln(rho)","Color (R,G,B)","Opacity","Structure","Lighting"],
    [["1","8.0","(0.13,0.40,0.67) Deep Blue","0.08","Deep voids","Standard"],
     ["2","8.6","(0.35,0.58,0.80) Mid Blue","0.12","Shallow voids","Standard"],
     ["3","9.1","(0.60,0.75,0.90) Light Blue","0.18","Void boundary","Standard"],
     ["4","9.7","(0.90,0.90,0.90) Light Gray","0.25","Filament web","Standard"],
     ["5","10.3","(0.95,0.78,0.68) Warm Pink","0.32","Warm filament","Standard"],
     ["6","10.9","(0.88,0.50,0.38) Orange-Red","0.45","Cluster halo","EMISSIVE"],
     ["7","11.8","(0.75,0.25,0.22) Red","0.55","Cluster core","EMISSIVE"],
     ["8","14.0","(0.60,0.10,0.15) Deep Red","0.70","Extreme peak","EMISSIVE"]],
    "table_t1_isosurface.png","Task 1 — Isosurface Layer Definition & Transfer Function")

tab(["Parameter","Standard (L1-5)","Emissive (L6-8)","Meaning"],
    [["k_a (ambient)","0.18","1.00","Base illumination"],
     ["k_d (diffuse)","0.72","0.25","Directional light component"],
     ["k_s (specular)","0.35","0.35","Surface highlight"],
     ["alpha (shininess)","14","14","Highlight concentration"]],
    "table_t1_lighting.png","Task 1 — Blinn-Phong Lighting Parameters")

tab(["Time Step","Visual Feature","Physical Meaning"],
    [["t=0-15","Large blue regions (void fraction < 1%)","Uniform distribution, near-Gaussian"],
     ["t=25-40","Blue expands, red points emerge","Gravitational instability onset"],
     ["t=50-70","Gray filament web clearly visible","Cosmic web topology established"],
     ["t=75-99","Red clusters contract & brighten, voids deepen","Nonlinear collapse, bipolarization accelerates"]],
    "table_t1_evolution.png","Task 1 — Visual Evolution Timeline")

# ========================================================================
# task2_report.md tables
# ========================================================================
tab(["Metric","Definition","Physical Meaning"],
    [["mu (mean)","1/N sum(rho_i)","Global average; decline = void expansion"],
     ["sigma (std)","sqrt(1/N sum(rho_i-mu)^2)","Dispersion; rise = clumpification"],
     ["IQR","P75 - P25","Robust dispersion, excludes extremes"],
     ["gamma_1 (skewness)","mu_3 / sigma^3","Asymmetry; positive = right tail develops"],
     ["gamma_2 (exc. kurtosis)","mu_4/sigma^4 - 3","Tail weight; >0 = heavy tails"],
     ["P1, P99","1st, 99th percentiles","Extreme value tracking"],
     ["P99-P01 spread","--","Bipolarization magnitude"]],
    "table_t2_metrics.png","Task 2 — Statistical Metric System")

tab(["Figure","Type","Analysis Function"],
    [["Fig 2a","4-panel dashboard","Global evolution overview: tendency, dispersion, shape, extremes"],
     ["Fig 2b","Violin sequence","Distribution morphology tracking across epochs"],
     ["Fig 2c","Histogram overlay","Direct initial-final comparison: t=0 vs t=99"],
     ["Fig 2d","Hexbin joint dist.","Single voxel fate: which voxels gained/lost density?"],
     ["Fig 2e","6-metric panel","Multi-dimensional clumpification quantification"]],
    "table_t2_figures.png","Task 2 — Five-Figure Analysis Framework")

# ========================================================================
# task3_report.md tables
# ========================================================================
tab(["Figure","Type","Analysis Function","Technique"],
    [["Fig 3a","Evolution heatmap","100-step x 128-bin density overview","pcolormesh + log color"],
     ["Fig 3b","Peak & width","Mode + FWHM tracking","Mode argmax + half-max threshold"],
     ["Fig 3c","Void/peak fraction","Extreme region volume evolution","Absolute density thresholds"],
     ["Fig 3d","Temporal derivative","Distribution change rate dH/dt","Central difference"],
     ["Fig 3e","Ridge plot","11-step histogram overlay","Offset fill-between curves"]],
    "table_t3_figures.png","Task 3 — Five-Figure Analysis Framework")

tab(["Phase","Time Range","Heatmap Feature","Derivative Feature","Physical Process"],
    [["I: Linear growth","t=0-30","Narrow peak, high center","Uniform derivative","Initial gravitational instability"],
     ["II: Accelerated","t=30-70","Peak broadening, tail growth","Positive at ends, negative at mid","Nonlinear collapse onset"],
     ["III: Asymptotic","t=70-99","Broad peak, long tails","Decelerating derivative","Quasi-equilibrium approach"]],
    "table_t3_phases.png","Task 3 — Three-Phase Distribution Evolution Model")

print(f"\nDone! {sum(1 for _ in open(__file__) if 'tab(' in _)} tables saved to {OUT}/")
