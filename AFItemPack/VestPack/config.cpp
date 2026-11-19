// AF Vest Pack: a backpack built like a load-bearing vest (chest and hip pouches, a flat pack
// panel on the back that fits under the Field Cape). It goes in the backpack slot ("Back"), so the vest slot
// stays free. Made to be worn with the Field Cape. See README.md in this folder.

class CfgPatches
{
	class AFItemPack_VestPack
	{
		units[] = {"AF_VestPack"};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Characters", "DZ_Characters_Backpacks"};
	};
};

class CfgVehicles
{
	class Clothing;

	class AF_VestPack: Clothing
	{
		scope = 2;
		displayName = "Field Vest Pack";
		descriptionShort = "A wool and leather load-bearing harness with chest and hip pouches and a flat pack panel on the back that fits under a cape. Carried like a backpack, worn like a vest.";
		model = "\AFItemPack\VestPack\VestPack_g.p3d";
		inventorySlot[] = {"Back"};
		itemInfo[] = {"Clothing", "Back"};
		rotationFlags = 16;
		itemSize[] = {5, 6};
		itemsCargoSize[] = {10, 6}; // 60 slots
		weight = 2200; // grams, empty
		varWetMax = 0.79;
		heatIsolation = 0.5;
		visibilityModifier = 0.9;
		repairableWithKits[] = {5, 2};
		repairCosts[] = {30, 25};
		soundAttType = "Outdoor";
		randomQuantity = 3;
		attachments[] = {"Chemlight", "WalkieTalkie"};
		class ClothingTypes
		{
			male = "\AFItemPack\VestPack\VestPack_m.p3d";
			female = "\AFItemPack\VestPack\VestPack_f.p3d";
		};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 180;
					healthLevels[] =
					{
						{1.0, {"AFItemPack\VestPack\data\vest_pack.rvmat"}},
						{0.7, {"AFItemPack\VestPack\data\vest_pack.rvmat"}},
						{0.5, {"AFItemPack\VestPack\data\vest_pack_damage.rvmat"}},
						{0.3, {"AFItemPack\VestPack\data\vest_pack_damage.rvmat"}},
						{0.0, {"AFItemPack\VestPack\data\vest_pack_destruct.rvmat"}}
					};
				};
			};
		};
		class AnimEvents
		{
			class SoundWeapon
			{
				class pickUpItem
				{
					soundSet = "pickUpBackPack_Metal_SoundSet";
					id = 797;
				};
				class drop
				{
					soundset = "taloonbag_drop_SoundSet";
					id = 898;
				};
			};
		};
	};
};
