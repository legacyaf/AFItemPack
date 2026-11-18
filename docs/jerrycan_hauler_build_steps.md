# Jerrycan Hauler: from Meshy model to a working DayZ item

These steps were written from memory of the DayZ modding workflow and have not been run
against this model. Menu names and buttons may differ slightly between tool versions.
Do the parts in order; each part ends with a check so you know it worked before moving on.

Expect the first pass to take a few evenings. Part 4 (fitting and weighting) is the hard one.

---

## Part 1 - Install the tools (once)

1. **DayZ Tools**: Steam > Library > change the filter to include *Tools* > install *DayZ Tools*.
2. **Blender** (free, blender.org). Any recent version.
3. **Arma 3 Object Builder add-on for Blender** (by MrClock, on GitHub and Blender Extensions).
   It lets Blender import and export `.p3d` files, which is the model format DayZ uses.
   Install it in Blender under Edit > Preferences > Add-ons / Get Extensions.
4. **Git** or just download this repository as a ZIP from GitHub (Code > Download ZIP).

**Check:** DayZ Tools opens and shows its launcher with buttons such as Object Builder,
Addon Builder, TexView and Workbench.

## Part 2 - Set up the work drive

DayZ Tools uses a virtual `P:` drive as the root of all mod files.

1. In the DayZ Tools launcher open **Settings** and set the *Path to the Project Drive*
   (any empty folder, for example `C:\DayZWorkdrive`).
2. In the launcher choose **Tools > Extract Game Data**. This unpacks the vanilla game files to
   `P:\DZ`. It takes a while and needs roughly 20 GB.
