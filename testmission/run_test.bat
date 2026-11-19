@echo off
rem Starts DayZ offline (no server) with the locally built AFItemPack mod. Steam must be running.
cd /d "C:\Program Files (x86)\Steam\steamapps\common\DayZ"
start "" DayZDiag_x64.exe "-mission=C:\DayZMods\testmission\AFTest.ChernarusPlus" "-mod=C:\DayZMods\@AFItemPack" "-profiles=C:\DayZMods\testmission\profiles" -window -nosplash -noPause -scriptDebug=true
