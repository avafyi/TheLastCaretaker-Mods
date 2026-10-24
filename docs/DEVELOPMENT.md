# Development

## Toolchain

Use PowerShell 7, Git, and **Python 3.12 x64**. Wrappers prefer Codex's bundled interpreter, then `python` on PATH. Bootstrap verifies the SHA-256 of `lupa-2.6-cp312-cp312-win_amd64.whl`, extracts it under `.tools/python`, and explicitly uses its Lua 5.4 runtime to parse scripts without executing them. The version is a reproducible baseline, not a claim to be latest. No machine PATH/global Python configuration changes.

```powershell
.\tools\bootstrap.ps1
# Offline alternative, same checksum verification:
.\tools\bootstrap.ps1 -LuaWheel '<path-to-lupa-2.6-cp312-cp312-win_amd64.whl>'
```

Steam discovery reads `libraryfolders.vdf` and app `1783560`'s `installdir`; the current folder is `Voyage`. `CARETAKER_GAME_ROOT` takes precedence over `.caretakerdev.local.json`. The root must contain `Voyage.exe` and `Voyage/Binaries/Win64/VoyageSteam-Win64-Shipping.exe`. Explicitly configured invalid paths fail instead of falling back to another install.

## Commands

| Command | Result |
| --- | --- |
| `tools/caretakermods.ps1 doctor` | Read-only game path/executable hash, Lua checker, installed loader presence/hashes |
| `tools/caretakermods.ps1 check` | Validate registry uniqueness, payload paths, required files |
| `tools/caretakermods.ps1 build [--mod id]` | Parse each Lua source and stage a fresh local payload |
| `tools/caretakermods.ps1 package [--mod id]` | Build a ZIP rooted at `ue4ss/Mods/<Name>/` |
| `deploy.ps1 [-Mod id] [-DryRun]` | Build/package and install only owned payload files |
| `tools/caretakermods.ps1 install-loader [--dry-run]` | Plan/install the locally staged, verified loader |
| `tools/test.ps1` | Run filesystem fixtures and the isolated DevProbe Lua harness |

`-DryRun` builds artifacts but writes nothing to the game; it is valid while the game runs and while source is uncommitted. It reports a missing loader without pretending installation happened. A live deploy requires an initial Git commit and a clean repository. Build/package/doctor/check do not require an installed loader or a running game.

## Loader setup

