// ============================================================================
// SlicePlanes.jsx — XYZ 三向正交切片平面 V2
// 直接从 Float32Array raw data 生成纹理，不依赖预构建嵌套数组
// ============================================================================
import React, { useMemo } from 'react';
import * as THREE from 'three';

/* ---- Canvas 2D → coolwarm 纹理 ---- */
function makeSliceTexture(data2D, N) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = N;
  const ctx = canvas.getContext('2d');
  const img = ctx.createImageData(N, N);
  const vmin = 7.5, vmax = 14.5;

  for (let i = 0; i < N * N; i++) {
    const v = data2D[i] ?? 9.5;
    const t = Math.max(0, Math.min(1, (v - vmin) / (vmax - vmin)));

    let r, g, b;
    if (t < 0.3) {
      const s = t / 0.3; r = 0.03 + 0.23 * s; g = 0.09 + 0.49 * s; b = 0.25 + 0.51 * s;
    } else if (t < 0.55) {
      const s = (t - 0.3) / 0.25; r = 0.26 + 0.41 * s; g = 0.58 - 0.05 * s; b = 0.76 + 0.04 * s;
    } else if (t < 0.8) {
      const s = (t - 0.55) / 0.25; r = 0.67 + 0.29 * s; g = 0.53 - 0.08 * s; b = 0.80 - 0.09 * s;
    } else {
      const s = (t - 0.8) / 0.2; r = 0.96 + 0.04 * s; g = 0.45 + 0.49 * s; b = 0.71 + 0.25 * s;
    }

    const idx = i * 4;
    img.data[idx] = Math.floor(r * 255);
    img.data[idx + 1] = Math.floor(g * 255);
    img.data[idx + 2] = Math.floor(b * 255);
    img.data[idx + 3] = 220;
  }

  ctx.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.needsUpdate = true;
  return tex;
}

/* ---- 从 flat Float32Array 提取 2D 切片 ---- */
function extractSlice(arr, N, axis, fixedIdx) {
  // arr: XYZ C-order (x fastest, then y, then z)
  // axis: 'z'=XY, 'y'=XZ, 'x'=YZ
  const out = new Float32Array(N * N);
  if (axis === 'z') {
    // XY slice: z fixed, iterate x,y
    for (let y = 0; y < N; y++)
      for (let x = 0; x < N; x++)
        out[y * N + x] = arr[fixedIdx * N * N + y * N + x];
  } else if (axis === 'y') {
    // XZ slice: y fixed
    for (let z = 0; z < N; z++)
      for (let x = 0; x < N; x++)
        out[z * N + x] = arr[z * N * N + fixedIdx * N + x];
  } else {
    // YZ slice: x fixed
    for (let z = 0; z < N; z++)
      for (let y = 0; y < N; y++)
        out[z * N + y] = arr[z * N * N + y * N + fixedIdx];
  }
  return out;
}

/* ================================================================
   SlicePlanes — 直接读 flat Float32Array，不依赖嵌套结构
   ================================================================ */
export default function SlicePlanes({
  rawData,        // Float32Array (flat, N³)
  size = 64,
  sliceX = 32, sliceY = 32, sliceZ = 32,
  opacity = 0.82,
}) {
  const textures = useMemo(() => {
    if (!rawData || rawData.length === 0) return null;

    const N = size;
    const zData = extractSlice(rawData, N, 'z', Math.min(sliceZ, N - 1));
    const yData = extractSlice(rawData, N, 'y', Math.min(sliceY, N - 1));
    const xData = extractSlice(rawData, N, 'x', Math.min(sliceX, N - 1));

    return {
      texXY: makeSliceTexture(zData, N),
      texXZ: makeSliceTexture(yData, N),
      texYZ: makeSliceTexture(xData, N),
    };
  }, [rawData, size, sliceX, sliceY, sliceZ]);

  if (!textures) return null;

  const N = size;
  const sx = Math.min(sliceX, N - 1);
  const sy = Math.min(sliceY, N - 1);
  const sz = Math.min(sliceZ, N - 1);

  return (
    <group>
      {/* XY 切片 (Z = sliceZ) */}
      <mesh position={[N / 2, N / 2, sz]}>
        <planeGeometry args={[N, N]} />
        <meshBasicMaterial map={textures.texXY} transparent opacity={opacity}
          side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <lineSegments position={[N / 2, N / 2, sz]}>
        <edgesGeometry args={[new THREE.PlaneGeometry(N, N)]} />
        <lineBasicMaterial color="white" transparent opacity={0.35} />
      </lineSegments>

      {/* XZ 切片 (Y = sliceY) */}
      <mesh position={[N / 2, sy, N / 2]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[N, N]} />
        <meshBasicMaterial map={textures.texXZ} transparent opacity={opacity}
          side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <lineSegments position={[N / 2, sy, N / 2]} rotation={[-Math.PI / 2, 0, 0]}>
        <edgesGeometry args={[new THREE.PlaneGeometry(N, N)]} />
        <lineBasicMaterial color="white" transparent opacity={0.35} />
      </lineSegments>

      {/* YZ 切片 (X = sliceX) */}
      <mesh position={[sx, N / 2, N / 2]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[N, N]} />
        <meshBasicMaterial map={textures.texYZ} transparent opacity={opacity}
          side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <lineSegments position={[sx, N / 2, N / 2]} rotation={[0, Math.PI / 2, 0]}>
        <edgesGeometry args={[new THREE.PlaneGeometry(N, N)]} />
        <lineBasicMaterial color="white" transparent opacity={0.35} />
      </lineSegments>
    </group>
  );
}
