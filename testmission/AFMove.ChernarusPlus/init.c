// Offline movement test for the AF Cape and AF Vest Pack worn together. Runs only in
// DayZDiag_x64.exe on this PC; it never connects to a server. Start it with
// testmission\capture_tour.ps1 -Mission AFMove.
//
// Five characters in T-shirts wear both items. Each is put in one pose (standing, crouched,
// prone, jogging, sprinting) and photographed from the front, back, left and right.

ref array<PlayerBase> g_AFDummy = new array<PlayerBase>;
ref array<string> g_AFPose = new array<string>;

void Poser(string pose, vector origin, float dx)
{
	vector pos = origin;
	pos[0] = pos[0] + dx;
	pos[2] = pos[2] + 6;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	PlayerBase dummy = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Boris", pos, 0, "NONE"));
	if (!dummy)
	{
		Print("[AFTest] FAILED to create the " + pose + " character");
		return;
	}
	dummy.SetOrientation("180 0 0");
	dummy.GetInventory().CreateInInventory("TShirt_White");
	dummy.GetInventory().CreateInInventory("CargoPants_Black");
	dummy.GetInventory().CreateInInventory("AthleticShoes_Black");
	if (!dummy.GetInventory().CreateInInventory("AF_Cape"))
		Print("[AFTest] FAILED to put the cape on the " + pose + " character");
	if (!dummy.GetInventory().CreateInInventory("AF_VestPack"))
		Print("[AFTest] FAILED to put the vest pack on the " + pose + " character");
	g_AFDummy.Insert(dummy);
	g_AFPose.Insert(pose);
	Print("[AFTest] character ready: " + pose);
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

	// All of them stand on the concrete east of the player (tall grass hides a prone character),
	// and the runners run south past him, not into him.
	Poser("stand", pos, 8);
	Poser("crouch", pos, 11);
	Poser("prone", pos, 14);
	Poser("jog", pos, 18);
	Poser("sprint", pos, 21);
}

class CustomMission: MissionGameplay
{
	protected float m_AFTime;
	protected int m_AFShot = -1;
	protected bool m_AFPosed;

	// Height of the point the camera looks at, per pose.
	float LookHeight(string pose)
	{
		if (pose == "crouch") return 0.75;
		if (pose == "prone") return 0.25;
		return 1.1;
	}

	void SetRunning(PlayerBase who, float speed)
	{
		// 2 = jog, 3 = sprint; straight ahead.
		who.GetInputController().OverrideMovementSpeed(speed > 0, speed);
		who.GetInputController().OverrideMovementAngle(speed > 0, 0);
	}

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);
		m_AFTime += timeslice;
		int total = g_AFDummy.Count() * 4;
		if (total == 0)
			return;

		if (!m_AFPosed && m_AFTime > 6)
		{
			m_AFPosed = true;
			for (int i = 0; i < g_AFDummy.Count(); i++)
			{
				HumanCommandMove move = g_AFDummy.Get(i).GetCommand_Move();
				if (!move)
				{
					Print("[AFTest] FAILED: no movement command on the " + g_AFPose.Get(i) + " character");
					continue;
				}
				if (g_AFPose.Get(i) == "crouch")
					move.ForceStance(DayZPlayerConstants.STANCEIDX_CROUCH);
				if (g_AFPose.Get(i) == "prone")
					move.ForceStance(DayZPlayerConstants.STANCEIDX_PRONE);
			}
		}
		if (m_AFTime < 12 || m_AFShot > total)
			return;

		int shot = Math.Floor((m_AFTime - 12) / 2.5);
		FreeDebugCamera cam = FreeDebugCamera.GetInstance();
		if (shot >= total)
		{
			if (m_AFShot <= total)
			{
				m_AFShot = total + 1;
				for (int k = 0; k < g_AFDummy.Count(); k++)
					SetRunning(g_AFDummy.Get(k), 0);
				cam.SetFreezed(false);
				cam.SetActive(false);
				GetHud().ShowHudUI(true);
				Print("[AFTest] TOUR DONE");
			}
			return;
		}

		int who = shot / 4;
		int view = shot % 4;
		PlayerBase dummy = g_AFDummy.Get(who);
		string pose = g_AFPose.Get(who);
		if (shot != m_AFShot && view == 0)
		{
			// Runners start when their first picture is due and stop after their last.
			if (who > 0)
				SetRunning(g_AFDummy.Get(who - 1), 0);
			if (pose == "jog")
				SetRunning(dummy, 2);
			if (pose == "sprint")
				SetRunning(dummy, 3);
		}

		// The camera follows the character every frame, so runners stay in the picture.
		vector target = dummy.GetPosition();
		target[1] = target[1] + LookHeight(pose);
		vector from = target;
		string label;
		if (view == 0) { from[2] = from[2] - 2.3; label = "front"; }
		if (view == 1) { from[2] = from[2] + 2.3; label = "back"; }
		if (view == 2) { from[0] = from[0] + 2.0; label = "left"; }
		if (view == 3) { from[0] = from[0] - 2.0; label = "right"; }
		from[1] = from[1] + 0.25;
		if (pose == "prone")
			from[1] = from[1] + 0.9;   // look down on a prone character
		GetHud().ShowHudUI(false);
		GetHud().ShowQuickbarUI(false);
		cam.SetActive(true);
		cam.SetFreezed(true);
		cam.SetPosition(from);
		cam.SetDirection(vector.Direction(from, target).Normalized());

		if (shot != m_AFShot)
		{
			m_AFShot = shot;
			vector speed = GetVelocity(dummy);
			Print("[AFTest] SHOT " + pose + "_" + label + " moving " + speed.Length().ToString() + " m/s, height above ground " + (dummy.GetBonePositionWS(dummy.GetBoneIndexByName("Pelvis"))[1] - dummy.GetPosition()[1]).ToString());
		}
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
