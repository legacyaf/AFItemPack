// AF Cape: a knee-length wool cape worn in the belt slot ("Hips"), so it can be worn
// together with a backpack, a vest and an armband. It has no attachment slots of its own,
// so nothing can hang from the belt while it is worn. See README.md in this folder.

class CfgPatches
{
	class AFItemPack_Cape
	{
		units[] = {"AF_Cape"};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Characters", "DZ_Characters_Belts"};
	};
};

class CfgVehicles
{
	class Clothing;

	class AF_Cape: Clothing
	{
		scope = 2;
		displayName = "Field Cape";
		descriptionShort = "A heavy wool cape that hangs from the shoulders to the knee, fastened across the chest with a leather cord and a brass clasp. Worn in place of a belt.";
		model = "\AFItemPack\Cape\Cape_g.p3d";
		vehicleClass = "Clothing";
		simulation = "clothing";
		inventorySlot[] = {"Hips"};
		itemInfo[] = {"Clothing", "Hips"};
		rotationFlags = 16;
		itemSize[] = {3, 3};
		weight = 600; // grams
		varWetMax = 1.0;
		heatIsolation = 0.5;
		repairableWithKits[] = {5, 2};
		repairCosts[] = {30, 25};
		soundAttType = "Outdoor";
		class ClothingTypes
		{
			male = "\AFItemPack\Cape\Cape_m.p3d";
			female = "\AFItemPack\Cape\Cape_f.p3d";
		};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 100;
					healthLevels[] =
					{
						{1.0, {"AFItemPack\Cape\data\cape.rvmat"}},
						{0.7, {"AFItemPack\Cape\data\cape.rvmat"}},
						{0.5, {"AFItemPack\Cape\data\cape_damage.rvmat"}},
						{0.3, {"AFItemPack\Cape\data\cape_damage.rvmat"}},
						{0.0, {"AFItemPack\Cape\data\cape_destruct.rvmat"}}
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
					soundSet = "Shirt_pickup_SoundSet";
					id = 797;
				};
				class drop
				{
					soundset = "Shirt_drop_SoundSet";
					id = 898;
				};
			};
		};
	};
};
