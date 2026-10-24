# DevProbe

Original diagnostic Lua mod for The Last Caretaker. Logs startup, version, intent, API availability, fallback, and ready/failure outcomes. No gameplay hooks, recurring callbacks, configuration mutations, or save writes.

Build/package with `tools/caretakermods.ps1 package --mod dev-probe`. Install the verified UE4SS loader separately, then deploy with `deploy.ps1 -Mod dev-probe` while the game is closed. Packages contain `ue4ss/Mods/DevProbe/scripts/main.lua`, an empty `enabled.txt`, and this README.

After a fresh launch, inspect `Voyage/Binaries/Win64/ue4ss/UE4SS.log` for `[Caretaker.DevProbe] ready`. Confirm the main menu and a disposable save load without new exceptions. To disable, remove this mod's `enabled.txt`; also check any manually added `DevProbe : 1` entry in shared `mods.txt`. A subsequent deploy restores the enable marker. Never delete other mods or their configuration.
