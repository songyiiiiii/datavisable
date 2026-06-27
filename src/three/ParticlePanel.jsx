// ============================================================================
// ParticlePanel.jsx — 纯联动聚焦版 (无刷选展示全量，有刷选剔除非目标)
// ============================================================================
import React, { useMemo, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// 1. 物理结构密度区间定义 (默认全量展示时的颜色)
const STRUCTURE_RANGES = {
  void:     { lo: 0,    hi: 8.5,  name: '空洞', color: '#48BFE3' },
  sheet:    { lo: 8.5,  hi: 9.8,  name: '薄片', color: '#62B6A7' },
  filament: { lo: 9.8,  hi: 11.2, name: '纤维', color: '#E8896E' },
  node:     { lo: 11.2, hi: 20,   name: '节点', color: '#F25F5C' }
};

// 2. 生成发光圆形纹理
function createParticleTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(0.2, 'rgba(255,255,255,0.9)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(canvas);
}

// 3. 粒子系统核心组件
function ParticleCloud({ voxelSample, brushRange }) {
  const pointsRef = useRef();
  const texture = useMemo(() => createParticleTexture(), []);

  // 数据预处理与映射
  const processedData = useMemo(() => {
    if (!voxelSample) return { positions: [], colors: [], count: 0 };
    const { xs, ys, zs, rhos } = voxelSample;

    // 构造数据结构，包含位置和密度，供后续筛选
    const sourceData = [];
    for(let i=0; i<xs.length; i++) {
      sourceData.push({ x: xs[i], y: ys[i], z: zs[i], rho: rhos[i] });
    }

    // 倍增粒子的数量，营造出高度浓密的星云效果
    const sampleMul = 16; 
    let totalCount = sourceData.length * sampleMul;

    const positions = new Float32Array(totalCount * 3);
    const colors = new Float32Array(totalCount * 3);

    // 【核心逻辑变更】：判断是否需要筛选
    const isFiltering = brushRange !== null && brushRange !== undefined;
    let lo = 0, hi = 0;
    if (isFiltering) {
      [lo, hi] = brushRange;
    }

    let idx = 0;
    for (let i = 0; i < sourceData.length; i++) {
      const baseX = sourceData[i].x - 64; // 居中对齐，保证自转不发生公转
      const baseY = sourceData[i].y - 64;
      const baseZ = sourceData[i].z - 64;
      const baseRho = sourceData[i].rho;

      // 如果有刷选，判断当前粒子是否在范围内
      if (isFiltering && (baseRho < lo || baseRho > hi)) {
        continue; // 越过此粒子，不渲染它
      }

      // 确定颜色 (无刷选时，根据物理结构自动配色；有刷选时，全用高亮玫红)
      let baseColor = new THREE.Color('#F25F5C'); // 默认联动脉冲色
      if (!isFiltering) {
        for (const [key, range] of Object.entries(STRUCTURE_RANGES)) {
          if (baseRho >= range.lo && baseRho < range.hi) {
            baseColor = new THREE.Color(range.color);
            break;
          }
        }
      }

      // 倍增采样渲染
      for (let j = 0; j < sampleMul; j++) {
        const spread = 0.6; 
        positions[idx * 3] = baseX + (Math.random() - 0.5) * spread;
        positions[idx * 3 + 1] = baseY + (Math.random() - 0.5) * spread;
        positions[idx * 3 + 2] = baseZ + (Math.random() - 0.5) * spread;

        const bright = 0.7 + Math.random() * 0.3;
        colors[idx * 3] = baseColor.r * bright;
        colors[idx * 3 + 1] = baseColor.g * bright;
        colors[idx * 3 + 2] = baseColor.b * bright;
        idx++;
      }
    }
    
    // 更新实际渲染数量，防止出现数组空缺导致的画面闪烁
    totalCount = idx; 

    return { positions, colors, count: totalCount };
  }, [voxelSample, brushRange]);

  // 更新几何体数据
  useEffect(() => {
    if (!pointsRef.current || !processedData) return;
    const geometry = pointsRef.current.geometry;
    // 注意：必须用 setAttribute 才能在数量发生动态变化时正确工作
    geometry.setAttribute('position', new THREE.BufferAttribute(processedData.positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(processedData.colors, 3));
    geometry.setDrawRange(0, processedData.count);
  }, [processedData]);

  // 原地自转动画
  useFrame(() => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += 0.002;
    }
  });

  if (!voxelSample) return null;

  return (
    <points ref={pointsRef} position={[0, 0, 0]}>
      <bufferGeometry attach="geometry">
        <bufferAttribute attach="attributes-position" count={processedData.count} array={processedData.positions} itemSize={3} />
        <bufferAttribute attach="attributes-color" count={processedData.count} array={processedData.colors} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial 
        size={1.4}
        map={texture}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        transparent={true}
        opacity={0.85}
        vertexColors={true}
        sizeAttenuation={true}
      />
    </points>
  );
}

// 4. 主面板导出
export default function ParticlePanel({ voxelSample, brushRange }) {
  if (!voxelSample) return null;

  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 0, 140], fov: 35 }}>
        <ambientLight intensity={0.6} />
        <ParticleCloud voxelSample={voxelSample} brushRange={brushRange} />
        <OrbitControls enableDamping dampingFactor={0.05} minDistance={40} maxDistance={300} target={[0, 0, 0]} />
      </Canvas>
    </div>
  );
}