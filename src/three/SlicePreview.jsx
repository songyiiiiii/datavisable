// SlicePreview.jsx — 三相切片 3D 位置展示 (小窗口)
import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

function SlicePlanes3D({ sXY, sXZ, sYZ }) {
  const texXY = useMemo(() => new THREE.TextureLoader().load(sXY), [sXY]);
  const texXZ = useMemo(() => new THREE.TextureLoader().load(sXZ), [sXZ]);
  const texYZ = useMemo(() => new THREE.TextureLoader().load(sYZ), [sYZ]);

  const S = 128, mid = 64;

  return (
    <group>
      {/* XY 俯视 Z=64 */}
      <mesh position={[mid, mid, mid]} rotation={[0, 0, 0]}>
        <planeGeometry args={[S, S]} />
        <meshBasicMaterial map={texXY} transparent opacity={0.7} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {/* XZ 侧视 Y=64 */}
      <mesh position={[mid, mid, mid]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[S, S]} />
        <meshBasicMaterial map={texXZ} transparent opacity={0.7} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {/* YZ 正视 X=64 */}
      <mesh position={[mid, mid, mid]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[S, S]} />
        <meshBasicMaterial map={texYZ} transparent opacity={0.7} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {/* 边界框 */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(S, S, S)]} />
        <lineBasicMaterial color="#48BFE3" transparent opacity={0.3} />
      </lineSegments>
    </group>
  );
}

export default function SlicePreview({ sXY, sXZ, sYZ }) {
  return (
    <Canvas camera={{ position: [180, 150, 180], fov: 55, near: 1, far: 500 }}
      gl={{ antialias: true, alpha: true }} style={{ background: 'transparent' }}>
      <ambientLight intensity={0.5} />
      <SlicePlanes3D sXY={sXY} sXZ={sXZ} sYZ={sYZ} />
      <OrbitControls enableDamping dampingFactor={0.15} minDistance={80} maxDistance={300}
        target={[64, 64, 64]} enableZoom={false} />
    </Canvas>
  );
}
