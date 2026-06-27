"""
extract_network_graph.py — 从 Nyx 密度场提取宇宙网拓扑图
Hessian T-web → 节点连通分量 → 纤维连接 → 图结构 → JSON
输出: output/frontend_data/network_graphs.json
"""
import numpy as np
from scipy.ndimage import gaussian_filter, sobel, label
from collections import defaultdict
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

def hessian_eigenvalues(data_3d, sigma=1.5):
    """返回 (lam1, lam2, lam3) λ1≥λ2≥λ3"""
    s = gaussian_filter(data_3d.astype(np.float64), sigma=sigma)
    dx=sobel(s,axis=2)/2; dy=sobel(s,axis=1)/2; dz=sobel(s,axis=0)/2
    a=sobel(dx,axis=2)/2; d=sobel(dy,axis=1)/2; f=sobel(dz,axis=0)/2
    b=sobel(dx,axis=1)/2; c=sobel(dx,axis=0)/2; e=sobel(dy,axis=0)/2
    p=a+d+f; q=a*d+a*f+d*f-b*b-c*c-e*e; r=a*d*f-a*e*e-b*b*f+2*b*c*e-c*c*d
    p3=p/3; P=q-p*p3; Q=r-q*p3+2*p3**3
    neg=-P/3; sqrt_n=np.sqrt(np.maximum(neg,0))
    phi_arg=np.clip(3*Q/(np.maximum(2*P*sqrt_n,1e-30)),-1,1)
    phi=np.arccos(phi_arg)
    x=2*sqrt_n; x1=x*np.cos(phi/3); x2=x*np.cos((phi+2*np.pi)/3); x3=x*np.cos((phi+4*np.pi)/3)
    lam=np.stack([x1+p3,x2+p3,x3+p3],axis=-1); lam.sort(axis=-1)
    return lam[...,2],lam[...,1],lam[...,0]

def extract_graph(step, sigma=1.2, node_min_size=20):
    data = load_timestep(step)
    print(f"  t={step}: computing Hessian...")
    lam1, lam2, lam3 = hessian_eigenvalues(data, sigma=sigma)

    # T-web: node=3, filament=2
    web = np.zeros_like(lam1, dtype=np.uint8)
    web[lam1<=0] = 3
    web[(lam1>0)&(lam2<=0)] = 2
    n_node = (web==3).sum()
    print(f"    node voxels: {n_node} ({n_node/web.size*100:.1f}%)")

    # 节点连通分量
    node_mask = web == 3
    struct = np.ones((3,3,3), dtype=bool)
    node_labels, n_components = label(node_mask, structure=struct)
    print(f"    node components: {n_components}")

    # 提取每个分量的质心和体积
    nodes = []
    for cid in range(1, n_components+1):
        mask = node_labels == cid
        volume = mask.sum()
        if volume < node_min_size: continue
        coords = np.argwhere(mask)  # (z,y,x)
        centroid = coords.mean(axis=0).astype(float)
        # 该分量平均密度
        avg_rho = data[mask].mean()
        nodes.append({
            'id': cid,
            'x': float(centroid[2]), 'y': float(centroid[1]), 'z': float(centroid[0]),
            'volume': int(volume), 'rho': float(avg_rho),
        })
    print(f"    filtered nodes (>={node_min_size} vox): {len(nodes)}")

    # 取体积最大的 top N 节点
    nodes.sort(key=lambda n: n['volume'], reverse=True)
    nodes = nodes[:200]  # 增加到200个节点
    print(f"    kept top {len(nodes)} nodes by volume")

    filament_mask = web == 2
    edges = []
    for i, a in enumerate(nodes):
        connections = []
        for j, b in enumerate(nodes):
            if j <= i: continue
            ca = np.array([a['z'],a['y'],a['x']]); cb = np.array([b['z'],b['y'],b['x']])
            dist = np.linalg.norm(cb - ca)
            if dist > 90: continue
            n_steps = max(2, int(dist))
            points = np.linspace(ca, cb, n_steps).astype(int)
            points = np.clip(points, 0, 127)
            frac = filament_mask[points[:,0],points[:,1],points[:,2]].mean()
            if frac > 0.25: connections.append((b['id'], dist, frac))
        # 每个节点保留 top 5 最强连接
        connections.sort(key=lambda x: -x[2])
        for b_id, dist, frac in connections[:6]:  # 每节点最多6条边
            edges.append({'source': a['id'], 'target': b_id, 'distance': float(dist), 'filament_frac': float(frac)})

    print(f"    edges: {len(edges)}")
    return {'step': step, 'nodes': nodes, 'edges': edges}

if __name__ == "__main__":
    out_dir = os.path.join(OUTPUT_DIR, "frontend_data")
    os.makedirs(out_dir, exist_ok=True)

    step = 73
    graph = extract_graph(step, sigma=1.2)
    path = os.path.join(out_dir, f"network_t{step:04d}.json")
    with open(path, 'w') as f: json.dump(graph, f, indent=2)
    print(f"\nExported -> {path}")
    print(f"  Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
