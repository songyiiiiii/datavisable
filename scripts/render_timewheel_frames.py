"""
render_timewheel_frames.py — Plotly 版, 完全复刻 app.py fig_timewheel
新配色, 黑底 #09080D, 输出 100 帧 PNG (必须先装 kaleido: pip install kaleido)
"""
import numpy as np
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep, load_all_timesteps

OUT = os.path.join(OUTPUT_DIR, "timewheel_frames")
os.makedirs(OUT, exist_ok=True)

print("Loading 100 timesteps...")
ALL = load_all_timesteps(verbose=True)

_TW_RAW = np.zeros((N_TIMESTEPS, 10))
for t in range(N_TIMESTEPS):
    d = ALL[t].ravel()
    _TW_RAW[t] = [
        (d<8.5).sum()/d.size*100, (d>12.0).sum()/d.size*100,
        np.mean((d-d.mean())**4)/d.std()**4-3, np.mean((d-d.mean())**3)/d.std()**3,
        np.percentile(d,75)-np.percentile(d,25), d.std(), d.mean(), d.min(), d.max(),
        np.percentile(d,99)-np.percentile(d,1),
    ]
vmin = _TW_RAW.min(axis=0); vrng = _TW_RAW.max(axis=0)-vmin; vrng[vrng==0]=1
TW_N = (_TW_RAW - vmin) / vrng * 8 + 1

METRICS = ["Void%","Peak%","Kurt","Skew","IQR","Std","Mean","Min","Max","Spread"]
N_M = len(METRICS)

def color_fn(t):
    f = t/99
    if f<0.25: s=f/0.25; r=0.05+0.52*s; g=0.15+1.60*s; b=0.35+1.32*s
    elif f<0.5: s=(f-0.25)/0.25; r=0.57+0.45*s; g=1.75-2.0*s; b=1.67-1.08*s
    elif f<0.75: s=(f-0.5)/0.25; r=1.02-0.52*s; g=-0.25+0.70*s; b=0.59-0.14*s
    else: s=(f-0.75)/0.25; r=0.50+2.0*s; g=0.45+1.60*s; b=0.45-0.60*s
    return f'rgb({int(max(0,min(1,r))*255)},{int(max(0,min(1,g))*255)},{int(max(0,min(1,b))*255)})'

def render_one(step):
    fig = go.Figure()

    for i, (name, _) in enumerate([(m,i) for i,m in enumerate(METRICS)]):
        angle = 2*np.pi*i/N_M
        fig.add_trace(go.Scatter(x=[0,10*np.cos(angle)], y=[0,10*np.sin(angle)],
            mode='lines', line=dict(color='#444466',width=1.2),
            hoverinfo='skip', showlegend=False))
        fig.add_trace(go.Scatter(x=[11.5*np.cos(angle)], y=[11.5*np.sin(angle)],
            mode='text', text=[name], textfont=dict(color='#C5C3D8',size=10,family='Arial'),
            hoverinfo='skip', showlegend=False))
        for tv in [2,4,6,8]:
            fig.add_trace(go.Scatter(
                x=[(tv-0.05)*np.cos(angle+np.pi/2),(tv+0.05)*np.cos(angle+np.pi/2)],
                y=[(tv-0.05)*np.sin(angle+np.pi/2),(tv+0.05)*np.sin(angle+np.pi/2)],
                mode='lines', line=dict(color='#333355',width=0.4),
                hoverinfo='skip', showlegend=False))

    # 100 条纤维束
    for t in range(N_TIMESTEPS):
        color = color_fn(t)
        alpha = 0.28 if t!=step else 1.0
        lw = 1.5 if t!=step else 3.5
        px, py = [], []
        for i in range(N_M):
            angle = 2*np.pi*i/N_M; r = TW_N[t,i]
            px.append(r*np.cos(angle)); py.append(r*np.sin(angle))
        px.append(px[0]); py.append(py[0])
        fig.add_trace(go.Scatter(x=px, y=py, mode='lines',
            line=dict(color=color,width=lw), opacity=alpha,
            hoverinfo='skip', showlegend=False))

    # 十边形框
    fx, fy = [], []
    for i in range(N_M+1):
        a = 2*np.pi*(i%N_M)/N_M; fx.append(10*np.cos(a)); fy.append(10*np.sin(a))
    fig.add_trace(go.Scatter(x=fx, y=fy, mode='lines',
        line=dict(color='#555577',width=0.7,dash='dot'),
        hoverinfo='skip', showlegend=False))

    # 中心时间轴
    fig.add_trace(go.Scatter(x=[-8,8], y=[0,0], mode='lines',
        line=dict(color='#6B6880',width=2), hoverinfo='skip', showlegend=False))
    for ts in [0,25,50,75,99]:
        tx = -7+(ts/99)*14
        fig.add_trace(go.Scatter(x=[tx], y=[0], mode='markers+text',
            marker=dict(size=3,color='#6B6880'),
            text=[f't={ts}'], textposition='top center',
            textfont=dict(size=7,color='#6B6880'),
            hoverinfo='skip', showlegend=False))
    cx = -7+(step/99)*14
    fig.add_trace(go.Scatter(x=[cx], y=[0], mode='markers',
        marker=dict(size=10,color=color_fn(step),
        line=dict(color='#C5C3D8',width=1.5)),
        hoverinfo='skip', showlegend=False))

    fig.update_layout(
        xaxis=dict(visible=False,range=[-13,13]),
        yaxis=dict(visible=False,range=[-13,13],scaleanchor='x'),
        paper_bgcolor='#09080D', plot_bgcolor='#09080D',
        margin=dict(l=10,r=10,t=35,b=10),
        title=dict(text=f'Statistical Signature — t={step:03d}',font=dict(color='#C5C3D8',size=12)),
        width=500, height=500,
    )
    fig.write_image(os.path.join(OUT,f"tw_{step:04d}.png"), scale=2)
    return True

if __name__ == "__main__":
    from tqdm import tqdm
    for s in tqdm(range(N_TIMESTEPS)): render_one(s)
    print(f"Done -> {OUT}/")
