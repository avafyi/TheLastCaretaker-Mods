# Modding research

Evidence recorded 2026-10-23. Separate inspected facts from author claims and untested runtime assumptions.

## Local installation facts

- Steam `appmanifest_1783560.acf` names **The Last Caretaker**, `installdir=Voyage`, build ID `25982825`.
- Game root: `C:\Program Files (x86)\Steam\steamapps\common\Voyage`. Root `Voyage.exe` is the launcher; real executable is `Voyage/Binaries/Win64/VoyageSteam-Win64-Shipping.exe`.
- Real executable SHA-256: `08228b72d4590f9b00e2171f252d618464c2e04b785237fe728dddbf27d3b734`. Windows file/product version fields both say `UE5-CL-0`; they do not establish an engine minor version.
- Before setup, Win64 contained the shipping EXE, two TBB DLLs, `D3D12/`, and `DML/`. No `dwmapi.dll`, `ue4ss/UE4SS.dll`, or loader settings were present. Setup performed no game-file writes.
- `%LOCALAPPDATA%/Voyage` exists, but its inspected log folder only contained CEF logs, which did not establish engine version. No save-format claim is made from that directory name.
- The inspected local Vortex profile had other games' staging/download directories but no Last Caretaker directory or matching game-specific entry in the searched logs/plugins. This is evidence about the inspected location, not proof there is no custom Vortex staging location elsewhere.

## UE4SS baseline and uncertainty

Primary sources:

- [UE4SS installation](https://docs.ue4ss.com/dev/installation-guide.html): real shipping executable directory, basic/developer installation concepts.
- [Official release notes](https://github.com/UE4SS-RE/RE-UE4SS/releases): experimental builds use a `ue4ss` subfolder with the proxy DLL beside the executable. Old layouts exist; the starter pipeline deliberately targets the subfolder layout.
- [Lua mod authoring](https://docs.ue4ss.com/dev/guides/creating-a-lua-mod.html): entry point under a mod's scripts folder; reflection/Lua API rather than game-managed C# assemblies.
- [Enable marker documentation](https://docs.ue4ss.com/guides/installing-a-c%2B%2B-mod.html): `enabled.txt` is an alternative activation mechanism, with load-order limitations.
- [Game-specific loader author's page](https://www.nexusmods.com/thelastcaretaker/mods/4?tab=description): v1.3, updated 2026-09-06, identifies `UE4SS_v3.0.1-1125-g527a483b` (commit `527a483`) and DLL SHA-256 `4f9762f812329a640c8cfa14444c2bb97ecc213b8320bd4c5433383c3eef48f7`. Author claims UE5.8/game v0.8.5.X compatibility and says current mappings/key resources change with updates.

This justifies a reproducible candidate loader, not a claim it works on local build `25982825`. No loader ZIP downloaded/staged or runtime injection performed during setup. Nexus download may require the user's login; no account workaround attempted. The bootstrap accepts the reviewed archive's SHA-256 and separately checks the published DLL hash. Future updates require reviewing the pin and fresh startup evidence.

## Vortex package routing

The [extension author's description](https://www.nexusmods.com/site/mods/1624?tab=description) distinguishes ordinary PAK content, `LogicMods`, UE4SS Lua folders, and native UE4SS DLL folders. [Its Vortex review issue](https://github.com/Nexus-Mods/Vortex/issues/19333) is a further public entry point for the extension.

This workshop packages `ue4ss/Mods/<Name>/scripts/main.lua` and the mod's enable marker/README for the documented subfolder loader layout. Actual Vortex import/deployment was **not** exercised. Avoid managing the same live mod folder simultaneously with Vortex and the project deploy pipeline; Vortex hardlinks can link a deployed file to its staging copy. Project deployment uses replacement rather than writing into existing script bytes, but Vortex may later redeploy its version.

## Downloaded and inspected public examples

See `references/manifest.json` for immutable source URLs, commit IDs, hashes, and ignored local paths. None were executed or installed; no sample source was copied into the original diagnostic mod.

### MultiplayerSync (actual Lua source inspected)

[MrSkelee/TheLastCaretaker_MultiplayerMod](https://github.com/MrSkelee/TheLastCaretaker_MultiplayerMod), commit `e7c53010f7448d5a34f6d9717496b45410c71da6`, path `mod_files/ue4ss/Mods/MultiplayerSync/Scripts/main.lua`.

Observed patterns: imports `UEHelpers`, dispatches from `LoopAsync` to `ExecuteInGameThread`, checks player/pawn validity, and registers a hook in the reflected `/Script/Voyage` module. The sample also polls files, spawns an actor, and catches failures with `pcall`. It provides a concrete Lua folder/API example. Its behavior and method signatures were not verified against this installed game. Its polling, broad exception swallowing, and network-related behavior are not recommendations for our timing mod.

No scrapping or repairing contract was established from this sample. No repository SPDX license was reported by the GitHub API; treat it as study material unless reuse permission is established.

### TLC-Terminal (README inspected; mod source not established)

[Python727/TLC-Terminal](https://github.com/Python727/TLC-Terminal), commit `abe000669acd4a8e268bfe5a6e080fca6e173236`. The author describes an Electron navigation app plus a UE4SS waypoint integration, crediting Dmgvol for the mod. The inspected tree had no `.lua` source entry. Do not call this a verified Lua implementation or trust its save paths as local facts; it is a resource lead for later investigation.

### Dmgvol guides (README/topic map inspected)

[Dmgvol/UE_Modding](https://github.com/Dmgvol/UE_Modding), commit `5811a1af8e34a638da45a862548f327e3a662661`. Its topic map covers cooked assets, IoStore, mappings, FModel, Blueprint/LogicMods, default objects, and UE4SS header generation. Read individual topics only when a mod needs them; none of those asset tools are required for the diagnostic Lua starter. No game keys/mappings/assets were fetched.

## Next research

Establish loader startup first. Then inspect runtime reflection and the actual scrapping/repair upgrade calculation paths; see [first planned mod](scrapping-and-repair.md). Record each dump's game build, executable hash, loader version/hash, and date under ignored `references/dumps/`, with durable original observations linked here.

## Authorized live setup (2026-10-23)

The user requested loader installation and everything needed to make mods work. Nexus required sign-in and its legacy slow-download page failed; the user downloaded file 1088 in their usual browser. Found at Windows Downloads as `UE4SS TLC UE5 8 4 v1.3 2026-09-06T16-23Z P9QzVp5TK.zip` (8,392,579 bytes).

- Archive SHA-256 `28b1e3b5c4efd6898cf1edc16b4118b2067bec94eda42fe8e53b026e235087a4` matches the VirusTotal record linked from the current Nexus file entry.
- Actual DLL SHA-256 `91d5444f41d19d0bb502f0fbdc15d76421e20359e898caa39e41e134c8f87958`; embedded commit string `527a483b`.
- This differs from the author's description-quoted DLL hash. The original pipeline correctly refused it. Updated the baseline to the inspected package and additionally pinned the whole archive; do not describe the actual DLL hash as author-published.
- Guarded install wrote and verified 19 previously absent files with the game closed, including bundled shared Lua helpers and Blueprint loader. No existing shared list was overwritten. Staged per-file provenance is ignored under `.tools/loader-provenance.json`.
- No FModel, mapping file, or asset encryption key is required for native reflected Lua functions. Those may become research prerequisites if the timing paths require Blueprint disassembly.
