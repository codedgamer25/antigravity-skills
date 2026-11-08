# Web 3D Optimization Strategies

Goal targets for real-time web: **<50k triangles**, textures **≤1024px**, GLB **<1–5 MB**, **<2s** load.

## 1. Geometry

| Technique | How | Win |
|---|---|---|
| Draco compression | `export_draco_mesh_compression_enable=True` | 60–90% geometry size |
| Decimate | `DECIMATE` modifier, `ratio=0.3` | fewer tris |
| Merge by distance | `bpy.ops.mesh.merge(type='DISTANCE')` | removes dup verts |
| Triangulate | `quads_convert_to_tris()` | engine compatibility |
| Remove orphans | `bpy.ops.outliner.orphans_purge()` (or `bpy.data.orphans_purge()`) | drops unused data |

Order: cleanup → decimate → export. Always `export_apply=True` so modifiers bake in.

## 2. Textures (usually the biggest cost)

- Prefer **WebP** (`export_image_format='WEBP'`) → smallest; JPEG next; PNG only when alpha/quality demands.
- Downscale: 4k→1k or 512 for most assets.
- Atlas multiple materials into one texture (Smart UV Project) to cut draw calls.
- Bake complex node shaders to a single texture (COMBINED bake) so they survive export.

## 3. Materials

- Use **Principled BSDF** only — custom shader nodes don't export to glTF.
- Supported channels: Base Color, Metallic, Roughness, Normal, Emission, Alpha.
- Fewer unique materials = fewer draw calls.

## 4. Draw calls & scene structure

- Merge static meshes that share a material (`Ctrl+J` / `bpy.ops.object.join()`).
- Use GPU instancing on the web side for repeated objects rather than duplicating geometry.

## 5. LODs

Generate `LOD0/1/2` at 75/50/25% (see `scripts/generate_lods.py`); swap by camera distance on the web side (e.g. three.js `LOD`).

## 6. Measure

- File size: inspect the `.glb` on disk.
- Triangle/draw-call budget: glTF viewer stats, or three.js `renderer.info`.
- Validate: https://github.khronos.org/glTF-Validator/ and https://gltf-viewer.donmccurdy.com/

## Decision shortcut

1. Geometry too big? → Draco + Decimate.
2. File still big? → textures: WebP + downscale.
3. Laggy in browser? → fewer draw calls (join/atlas) + LODs.
