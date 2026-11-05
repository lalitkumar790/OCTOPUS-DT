"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

type ArmState = { joint_angle_rad: number };
type Props = {
  pressures: number[][];
  selectedArm: number;
  paused: boolean;
  underwater: boolean;
  onSelectArm: (index: number) => void;
  apiBase?: string;
  simulationAvailable?: boolean;
  mujocoArms?: ArmState[];
};

const SOFT_SEGMENTS_PER_ARM = 10;
const SOFT_SEGMENT_LENGTH = 0.022;

const STATIC_CAD_PARTS = [
  "structural_frame.stl", "interface_01.stl", "interface_02.stl",
  "interface_03.stl", "interface_04.stl", "interface_05.stl",
  "interface_06.stl", "interface_07.stl", "interface_08.stl",
  "camera_mount_boss.stl", "upper_shell.stl", "lower_shell.stl",
  "service_cover.stl", "electronics_tray.stl", "battery_tray.stl",
  "sensor_top_antenna.stl", "sensor_front_distance.stl",
  "sensor_bottom_pressure.stl", "sensor_bottom_depth.stl",
  "sensor_bottom_environmental.stl", "cable_central_trunk.stl",
  "cable_radial_channels.stl",
];

export default function OctopusScene({
  pressures, selectedArm, paused, underwater, onSelectArm,
  apiBase: configuredApiBase, simulationAvailable: externalSimulationAvailable,
  mujocoArms: externalMujocoArms = [],
}: Props) {
  const apiBase = (configuredApiBase ?? process.env.NEXT_PUBLIC_SIM_API_URL ?? "").replace(/\/$/, "");
  const [apiConnected, setApiConnected] = useState(false);
  const [liveMujocoArms, setLiveMujocoArms] = useState<ArmState[]>([]);
  const simulationAvailable = externalSimulationAvailable ?? apiConnected;
  const mujocoArms = externalMujocoArms.length ? externalMujocoArms : liveMujocoArms;
  const hostRef = useRef<HTMLDivElement>(null);
  const proceduralRootRef = useRef<THREE.Group | null>(null);
  const cadRootRef = useRef<THREE.Group | null>(null);
  const cadArmGroupsRef = useRef<THREE.Group[]>([]);
  const cadArmJointGroupsRef = useRef<THREE.Group[][]>([]);
  const softAnglesRef = useRef<number[][]>(Array.from({ length: 8 }, () => Array(10).fill(0)));
  const stateRef = useRef({
    pressures, selectedArm, paused, underwater, onSelectArm, mujocoArms,
  });

  useEffect(() => {
    if (!apiBase) {
      setApiConnected(false);
      return;
    }
    let active = true;
    const poll = async () => {
      try {
        const health = await fetch(apiBase + "/health", { cache: "no-store" });
        const payload = await health.json();
        if (!active) return;
        if (payload.status !== "ready") {
          setApiConnected(false);
          return;
        }
        const response = await fetch(apiBase + "/api/model", { cache: "no-store" });
        if (!response.ok) throw new Error("MuJoCo state unavailable");
        const state = await response.json();
        const softResponse = await fetch(apiBase + "/api/soft/model", { cache: "no-store" });
        if (!softResponse.ok) throw new Error("Soft continuum state unavailable");
        const softState = await softResponse.json();
        if (active) {
          setApiConnected(true);
          setLiveMujocoArms(state.arms ?? []);
          softAnglesRef.current = (softState.arms ?? []).map(
            (item: { joint_angles_rad?: number[] }) => item.joint_angles_rad ?? Array(10).fill(0),
          );
        }
      } catch {
        if (active) setApiConnected(false);
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 1200);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [apiBase]);

  useEffect(() => {
    stateRef.current = {
      pressures, selectedArm, paused, underwater, onSelectArm, mujocoArms,
    };
  }, [pressures, selectedArm, paused, underwater, onSelectArm, mujocoArms]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#07131b");
    const backgroundColor = scene.background as THREE.Color;
    const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 10);
    camera.up.set(0, 0, 1);
    camera.position.set(0.56, -0.68, 0.57);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0.04);
    // Allow a complete orbit, including views from directly above and below.
    // The old 0.48 * PI ceiling prevented the camera from crossing the horizon.
    controls.minPolarAngle = 0.015;
    controls.maxPolarAngle = Math.PI - 0.015;
    controls.minDistance = 0.22;
    controls.maxDistance = 2.2;
    controls.enableRotate = true;
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.screenSpacePanning = true;
    controls.saveState();
    scene.add(new THREE.AmbientLight("#9ab8c5", 1.4));
    const key = new THREE.DirectionalLight("#d9f5ff", 3.2);
    key.position.set(-0.4, -0.5, 1.1);
    key.castShadow = true;
    scene.add(key);
    const rim = new THREE.PointLight("#13d8c2", 18, 1.6);
    rim.position.set(0.4, 0.4, 0.4);
    scene.add(rim);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(0.48, 96),
      new THREE.MeshStandardMaterial({ color: "#0b202a", roughness: 0.92, metalness: 0.08 }),
    );
    floor.position.z = -0.085;
    floor.receiveShadow = true;
    scene.add(floor);
    const grid = new THREE.GridHelper(1.1, 22, "#1d5360", "#12313b");
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -0.082;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.45;
    scene.add(grid);

    const proceduralRoot = new THREE.Group();
    scene.add(proceduralRoot);
    proceduralRootRef.current = proceduralRoot;
    const core = new THREE.Mesh(
      new THREE.SphereGeometry(0.1, 48, 32),
      new THREE.MeshPhysicalMaterial({
        color: "#183b4a", metalness: 0.48, roughness: 0.28, clearcoat: 0.9,
      }),
    );
    core.scale.set(1, 1, 0.53);
    core.castShadow = true;
    proceduralRoot.add(core);
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.035, 0.035, 0.018, 48),
      new THREE.MeshStandardMaterial({
        color: "#13bfae", metalness: 0.7, roughness: 0.22, emissive: "#063b36",
      }),
    );
    hub.rotation.x = Math.PI / 2;
    hub.position.z = 0.057;
    proceduralRoot.add(hub);
    const accent = new THREE.Mesh(
      new THREE.TorusGeometry(0.078, 0.0025, 8, 72),
      new THREE.MeshBasicMaterial({ color: "#2ce0c7" }),
    );
    accent.position.z = 0.006;
    proceduralRoot.add(accent);

    const arms: THREE.Mesh[] = [];
    const armMaterials: THREE.MeshPhysicalMaterial[] = [];
    const palette = ["#27c7b5", "#398cc8", "#8c76d1", "#e28b54",
      "#27c7b5", "#398cc8", "#8c76d1", "#e28b54"];
    const length = 0.22;
    const base = 0.095;
    for (let i = 0; i < 8; i += 1) {
      const material = new THREE.MeshPhysicalMaterial({
        color: palette[i], roughness: 0.32, metalness: 0.12,
        clearcoat: 0.8, emissive: palette[i], emissiveIntensity: 0.035,
      });
      armMaterials.push(material);
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(base, 0, 0),
        new THREE.Vector3(base + length / 2, 0, 0),
        new THREE.Vector3(base + length, 0, 0),
      ]);
      const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, 0.012, 10, false), material);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.armIndex = i;
      arms.push(mesh);
      proceduralRoot.add(mesh);
      const angle = i * Math.PI / 4;
      const socket = new THREE.Mesh(
        new THREE.SphereGeometry(0.018, 20, 16),
        new THREE.MeshStandardMaterial({ color: "#b4d6db", metalness: 0.65, roughness: 0.28 }),
      );
      socket.position.set(base * Math.cos(angle), base * Math.sin(angle), 0);
      socket.scale.set(1, 1, 0.8);
      proceduralRoot.add(socket);
    }

    const cadRoot = new THREE.Group();
    cadRoot.visible = false;
    scene.add(cadRoot);
    cadRootRef.current = cadRoot;
    const water = new THREE.Mesh(
      new THREE.SphereGeometry(1.15, 32, 24),
      new THREE.MeshBasicMaterial({
        color: "#063c50", transparent: true, opacity: 0.07,
        side: THREE.BackSide, depthWrite: false,
      }),
    );
    water.visible = false;
    scene.add(water);

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const pick = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);
      const hits = cadRoot.visible
        ? raycaster.intersectObject(cadRoot, true)
        : raycaster.intersectObjects(arms);
      const hit = hits[0];
      if (!hit) return;
      let object: THREE.Object3D | null = hit.object;
      while (object && !Number.isInteger(object.userData.armIndex)) object = object.parent;
      if (object && Number.isInteger(object.userData.armIndex)) {
        stateRef.current.onSelectArm(object.userData.armIndex);
      }
    };
    renderer.domElement.addEventListener("pointerdown", pick);

    const resize = () => {
      const width = host.clientWidth;
      const height = host.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    let elapsed = 0;
    let previous = performance.now();
    let frame = 0;
    const animate = (now: number) => {
      frame = requestAnimationFrame(animate);
      const dt = Math.min((now - previous) / 1000, 0.04);
      previous = now;
      const state = stateRef.current;
      if (!state.paused) elapsed += dt;
      backgroundColor.set(state.underwater ? "#062330" : "#07131b");
      water.visible = state.underwater;

      if (!cadRoot.visible) {
        for (let i = 0; i < 8; i += 1) {
          const angle = i * Math.PI / 4;
          const radial = new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0);
          const tangent = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0);
          const points: THREE.Vector3[] = [];
          const chambers = state.pressures[i] ?? Array(10).fill(0);
          const mean = chambers.reduce((sum, pressure) => sum + pressure, 0) / 10;
          const pressureGain = mean / 80;
          const wave = elapsed * 0.75 + i * 0.18;
          for (let j = 0; j <= 40; j += 1) {
            const u = j / 40;
            const radius = base + length * u;
            const chamberIndex = Math.min(9, Math.floor(u * 10));
            const pressure = (chambers[chamberIndex] ?? 0) / 80;
            const distal = chambers.slice(0, chamberIndex + 1)
              .reduce((sum, value) => sum + value, 0) / Math.max(1, chamberIndex + 1) / 80;
            const bend = (0.015 + 0.105 * pressure + 0.045 * distal)
              * u * Math.sin(wave - u * 2.3);
            const side = (0.008 + 0.018 * pressure) * u * Math.cos(wave - u * 2.1);
            points.push(
              radial.clone().multiplyScalar(radius)
                .add(tangent.clone().multiplyScalar(side))
                .add(new THREE.Vector3(0, 0, bend)),
            );
          }
          const geometry = new THREE.TubeGeometry(
            new THREE.CatmullRomCurve3(points), 64, 0.012, 10, false,
          );
          arms[i].geometry.dispose();
          arms[i].geometry = geometry;
          armMaterials[i].emissiveIntensity = i === state.selectedArm
            ? 0.24 + pressureGain * 0.18 : 0.025 + pressureGain * 0.05;
          armMaterials[i].roughness = i === state.selectedArm ? 0.22 : 0.32;
        }
      } else {
        cadArmGroupsRef.current.forEach((group, index) => {
          const angles = softAnglesRef.current[index] ?? [];
          cadArmJointGroupsRef.current[index]?.forEach((jointGroup, segment) => {
            jointGroup.rotation.y = angles[segment] ?? 0;
          });
          group.scale.setScalar(index === state.selectedArm ? 1.025 : 1);
        });
      }
      controls.update();
      // The ground disc is useful as a reference plane, but it would occlude
      // the robot when the camera moves underneath it.
      const viewingFromBelow = camera.position.z < floor.position.z;
      floor.visible = !viewingFromBelow;
      grid.visible = !viewingFromBelow;
      renderer.render(scene, camera);
    };
    frame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener("pointerdown", pick);
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      renderer.dispose();
      if (renderer.domElement.parentElement === host) host.removeChild(renderer.domElement);
      proceduralRootRef.current = null;
      cadRootRef.current = null;
      cadArmGroupsRef.current = [];
      cadArmJointGroupsRef.current = [];
    };
  }, []);

  useEffect(() => {
    const cadRoot = cadRootRef.current;
    const proceduralRoot = proceduralRootRef.current;
    if (!cadRoot || !proceduralRoot) return;
    let cancelled = false;
    cadRoot.visible = false;
    proceduralRoot.visible = true;
    if (!simulationAvailable || !apiBase) return () => { cancelled = true; };

    const loader = new STLLoader();
    const load = async () => {
      try {
        const staticMeshes = await Promise.all(STATIC_CAD_PARTS.map(async (filename) => {
          const geometry = await loader.loadAsync(
            `${apiBase.replace(/\/$/, "")}/assets/meshes/${filename}`,
          );
          geometry.scale(0.001, 0.001, 0.001);
          geometry.computeVertexNormals();
          const color = filename === "structural_frame.stl" ? "#8099a3" : "#315664";
          const mesh = new THREE.Mesh(
            geometry,
            new THREE.MeshStandardMaterial({ color, metalness: 0.42, roughness: 0.48 }),
          );
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          return mesh;
        }));
        if (cancelled) {
          staticMeshes.forEach((mesh) => {
            mesh.geometry.dispose();
            (mesh.material as THREE.Material).dispose();
          });
          return;
        }
        const assembled = new THREE.Group();
        staticMeshes.forEach((mesh) => assembled.add(mesh));
        const armGroups: THREE.Group[] = [];
        const armJointGroups: THREE.Group[][] = [];
        for (let index = 0; index < 8; index += 1) {
          const angle = index * Math.PI / 4;
          const group = new THREE.Group();
          group.position.set(0.075 * Math.cos(angle), 0.075 * Math.sin(angle), 0);
          group.rotation.z = angle;
          group.userData.armIndex = index;
          const joints: THREE.Group[] = [];
          let parent: THREE.Group = group;
          for (let segment = 0; segment < SOFT_SEGMENTS_PER_ARM; segment += 1) {
            const joint = new THREE.Group();
            parent.add(joint);
            joints.push(joint);
            const link = new THREE.Mesh(
              new THREE.CylinderGeometry(0.012, 0.012, SOFT_SEGMENT_LENGTH, 18, 1),
              new THREE.MeshPhysicalMaterial({
                color: "#28bfae", roughness: 0.34, metalness: 0.08,
                clearcoat: 0.8, emissive: "#06443e",
              }),
            );
            link.rotation.z = -Math.PI / 2;
            link.position.x = SOFT_SEGMENT_LENGTH / 2;
            link.castShadow = true;
            link.receiveShadow = true;
            joint.add(link);
            const jointCap = new THREE.Mesh(
              new THREE.SphereGeometry(0.0125, 12, 10),
              new THREE.MeshStandardMaterial({ color: "#54d9ca", metalness: 0.12, roughness: 0.38 }),
            );
            joint.add(jointCap);
            const next = new THREE.Group();
            next.position.x = SOFT_SEGMENT_LENGTH;
            joint.add(next);
            parent = next;
          }
          assembled.add(group);
          armGroups.push(group);
          armJointGroups.push(joints);
        }
        if (cancelled) return;
        cadRoot.clear();
        cadRoot.add(assembled);
        cadArmGroupsRef.current = armGroups;
        cadArmJointGroupsRef.current = armJointGroups;
        cadRoot.visible = true;
        proceduralRoot.visible = false;
      } catch (error) {
        console.error("CAD mesh load failed; retaining procedural preview.", error);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [apiBase, simulationAvailable]);

  return (
    <div
      className="scene-host"
      ref={hostRef}
      aria-label="CAD-derived octopus model when MuJoCo backend is connected; otherwise procedural preview"
    />
  );
}
