// AF Command Post: an enterable desert outpost building. Command room in front, a large
// windowless panic room behind a vault door. Place it with DayZ Editor or a server object
// spawner as Land_AF_CommandPost. See README.md in this folder.

class CfgPatches
{
	class AFItemPack_CommandPost
	{
		units[] = {"Land_AF_CommandPost"};
		weapons[] = {};
		requiredVersion = 0.1;
		// Its walls, concrete and steel use textures from the game's own structure data.
		requiredAddons[] = {"DZ_Data", "DZ_Structures_Military", "DZ_Structures_Nasdara_Military"};
	};
};

class CfgVehicles
{
	class HouseNoDestruct;

	class Land_AF_CommandPost: HouseNoDestruct
	{
		scope = 2;
		displayName = "AF Command Post";
		model = "\AFItemPack\Structures\CommandPost\AF_CommandPost.p3d";
		class Doors
		{
			class Doors1 // entrance
			{
				displayName = "door 1";
				component = "Doors1";
				soundPos = "doors1_action";
				animPeriod = 1;
				initPhase = 0;
				initOpened = 0;
				soundOpen = "doorMetalSmallOpen";
				soundClose = "doorMetalSmallClose";
				soundLocked = "doorMetalSmallRattle";
				soundOpenABit = "doorMetalSmallOpenABit";
			};
			class Doors2 // vault door to the panic room
			{
				displayName = "door 2";
				component = "Doors2";
				soundPos = "doors2_action";
				animPeriod = 2.5;
				initPhase = 0;
				initOpened = 0;
				soundOpen = "doorHeavyMetalBunkerOpen";
				soundClose = "doorHeavyMetalBunkerClose";
				soundLocked = "doorHeavyMetalBunkerRattle";
				soundOpenABit = "doorHeavyMetalBunkerOpenABit";
				// The vault takes the game's own code lock (DigitalCodeLock), the same way the
				// rebuildable Nasdara houses do: the lock goes in this slot and locks this door.
				relatedInventorySlots[] = {"Att_CodeLock1_Metal"};
				lockCompatibilityBitMask = 0; // no lock picks on the vault
			};
		};
		// The slot the code lock attaches to, and how it is listed when looking at the building.
		attachments[] = {"Att_CodeLock1_Metal"};
		class GUIInventoryAttachmentsProps
		{
			headerDisplayName = "AF Command Post";
			class VaultDoor
			{
				name = "Vault door";
				description = "";
				attachmentSlots[] = {"Att_CodeLock1_Metal"};
				icon = "set:dayz_inventory_additional image:door_metal";
				selection = "doors2";
			};
		};
		// An empty construction block: the code lock only works on buildings that have a
		// construction component (see CodeLockComponent.HandleHierarchyRootLock).
		class Construction
		{
		};
	};
};

// Where an attached code lock is drawn: the class is "Proxy" + the file name of the placeholder
// model placed on the wall beside the vault door.
class CfgNonAIVehicles
{
	class ProxyAttachment;
	class ProxyAF_proxy_codelock: ProxyAttachment
	{
		scope = 2;
		inventorySlot[] = {"Att_CodeLock1_Metal"};
		model = "\AFItemPack\Structures\CommandPost\proxy\AF_proxy_codelock.p3d";
	};
};
