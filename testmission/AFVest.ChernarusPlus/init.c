// Offline test mission for the AF Vest Pack (worn with and without the AF Cape). Runs only in DayZDiag_x64.exe on this PC; it never
// connects to a server. Start it with testmission\capture_tour.ps1 -Mission AFVest.

ref array<vector> g_AFDummyPos = new array<vector>;
ref array<string> g_AFDummyName = new array<string>;
ref array<PlayerBase> g_AFDummy = new array<PlayerBase>;

// A standing character wearing the cape over the given clothes. They stand in a row 6 m
// north of the player, 3 m apart, number 1 at the west end, facing south toward the player.
// health is the cape's condition from 1.0 (pristine) down to 0.0 (ruined).
void Mannequin(int number, vector origin, string body, TStringArray clothes, float health = 1.0, bool withCape = true)
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
	if (withCape)
		dummy.GetInventory().CreateInInventory("AF_Cape");
	EntityAI cape = dummy.GetInventory().CreateInInventory("AF_VestPack");
	if (!cape)
	{
		Print("[AFTest] mannequin " + number.ToString() + ": FAILED to put the vest pack on");
		return;
	}
	InventoryLocation loc = new InventoryLocation;
	cape.GetInventory().GetCurrentInventoryLocation(loc);
	Print("[AFTest] mannequin " + number.ToString() + ": " + body + " wearing " + wearing + "vest pack in slot " + InventorySlots.GetSlotName(loc.GetSlot()));
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

// Torso cross-sections: at each height, rays from all around aimed at the body's centre
// line. Prints the hit point (x to the character's right, z forward). Arms are hit too.
void MeasureRadial(PlayerBase who, string name)
{
	vector hit, dir;
	int component;
	for (float h = 0.80; h < 1.61; h += 0.025)
	{
		string line = "[AFMeasure] " + name + " ring h=" + h.ToString() + ":";
		for (int k = 0; k < 24; k++)
		{
			float a = k * 15 * Math.DEG2RAD;
			vector outside = who.ModelToWorld(Vector(Math.Sin(a) * 0.7, h, Math.Cos(a) * 0.7 - 0.03));
			vector centre = who.ModelToWorld(Vector(0, h, -0.03));
			if (DayZPhysics.RaycastRV(outside, centre, hit, dir, component, NULL, NULL, NULL, false, false, ObjIntersectFire))
			{
				vector p = who.WorldToModel(hit);
				line = line + " " + (k * 15).ToString() + "=" + p[0].ToString() + "," + p[2].ToString();
			}
		}
		Print(line);
	}
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
	player.GetInventory().CreateInInventory("AF_Cape");
	if (player.GetInventory().CreateInInventory("AF_VestPack"))
		Print("[AFTest] AF_VestPack created on the player");
	else
		Print("[AFTest] FAILED to create AF_VestPack on the player");

	// The ground model, and a vanilla belt to check the cape and a belt exclude each other.
	Object ground = GetGame().CreateObjectEx("AF_VestPack", pos + "1.5 0 2", ECE_PLACE_ON_SURFACE);
	if (!ground)
		Print("[AFTest] FAILED to spawn AF_VestPack on the ground");
	GetGame().CreateObjectEx("MilitaryBelt", pos + "-1.5 0 2", ECE_PLACE_ON_SURFACE);

	Mannequin(1, pos, "SurvivorF_Eva", {"TShirt_White"});
	Mannequin(2, pos, "SurvivorM_Boris", {"TShirt_White"}, 1.0, false);
	Mannequin(3, pos, "SurvivorM_Boris", {"TShirt_White"});
	Mannequin(4, pos, "SurvivorM_Boris", {"M65Jacket_Olive"});
	Mannequin(5, pos, "SurvivorM_Boris", {"GorkaEJacket_Summer", "PlateCarrierVest"});
	Mannequin(6, pos, "SurvivorF_Linda", {"HuntingJacket_Brown"}, 1.0, false);
	Mannequin(7, pos, "SurvivorM_Boris", {"TShirt_White"}, 0.4, false);
	Mannequin(8, pos, "SurvivorM_Boris", {"TShirt_White"}, 0.0, false);
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
		if (false)
		{
			m_AFMeasured = true;
			MeasureBody(g_AFDummy.Get(0), "female_tshirt");
			MeasureBody(g_AFDummy.Get(1), "male_tshirt");
			MeasureRadial(g_AFDummy.Get(1), "male_tshirt");
			MeasureRadial(g_AFDummy.Get(0), "female_tshirt");
			Print("[AFMeasure] done");
		}
		int total = g_AFDummyPos.Count() * 4;
		if (total == 0 || m_AFTime < 12 || m_AFShot >= total + 8)
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
		else if (shot > total && shot <= total + 6)
		{
			// Far LODs: the backs of mannequins 2 (no cape) and 3 (with cape) from 5, 10, 20, 40,
			// 80 and 160 m, from behind and 20 degrees up.
			float metres = 5 * Math.Pow(2, shot - total - 1);
			target = (g_AFDummyPos.Get(1) + g_AFDummyPos.Get(2)) * 0.5;
			target[1] = target[1] + 1.2;
			from = target;
			from[1] = from[1] + metres * 0.342;
			from[2] = from[2] + metres * 0.940;
			label = "dist_" + metres.ToString() + "m";
		}
		else if (shot > total + 6)
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
