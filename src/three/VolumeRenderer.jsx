// ============================================================================
// VolumeRenderer.jsx — 真正的 Ray-Marching 体渲染
// Data3DTexture + 自定义 GLSL shader + 传递函数 + 三向切片支持
// ============================================================================
import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/* ================================================================
   Vertex Shader
   ================================================================ */
const VOL_VERTEX = /* glsl */ `
  varying vec3 vOrigin;
  varying vec3 vDirection;

  void main() {
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vOrigin = cameraPosition;
    vDirection = worldPos.xyz - cameraPosition;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

/* ================================================================
   Fragment Shader — Ray-Marching
   ================================================================ */
const VOL_FRAGMENT = /* glsl */ `
  varying vec3 vOrigin;
  varying vec3 vDirection;
  uniform sampler3D uVolume;
  uniform vec3 uVolumeSize;
  uniform float uStepSize;
  uniform float uAlphaScale;
  uniform float uDensityMin;
  uniform float uDensityMax;

  // 传递函数: density (0..1) → vec4(r,g,b,a)
  vec4 tf(float t) {
    t = clamp(t, 0.0, 1.0);

    // 5-stop colormap
    vec3 col = mix(vec3(0.03, 0.09, 0.25), vec3(0.26, 0.58, 0.76), smoothstep(0.0, 0.3, t));
    col = mix(col, vec3(0.67, 0.53, 0.80), smoothstep(0.3, 0.55, t));
    col = mix(col, vec3(0.96, 0.45, 0.71), smoothstep(0.55, 0.80, t));
    col = mix(col, vec3(1.0, 0.94, 0.96), smoothstep(0.80, 1.0, t));

    // 透明度
    float a = smoothstep(0.0, 0.08, t) * 0.50
            + smoothstep(0.15, 0.40, t) * 0.30
            + smoothstep(0.55, 0.85, t) * 0.40;
    a = clamp(a * uAlphaScale, 0.0, 1.0);

    return vec4(col, a);
  }

  void main() {
    vec3 rayOrigin = vOrigin;
    vec3 rayDir = normalize(vDirection);

    // 与 [0, uVolumeSize] 包围盒求交
    vec3 t0 = (-rayOrigin) / (rayDir + 0.0001);
    vec3 t1 = (uVolumeSize - rayOrigin) / (rayDir + 0.0001);
    vec3 tmin3 = min(t0, t1);
    vec3 tmax3 = max(t0, t1);
    float tNear = max(max(tmin3.x, tmin3.y), tmin3.z);
    float tFar  = min(min(tmax3.x, tmax3.y), tmax3.z);

    if (tNear >= tFar || tFar < 0.0) discard;
    tNear = max(tNear, 0.0);

    // Ray-marching 前向后合成
    vec4 acc = vec4(0.0);
    float t = tNear + uStepSize * 0.3;
    float stepSize = uStepSize;

    for (int i = 0; i < 384; i++) {
      if (t >= tFar || acc.a >= 0.97) break;

      vec3 pos = rayOrigin + rayDir * t;
      if (any(lessThan(pos, vec3(0.0))) || any(greaterThan(pos, uVolumeSize))) break;

      // 归一化纹理坐标 (0..1)
      vec3 texCoord = pos / uVolumeSize;

      // 采样 3D 纹理
      float density = texture(uVolume, texCoord).r;
      float norm = (density - uDensityMin) / (uDensityMax - uDensityMin + 0.001);

      if (norm > 0.01) {
        vec4 sample = tf(norm);
        sample.a *= stepSize * 0.28;

        // 前向后 alpha 合成
        acc.rgb += (1.0 - acc.a) * sample.rgb * sample.a;
        acc.a   += (1.0 - acc.a) * sample.a;
      }

      t += stepSize;
    }

    if (acc.a < 0.01) discard;
    gl_FragColor = acc;
  }
`;

/* ================================================================
   VolumeCube — 体渲染核心
   ================================================================ */
function VolumeCube({ rawField, fieldSize }) {
  const meshRef = useRef();

  // 创建 Data3DTexture
  const dataTex = useMemo(() => {
    if (!rawField) return null;
    // rawField: Float32Array, (X,Y,Z) C-order layout
    // Data3DTexture expects: width=X, height=Y, depth=Z
    const tex = new THREE.Data3DTexture(
      rawField,
      fieldSize, fieldSize, fieldSize
    );
    tex.format = THREE.RedFormat;
    tex.type = THREE.FloatType;
    tex.minFilter = THREE.LinearFilter;
    tex.magFilter = THREE.LinearFilter;
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.wrapR = THREE.ClampToEdgeWrapping;
    tex.unpackAlignment = 1;
    tex.needsUpdate = true;
    return tex;
  }, [rawField, fieldSize]);

  if (!dataTex) return null;

  const sz = fieldSize;

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[sz, sz, sz]} />
      <shaderMaterial
        vertexShader={VOL_VERTEX}
        fragmentShader={VOL_FRAGMENT}
        uniforms={{
          uVolume:      { value: dataTex },
          uVolumeSize:  { value: new THREE.Vector3(sz, sz, sz) },
          uStepSize:    { value: 1.2 },
          uAlphaScale:  { value: 2.2 },
          uDensityMin:  { value: 7.5 },
          uDensityMax:  { value: 14.5 },
        }}
        transparent
        depthWrite={false}
        side={THREE.BackSide}
      />
    </mesh>
  );
}

/* ================================================================
   VolumeRenderer — 入口组件
   ================================================================ */
export default function VolumeRenderer({ rawField, fieldSize = 64, voxelSample }) {
  const hasVolume = rawField && rawField.length > 0;

  if (!hasVolume) {
    // 回退：粒子云
    const { xs, ys, zs, rhos } = voxelSample || {};
    if (!xs) return null;
    const p = new Float32Array(xs.length * 3);
    const c = new Float32Array(xs.length * 3);
    for (let i = 0; i < xs.length; i++) {
      p[i*3]=xs[i]; p[i*3+1]=ys[i]; p[i*3+2]=zs[i];
      const t = Math.max(0,Math.min(1,(rhos[i]-7.5)/7.0));
      let r,g,b;
      if(t<0.3){r=0.03+0.77*t;g=0.09+1.63*t;b=0.25+1.7*t;}
      else if(t<0.55){const s=(t-0.3)/0.25;r=0.26+1.64*s;g=0.58-0.2*s;b=0.76+0.16*s;}
      else if(t<0.8){const s=(t-0.55)/0.25;r=0.67+1.16*s;g=0.53-0.32*s;b=0.80-0.36*s;}
      else{const s=(t-0.8)/0.2;r=0.96+0.2*s;g=0.45+2.45*s;b=0.71+1.25*s;}
      c[i*3]=r;c[i*3+1]=g;c[i*3+2]=b;
    }
    const tex = (()=>{
      const cv=document.createElement('canvas');cv.width=cv.height=64;
      const ct=cv.getContext('2d');
      const g=ct.createRadialGradient(32,32,0,32,32,32);
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
        <pointsMaterial size={1.6} map={tex} vertexColors transparent opacity={0.55}
          depthWrite={false} blending={THREE.AdditiveBlending} sizeAttenuation/>
      </points>
    );
  }

  return <VolumeCube rawField={rawField} fieldSize={fieldSize} />;
}
