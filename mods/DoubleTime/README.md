# DoubleTime

Scrapping and repairing in half their vanilla effective time, including enhancement scaling. Version 0.1.0; UE4SS Lua; log namespace `[Caretaker.DoubleTime]`.

The mod post-hooks the native `VoyageItemBlueprintFunctionLibrary:GetPlayerItemActionTotalDuration` query and returns half its original result for `Dismantle` and `Repair`. Tool multipliers applied to that duration retain their relative benefits. Build/craft queries are unchanged. It never edits base item data, enhancements, tool stats, saves, costs, or yields, and never caches a modified duration. Disabling the mod and restarting restores vanilla.

**Validation status:** source/static analysis and isolated Lua checks are distinct from gameplay coverage. Until the working-notes matrix is completed, coverage of every tool/custom destructible and actual half-duration completion remain unverified. Time-based tool consumption can change with elapsed time; unchanged total electricity/fuel/durability is not promised.

Build/package with `tools/caretakermods.ps1 package --mod double-time`. Install through `deploy.ps1 -Mod double-time` with the game closed and source committed. The game-specific loader is a separate prerequisite. The generated `enabled.txt` activates this mod without editing shared load lists.

After a fresh launch, inspect `ue4ss/UE4SS.log` for `ready`, then compare scrapping and repair with the same object, tool tier, damage level, and enhancement setup. A 10-second vanilla action should take about 5 seconds; a 4-second upgraded action should take about 2 seconds, subject to game tick granularity. Check cancellation/retry, switching tools, save/load, yields, and the smallest jobs. A duration diagnostic is a query observation, not proof that an action completed.
