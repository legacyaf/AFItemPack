// Offline test mission for the Jerrycan Hauler. Runs only in DayZDiag_x64.exe on this PC;
// it never connects to a server. Start it with testmission\run_test.bat.

void SpawnNear(vector origin, string type, float dx, float dz)
{
	vector pos = origin;
	pos[0] = pos[0] + dx;
	pos[2] = pos[2] + dz;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	Object obj = GetGame().CreateObjectEx(type, pos, ECE_PLACE_ON_SURFACE);
	if (!obj)
		Print("[AFTest] FAILED to spawn " + type);
	else
		Print("[AFTest] spawned " + type);
}

void AttachTo(EntityAI parent, string type)
{
	// Create the item in the world, then let the inventory system pick a free attachment
	// slot. Unlike CreateAttachment, this runs the same script checks as a player's drag.
	EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, parent.GetPosition(), ECE_PLACE_ON_SURFACE));
	if (!item)
	{
		Print("[AFTest] FAILED to create " + type);
		return;
	}
	InventoryLocation loc = new InventoryLocation;
	if (!parent.GetInventory().FindFreeLocationFor(item, FindInventoryLocationType.ATTACHMENT, loc))
	{
		Print("[AFTest] FAILED to attach " + type + " to its target: no free slot accepts it");
		return;
	}
	parent.LocalTakeEntityAsAttachmentEx(item, loc.GetSlot());
	item.GetInventory().GetCurrentInventoryLocation(loc);
	if (loc.GetType() == InventoryLocationType.ATTACHMENT)
		Print("[AFTest] attached " + type + " to its target in slot " + InventorySlots.GetSlotName(loc.GetSlot()));
	else
		Print("[AFTest] FAILED to attach " + type + " to its target: it stayed on the ground");
}

void DumpSlots(EntityAI pack)
{
	int count = pack.GetInventory().GetAttachmentSlotsCount();
	for (int i = 0; i < count; i++)
	{
		int id = pack.GetInventory().GetAttachmentSlotId(i);
		Print("[AFTest] pack slot " + i.ToString() + ": " + InventorySlots.GetSlotName(id) + " (id " + id.ToString() + ")");
	}
	TStringArray slots = new TStringArray;
	GetGame().ConfigGetTextArray("CfgWeapons Mosin9130 inventorySlot", slots);
	for (int j = 0; j < slots.Count(); j++)
		Print("[AFTest] Mosin9130 fits slot: " + slots.Get(j) + " (id " + InventorySlots.GetSlotIdFromString(slots.Get(j)).ToString() + ")");
	slots.Clear();
	GetGame().ConfigGetTextArray("CfgVehicles Shovel inventorySlot", slots);
	for (int k = 0; k < slots.Count(); k++)
		Print("[AFTest] Shovel fits slot: " + slots.Get(k));
}

// Where each mannequin stands and what it is, for the camera tour in CustomMission.
ref array<vector> g_AFDummyPos = new array<vector>;
ref array<string> g_AFDummyName = new array<string>;

