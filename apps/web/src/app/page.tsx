"use client";
import { useState } from "react";
import OctopusScene from "@/components/octopus-scene";
const armNames = ["North","North-east","East","South-east","South","South-west","West","North-west"];
export default function Home() {
  const [amplitude,setAmplitude] = useState(0.55);
  const [frequency,setFrequency] = useState(0.25);
  const [phase,setPhase] = useState(0.3);
  const [selectedArm,setSelectedArm] = useState(0);
  const [paused,setPaused] = useState(false);
  return <main className="shell">
    <header className="topbar">
      <a className="brand" href="#"><span className="brand-mark">O</span><span>OCTOPUS<span className="brand-dim">-DT</span></span></a>
      <div className="topbar-center"><span className="live-dot"/> DIGITAL TWIN <span className="topbar-divider">/</span> RESEARCH BUILD 0.1</div>
      <a className="github-link" href="https://github.com/lalitkumar790/OCTOPUS-DT" target="_blank" rel="noreferrer">SOURCE ↗</a>
    </header>
    <section className="hero">
      <div className="eyebrow"><span>FIELD NOTE 001</span><i/> SOFT ROBOTICS / UNDERWATER SYSTEMS</div>
      <h1>Eight arms.<br/><em>One living system.</em></h1>
      <p className="hero-copy">A digital twin for exploring the mechanics, actuation and locomotion of a pneumatic soft robotic octopus.</p>
    </section>
    <section className="workspace">
      <div className="simulation-panel">
        <div className="panel-head"><div><div className="panel-kicker">01 / SIMULATION VIEWPORT</div><h2>Robot morphology</h2></div><div className="viewport-status"><span className="live-dot"/> LIVE PREVIEW</div></div>
        <div className="viewport">
          <div className="viewport-grid"/>
          <OctopusScene amplitude={amplitude} frequency={frequency} phase={phase} selectedArm={selectedArm} paused={paused}/>
          <div className="axis-label axis-x">X <span>→</span></div><div className="axis-label axis-y">Y <span>↑</span></div>
          <div className="viewport-caption">FIG 01. / PARAMETRIC CABLE MORPHOLOGY <span>NOT TO SCALE</span></div>
          <div className="viewport-tools"><span>3D</span><span>ORBIT / ZOOM</span></div>
        </div>
        <div className="arm-selector"><div className="selector-label">SELECT ARM</div>
          <div className="arm-buttons">{armNames.map((name,index)=><button key={name} onClick={()=>setSelectedArm(index)} className={selectedArm===index?"arm-button active":"arm-button"} aria-label={"Select "+name+" arm"}>{String(index+1).padStart(2,"0")}</button>)}</div>
          <div className="selected-arm">{armNames[selectedArm].toUpperCase()} <span>ARM {String(selectedArm+1).padStart(2,"0")}</span></div>
        </div>
      </div>
      <aside className="control-panel">
        <div className="panel-kicker">02 / CONTROL SURFACE</div><h2>Actuation inputs</h2>
        <p className="control-intro">Adjust the visualized travelling-wave profile. These are preview parameters, not calibrated pressure commands.</p>
        <div className="control-group"><div className="control-label"><label htmlFor="amplitude">BENDING AMPLITUDE</label><output>{amplitude.toFixed(2)} <small>scale*</small></output></div><input id="amplitude" type="range" min="0.05" max="1.2" step="0.01" value={amplitude} onChange={e=>setAmplitude(Number(e.target.value))}/><div className="range-ends"><span>RELAXED</span><span>HIGH</span></div></div>
        <div className="control-group"><div className="control-label"><label htmlFor="frequency">WAVE FREQUENCY</label><output>{frequency.toFixed(2)} <small>Hz</small></output></div><input id="frequency" type="range" min="0.05" max="1" step="0.01" value={frequency} onChange={e=>setFrequency(Number(e.target.value))}/><div className="range-ends"><span>0.05 Hz</span><span>1.00 Hz</span></div></div>
        <div className="control-group"><div className="control-label"><label htmlFor="phase">WAVE PHASE</label><output>{phase.toFixed(2)} <small>rad</small></output></div><input id="phase" type="range" min="0" max="6.28" step="0.01" value={phase} onChange={e=>setPhase(Number(e.target.value))}/><div className="range-ends"><span>0</span><span>2π</span></div></div>
        <div className="control-actions"><button className="run-button" onClick={()=>setPaused(!paused)}><span>{paused?"▶":"Ⅱ"}</span>{paused?"RESUME PREVIEW":"PAUSE PREVIEW"}</button><button className="reset-button" onClick={()=>{setAmplitude(0.55);setFrequency(0.25);setPhase(0.3);setPaused(false);}}>RESET ↺</button></div>
        <div className="control-footnote">* Visualization scale only; not a measured tip displacement.</div>
      </aside>
    </section>
    <section className="metrics">
      <div className="metric"><span className="metric-label">ARM COUNT</span><strong>08</strong><small>RADIAL ARRANGEMENT</small></div>
      <div className="metric"><span className="metric-label">ACTIVE LENGTH</span><strong>220<span>mm</span></strong><small>CAD-DERIVED INPUT</small></div>
      <div className="metric"><span className="metric-label">CHAMBERS / ARM</span><strong>10</strong><small>PNEUMATIC DESIGN</small></div>
      <div className="metric"><span className="metric-label">MODEL STATUS</span><strong className="status-text">EARLY</strong><small>CABLE APPROXIMATION</small></div>
    </section>
    <section className="research-note"><div className="note-icon">i</div><div><strong>RESEARCH INTEGRITY NOTICE</strong><p>This browser viewport is a procedural 3D visualization for interface development. It is not a live MuJoCo simulation. The cable model approximates centerline bending and twist; it does not resolve chamber inflation, 3D silicone hyperelasticity, or fluid-structure interaction. Validate against physical measurements before drawing performance conclusions.</p></div><a href="https://github.com/lalitkumar790/OCTOPUS-DT/blob/main/docs/model-assumptions.md" target="_blank" rel="noreferrer">MODEL ASSUMPTIONS ↗</a></section>
    <footer><span>OCTOPUS-DT <i>—</i> OPEN RESEARCH PLATFORM</span><span>MUJOCO × PYTHON × THREE.JS</span><span>BUILD 0.1.0 <i>© 2026</i></span></footer>
  </main>;
}