The [game-specific loader author](https://www.nexusmods.com/thelastcaretaker/mods/4?tab=description) identifies v1.3 as UE4SS `3.0.1-1125-g527a483b`, with commit `527a483b`. The reviewed Nexus file 1088 ZIP has SHA-256 `28b1e3b5c4efd6898cf1edc16b4118b2067bec94eda42fe8e53b026e235087a4` and its actual `UE4SS.dll` has SHA-256 `91d5444f41d19d0bb502f0fbdc15d76421e20359e898caa39e41e134c8f87958`. Their notes claim UE5.8/game v0.8.5.X compatibility. The installed game's exact engine minor version and compatibility have **not** been independently established. Revisit the baseline if startup fails or the game updates; do not substitute an arbitrary latest archive.

1. Download the author's v1.3 ZIP from the [files page](https://www.nexusmods.com/thelastcaretaker/mods/4?tab=files). Nexus may require your login. Setup does not automate account access or install this loader.
2. Review the archive source and compute its SHA-256 with `Get-FileHash '<archive.zip>' -Algorithm SHA256`. Pass that exact hash to pin the entire reviewed archive; the pipeline additionally enforces the reviewed package DLL hash.
3. Stage it locally; expected ZIP layout is `dwmapi.dll` plus `ue4ss/UE4SS.dll`, settings, and bundled support files:

```powershell
.\tools\bootstrap.ps1 -LoaderArchive '<archive.zip>' -ArchiveSha256 '<64-hex-archive-hash>'
.\tools\caretakermods.ps1 install-loader --dry-run
# Close The Last Caretaker before any real install.
.\tools\caretakermods.ps1 install-loader
# Launch once; confirm UE4SS startup, then quit.
# Commit completed mod/tooling changes before deployment.
.\deploy.ps1 -Mod dev-probe -DryRun
.\deploy.ps1 -Mod dev-probe
# Freshly launch; check ue4ss/UE4SS.log for [Caretaker.DevProbe] ready.
```

Bootstrap records per-file hashes and archive provenance in ignored `.tools/loader-provenance.json`. Loader installation preflights all files and refuses differing existing content. It does not silently upgrade existing UE4SS installations or overwrite settings. Loader changes are an explicit maintenance operation. Build tooling and diagnostics remain usable without the loader ZIP.

## New Lua mods

1. Create `mods/<PascalCaseName>/scripts/main.lua`, README, `AGENT-NOTES.md`, and `WORKING-NOTES.md`. Use DevProbe's structure, unique log namespace, and version.
2. Register unique lowercase kebab-case `id`/`prefix`, alphanumeric/dotted `folder`, unique dotted `guid`, and `kind: ue4ss-lua`. GUID is registry identity; Lua loading uses the folder name.
3. Inspect relevant current-game reflected types/functions and signatures. Save dumps under ignored `references/dumps/`, with source build/hash and original observations in the topic notes. Never infer offsets from Unity samples or hard-code a guessed Unreal method.
4. Prefer narrow event-driven changes on the game thread when touching Unreal objects. Check object validity/lifetime, handle hook registration failures, and preserve base-game upgrade calculations. Avoid repeatedly multiplying already modified values.
5. Add transition-based temporary diagnostics and an exact fresh-launch test. Document cleanup criteria. Build/package and commit task-owned source before deployment.

Only `.lua` files under `scripts/` are accepted in the starter pipeline. Native C++ mods, custom binary dependencies, and cooked Blueprint/PAK content need an explicit tooling extension; do not shoehorn them into a Lua package.

## Deployment and recovery

All pipeline mutations share `.cache/pipeline.lock` with PID/time. Remove a stale lock only after verifying its owner is no longer working. Scripts recheck the running-game guard immediately before writes; they never kill the game. Process enumeration failures block live writes.

Mods are installed under `Voyage/Binaries/Win64/ue4ss/Mods/<Name>/` with `.caretakermods-install.json`. Ownership collisions and externally edited managed files block deployment. Obsolete owned files require reviewed removal rather than automatic deletion. Unrelated mod files, user configurations, and shared `mods.txt`/`mods.json` are preserved.

The generated empty `enabled.txt` activates an independent mod without rewriting the shared load order. [UE4SS documents this activation mode](https://docs.ue4ss.com/guides/installing-a-c%2B%2B-mod.html). Do not use it for mods that need explicit ordering without adding appropriate support. Disable a mod by removing its marker and checking for any manually configured enabling entry in the shared list; redeployment restores the marker.

Replacements use same-directory staged files, SHA-256 verification, and rollback on an exception. Replaced bytes are retained under `artifacts/backups/<transaction>/`, with `index.json` mapping numbered backup files to original absolute paths. With the game closed, restore the affected files and matching ownership manifest together. A sudden power/process loss can interrupt a multi-file transaction; backups and the manifest enable inspection/recovery. Never restore by synchronizing/deleting the entire Mods tree.

Package/syntax checks and file hashes do not establish runtime compatibility. After a fresh launch, check loader startup, expected mod version/ready log, relevant behavior, fallback, and new errors. Use a disposable save for gameplay changes. Initial scaffolding performed no deployment. On 2026-10-23 the user authorized live mod setup; the verified v1.3 loader was installed. Fresh launch verification is tracked in the ops working notes.

## Handoff

Use `AGENT-NOTES.md` for durable verified facts and `WORKING-NOTES.md` for uncertainty, pending tests, and temporary diagnostics. Shared policy is in root `AGENTS.md`; deeper research routes through `ops/README.md`. Commit shared work with `ops:` and mod work with its registered prefix. No remote/push/release is configured by setup.
