---
name: threejs-3d-visualizer
description: Best practices for Three.js 3D rendering, mesh instantiation, procedural building generation, road masks, particle systems, and canvas interaction in Pipeline City.
---

# Three.js 3D Visualizer Skill Guide

## 1. Core Scene Structure in Pipeline City
- **Scene Root**: `web/src/scene/`
- **Camera Management**: `web/src/cameras.ts` (`Cameras.flyTo(lot)`, tween position & target).
- **Picking & Hover**: `web/src/picking.ts` (Raycasting on GPU/mesh bounds).
- **Road Mask & Curbs**: `web/src/scene/road_mask.ts` (Procedural sidewalk curbs and road tiles).
- **Particle Systems**: `web/src/scene/fire.ts`, `web/src/scene/weather.ts` (Fog, rain, smoke particle rendering).

## 2. Performance Guidelines for High Object Counts (500+ Buildings)
- **InstancedMesh**: Group repeated meshes (street tiles, trees, sidewalk segments) into `THREE.InstancedMesh` to keep draw calls < 50.
- **BufferGeometry Disposal**: Explicitly dispose of geometries and materials when refreshing scenes to prevent WebGL memory leaks.
- **Frame Rate Optimization**: Limit dynamic shadow recalculations to moving vehicles; keep building geometry shadows static.

## 3. Aesthetic Standards
- Avoid default browser colors. Use curated HSL/RGB palettes from `web/src/palette.ts`.
- Maintain dark glassmorphic UI overlay styling with smooth micro-interactions.
