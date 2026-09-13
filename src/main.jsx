import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber';
import { Activity, Box, Info, Maximize2, RotateCcw, ScanLine, X } from 'lucide-react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import './styles.css';

const modules = [
  { id: 'head', label: 'Cranium', cn: '头部装甲', color: '#237bff', explode: [0, 1.22, 0.18], code: 'OPT-C01' },
  { id: 'left-arm', label: 'Left actuator', cn: '左肩臂组件', color: '#ffc247', explode: [-1.02, 0.25, 0.08], code: 'OPT-C02' },
  { id: 'right-arm', label: 'Right actuator', cn: '右肩臂组件', color: '#ffc247', explode: [1.02, 0.25, 0.08], code: 'OPT-C03' },
  { id: 'left-chest', label: 'Left chest plate', cn: '左胸甲', color: '#ff3b42', explode: [-0.56, 0.12, 0.72], code: 'OPT-C04' },
  { id: 'right-chest', label: 'Right chest plate', cn: '右胸甲', color: '#ff3b42', explode: [0.56, 0.12, 0.72], code: 'OPT-C05' },
  { id: 'core', label: 'Energon core', cn: '核心躯干', color: '#ff5c50', explode: [0, -0.08, 1.02], code: 'OPT-C06' },
  { id: 'left-leg', label: 'Left leg / foot', cn: '左腿与脚部', color: '#49b7ff', explode: [-0.58, -0.25, 0.12], code: 'OPT-C07' },
  { id: 'right-leg', label: 'Right leg / foot', cn: '右腿与脚部', color: '#49b7ff', explode: [0.58, -0.25, 0.12], code: 'OPT-C08' },
];

function Model({ explodeProgress, active, autoRotate, wire }) {
  const group = useRef();
  const animatedProgress = useRef(0);
  const { scene } = useLoader(GLTFLoader, '/optimus-bang.glb');
  const model = useMemo(() => scene.clone(true), [scene]);
  const nodeMapping = ['root2', 'root0', 'root5', 'root3', 'root4', 'root6', 'root1', 'root7'];
  const partGroups = useMemo(() => modules.map((part, index) => ({ ...part, nodeName: nodeMapping[index] })), []);
  const partNodes = useMemo(() => partGroups.map((part) => ({ ...part, node: model.getObjectByName(part.nodeName) })), [model, partGroups]);

  useEffect(() => {
    model.traverse((object) => {
      if (!object.isMesh) return;
      object.castShadow = true;
      object.receiveShadow = true;
      object.material = object.material.clone();
      object.material.metalness = Math.max(object.material.metalness ?? 0, 0.55);
      object.material.roughness = Math.min(object.material.roughness ?? 0.45, 0.35);
      object.material.clippingPlanes = [];
    });
    partNodes.forEach((part) => {
      if (!part.node) return;
      part.node.userData.partId = part.id;
      part.node.userData.basePosition = part.node.position.clone();
      part.node.traverse((object) => { object.userData.partId = part.id; });
    });
  }, [model, partNodes]);

  useFrame((_, delta) => {
    animatedProgress.current = THREE.MathUtils.damp(animatedProgress.current, explodeProgress / 100, 3.5, delta);
    const progress = animatedProgress.current;
    if (group.current) {
      if (progress < 0.01 && autoRotate) group.current.rotation.y += delta * 0.12;
      if (progress > 0.01) group.current.rotation.y = THREE.MathUtils.lerp(group.current.rotation.y, 0, 0.1);
      const targetScale = progress > 0.01 ? 1.34 : 2.15;
      group.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.08);
    }

    partNodes.forEach((part) => {
      const root = part.node;
      if (!root?.userData.basePosition) return;
      const [explodeX, explodeY, explodeZ] = part.explode;
      root.position.set(
        THREE.MathUtils.lerp(root.userData.basePosition.x, explodeX, progress),
        THREE.MathUtils.lerp(root.userData.basePosition.y, explodeY, progress),
        THREE.MathUtils.lerp(root.userData.basePosition.z, explodeZ, progress),
      );
    });

    model.traverse((object) => {
      if (!object.isMesh) return;
      const partId = object.userData.partId;
      const isActive = active === 'all' || active === partId;
      const part = partNodes.find((entry) => entry.id === partId);
      object.material.emissive.set(active === 'all' ? '#123f93' : isActive ? part.color : '#020407');
      object.material.emissiveIntensity = active === 'all' ? 0.18 : isActive ? 1.15 : 0.01;
      object.material.transparent = active !== 'all';
      object.material.opacity = active === 'all' || isActive ? 1 : 0.2;
      object.material.depthWrite = active === 'all' || isActive;
      object.material.wireframe = wire;
    });
  });

  return <group ref={group} scale={2.15} position={[0.3, -0.85, 0]}>
    <primitive object={model} />
  </group>;
}

