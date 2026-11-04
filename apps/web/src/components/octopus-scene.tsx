"use client";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
type Props={amplitude:number;frequency:number;phase:number;selectedArm:number;paused:boolean};
export default function OctopusScene({amplitude,frequency,phase,selectedArm,paused}:Props) {
  const hostRef=useRef<HTMLDivElement>(null);
  const stateRef=useRef({amplitude,frequency,phase,selectedArm,paused});
  useEffect(()=>{stateRef.current={amplitude,frequency,phase,selectedArm,paused};},[amplitude,frequency,phase,selectedArm,paused]);
  useEffect(()=>{
    const host=hostRef.current;if(!host)return;
    const scene=new THREE.Scene();scene.background=new THREE.Color("#07131b");
    const camera=new THREE.PerspectiveCamera(38,1,0.01,10);camera.position.set(0.56,-0.68,0.57);
    const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.outputColorSpace=THREE.SRGBColorSpace;host.appendChild(renderer.domElement);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,0,0);controls.minDistance=0.36;controls.maxDistance=1.8;controls.maxPolarAngle=Math.PI*0.48;
    scene.add(new THREE.AmbientLight("#9ab8c5",1.4));
    const key=new THREE.DirectionalLight("#d9f5ff",3.2);key.position.set(-0.4,-0.5,1.1);key.castShadow=true;scene.add(key);
    const rim=new THREE.PointLight("#13d8c2",18,1.6);rim.position.set(0.4,0.4,0.4);scene.add(rim);
    const floor=new THREE.Mesh(new THREE.CircleGeometry(0.48,96),new THREE.MeshStandardMaterial({color:"#0b202a",roughness:0.92,metalness:0.08}));floor.position.z=-0.085;floor.receiveShadow=true;scene.add(floor);
    const grid=new THREE.GridHelper(1.1,22,"#1d5360","#12313b");grid.rotation.x=Math.PI/2;grid.position.z=-0.082;(grid.material as THREE.Material).transparent=true;(grid.material as THREE.Material).opacity=0.45;scene.add(grid);
    const core=new THREE.Mesh(new THREE.SphereGeometry(0.1,48,32),new THREE.MeshPhysicalMaterial({color:"#183b4a",metalness:0.48,roughness:0.28,clearcoat:0.9}));core.scale.set(1,1,0.53);core.castShadow=true;scene.add(core);
    const hub=new THREE.Mesh(new THREE.CylinderGeometry(0.035,0.035,0.018,48),new THREE.MeshStandardMaterial({color:"#13bfae",metalness:0.7,roughness:0.22,emissive:"#063b36"}));hub.rotation.x=Math.PI/2;hub.position.z=0.057;scene.add(hub);
    const accent=new THREE.Mesh(new THREE.TorusGeometry(0.078,0.0025,8,72),new THREE.MeshBasicMaterial({color:"#2ce0c7"}));accent.position.z=0.006;scene.add(accent);
    const arms:THREE.Mesh[]=[];const mats:THREE.MeshPhysicalMaterial[]=[];
    const palette=["#27c7b5","#398cc8","#8c76d1","#e28b54","#27c7b5","#398cc8","#8c76d1","#e28b54"];
    const length=0.22,base=0.095;
    for(let i=0;i<8;i++){
      const mat=new THREE.MeshPhysicalMaterial({color:palette[i],roughness:0.32,metalness:0.12,clearcoat:0.8,emissive:palette[i],emissiveIntensity:0.035});mats.push(mat);
      const curve=new THREE.CatmullRomCurve3([new THREE.Vector3(base,0,0),new THREE.Vector3(base+length/2,0,0),new THREE.Vector3(base+length,0,0)]);
      const mesh=new THREE.Mesh(new THREE.TubeGeometry(curve,48,0.012,10,false),mat);mesh.castShadow=true;mesh.receiveShadow=true;arms.push(mesh);scene.add(mesh);
      const socket=new THREE.Mesh(new THREE.SphereGeometry(0.018,20,16),new THREE.MeshStandardMaterial({color:"#b4d6db",metalness:0.65,roughness:0.28}));socket.position.set(base*Math.cos(i*Math.PI/4),base*Math.sin(i*Math.PI/4),0);socket.scale.set(1,1,0.8);scene.add(socket);
    }
    const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);};
    const observer=new ResizeObserver(resize);observer.observe(host);resize();
    let elapsed=0,previous=performance.now(),frame=0;
    const animate=(now:number)=>{frame=requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,0.04);previous=now;const s=stateRef.current;if(!s.paused)elapsed+=dt;
      for(let i=0;i<8;i++){const a=i*Math.PI/4;const radial=new THREE.Vector3(Math.cos(a),Math.sin(a),0);const tangent=new THREE.Vector3(-Math.sin(a),Math.cos(a),0);const pts:THREE.Vector3[]=[];const wp=elapsed*s.frequency*Math.PI*2+s.phase+i*0.22;
        for(let j=0;j<=36;j++){const u=j/36,r=base+length*u,e=Math.pow(u,1.35);const bend=s.amplitude*0.095*e*Math.sin(wp-u*Math.PI*1.65);const side=s.amplitude*0.025*e*Math.cos(wp-u*Math.PI*1.65);pts.push(radial.clone().multiplyScalar(r).add(tangent.clone().multiplyScalar(side)).add(new THREE.Vector3(0,0,bend)));}
        const curve=new THREE.CatmullRomCurve3(pts);const geometry=new THREE.TubeGeometry(curve,64,0.012,10,false);arms[i].geometry.dispose();arms[i].geometry=geometry;mats[i].emissiveIntensity=i===s.selectedArm?0.22:0.035;mats[i].roughness=i===s.selectedArm?0.22:0.32;
      }
      controls.update();renderer.render(scene,camera);
    };
    frame=requestAnimationFrame(animate);
    return ()=>{cancelAnimationFrame(frame);observer.disconnect();controls.dispose();scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m.dispose());}});renderer.dispose();if(renderer.domElement.parentElement===host)host.removeChild(renderer.domElement);};
  },[]);
  return <div className="scene-host" ref={hostRef} aria-label="Interactive 3D octopus robot preview"/>;
}
