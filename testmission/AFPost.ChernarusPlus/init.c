// Offline test for the AF Command Post. Runs only in DayZDiag_x64.exe on this PC; it never
// connects to a server. Start it with testmission\capture_tour.ps1 -Mission AFPost.
//
// The building stands on the concrete east of the player, entrance facing south. The camera
// looks at it from outside, inside and above; both doors are opened by script; one character
// is stood on each floor and on the roof, and one walks in through the entrance and the vault.

Building g_AFPost;
PlayerBase g_AFWalker;
ref array<PlayerBase> g_AFStanders = new array<PlayerBase>;
ref array<string> g_AFStanderName = new array<string>;
vector g_AFPostPos;

PlayerBase Stand(string name, vector offset)
{
	// offset: metres from the building's middle (x to the east, y up from its base, z north).
	vector pos = g_AFPostPos + offset;
	PlayerBase who = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Boris", pos, 0, "NONE"));
	if (!who)
	{
		Print("[AFTest] FAILED to create the character for " + name);
		return NULL;
	}
	who.SetPosition(pos);
	who.GetInventory().CreateInInventory("TShirt_White");
	who.GetInventory().CreateInInventory("CargoPants_Black");
	who.GetInventory().CreateInInventory("AthleticShoes_Black");
	g_AFStanders.Insert(who);
	g_AFStanderName.Insert(name);
	return who;
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

	g_AFPostPos = pos + "16 0 16";
	g_AFPostPos[1] = GetGame().SurfaceY(g_AFPostPos[0], g_AFPostPos[2]);
	Object obj = GetGame().CreateObjectEx("Land_AF_CommandPost", g_AFPostPos, ECE_SETUP | ECE_UPDATEPATHGRAPH | ECE_CREATEPHYSICS);
	g_AFPost = Building.Cast(obj);
	if (!g_AFPost)
	{
		Print("[AFTest] FAILED to create Land_AF_CommandPost as a building");
		return;
	}
	g_AFPost.SetPosition(g_AFPostPos);
	g_AFPost.SetOrientation("0 0 0");
	vector box[2];
	g_AFPost.GetCollisionBox(box);
	Print("[AFTest] building created at " + g_AFPost.GetPosition().ToString() + ", collision box " + box[0].ToString() + " to " + box[1].ToString());

	// Dropped from 1 m above each surface; where they come to rest is printed later.
	Stand("command room floor", "2.5 1.2 -4");
	Stand("panic room floor", "0 1.2 3");
	Stand("roof", "0 4.5 2");
	g_AFWalker = Stand("walker", "0.45 0.3 -11");
}

class CustomMission: MissionGameplay
{
	protected float m_AFTime;
	protected int m_AFStep = -1;

	void Look(string label, vector fromLocal, vector toLocal)
	{
		FreeDebugCamera cam = FreeDebugCamera.GetInstance();
		GetHud().ShowHudUI(false);
		GetHud().ShowQuickbarUI(false);
		cam.SetActive(true);
		cam.SetFreezed(true);
		vector from = g_AFPostPos + fromLocal;
		vector to = g_AFPostPos + toLocal;
		cam.SetPosition(from);
		cam.SetDirection(vector.Direction(from, to).Normalized());
		Print("[AFTest] SHOT " + label);
	}

	void Report()
	{
		for (int i = 0; i < g_AFStanders.Count(); i++)
		{
			vector p = g_AFStanders.Get(i).GetPosition() - g_AFPostPos;
			Print("[AFTest] " + g_AFStanderName.Get(i) + ": stands " + p[1].ToString() + " m above the building's base, at x " + p[0].ToString() + " z " + p[2].ToString());
		}
	}