// Gap tests: a standing character wearing the pack over the given clothes, with a jerrycan,
// a shovel and the given long gun on the pack. They stand in a row 6 m north of the player,
// 3 m apart, number 1 at the west end, facing south toward the player.
// packHealth is the pack's condition from 1.0 (pristine) down to 0.0 (ruined).
void Mannequin(int number, vector origin, string body, TStringArray clothes, string gun, float packHealth = 1.0, string packType = "AF_JerrycanHauler")
{
	vector pos = origin;
	pos[0] = pos[0] + (number - 4.5) * 3.0;
	pos[2] = pos[2] + 6;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	PlayerBase dummy = PlayerBase.Cast(GetGame().CreatePlayer(NULL, body, pos, 0, "NONE"));
	if (!dummy)
	{
		Print("[AFTest] mannequin " + number.ToString() + ": FAILED to create " + body);
		return;
	}
	dummy.SetOrientation("180 0 0");
	string wearing = "";
	foreach (string item : clothes)
	{
		if (dummy.GetInventory().CreateInInventory(item))
			wearing = wearing + item + " ";
		else
			Print("[AFTest] mannequin " + number.ToString() + ": FAILED to create " + item);
	}
	dummy.GetInventory().CreateInInventory("CargoPants_Black");
	dummy.GetInventory().CreateInInventory("AthleticShoes_Black");
	EntityAI pack = dummy.GetInventory().CreateInInventory(packType);
	if (!pack)
	{
		Print("[AFTest] mannequin " + number.ToString() + ": FAILED to put the pack on");
		return;
	}
	Print("[AFTest] mannequin " + number.ToString() + ": " + body + " wearing " + wearing + "with " + gun);
	if (packHealth < 1.0)
	{
		pack.SetHealth01("", "", packHealth);
		Print("[AFTest] mannequin " + number.ToString() + ": pack health set to " + pack.GetHealth01("", "").ToString() + ", level " + pack.GetHealthLevel().ToString());
	}
	if (packType == "AF_JerrycanHauler")
	{
		AttachTo(pack, "CanisterGasoline");
		AttachTo(pack, "Shovel");
		AttachTo(pack, gun);
	}
	g_AFDummyPos.Insert(pos);
	g_AFDummyName.Insert(number.ToString());
}

void main()
{
	// Midday, clear weather, so the model is easy to see.
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Weather weather = GetGame().GetWeather();
	weather.GetOvercast().Set(0, 0, 0);
	weather.GetRain().Set(0, 0, 0);
	weather.GetFog().Set(0, 0, 0);

	// North-west airfield runway: flat and open.
	vector pos = "4660 0 10330";
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);

	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", pos, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);

	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");

	// Check 1: the pack is worn on the back.
	EntityAI pack = player.GetInventory().CreateInInventory("AF_JerrycanHauler");
	if (!pack)
		Print("[AFTest] FAILED to create AF_JerrycanHauler on the player");
	else
	{
		Print("[AFTest] AF_JerrycanHauler created on the player");
		// Check 3: attach one of each item straight onto the worn pack.
		// The player's own pack is left empty so the inventory screen shows the slot icons;
		// attaching is tested on the mannequins.
		DumpSlots(pack);
		// Check 4: a second shovel must still go on the character itself (vanilla slots).
		Print("[AFTest] now attaching a second shovel to the character");
		AttachTo(player, "Shovel");
	}

	// Check 2: a second pack on the ground, to see the ground model.
	SpawnNear(pos, "AF_JerrycanHauler", 2, 2);

	// Checks 3 and 4: items to try in the pack's slots and in their normal vanilla places.
	SpawnNear(pos, "CanisterGasoline", 1, 3);
	SpawnNear(pos, "Shovel", 0, 3);
	SpawnNear(pos, "Mosin9130", -1, 3);
	SpawnNear(pos, "Shovel", -2, 3);
	// Gap tests (see Mannequin above). Number 1 is at the west end of the row, 8 at the east end.
	Mannequin(1, pos, "SurvivorF_Eva", {"TShirt_White"}, "Mosin9130");
	Mannequin(2, pos, "SurvivorF_Linda", {"HuntingJacket_Brown", "PressVest_Blue"}, "Mp133Shotgun");
	Mannequin(3, pos, "SurvivorM_Boris", {"M65Jacket_Olive"}, "AKM");
	Mannequin(4, pos, "SurvivorM_Boris", {"GorkaEJacket_Summer", "PlateCarrierVest"}, "M4A1");
	Mannequin(5, pos, "SurvivorM_Boris", {"WoolCoat_Black"}, "SVD");
	Mannequin(6, pos, "SurvivorM_Boris", {"QuiltedJacket_Black", "HighCapacityVest_Black"}, "Winchester70");
	Mannequin(7, pos, "SurvivorM_Boris", {"Raincoat_Orange"}, "SKS");
	Mannequin(8, pos, "SurvivorM_Boris", {"TShirt_White", "UKAssVest_Olive"}, "Izh18");
	// Damage materials: 9 is badly damaged, 10 is ruined.
	Mannequin(9, pos, "SurvivorM_Boris", {"TShirt_White"}, "Mosin9130", 0.4);
	Mannequin(10, pos, "SurvivorM_Boris", {"TShirt_White"}, "Mosin9130", 0.0);
	// Control for the distance shots: a vanilla pack, to compare how far worn packs are drawn.
	Mannequin(11, pos, "SurvivorM_Boris", {"TShirt_White"}, "", 1.0, "AliceBag_Black");
}

