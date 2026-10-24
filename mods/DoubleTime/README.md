# DoubleTime

Scrapping and repairing in half their vanilla time, preserving enhancement/tool-upgrade scaling. Version 0.3.0 candidate; UE4SS Lua; logs `[Caretaker.DoubleTime]`.

**Extender regression:** the user confirmed that built electric cable extenders disappear at vanilla timing and survive at 0.2.x's 2× timing. Version 0.3.0 preserves their base dismantling data and instead halves the maintenance scrapping tool's final `GetActionDuration` output, after the game's target/enhancement calculations. Runtime validation of this replacement is pending; it is not yet a confirmed fix.

Scrapping uses the loaded `BP_ToolAbility_Maintenance_Dismantle_C:GetActionDuration` Blueprint post-hook and changes its `duration` DoubleProperty out parameter. `DismantleDuration` remains vanilla, including restoration of journaled 0.2.x values on a Lua reload. Until the tool class loads and the hook registers, scrapping keeps vanilla timing. Repair still halves each loaded item asset's reflected `RepairDuration`; native enhancement/tool factors continue through the original calculations. Build/craft durations and consumption-rate/yield properties are not edited. Actual total time-based consumption can change with shortened actions.

Temporary comparison control: with the game focused and no action in progress, press **Ctrl+Shift+F10** to switch between vanilla and 2× timing. Wait two seconds before testing; the log confirms `duration-factor=1.0` (vanilla) or `0.5` (2×). A fresh launch starts at 2×. Diagnostic observers leave destruction and eligibility results unchanged.

Scans run on the game thread after startup, map loads, and debounced item/ability loads. Original asset fields are journaled in `runtime-baselines.tsv` beside this README before any asset write. This local runtime file prevents repeated scans and Lua reloads from compounding the repair factor and restores old dismantling edits. It is keyed to the process-local GameEngine identity; cold starts capture newly loaded vanilla values. Keep the journal while the game is running; if it becomes damaged, quit the game before removing it. Disabling the mod and fully restarting restores original game assets; no save-file edits are made.

**Validation:** see WORKING-NOTES for fresh-launch and gameplay results. Custom destructibles with hard-coded timings, every upgraded tool/enhancement combination, very short jobs, and resource totals require gameplay verification. The first 0.1.0 query hook initialized but was bypassed by the tested gameplay and has been removed.

Use `tools/caretakermods.ps1 package --mod double-time` to package. Deploy with `deploy.ps1 -Mod double-time` after closing the game and committing source. The loader is installed separately. `enabled.txt` activates the mod without editing shared lists.

Compare matching vanilla/modded targets and tool/enhancement setups: 10 seconds should become about 5; 4 seconds should become about 2, subject to ticks/animations. Test both actions, partly damaged repair, small/large jobs, cancel/retry, switching tools, repeated actions, save/load, costs/yields, and progress/completion. A verified field write does not by itself prove an action completed in half the time.
