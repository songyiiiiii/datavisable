// ============================================================================
// ThreeScene.jsx V3 — PNG 纹理驱动 3D 视图
// 主视图: GPU 体渲染 PNG 平面 + 三向切片平面
// 配色: 科学红白蓝 divergent
// ============================================================================
import React, { useState, useMemo, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

/* ---- 远程 PNG → Texture ---- */
function useTexture(url) {
  const [tex, setTex] = useState(null);
  useEffect(() => {
    if (!url) return;
    const loader = new THREE.TextureLoader();
    loader.load(url,
      t => { t.colorSpace = THREE.SRGBColorSpace; t.needsUpdate = true; setTex(t); },
      undefined,
      () => console.warn('Texture load failed:', url)
    );
    return () => { if (tex) tex.dispose(); };
  }, [url]);
  return tex;
}

/* ---- 当前帧体积渲染纹理平面 ---- */
function VolumePlane({ timestep, size = 128 }) {
  const url = `/output/task1/layer_composite_t${String(timestep).padStart(4, '0')}.png`;
  const tex = useTexture(url);
  if (!tex) return null;
  return (
    <mesh position={[size / 2, size / 2, size / 2]} rotation={[0, 0, 0]}>
      <planeGeometry args={[size, size]} />
      <meshBasicMaterial map={tex} transparent opacity={0.85} side={THREE.DoubleSide} />
    </mesh>
  );
}

/* ---- 单张切片平面 ---- */
function SlicePlane({ plane, position, rotation, timestep, size = 128 }) {
  // plane: 'xy' | 'xz' | 'yz'
  const base = `/output/slices/${plane}/t${String(timestep).padStart(4, '0')}.png`;
  const url = `/output/slices/${plane}/t${String(timestep).padStart(4, '0')}.png`;
  const tex = useTexture(url);

  // 回退到 GPU render
  const fallback = `/output/task1/layer_composite_t${String(timestep).padStart(4, '0')}.png`;
  const fbTex = useTexture(fallback);

  const t = tex || fbTex;
  if (!t) return null;

  return (
    <group>
      <mesh position={position} rotation={rotation}>
        <planeGeometry args={[size, size]} />
        <meshBasicMaterial map={t} transparent opacity={0.82} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <lineSegments position={position} rotation={rotation}>
        <edgesGeometry args={[new THREE.PlaneGeometry(size, size)]} />
        <lineBasicMaterial color="white" transparent opacity={0.3} />
      </lineSegments>
    </group>
  );
}

/* ---- 粒子云 (回退) ---- */
function FallbackCloud({ voxelSample }) {
  const { xs, ys, zs, rhos } = voxelSample || {};
  if (!xs) return null;
  const p = new Float32Array(xs.length * 3);
  const c = new Float32Array(xs.length * 3);
  for (let i = 0; i < xs.length; i++) {
    p[i*3]=xs[i]; p[i*3+1]=ys[i]; p[i*3+2]=zs[i];
    const t = Math.max(0,Math.min(1,(rhos[i]-7.5)/7.0));
    let r,g,b;
    // 红白蓝
    if(t<0.5){const s=t*2; r=s; g=s; b=1;}
    else{const s=(t-0.5)*2; r=1; g=1-s; b=1-s;}
    c[i*3]=r; c[i*3+1]=g; c[i*3+2]=b;
  }
  const gloTex = (()=>{
    const cv=document.createElement('canvas');cv.width=cv.height=64;
    const ct=cv.getContext('2d');const g=ct.createRadialGradient(32,32,0,32,32,32);
    g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(0.06,'rgba(255,255,255,0.9)');
    g.addColorStop(0.25,'rgba(255,255,255,0.4)');g.addColorStop(0.55,'rgba(255,255,255,0.06)');
    g.addColorStop(1,'rgba(255,255,255,0)');ct.fillStyle=g;ct.fillRect(0,0,64,64);
    return new THREE.CanvasTexture(cv);
  })();
  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" array={p} count={xs.length} itemSize={3}/>
        <bufferAttribute attach="attributes-color" array={c} count={xs.length} itemSize={3}/>
      </bufferGeometry>
      <pointsMaterial size={1.5} map={gloTex} vertexColors transparent opacity={0.5}
        depthWrite={false} blending={THREE.AdditiveBlending} sizeAttenuation/>
    </points>
  );
}

/* ---- 边界框 ---- */
function BBox({ size = 128 }) {
  return (
    <lineSegments>
      <edgesGeometry args={[new THREE.BoxGeometry(size, size, size)]} />
      <lineBasicMaterial color="#475569" transparent opacity={0.25} />
    </lineSegments>
  );
}

/* ================================================================
   ThreeScene 主入口
   ================================================================ */
export default function ThreeScene({ voxelSample, mode = 'volume', timeStep = 73 }) {
  const size = 128;

  return (
    <div className="relative w-full h-full">
      <Canvas
        id="threejs-canvas"
        camera={{ position: [180, 150, 180], fov: 40, near: 1, far: 500 }}
        gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.4} />
        <BBox size={size} />
        <axesHelper args={[80]} />

        {/* 粒子云始终显示做空间参考 */}
        {voxelSample && (
          <FallbackCloud voxelSample={voxelSample} />
        )}

        {/* 体渲染平面 (volume 模式) */}
        {mode === 'volume' && (
          <VolumePlane timestep={timeStep} size={size} />
        )}

        {/* 三向切片 (slices 模式) */}
        {mode === 'slices' && (
          <>
            <SlicePlane plane="xy" position={[size/2, size/2, 64]} rotation={[0,0,0]} timestep={timeStep} size={size} />
            <SlicePlane plane="xz" position={[size/2, 64, size/2]} rotation={[-Math.PI/2,0,0]} timestep={timeStep} size={size} />
            <SlicePlane plane="yz" position={[64, size/2, size/2]} rotation={[0,Math.PI/2,0]} timestep={timeStep} size={size} />
          </>
        )}

        <OrbitControls enableDamping dampingFactor={0.08} minDistance={60} maxDistance={400}
          target={[size/2, size/2, size/2]} />
      </Canvas>

      {/* XYZ 轴图例 */}
      <div className="absolute top-3 right-3 flex flex-col gap-1 z-20">
        {[{a:'X',c:'#EF4444'},{a:'Y',c:'#3B82F6'},{a:'Z',c:'#22C55E'}].map(({a,c})=>(
          <div key={a} className="flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-sm flex items-center justify-center text-[9px] font-bold text-white"
              style={{backgroundColor:c+'25',border:`1px solid ${c}50`}}>{a}</span>
            <span className="text-[10px] text-gray-500 font-mono">0 - 127</span>
          </div>
        ))}
      </div>
    </div>
  );
}