// Camera tour: 12 s after start the free debug camera visits every mannequin (front, back,
// its left side, its right side), holding each view for 2.5 s and printing a SHOT line so an
// outside script can capture the window. Afterwards control returns to the player.
class CustomMission: MissionGameplay
{
	protected float m_AFTime;
	protected int m_AFShot = -1;
	// Distance shots at 5, 10, 20, 40, 80 and 160 m.
	static const int DIST_SHOTS = 6;

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);

		m_AFTime += timeslice;
		int total = g_AFDummyPos.Count() * 4;
		if (total == 0 || m_AFTime < 12 || m_AFShot >= total + 2 + DIST_SHOTS)
			return;

		int shot = Math.Floor((m_AFTime - 12) / 2.5);
		if (shot == m_AFShot)
			return;
		m_AFShot = shot;

		FreeDebugCamera cam = FreeDebugCamera.GetInstance();
		if (shot == total)
		{
			// Last stop: back to the player with the inventory open, to show the slot icons.
			cam.SetFreezed(false);
			cam.SetActive(false);
			GetHud().ShowHudUI(true);
			GetHud().ShowQuickbarUI(true);
			ShowInventory();
			Print("[AFTest] SHOT inventory");
			return;
		}
		if (shot > total && shot < total + 2)
			return;
		if (shot >= total + 2)
		{
			// LOD check: look at the backs of the last two mannequins from further and further
			// away. On the left of the picture is the vanilla Alice pack (control), on the right
			// the ruined hauler, which has nothing attached so the pack shows against the shirt.
			int step = shot - (total + 2);
			if (step >= DIST_SHOTS)
			{
				cam.SetFreezed(false);
				cam.SetActive(false);
				GetHud().ShowHudUI(true);
				GetHud().ShowQuickbarUI(true);
				Print("[AFTest] TOUR DONE");
				return;
			}
			if (step == 0)
				GetGame().GetUIManager().CloseAll();
			float metres = 5 * Math.Pow(2, step);
			vector focus = (g_AFDummyPos.Get(g_AFDummyPos.Count() - 1) + g_AFDummyPos.Get(g_AFDummyPos.Count() - 2)) * 0.5;
			focus[1] = focus[1] + 1.2;
			// From behind and 20 degrees up, so walls and containers do not block the view.
			vector eye = focus;
			eye[1] = eye[1] + metres * 0.342;
			eye[2] = eye[2] + metres * 0.940;
			GetHud().ShowHudUI(false);
			GetHud().ShowQuickbarUI(false);
			cam.SetActive(true);
			cam.SetFreezed(true);
			cam.SetPosition(eye);
			cam.SetDirection(vector.Direction(eye, focus).Normalized());
			Print("[AFTest] SHOT dist_" + metres.ToString() + "m");
			return;
		}

		int who = shot / 4;
		int view = shot % 4;
		vector target = g_AFDummyPos.Get(who);
		target[1] = target[1] + 1.2;
		vector from = target;
		string label;
		if (view == 0) { from[2] = from[2] - 2.3; label = "front"; }
		if (view == 1) { from[2] = from[2] + 2.3; label = "back"; }
		if (view == 2) { from[0] = from[0] + 2.0; label = "left"; }
		if (view == 3) { from[0] = from[0] - 2.0; label = "right"; }
		from[1] = from[1] + 0.1;

		GetHud().ShowHudUI(false);
		GetHud().ShowQuickbarUI(false);
		cam.SetActive(true);
		cam.SetFreezed(true);
		cam.SetPosition(from);
		cam.SetDirection(vector.Direction(from, target).Normalized());
		Print("[AFTest] SHOT m" + g_AFDummyName.Get(who) + "_" + label);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
