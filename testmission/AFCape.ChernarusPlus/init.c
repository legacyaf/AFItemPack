// Offline test mission for the AF Cape. Runs only in DayZDiag_x64.exe on this PC; it never
// connects to a server. Start it with testmission\capture_tour.ps1 -Mission AFCape.

ref array<vector> g_AFDummyPos = new array<vector>;
ref array<string> g_AFDummyName = new array<string>;
ref array<PlayerBase> g_AFDummy = new array<PlayerBase>;

// A standing character wearing the cape over the given clothes. They stand in a row 6 m
// north of the player, 3 m apart, number 1 at the west end, facing south toward the player.
// health is the cape's condition from 1.0 (pristine) down to 0.0 (ruined).
void Mannequin(int number, vector origin, string body, TStringArray clothes, float health = 1.0)
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
	EntityAI cape = dummy.GetInventory().CreateInInventory("AF_Cape");
	if (!cape)
	{
		Print("[AFTest] mannequin " + number.ToString() + ": FAILED to put the cape on");
		return;
	}
	InventoryLocation loc = new InventoryLocation;
	cape.GetInventory().GetCurrentInventoryLocation(loc);
	Print("[AFTest] mannequin " + number.ToString() + ": " + body + " wearing " + wearing + "cape in slot " + InventorySlots.GetSlotName(loc.GetSlot()));
	if (health < 1.0)
		cape.SetHealth01("", "", health);
	g_AFDummyPos.Insert(pos);
	g_AFDummyName.Insert(number.ToString());
	g_AFDummy.Insert(dummy);
}

// Body measurements for fitting worn models: fires rays at a standing character's hit
// shape and prints where they land, in the character's own coordinates (x = to its right,
// y = up, z = forward, metres). "back" rays come from behind, "front" from ahead, "top"
// from above. Read the [AFMeasure] lines in the script log.
void MeasureBody(PlayerBase who, string name)
{
	vector hit, dir;
	int component;
	TFloatArray xs = {0, 0.08, 0.15, 0.20, 0.26};
	for (float h = 0.45; h < 1.66; h += 0.05)
	{
		foreach (float x : xs)
		{
			vector a = who.ModelToWorld(Vector(x, h, -1.0));
			vector b = who.ModelToWorld(Vector(x, h, 1.0));
			if (DayZPhysics.RaycastRV(a, b, hit, dir, component, NULL, NULL, NULL, false, false, ObjIntersectFire))
				Print("[AFMeasure] " + name + " back x=" + x.ToString() + " h=" + h.ToString() + " z=" + who.WorldToModel(hit)[2].ToString());
			if (DayZPhysics.RaycastRV(b, a, hit, dir, component, NULL, NULL, NULL, false, false, ObjIntersectFire))
				Print("[AFMeasure] " + name + " front x=" + x.ToString() + " h=" + h.ToString() + " z=" + who.WorldToModel(hit)[2].ToString());
		}
	}
	for (float tx = 0.06; tx < 0.27; tx += 0.03)
	{
		for (float tz = -0.10; tz < 0.11; tz += 0.05)
		{
			vector top = who.ModelToWorld(Vector(tx, 2.0, tz));
			vector low = who.ModelToWorld(Vector(tx, 1.0, tz));
			if (DayZPhysics.RaycastRV(top, low, hit, dir, component, NULL, NULL, NULL, false, false, ObjIntersectFire))
				Print("[AFMeasure] " + name + " top x=" + tx.ToString() + " z=" + tz.ToString() + " h=" + who.WorldToModel(hit)[1].ToString());
		}
	}
	TStringArray bones = {"Pelvis", "Spine", "Spine1", "Spine2", "Spine3", "Neck", "Head", "LeftShoulder", "LeftArm", "RightArm", "LeftUpLeg", "LeftLeg"};
	foreach (string bone : bones)
		Print("[AFMeasure] " + name + " bone " + bone + " " + who.GetBonePositionMS(who.GetBoneIndexByName(bone)).ToString());
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Weather weather = GetGame().GetWeather();
	weather.GetOvercast().Set(0, 0, 0);
	weather.GetRain().Set(0, 0, 0);
	weather.GetFog().Set(0, 0, 0);

	vector pos = "4660 0 10330";
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);

	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", pos, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");
	if (player.GetInventory().CreateInInventory("AF_Cape"))
		Print("[AFTest] AF_Cape created on the player");
	else
		Print("[AFTest] FAILED to create AF_Cape on the player");

	// The ground model, and a vanilla belt to check the cape and a belt exclude each other.
	Object ground = GetGame().CreateObjectEx("AF_Cape", pos + "1.5 0 2", ECE_PLACE_ON_SURFACE);
	if (!ground)
		Print("[AFTest] FAILED to spawn AF_Cape on the ground");
	GetGame().CreateObjectEx("MilitaryBelt", pos + "-1.5 0 2", ECE_PLACE_ON_SURFACE);

	Mannequin(1, pos, "SurvivorF_Eva", {"TShirt_White"});
	Mannequin(2, pos, "SurvivorM_Boris", {"TShirt_White"});
	Mannequin(3, pos, "SurvivorM_Boris", {"M65Jacket_Olive"});
	Mannequin(4, pos, "SurvivorM_Boris", {"GorkaEJacket_Summer", "PlateCarrierVest"});
	Mannequin(5, pos, "SurvivorM_Boris", {"WoolCoat_Black"});
	Mannequin(6, pos, "SurvivorF_Linda", {"HuntingJacket_Brown", "AliceBag_Black"});
	Mannequin(7, pos, "SurvivorM_Boris", {"TShirt_White"}, 0.4);
	Mannequin(8, pos, "SurvivorM_Boris", {"TShirt_White"}, 0.0);
}

