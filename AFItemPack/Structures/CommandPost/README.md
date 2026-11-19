# AF Command Post

An enterable desert outpost building, class `Land_AF_CommandPost`. 8 x 14 m, one storey:

- **Command room** in front (about 7.3 x 5.6 m inside): steel entrance door under a corrugated
  awning, six shuttered slit windows, "AF" stencilled on the front wall.
- **Panic room** behind it (6.6 x 6.6 m inside): no windows, no outside door, 0.7 m walls. The
  only way in is the **vault door** in the dividing wall.
- Flat roof with parapet, sandbags and an antenna mast, reached by a **ladder** on the back wall.
- The vault door takes the game's own **code lock** (`DigitalCodeLock`): attached, it shows as
  a keypad on the wall beside the vault and locks that door only. The vault cannot be lock-picked.

First version, built and tested offline in DayZ 1.30. It has not been on a server.

## Files

| File | What it is | Made by |
|---|---|---|
| `AF_CommandPost.p3d` | The model: visual LODs 1-3, shadow, collision, walkable floors, door axes, ladder points, lock mount | `tools/build_commandpost_p3d.py` |
| `model.cfg` | Turns the two doors | hand-written |
| `config.cpp` | The building class and its doors | hand-written |
| `data/af_*.rvmat` | Materials | hand-written |
| `proxy/AF_proxy_codelock.p3d` | Placeholder marking where the code lock is drawn | `tools/build_commandpost_p3d.py` |

There is no source model: every wall, slab and door is generated from the layout numbers at
the top of the build script. Its textures are the game's own (Nasdara plaster, vanilla
concrete and steel), referenced by path, so the mod carries none for it.

## Placing it

Spawn `Land_AF_CommandPost` with DayZ Editor or a server object spawner. The model's origin
is the middle of the footprint **at ground level**, and the foundation reaches 1.2 m below
that, so it can sit on a gentle slope. The entrance faces the object's rear (south at a
rotation of 0).

The rest of the outpost is meant to be vanilla Nasdara pieces placed around it in the Editor:
HESCO walls and corners (`hbarrierwall_*_tk`), the container watchtower
(`mil_containerwatchtower`), desert camo nets, sandbag roadblocks, razor wire, gates.

## Tested offline

`testmission\capture_tour.ps1 -Mission AFPost` places the building and:

- fires rays at it: the front wall, a side wall and the closed vault door stop them, a window
  and the open vault let them through;
- opens both doors by script (both report open);
- walks a character in through the entrance, across the command room, through the vault
  doorway and into the panic room, where the back wall stops him. He stands on the floor
  (0.12 m) the whole way;
- attaches a `DigitalCodeLock` by script: it goes into slot `Att_CodeLock1_Metal`, reports that
  it controls door 2 (the vault), and setting a code locks the vault door and not the
  entrance; releasing it unlocks the door again;
- starts a character up the roof ladder: he climbs to roof height (3.37 m), steps off through
  the opening in the parapet and walks across the roof.

## Known gaps

- **Nobody has used it by hand.** Doors, lock and ladder were all driven by script. Not tried:
  a player's action prompts (open door, enter ladder), attaching a code lock from the hands,
  and typing a code on the keypad.
- **The keypad is on the command-room side only.** Someone shut inside the panic room has no
  keypad to reach; whether the game lets the lock be worked from behind was not tested.
- A code lock needs a battery when a player fits it; the test set the code directly.
- **Plain look.** Flat walls with tiling textures, box sandbags in one colour, a slab for a vault
  door. No wear, decals, wiring or lights, and no furniture (place vanilla props).
- Interiors are not darkened; there are no loot spawn points and no AI navigation paths.
- Checked on Chernarus only; the building has not been placed on Nasdara.