	void Probe(string name, vector fromLocal, vector toLocal)
	{
		// A ray against the fire geometry: does a wall stop it?
		vector hit, dir;
		int component;
		vector a = g_AFPostPos + fromLocal;
		vector b = g_AFPostPos + toLocal;
		if (DayZPhysics.RaycastRV(a, b, hit, dir, component, NULL, NULL, NULL, false, false, ObjIntersectFire))
			Print("[AFTest] ray " + name + ": stopped at " + (hit - g_AFPostPos).ToString());
		else
			Print("[AFTest] ray " + name + ": passed through");
	}

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);
		if (!g_AFPost)
			return;
		m_AFTime += timeslice;
		if (m_AFTime < 10)
			return;
		int step = Math.Floor((m_AFTime - 10) / 2.5);
		// The walker is steered every frame once the doors are open (steps 9-16).
		if (g_AFWalker && step >= 9 && step <= 16)
		{
			g_AFWalker.SetOrientation("0 0 0");
			g_AFWalker.GetInputController().OverrideMovementSpeed(true, 1);
			g_AFWalker.GetInputController().OverrideMovementAngle(true, 0);
		}
		if (step == m_AFStep)
			return;
		m_AFStep = step;
		switch (step)
		{
			case 0:
				Report();
				Probe("through the front wall beside the door", "2.5 1.5 -12", "2.5 1.5 -4");
				Probe("through a front window", "-2.5 1.87 -12", "-2.5 1.87 -4");
				Probe("through the closed entrance door", "0.45 1.2 -12", "0.45 1.2 -4");
				Probe("through the closed vault door", "0 1.2 -4", "0 1.2 3");
				Probe("through the panic room's side wall", "8 1.5 3", "0 1.5 3");
				Look("ext_front", "9 6 -19", "0 1.8 0");
				break;
			case 1: Look("ext_back", "-10 6 19", "0 1.8 0"); break;
			case 2: Look("ext_front_close", "1.5 1.7 -13", "1 1.6 -7"); break;
			case 3: Look("ext_side", "14 3 -2", "0 1.8 0"); break;
			case 4: Look("roof", "5 9 -10", "0 3.4 0"); break;
			case 5: Look("command_room", "3.2 1.8 -6.2", "-1 1.3 -1"); break;
			case 6: Look("command_room_to_door", "-3 1.8 -1.6", "1 1.3 -7"); break;
			case 7:
				g_AFPost.OpenDoor(0);
				g_AFPost.OpenDoor(1);
				Print("[AFTest] doors opened by script: entrance " + g_AFPost.IsDoorOpen(0).ToString() + ", vault " + g_AFPost.IsDoorOpen(1).ToString() + " (of " + g_AFPost.GetDoorCount().ToString() + " doors)");
				break;
			case 8:
				Probe("through the open entrance", "0.45 1.2 -12", "0.45 1.2 -4");
				Probe("through the open vault", "0 1.2 -4", "0 1.2 3");
				Look("command_room_vault_open", "3.2 1.8 -6.2", "-1 1.3 -1");
				break;
			case 9: Look("ext_front_door_open", "1.5 1.7 -13", "1 1.6 -7"); break;
			case 10: Look("panic_room", "2.9 1.9 0.2", "-1.5 1.2 5.5"); break;
			case 11: Look("panic_room_to_vault", "-2.8 1.9 5.8", "0 1.2 -1"); break;
			case 12: Look("walker_in_command_room", "3.2 1.8 -6.2", "-1 1.3 -1"); break;
			case 14: Look("walker_overview", "0 14 -4", "0 0 0.1"); break;
			case 17:
				if (g_AFWalker)
				{
					g_AFWalker.GetInputController().OverrideMovementSpeed(false, 0);
					g_AFWalker.GetInputController().OverrideMovementAngle(false, 0);
				}
				Report();
				Look("walker_end", "2.9 1.9 0.2", "-1.5 1.2 5.5");
				break;
			case 18:
				FreeDebugCamera.GetInstance().SetFreezed(false);
				FreeDebugCamera.GetInstance().SetActive(false);
				GetHud().ShowHudUI(true);
				Print("[AFTest] TOUR DONE");
				break;
		}
		if (g_AFWalker && step >= 9 && step <= 17)
		{
			vector w = g_AFWalker.GetPosition() - g_AFPostPos;
			Print("[AFTest] walker at step " + step.ToString() + ": x " + w[0].ToString() + " z " + w[2].ToString() + " height " + w[1].ToString());
		}
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
