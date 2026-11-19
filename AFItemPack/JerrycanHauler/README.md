# Jerrycan Hauler mod folder

Laid out the way the packed mod expects (`AFItemPack\JerrycanHauler\...`). Everything here has
been built and tested offline in DayZ 1.30 (`DayZDiag_x64.exe`, test mission in `testmission/`).
It has not been run on a server.

## Files

| File | What it is | Made by |
|---|---|---|
| `config.cpp` | Item, slots, proxies, script registration | hand-written |
| `model.cfg` | Character skeleton for the worn models (bone list read from the vanilla backpack models) | hand-written |
| `JerrycanHauler_m.p3d`, `_f.p3d`, `_g.p3d` | Worn (male, female) and ground models | `tools/build_hauler_p3d.py` |
| `proxy/AF_Hauler_proxy_*.p3d` | Attachment-point placeholders | `tools/build_hauler_p3d.py` |
| `data/*.paa`, `data/jerrycan_hauler.rvmat`, `_damage.rvmat`, `_destruct.rvmat` | Textures and the pristine, damaged and ruined materials | ImageToPAA from the PNGs; rvmats adapted from the vanilla Alice pack |
| `scripts/4_World/AF_JerrycanHauler.c` | Makes the pack's `Shoulder` (scabbard) slot firearms-only | hand-written |

## Rebuilding

Close DayZ, then run `tools\build.ps1` (add `-PackOnly` after config or script changes only).
It needs DayZ Tools, Blender with the Arma 3 Object Builder add-on, and the `P:` work drive
with `P:\AFItemPack` linked to this repository's `AFItemPack` folder. The PBO is written to
`@AFItemPack\Addons` and signed with `keys\AFItemPack.biprivatekey` (kept out of git; without
it the PBO is left unsigned). `workshop/` holds the Workshop preview picture and description.

All fit numbers (pack height and position, strap lift, attachment points) are named settings
at the top of `tools/build_hauler_p3d.py`.

## What the model build does to the Meshy mesh

- Scales it to 0.75 m and places it on the back (the character faces -Y in Blender).
- Derives the lower LODs from the finished LOD 1 mesh (edge collapse for 2 and 3, vertex
  merging for 4 and 5).
- Mirrors the hip belt to the wearer's side; in the source mesh it loops away from the body.
- Replaces the left shoulder strap with a mirror of the right one, raises both by 5 cm and
  pushes the lower webbing outward so the straps clear the shoulders and ribs.
- Weights the belt to `Pelvis` and everything else to `Spine3`.

## Tested offline

- Pack is worn on the back, shows in hands, on the ground and in the inspect view.
- 10 x 9 cargo.
- Jerrycan, shovel and Mosin attach to the pack, each in its own slot, and are drawn on it.
- A shovel still attaches to the character's own shoulder slot.

## Known gaps

- `_f.p3d` is the same mesh as `_m.p3d`. It was checked on two female characters and fits,
  but it is not separately fitted.
- Visual LODs 1-5 (about 14,700 / 7,300 / 4,600 / 1,500 / 600 triangles) and a first-person
  LOD, generated automatically. LODs 4 and 5 are crude (merged vertices); at the ranges
  where the pack was seen in the offline test (out to 160 m) it reads the same as a vanilla
  pack beside it, but they were never inspected up close in game. No shadow LOD, as in the
  vanilla packs. LOD 1 is heavy for a backpack.
- The damage look comes from the generic vanilla vest damage overlays, not from art made
  for this pack: damaged is a slight dulling, ruined is clearly darker and dirtier.
- The jerrycan slot uses the vanilla gas-canister icon; there is no vanilla jerrycan icon.
- Bulky tops partly swallow the hip belt (seen with the raincoat).
- Long guns share one attachment point, so their height differs by model: rifles such as
  the Mosin, SVD and SKS reach from about head height to the knee; the AKM and M4A1 sit
  shorter. Tried: Mosin, MP-133, AKM, M4A1, SVD, Winchester 70, SKS, IZH-18.
- Everything was checked on standing characters only, not while moving, crouching or prone.

## Gap test line-up

`testmission\capture_tour.ps1` starts the offline mission, which stands eight characters in a
row (two female; T-shirt, jackets, coats and vests; eight different long guns; plus one
damaged and one ruined pack, and one vanilla Alice pack as a control), flies the
debug camera around each, and saves the views to `testmission\captures`.
`testmission\make_sheets.ps1` combines them into one picture per character. The last capture
but six is the inventory screen with the pack empty, which shows the slot icons. The final
six look at the last two characters from 5 m out to 160 m, to check the pack at range.

## Server side

`server/types_snippet.xml` (repo root) is the loot table entry to paste into the mission's `db/types.xml`.