function CameraControls({ autoRotate }) {
  const { camera, gl, size } = useThree();
  const controls = useRef();
  const controlsObject = useMemo(() => new OrbitControls(camera, gl.domElement), [camera, gl]);
  useEffect(() => {
    const centerX = Number.parseFloat(getComputedStyle(gl.domElement).getPropertyValue('--model-center-x')) / 100;
    camera.setViewOffset(size.width, size.height, size.width * (0.5 - centerX), 0, size.width, size.height);
    return () => camera.clearViewOffset();
  }, [camera, gl, size.width, size.height]);
  useEffect(() => {
    controlsObject.enablePan = false;
    controlsObject.minDistance = 5.3;
    controlsObject.maxDistance = 10;
    controlsObject.target.set(0.3, -0.7, 0);
    controlsObject.autoRotateSpeed = 0.7;
    return () => controlsObject.dispose();
  }, [controlsObject]);
  useEffect(() => { controlsObject.autoRotate = autoRotate; }, [autoRotate, controlsObject]);
  useFrame(() => controls.current?.update());
  return <primitive ref={controls} object={controlsObject} />;
}

function Scene({ explodeProgress, active, autoRotate, wire }) {
  return <Canvas shadows gl={{ localClippingEnabled: true }} camera={{ position: [0.3, 0.05, 9.3], fov: 38 }} dpr={[1, 2]}>
    <color attach="background" args={['#080b12']} />
    <fog attach="fog" args={['#080b12', 7, 13]} />
    <ambientLight intensity={0.42} />
    <directionalLight position={[4, 6, 5]} intensity={3.4} color="#b9d7ff" castShadow />
    <pointLight position={[-3, 0, 2]} intensity={16} distance={9} color="#0d73ff" />
    <pointLight position={[3, -2, 2]} intensity={12} distance={8} color="#ff3549" />
    <Model explodeProgress={explodeProgress} active={active} autoRotate={autoRotate} wire={wire} />
    <gridHelper args={[18, 36, '#1c3853', '#0d1827']} rotation={[0, 0, 0]} position={[0.3, -3.1, 0]} />
    <CameraControls autoRotate={autoRotate && explodeProgress === 0} />
  </Canvas>;
}

