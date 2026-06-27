"""批量提取 100 步网络图"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS
from scripts.extract_network_graph import extract_graph
from tqdm import tqdm

out = os.path.join(OUTPUT_DIR, "frontend_data")
os.makedirs(out, exist_ok=True)

for step in tqdm(range(N_TIMESTEPS), desc="Extracting networks"):
    graph = extract_graph(step, sigma=1.2, node_min_size=20)
    path = os.path.join(out, f"network_t{step:04d}.json")
    import json
    with open(path, 'w') as f: json.dump(graph, f)
print(f"Done -> {out}/")
