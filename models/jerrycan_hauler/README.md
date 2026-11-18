# Jerrycan Hauler

Desert wasteland backpack rig for DayZ, built from `concepts/jerrycan_v2.png`.

- Meshy image-to-3d task: `01a1f104-b2bb-7730-a806-bec40f8c920b` (source image task `01a1f102-4c52-717b-be0a-67acd6ae1398`)
- Raw export: about 3.76 million triangles, 4k PBR textures. GLB (129 MB) and FBX (183 MB) are not committed;
  re-download them from the Meshy account with the task ID above.
- Planned in-game setup: Back slot, 10x9 cargo (90 slots), attachment slots for a jerrycan, a shovel and one long gun.

## Low-poly version (`lowpoly/`)

- Meshy remesh task: `01a1f10b-a95f-77fd-95d6-d55145369934`, 14,704 triangles.
- `jerrycan_hauler_15k.glb` has the textures embedded and imports directly into Blender.
- `textures/` holds the 4k base colour, normal, roughness and metallic maps as PNG, for conversion to PAA.
- The model is not at real-world scale (about 1.9 units tall); scale it when fitting it to the DayZ character.
- An FBX of the same mesh is available from the Meshy task but is not committed.