function App() {
  const [active, setActive] = useState('all');
  const [autoRotate, setAutoRotate] = useState(true);
  const [wire, setWire] = useState(false);
  const [explodeProgress, setExplodeProgress] = useState(0);
  const [aboutOpen, setAboutOpen] = useState(false);
  const exploded = explodeProgress > 0;
  const updateExplode = (value) => setExplodeProgress(value);
  const selectPart = (partId) => {
    setActive(partId);
    if (partId !== 'all' && explodeProgress < 100) updateExplode(100);
  };
  const resetExperience = () => { setAutoRotate(true); setWire(false); updateExplode(0); setActive('all'); };
  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) await document.documentElement.requestFullscreen?.();
    else await document.exitFullscreen?.();
  };
  return <main className={`app-shell ${exploded ? 'exploded' : ''}`}>
    <div className="viewport"><Scene explodeProgress={explodeProgress} active={active} autoRotate={autoRotate} wire={wire} /></div>
    <div className="vignette" /><div className="grain" />
    <header className="topbar"><a className="wordmark" href="/" onClick={(event) => event.preventDefault()}><span className="brand-mark">P<span>\</span></span> PRIME<span className="wordmark-divider" /><span className="archive">机械档案 / 001</span></a><div className="header-right"><span className="live-dot" /><span className="status">CYBERTRON ARCHIVE</span><button className="replay" onClick={() => resetExperience()}>重新唤醒 ↗</button><button className="round" onClick={() => setAboutOpen(true)} aria-label="查看档案资料"><Info size={16} /></button></div></header>
    <main className="intro"><p className="eyebrow"><span /> AUTOBOT COMMANDER</p><h1>OPTIMUS<br /><span>PRIME</span><em>Q版擎天柱</em></h1><p className="tagline">钢铁之躯。自由之魂。</p><p className="description">穿过装甲，窥见传奇的内部。<br />亲手拆解每一层机械结构。</p><button className="primary" onClick={() => updateExplode(exploded ? 0 : 100)}><span>{exploded ? '收起拆解' : '启动拆解'}</span><span className="arrow">→</span></button><div className="edition"><span>01 /</span> CHIBI EDITION<br /><small>IMAGEGEN × HYPER3D</small></div></main>
    <div className="specimen"><span className="cross">+</span><span>OP—001<br /><b>{exploded ? 'EXPLODED' : 'ASSEMBLED'}</b></span></div>
    <aside className="part-panel" aria-label="模型零件"><div className="panel-head"><span>结构索引</span><span>08</span></div><button className={`part-button ${active === 'all' ? 'selected' : ''}`} onClick={() => selectPart('all')}><span>00</span>完整形态</button>{modules.map((item, index) => <button className={`part-button ${active === item.id ? 'selected' : ''}`} key={item.id} onClick={() => selectPart(item.id)}><span style={{ color: item.color }}>{String(index + 1).padStart(2, '0')}</span>{item.cn}</button>)}</aside>
    <div className="viewer-tools"><button className={`round ${autoRotate ? 'active' : ''}`} onClick={() => setAutoRotate(!autoRotate)} aria-label="自动旋转"><RotateCcw size={16} /></button><button className={`round ${wire ? 'active' : ''}`} onClick={() => setWire(!wire)} aria-label="线框模式"><Box size={16} /></button><button className="round" onClick={resetExperience} aria-label="重置视角"><RotateCcw size={16} /></button><button className="round" onClick={toggleFullscreen} aria-label="全屏展示"><Maximize2 size={16} /></button></div>
    <footer><div className="footer-note"><span className="live-dot" /> <span>{exploded ? '正在拆解机械档案…' : '机械档案已就绪'}</span></div><div className="timeline"><div className="timeline-top"><button className={`text-button ${!exploded ? 'selected' : ''}`} onClick={() => updateExplode(0)}>完整形态</button><span id="percentage">{String(explodeProgress).padStart(2, '0')}<small>%</small></span><button className={`text-button ${exploded ? 'selected' : ''}`} onClick={() => updateExplode(100)}>爆炸视图</button></div><input style={{ '--progress': `${explodeProgress}%` }} type="range" min="0" max="100" value={explodeProgress} onChange={(event) => updateExplode(Number(event.target.value))} /><div className="ticks">{Array.from({ length: 11 }, (_, index) => <i key={index} />)}</div></div><div className="gesture"><span>◌</span><span>拖动旋转 · 滚轮缩放<br /><small>触屏拖动 · 双指缩放</small></span></div></footer>
    {aboutOpen && <div className="about-backdrop" role="presentation" onClick={() => setAboutOpen(false)}><section className="about-card" role="dialog" aria-modal="true" aria-labelledby="about-title" onClick={(event) => event.stopPropagation()}><button className="round about-close" onClick={() => setAboutOpen(false)} aria-label="关闭档案"><X size={16} /></button><div className="about-scroll"><p className="eyebrow">THE MAKING OF A LEGEND</p><h2 id="about-title">传奇，逐层展开。</h2><p className="about-lead">擎天柱（Optimus Prime）是《变形金刚》系列最具代表性的角色之一，也是汽车人阵营的核心领袖。</p><div className="profile-grid"><div><span>身份 / ROLE</span><strong>汽车人领袖</strong></div><div><span>阵营 / FACTION</span><strong>汽车人 AUTOBOTS</strong></div><div><span>载具 / ALT MODE</span><strong>卡车形态</strong></div><div><span>母星 / ORIGIN</span><strong>塞伯坦 CYBERTRON</strong></div></div><div className="about-section"><span className="about-label">CHARACTER FILE // 角色档案</span><p>在不同动画、漫画与电影版本中，擎天柱通常以沉着、勇敢且富有责任感的领袖形象出现。他带领汽车人与霸天虎对抗，守护自由，并把保护生命与追求和平置于个人安危之上。</p></div><div className="about-section theme-section"><span className="about-label">CORE THEMES // 核心主题</span><div className="theme-list"><span>自由</span><span>责任</span><span>牺牲</span><span>领导力</span></div></div><div className="about-section model-note"><span className="about-label">ABOUT THIS MODEL // 本次展示</span><p>当前页面以擎天柱的经典红蓝视觉为灵感，通过 Hyper3D Rodin 重建为 Q 版 3D 研究模型，并拆分为 8 个独立部件进行对称爆炸展示。它是 AI 生成的视觉再创作，不代表官方模型，也不还原真实变形机构。</p></div><div className="about-meta"><span>ASSET // OPT-01</span><span>PARTS // 08</span><span>ENGINE // RODIN</span></div><div className="about-sources"><span>资料来源 / SOURCES</span><a href="https://transformers.hasbro.com/" target="_blank" rel="noreferrer">Hasbro Transformers 官方站 ↗</a><a href="https://en.wikipedia.org/wiki/Optimus_Prime" target="_blank" rel="noreferrer">Optimus Prime 角色概览 ↗</a></div></div></section></div>}
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
