# Field Vest Pack mod folder

A backpack built like a load-bearing vest, class `AF_VestPack`: chest and hip pouches in
front and a flat pack panel on the back. It goes in the **backpack slot** (`Back`) with
60 cargo slots (10 x 6), so the vest slot stays free. Made to be worn with the Field Cape.
Built and tested offline in DayZ 1.30. It has not been run on a server.

## Files

| File | What it is | Made by |
|---|---|---|
| `config.cpp` | The item | hand-written |
| `model.cfg` | Character skeleton for the worn models (same as the hauler's) | copied |
| `VestPack_m.p3d`, `_f.p3d`, `_g.p3d` | Worn (male, female) and ground models | `tools/build_vestpack_p3d.py` |
| `data/vest_pack_*.png`, `.paa` | Colour, normal and specular textures | taken from the GLB by the build script, then ImageToPAA |
| `data/vest_pack.rvmat`, `_damage.rvmat`, `_destruct.rvmat` | Pristine, damaged and ruined materials | adapted from the hauler's |

The source model is `models/vest_pack/lowpoly/vest_pack_12k.glb` (Meshy, from the pictures in
`concepts/vest_pack`). Rebuild with `tools\build.ps1`. The fit numbers are named settings at
the top of the build script.

## What the build does to the Meshy mesh

- Scales it to 0.78 x 0.96 x 0.75 (width, depth, height) and places the inside of its back
  panel just behind the shoulder blades and its straps on the shoulders, using the body
  measurements in `tools/body_measurements.txt`.
- Narrows the hip pouches so they sit in front of the hanging arms.
- Removes the bedroll and squeezes the pack body flat (22 cm down to about 3 cm) so the whole
  pack sits **under the Field Cape with at least 6 mm to spare**. The limit is the cape's own
  shape (`tools/p3d_common.py`), and `tools/check_cape_clearance.py` tests every LOD of the
  pack against every LOD of the cape for intersecting triangles; `build.ps1` fails if there are any.
- Weights the back of the pack exactly like the cape (`p3d.cape_weights`) so the two move
  together; the front follows `Spine3` at the chest and `Pelvis` at
  the hips.
- Derives visual LODs 2-8 (about 5,600 / 2,800 / 1,100 / 440 / 220 / 80 / 30 triangles) from
  LOD 1 (11,200). LODs 6-8 are only a silhouette for far distances.

## Tested offline

`testmission\capture_tour.ps1 -Mission AFVest` stands eight characters in a row and
photographs each from four sides.

- Goes into the backpack slot on male and female characters.
- Sits outside the body over a T-shirt, M65 jacket, hunting jacket, and a Gorka jacket with
  a plate carrier.
- Worn with the cape: the cape's cord and clasp show in the gap at the chest, and the pack is
  entirely under the cape from every side.
- Damaged and ruined looks.

## Known gaps

- Checked standing, crouched, prone, jogging and sprinting with the cape on
  (`capture_tour.ps1 -Mission AFMove`): the pack stayed under the cape in every picture.
  That is judged by eye from four sides per pose; the triangle test only covers the rest pose.
  When crouched the hip pouches press into the thighs.
- The hands of a standing character touch the outer hip pouches.
- The concept's bedroll is gone and the back pack is a flat panel; the 60 slots are carried
  visually by the front pouches.
- `_f.p3d` is the same mesh as `_m.p3d`.
- LODs 4 and up are crude (merged vertices). The pack is still drawn in the offline distance
  shots (out to 160 m), but the low LODs were never inspected up close in game; neither was
  first person or the ground model up close.
