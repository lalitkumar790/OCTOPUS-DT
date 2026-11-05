"use client";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
type Props={pressures:number[][];selectedArm:number;paused:boolean;underwater:boolean;onSelectArm:(index:number)=>void};
export default function OctopusScene({pressures,selectedArm,paused,underwater,onSelectArm}:Props) {
 const hostRef=useRef<HTMLDivElement>(null);
 const stateRef=useRef({pressures,selectedArm,paused,underwater,onSelectArm});
 useEffect(()=>{stateRef.current={pressures,selectedArm,paused,underwater,onSelectArm};},[pressures,selectedArm,paused,underwater,onSelectArm]);
 useEffect(()=>{
  const host=hostRef.current;if(!host)return;
  const scene=new THREE.Scene();scene.background=new THREE.Color("#07131b");const backgroundColor=scene.background as THREE.Color;
  const camera=new THREE.PerspectiveCamera(38,1,0.01,10);camera.up.set(0,0,1);camera.position.set(.56,-.68,.57);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.outputColorSpace=THREE.SRGBColorSpace;host.appendChild(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,0,0);controls.minDistance=.36;controls.maxDistance=1.8;controls.maxPolarAngle=Math.PI*.48;
  scene.add(new THREE.AmbientLight("#9ab8c5",1.4));const key=new THREE.DirectionalLight("#d9f5ff",3.2);key.position.set(-.4,-.5,1.1);key.castShadow=true;scene.add(key);const rim=new THREE.PointLight("#13d8c2",18,1.6);rim.position.set(.4,.4,.4);scene.add(rim);
  const floor=new THREE.Mesh(new THREE.CircleGeometry(.48,96),new THREE.MeshStandardMaterial({color:"#0b202a",roughness:.92,metalness:.08}));floor.position.z=-.085;floor.receiveShadow=true;scene.add(floor);
  const grid=new THREE.GridHelper(1.1,22,"#1d5360","#12313b");grid.rotation.x=Math.PI/2;grid.position.z=-.082;(grid.material as THREE.Material).transparent=true;(grid.material as THREE.Material).opacity=.45;scene.add(grid);
  const core=new THREE.Mesh(new THREE.SphereGeometry(.1,48,32),new THREE.MeshPhysicalMaterial({color:"#183b4a",metalness:.48,roughness:.28,clearcoat:.9}));core.scale.set(1,1,.53);core.castShadow=true;scene.add(core);
  const hub=new THREE.Mesh(new THREE.CylinderGeometry(.035,.035,.018,48),new THREE.MeshStandardMaterial({color:"#13bfae",metalness:.7,roughness:.22,emissive:"#063b36"}));hub.rotation.x=Math.PI/2;hub.position.z=.057;scene.add(hub);
  const accent=new THREE.Mesh(new THREE.TorusGeometry(.078,.0025,8,72),new THREE.MeshBasicMaterial({color:"#2ce0c7"}));accent.position.z=.006;scene.add(accent);
  const arms:THREE.Mesh[]=[];const mats:THREE.MeshPhysicalMaterial[]=[];const palette=["#27c7b5","#398cc8","#8c76d1","#e28b54","#27c7b5","#398cc8","#8c76d1","#e28b54"];const length=.22,base=.095;
  for(let i=0;i<8;i++){const mat=new THREE.MeshPhysicalMaterial({color:palette[i],roughness:.32,metalness:.12,clearcoat:.8,emissive:palette[i],emissiveIntensity:.035});mats.push(mat);const curve=new THREE.CatmullRomCurve3([new THREE.Vector3(base,0,0),new THREE.Vector3(base+length/2,0,0),new THREE.Vector3(base+length,0,0)]);const mesh=new THREE.Mesh(new THREE.TubeGeometry(curve,48,.012,10,false),mat);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData.armIndex=i;arms.push(mesh);scene.add(mesh);const a=i*Math.PI/4;const socket=new THREE.Mesh(new THREE.SphereGeometry(.018,20,16),new THREE.MeshStandardMaterial({color:"#b4d6db",metalness:.65,roughness:.28}));socket.position.set(base*Math.cos(a),base*Math.sin(a),0);socket.scale.set(1,1,.8);scene.add(socket);}
  const water=new THREE.Mesh(new THREE.SphereGeometry(1.15,32,24),new THREE.MeshBasicMaterial({color:"#063c50",transparent:true,opacity:.07,side:THREE.BackSide,depthWrite:false}));water.visible=false;scene.add(water);
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
  const pick=(event:PointerEvent)=>{const rect=renderer.domElement.getBoundingClientRect();pointer.set(((event.clientX-rect.left)/rect.width)*2-1,-((event.clientY-rect.top)/rect.height)*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(arms)[0];if(hit){const idx=hit.object.userData.armIndex;if(Number.isInteger(idx))stateRef.current.onSelectArm(idx);}};
  renderer.domElement.addEventListener("pointerdown",pick);
  const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);};const observer=new ResizeObserver(resize);observer.observe(host);resize();
  let elapsed=0,previous=performance.now(),frame=0;
  const animate=(now:number)=>{frame=requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,.04);previous=now;const s=stateRef.current;if(!s.paused)elapsed+=dt;backgroundColor.set(s.underwater?"#062330":"#07131b");water.visible=s.underwater;
   for(let i=0;i<8;i++){const a=i*Math.PI/4,radial=new THREE.Vector3(Math.cos(a),Math.sin(a),0),tangent=new THREE.Vector3(-Math.sin(a),Math.cos(a),0),pts:THREE.Vector3[]=[];const chambers=s.pressures[i]??Array(10).fill(0),mean=chambers.reduce((v,p)=>v+p,0)/10,pressureGain=mean/80,wave=elapsed*.75+i*.18;
    for(let j=0;j<=40;j++){const u=j/40,r=base+length*u,ci=Math.min(9,Math.floor(u*10)),p=(chambers[ci]??0)/80,distal=chambers.slice(0,ci+1).reduce((v,x)=>v+x,0)/Math.max(1,ci+1)/80;const bend=(.015+.105*p+.045*distal)*u*Math.sin(wave-u*2.3),side=(.008+.018*p)*u*Math.cos(wave-u*2.1);pts.push(radial.clone().multiplyScalar(r).add(tangent.clone().multiplyScalar(side)).add(new THREE.Vector3(0,0,bend)));}
    const geometry=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),64,.012,10,false);arms[i].geometry.dispose();arms[i].geometry=geometry;mats[i].emissiveIntensity=i===s.selectedArm?.24+pressureGain*.18:.025+pressureGain*.05;mats[i].roughness=i===s.selectedArm?.22:.32;
   }controls.update();renderer.render(scene,camera);
  };frame=requestAnimationFrame(animate);
  return ()=>{cancelAnimationFrame(frame);observer.disconnect();controls.dispose();renderer.domElement.removeEventListener("pointerdown",pick);scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m.dispose());}});renderer.dispose();if(renderer.domElement.parentElement===host)host.removeChild(renderer.domElement);};
 },[]);
 return <div className="scene-host" ref={hostRef} aria-label="Interactive 3D octopus robot preview; click an arm to select it"/>;
}