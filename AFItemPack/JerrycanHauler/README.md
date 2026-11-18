# Jerrycan Hauler mod folder

`config.cpp` is a draft written from memory and has not been run in DayZ. This folder is
laid out the way the packed mod expects (`AFItemPack\JerrycanHauler\...`), but the model and
texture files below still have to be made on a Windows PC with DayZ Tools.

## Files still needed here

| File | What it is | Made from |
|---|---|---|
| `JerrycanHauler_g.p3d` | Ground model (lying in the world) | `models/jerrycan_hauler/lowpoly/jerrycan_hauler_15k.glb` |
| `JerrycanHauler_m.p3d`, `JerrycanHauler_f.p3d` | Worn models, fitted and weighted to the male and female character skeletons | same mesh |
| `data/jerrycan_hauler_co.paa`, `_nohq.paa`, `_smdi.paa`, `jerrycan_hauler.rvmat` | Textures and material | PNGs in `models/jerrycan_hauler/lowpoly/textures/` |
| `proxy/AF_Hauler_proxy_jerrycan.p3d`, `_shovel.p3d`, `_weapon.p3d` | Attachment-point proxies placed in the worn and ground models | Object Builder |

## Lines to check in `config.cpp` (marked `CHECK`)

1. `requiredAddons` names.
2. The `+=` slot patches on `CanisterGasoline` and `Shovel`, and their parent classes.
3. The `Shoulder` slot on the pack accepting and showing a long gun.
4. Slot icons and the pick-up/drop sound set names.

## Server side

`server/types_snippet.xml` (repo root) is the loot table entry to paste into the mission's `db/types.xml`.