// Camera tour: 12 s after start the free debug camera visits every mannequin (front, back,
// its left side, its right side), holding each view for 2.5 s and printing a SHOT line so
// an outside script can capture the window. Then the ground model, then the inventory.
class CustomMission: MissionGameplay
{
	protected float m_AFTime;
	protected int m_AFShot = -1;
	protected bool m_AFMeasured;

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);

		m_AFTime += timeslice;
		if (!m_AFMeasured && m_AFTime > 8 && g_AFDummy.Count() > 1)
		{
			m_AFMeasured = true;
			MeasureBody(g_AFDummy.Get(0), "female_tshirt");
			MeasureBody(g_AFDummy.Get(1), "male_tshirt");
			Print("[AFMeasure] done");
		}
		int total = g_AFDummyPos.Count() * 4;
		if (total == 0 || m_AFTime < 12 || m_AFShot >= total + 2)
			return;

		int shot = Math.Floor((m_AFTime - 12) / 2.5);
		if (shot == m_AFShot)
			return;
		m_AFShot = shot;

		FreeDebugCamera cam = FreeDebugCamera.GetInstance();
		vector target;
		vector from;
		string label;
		if (shot == total)
		{
			// The folded cape on the ground, from 1 m.
			target = GetGame().GetPlayer().GetPosition() + "1.5 0.05 2";
			from = target + "0.6 0.5 -0.7";
			label = "ground";
		}
		else if (shot > total)
		{
			cam.SetFreezed(false);
			cam.SetActive(false);
			GetHud().ShowHudUI(true);
			GetHud().ShowQuickbarUI(true);
			ShowInventory();
			Print("[AFTest] SHOT inventory");
			Print("[AFTest] TOUR DONE");
			return;
		}
		else
		{
			int who = shot / 4;
			int view = shot % 4;
			target = g_AFDummyPos.Get(who);
			target[1] = target[1] + 1.1;
			from = target;
			if (view == 0) { from[2] = from[2] - 2.3; label = "front"; }
			if (view == 1) { from[2] = from[2] + 2.3; label = "back"; }
			if (view == 2) { from[0] = from[0] + 2.0; label = "left"; }
			if (view == 3) { from[0] = from[0] - 2.0; label = "right"; }
			from[1] = from[1] + 0.1;
			label = "m" + g_AFDummyName.Get(who) + "_" + label;
		}

		GetHud().ShowHudUI(false);
		GetHud().ShowQuickbarUI(false);
		cam.SetActive(true);
		cam.SetFreezed(true);
		cam.SetPosition(from);
		cam.SetDirection(vector.Direction(from, target).Normalized());
		Print("[AFTest] SHOT " + label);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
