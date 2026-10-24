# DoubleTime

Scrapping and repairing in half their vanilla time, preserving multiplicative enhancement/tool-upgrade scaling. Version 0.2.1 diagnostic build; UE4SS Lua; logs `[Caretaker.DoubleTime]`.

**Under investigation:** the user reports that built electric cable extenders survive a completed scrap action, including unconnected extenders. The cause is not yet established. With the game focused and no action in progress, press **Ctrl+Shift+F10** to switch between vanilla duration fields and 2× speed. Wait two seconds before testing; the log confirms `duration-factor=1.0` (vanilla) or `0.5` (2×). A fresh launch starts at 2×. This temporary diagnostic build also observes extender eligibility and the reflected destruction call without overriding their results. It is not a confirmed fix.

The mod halves each loaded item asset's reflected `DismantleDuration` and `RepairDuration`. Native gameplay reads those fields directly; enhancements/tool factors continue through the game's original calculations. No timing query hook is installed, so the data change is not applied twice. Build/craft durations and consumption-rate/yield properties are not edited. Actual total time-based consumption can change with the shortened action.

Scans run on the game thread after startup, map loads, and debounced item loads. Originals are journaled in `runtime-baselines.tsv` beside this README before any asset write. This local runtime file prevents repeated scans and Lua reloads from compounding the factor. It is keyed to the process-local GameEngine identity; cold starts capture newly loaded vanilla values. Keep the journal while the game is running; if it becomes damaged, quit the game before removing it. Disabling the mod and fully restarting restores original game assets; no save-file edits are made.

**Validation:** see WORKING-NOTES for fresh-launch and gameplay results. Custom destructibles with hard-coded timings, every upgraded tool/enhancement combination, very short jobs, and resource totals require gameplay verification. The first 0.1.0 query hook initialized but was bypassed by the tested gameplay and has been removed.

Use `tools/caretakermods.ps1 package --mod double-time` to package. Deploy with `deploy.ps1 -Mod double-time` after closing the game and committing source. The loader is installed separately. `enabled.txt` activates the mod without editing shared lists.

Compare matching vanilla/modded targets and tool/enhancement setups: 10 seconds should become about 5; 4 seconds should become about 2, subject to ticks/animations. Test both actions, partly damaged repair, small/large jobs, cancel/retry, switching tools, repeated actions, save/load, costs/yields, and progress/completion. A verified field write does not by itself prove an action completed in half the time.
