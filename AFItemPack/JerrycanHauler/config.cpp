// Jerrycan Hauler backpack. Tested offline in DayZ 1.30; see README.md in this folder.
// The CHECK notes below date from the first draft. Since verified against vanilla 1.30:
// requiredAddons names, the CanisterGasoline/Shovel parent classes and "+=" patches,
// both sound set names, and a rifle attaching to "Shoulder". Still open: the two
// placeholder slot icons.

class CfgPatches
{
	class AFItemPack_JerrycanHauler
	{
		units[] = {"AF_JerrycanHauler"};
		weapons[] = {};
		requiredVersion = 0.1;
		// CHECK: these must be the addons that define Clothing, Shovel and CanisterGasoline,
		// so this config loads after them.
		requiredAddons[] = {"DZ_Data", "DZ_Scripts","DZ_Characters", "DZ_Characters_Backpacks", "DZ_Gear_Tools", "DZ_Vehicles_Parts"};
	};
};

// Registers the script folder (scripts/4_World holds the pack's attachment rule).
class CfgMods
{
	class AFItemPack
	{
		dir = "AFItemPack";
		name = "AF Item Pack";
		type = "mod";
		dependencies[] = {"World"};
		class defs
		{
			class worldScriptModule
			{
				value = "";
				files[] = {"AFItemPack/JerrycanHauler/scripts/4_World"};
			};
		};
	};
};

// New attachment slots that exist only on this backpack.
class CfgSlots
{
	class Slot_AF_Hauler_Jerrycan
	{
		name = "AF_Hauler_Jerrycan";
		displayName = "Jerrycan";
		ghostIcon = "set:dayz_inventory image:missing"; // CHECK: placeholder icon
	};
	class Slot_AF_Hauler_Shovel
	{
		name = "AF_Hauler_Shovel";
		displayName = "Shovel";
		ghostIcon = "set:dayz_inventory image:missing"; // CHECK: placeholder icon
	};
};

class CfgVehicles
{
	class Clothing;
	class Inventory_Base;
	class Bottle_Base;

	class AF_JerrycanHauler: Clothing
	{
		scope = 2;
		displayName = "Jerrycan Hauler";
		descriptionShort = "A welded rebar pack frame built to carry a jerrycan across the wastes. Has mounts for a shovel and a long gun.";
		model = "\AFItemPack\JerrycanHauler\JerrycanHauler_g.p3d";
		inventorySlot[] = {"Back"};
		itemInfo[] = {"Clothing", "Back"};
		rotationFlags = 16;
		itemSize[] = {8, 9};
		itemsCargoSize[] = {10, 9}; // 90 slots
		weight = 4500; // grams, empty
		varWetMax = 0.49;
		heatIsolation = 0.3;
		visibilityModifier = 0.8;
		repairableWithKits[] = {5, 2};
		repairCosts[] = {30, 25};
		soundAttType = "Military";
		randomQuantity = 4;
		// "Shoulder" is the vanilla slot every long gun already fits, so no weapon needs patching.
		// CHECK in game: that a rifle attaches here and shows at the scabbard proxy.
		attachments[] = {"AF_Hauler_Jerrycan", "AF_Hauler_Shovel", "Shoulder", "Chemlight", "WalkieTalkie"};
		class ClothingTypes
		{
			male = "\AFItemPack\JerrycanHauler\JerrycanHauler_m.p3d";
			female = "\AFItemPack\JerrycanHauler\JerrycanHauler_f.p3d";
		};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					// Damage rvmats can be added per level once the materials exist.
					healthLevels[] = {{1.0, {}}, {0.7, {}}, {0.5, {}}, {0.3, {}}, {0.0, {}}};
				};
			};
		};
		class AnimEvents
		{
			class SoundWeapon
			{
				class pickUpItem
				{
					soundSet = "pickUpBackPack_Metal_SoundSet"; // CHECK: sound set name
					id = 797;
				};
				class drop
				{
					soundset = "taloonbag_drop_SoundSet"; // CHECK: sound set name
					id = 898;
				};
			};
		};
	};

	// Let the vanilla jerrycan and shovel go into the new slots.
	// CHECK: "+=" appends to the vanilla slot list. If the item stops fitting its
	// vanilla slots (or does not fit the pack), replace the line with the full vanilla
	// list plus the new slot, e.g. inventorySlot[] = {"<vanilla slots>", "AF_Hauler_Shovel"};
	// CHECK: the parent classes (Bottle_Base, Inventory_Base) must match vanilla.
	class CanisterGasoline: Bottle_Base
	{
		inventorySlot[] += {"AF_Hauler_Jerrycan"};
	};
	class Shovel: Inventory_Base
	{
		// The shovel also fits "Shoulder", which the pack uses as its scabbard. The script
		// in scripts/4_World keeps non-firearms out of that slot on the pack.
		inventorySlot[] += {"AF_Hauler_Shovel"};
	};
};

// Attachment points. Each class is "Proxy" + the file name of a proxy p3d placed in
// the backpack model in Object Builder; the attached item is drawn where that proxy sits.
class CfgNonAIVehicles
{
	class ProxyAttachment;
	class ProxyAF_Hauler_proxy_jerrycan: ProxyAttachment
	{
		scope = 2;
		inventorySlot[] = {"AF_Hauler_Jerrycan"};
		model = "\AFItemPack\JerrycanHauler\proxy\AF_Hauler_proxy_jerrycan.p3d";
	};
	class ProxyAF_Hauler_proxy_shovel: ProxyAttachment
	{
		scope = 2;
		inventorySlot[] = {"AF_Hauler_Shovel"};
		model = "\AFItemPack\JerrycanHauler\proxy\AF_Hauler_proxy_shovel.p3d";
	};
	class ProxyAF_Hauler_proxy_weapon: ProxyAttachment
	{
		scope = 2;
		inventorySlot[] = {"Shoulder"};
		model = "\AFItemPack\JerrycanHauler\proxy\AF_Hauler_proxy_weapon.p3d";
	};
};