3. Click **Mount P drive** (Workdrive). You should now see `P:` in File Explorer.
4. Copy the `AFItemPack` folder from this repository to `P:\`, so that this file exists:
   `P:\AFItemPack\JerrycanHauler\config.cpp`

**Check:** `P:\DZ\characters\backpacks` exists and contains vanilla backpack files.

## Part 3 - Textures

DayZ wants `.paa` textures with specific name endings. The source PNGs are in
`models/jerrycan_hauler/lowpoly/textures/`.

1. Steps 1-3 are already done: `AFItemPack/JerrycanHauler/data/` in this repository holds
   `jerrycan_hauler_co.png` (colour), `jerrycan_hauler_nohq.png` (normal map) and
   `jerrycan_hauler_smdi.png` (shininess, built from the metallic and roughness maps),
   all resized to 2048 x 2048. They arrive on `P:` when you copy the folder in Part 2.
4. Convert each PNG to PAA: in the DayZ Tools launcher open **ImageToPAA** (or open the PNG in
   **TexView 2** and File > Save As `.paa`). The name endings (`_co`, `_nohq`, `_smdi`) tell
   the converter which compression to use, so keep them.
5. Make the material file. Copy any `.rvmat` from `P:\DZ\characters\backpacks\data\` into
   `P:\AFItemPack\JerrycanHauler\data\` and rename it `jerrycan_hauler.rvmat`. Open it in
   Notepad and change the texture paths in the `Stage` blocks that end in `_nohq.paa` and
   `_smdi.paa` to:
   - `AFItemPack\JerrycanHauler\data\jerrycan_hauler_nohq.paa`
   - `AFItemPack\JerrycanHauler\data\jerrycan_hauler_smdi.paa`

   Leave the other stages as they are.

**Check:** the `data` folder holds three `.paa` files and one `.rvmat`.

## Part 4 - Fit the model to the character in Blender

You need a reference character to fit the pack to. Bohemia publishes unbinarized sample
models in the **DayZ-Samples** repository on GitHub (BohemiaInteractive/DayZ-Samples).
Download it and look for the character / clothing sample folder; it contains a sample
`.p3d` with the character skeleton and a `model.cfg`. Vanilla game models in `P:\DZ` are
binarized and will not open, which is why the samples are needed.

1. In Blender: File > Import > **Arma 3 P3D** and open the sample character or clothing
   model. This is your size and position reference.
2. File > Import > **glTF 2.0** and open
   `models/jerrycan_hauler/lowpoly/jerrycan_hauler_15k.glb`.
3. Scale and move the pack so it sits on the character's back:
   - total height roughly **0.75 m** (bedroll top just above shoulder height, hip belt at the hips);
   - shoulder straps over the shoulders, hip belt around the waist;
   - the frame a couple of centimetres off the back so it does not cut into jackets.
   Then apply the transform: Object > Apply > All Transforms.
4. The model is one fused mesh. In Edit Mode, clean up anything that pokes through the
   body (strap ends, belt). Select and move or delete as needed.
5. **Weighting** (what makes it follow the body). Using the sample's bone names, create
   vertex groups on the pack with exactly those names and assign:
   - the whole pack: weight 1.0 to `Spine3` (upper back);
   - the hip belt and the two hip pouches: weight 1.0 to `Pelvis` instead;
   - the lower third of the shoulder straps: blend between `Spine3` and `Spine1`.

   A simple first version with everything on `Spine3` is fine to get in game; refine after.
6. In the add-on's object properties, mark the object as a LOD with resolution **1**
   (the visual LOD). Set the face texture to
   `AFItemPack\JerrycanHauler\data\jerrycan_hauler_co.paa` and the material to
   `AFItemPack\JerrycanHauler\data\jerrycan_hauler.rvmat` in the add-on's material panel.
7. File > Export > **Arma 3 P3D** to
   `P:\AFItemPack\JerrycanHauler\JerrycanHauler_m.p3d`.
8. Save a second copy as `JerrycanHauler_f.p3d`. Re-fit it to the female sample if there is
   one; otherwise use the same mesh for a first test.
9. Copy the sample's `model.cfg` next to the p3d files and, at the bottom in `CfgModels`,
   add an entry for each of your worn models named exactly like the files without the
   extension (`JerrycanHauler_m`, `JerrycanHauler_f`), inheriting from the same parent the
   sample's clothing entry uses. Without this the pack will not follow the skeleton.

**Check:** open `JerrycanHauler_m.p3d` in **Object Builder** (DayZ Tools). It should show the
textured pack, and Window > Named Selections should list the bone names you weighted.

## Part 5 - Ground model

This is what lies on the floor before it is picked up. It has no skeleton.

1. In Blender, take the same mesh, remove the vertex groups, and lay it flat on its back
   at the world origin.
2. Mark it as LOD resolution **1** with the same texture and material.
3. Add a simple box around it as a second LOD of type **Geometry** (this is its collision).
   In the add-on, set a mass on it of about 4.5 kg and name the box selection `Component01`.
4. Duplicate the box as LODs of type **View Geometry** and **Fire Geometry**.
5. Export to `P:\AFItemPack\JerrycanHauler\JerrycanHauler_g.p3d`.

**Check:** opens in Object Builder with three or four LODs listed.

## Part 6 - Attachment points (proxies)

These make the jerrycan, shovel and rifle appear on the pack. Skip this part for the very
first test if you want to see the pack in game sooner; the slots still work, the items
just will not be drawn.

1. Make three tiny placeholder models. In Object Builder: File > New, create any small
   triangle, and save it three times into `P:\AFItemPack\JerrycanHauler\proxy\` as
   `AF_Hauler_proxy_jerrycan.p3d`, `AF_Hauler_proxy_shovel.p3d`, `AF_Hauler_proxy_weapon.p3d`.
   The names must match `config.cpp` exactly.
2. Open `JerrycanHauler_m.p3d` in Object Builder. In the visual LOD choose
   **Create > Proxy** and enter the path without extension:
   `\AFItemPack\JerrycanHauler\proxy\AF_Hauler_proxy_jerrycan`
3. Move and rotate the proxy triangle into the cradle. Add it to the same bone selection
   as the frame (`Spine3`) so it moves with the pack.
4. Repeat for the shovel (left side loops) and the weapon (inside the scabbard).
5. Do the same in `_f` and `_g`.

Proxy orientation is trial and error: place it, test in game, rotate, repeat.

## Part 7 - Pack the mod

1. DayZ Tools launcher > **Addon Builder**.
2. Source directory: `P:\AFItemPack`. Destination: a new folder such as
   `C:\DayZMods\@AFItemPack\Addons`.
3. Tick **Binarize**. In Options, set the addon prefix to `AFItemPack` and make sure the
   list of files to copy directly includes `*.paa;*.rvmat;*.cfg;*.xml`.
4. Click **Pack**. You should get `AFItemPack.pbo` in the Addons folder.

If packing fails with a config error, send me the error text - that is where the lines
marked `CHECK` in `config.cpp` will show up.

## Part 8 - Test locally before touching the live server

1. Start DayZ from the DayZ launcher with the mod loaded: Parameters > All Parameters >
   Additional Parameters, or run `DayZDiag_x64.exe` with
   `-mod=C:\DayZMods\@AFItemPack` in an offline mission.
2. Spawn the pack. The simplest way is in your test mission's `init.c`, inside
   `StartingEquipSetup`, add:

   ```
   player.GetInventory().CreateInInventory("AF_JerrycanHauler");
   ```

3. Check, in this order:
   - the pack appears on the character and follows the body when moving;
   - the inventory shows a 10 x 9 grid;
   - a jerrycan, a shovel and a rifle each attach to the pack;
   - the jerrycan and shovel still fit their normal vanilla places (for example a shovel
     on the shoulder).

Tell me which of these fail and what you see; each one maps to a specific line in `config.cpp`.

## Part 9 - Put it on the server

1. **Sign the mod**: DayZ Tools > DS Utils. Create a key pair with your name, then sign
   `AFItemPack.pbo`. Copy the `.bikey` file into `@AFItemPack\Keys\`.
2. Upload the `@AFItemPack` folder to the server root, copy the `.bikey` into the server's
   `keys` folder, and add `@AFItemPack` to the server's `-mod=` start parameter.
3. Paste `server/types_snippet.xml` from this repository inside `<types>` in the mission's
   `db\types.xml` so the pack spawns as loot.
4. Players need the same mod. The usual route is publishing it to the Steam Workshop with
   DayZ Tools > Publisher, then adding it to the server's mod list.
