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
  mission) and the cloth is placed 3-5 cm outside it.
- The cloth follows the upper back (`Spine3`) at the shoulders and the hips (`Pelvis`) at the
  hem, mixed evenly in between, so it hangs in one curve when the chest turns or leans.
- Visual LODs 1-4 (about 5,400 / 2,100 / 800 / 350 triangles) and a first-person LOD.

## Tested offline

`testmission\capture_tour.ps1 -Mission AFCape` stands eight characters in a row and
photographs each from four sides, then the ground model and the inventory screen.

- Goes into the belt slot on male and female characters.
- Hangs outside the body over a T-shirt, M65 jacket, Gorka jacket with plate carrier, wool
  coat and hunting jacket.
- Worn with an Alice pack: the pack sits over the cape and the cape shows below it.
- Damaged and ruined looks.

## Known gaps

- Checked on standing characters only. The cape is not simulated cloth: it will pass through
  the legs when crouching or sitting and through the ground when prone.
- A backpack passes through the upper part of the cape.
- `_f.p3d` is the same mesh as `_m.p3d`.
- Never looked at from far away (lower LODs) or in first person.
- The ground model was only seen in tall grass and as the inventory icon.
