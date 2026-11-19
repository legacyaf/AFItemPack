# Field Cape mod folder

A knee-length wool cape, class `AF_Cape`, worn in the **belt slot** (`Hips`). It can be worn
together with a backpack, vest and armband; it has no attachment slots, so nothing hangs from
the belt while it is worn. Built and tested offline in DayZ 1.30. It has not been run on a
server.

## Files

| File | What it is | Made by |
|---|---|---|
| `config.cpp` | The item | hand-written |
| `model.cfg` | Character skeleton for the worn models (same as the hauler's) | copied |
| `Cape_m.p3d`, `_f.p3d`, `_g.p3d` | Worn (male, female) and ground models | `tools/build_cape_p3d.py` |
| `data/cape_*.png`, `.paa` | Colour, normal and specular textures | `tools/build_cape_p3d.py`, then ImageToPAA |
| `data/cape.rvmat`, `_damage.rvmat`, `_destruct.rvmat` | Pristine, damaged and ruined materials | adapted from the hauler's |

There is no source model: the cloth, the shoulder cords, the clasp, the folded ground bundle
and the textures are all generated from the numbered settings at the top of
`tools/build_cape_p3d.py`. Rebuild with `tools\build.ps1`.

## How it is fitted

- The body shape was measured in game (the `[AFMeasure]` lines printed by the `AFCape` test
  mission) and the cloth is placed 6-10 cm behind it, which leaves room for the Field Vest Pack's back
  panel underneath (the cape's shape is shared with that build in `tools/p3d_common.py`).
- The cloth follows the upper back (`Spine3`) at the shoulders, fades to the hips (`Pelvis`)
  by the waist, and below the seat is shared with the thighs (`LeftUpLeg`, `RightUpLeg`, up
  to 60%, left half to the left thigh). An earlier even mix of upper back and hips stood well
  but moved like a board: it tented when crouching and hovered over the legs when prone.
- Visual LODs 1-7 (about 5,600 / 2,200 / 800 / 370 / 110 / 40 / 16 triangles) and a
  first-person LOD. LODs 5-7 are flat sheets without folds, cords or clasp, for far distances.

## Tested offline

`testmission\capture_tour.ps1 -Mission AFCape` stands eight characters in a row and
photographs each from four sides, then the ground model and the inventory screen.

- Goes into the belt slot on male and female characters.
- Hangs outside the body over a T-shirt, M65 jacket, Gorka jacket with plate carrier, wool
  coat and hunting jacket.
- Worn with the Field Vest Pack: the pack is entirely under the cape. Worn with an Alice
  pack: the pack passes through the cape and the cape shows below it.
- Damaged and ruined looks.

## Known gaps

- The cape is skinned, not simulated cloth. Checked standing, crouched, prone, jogging and
  sprinting (`capture_tour.ps1 -Mission AFMove`): it drapes over the back and legs in all of
  them, but the hem corners stick out as flat tabs when a thigh swings far (sprint, crouch),
  a heel can pass through the hem mid-stride, and when prone the cloth hinges at the seat
  instead of lying smoothly. Sitting, swimming, ladders and vehicles were not looked at.
- Any backpack other than the Field Vest Pack passes through the upper part of the cape.
- `_f.p3d` is the same mesh as `_m.p3d`.
- Never looked at from far away (lower LODs) or in first person.
- The ground model was only seen in tall grass and as the inventory icon.
