# The Last Caretaker Mods

A Windows modding workshop modeled on `Flotsam-Mods`: one folder per mod, a registry, shared tooling, five Codex workflows, and durable operations notes. The target is **The Last Caretaker** (Steam app `1783560`, install folder `Voyage`). This game's Unreal/UE4SS Lua baseline replaces Flotsam's Unity/BepInEx/C# baseline.

Source repository: [avafyi/TheLastCaretaker-Mods](https://github.com/avafyi/TheLastCaretaker-Mods) (public). Completed changes are committed at meaningful checkpoints and before live deployment preparation; GitHub pushes and releases require explicit authorization.

## Start here

Open a new chat in this project and say `$caretaker-refresh`, then describe the mod. Read [Development](docs/DEVELOPMENT.md) for commands and [Operations](ops/README.md) for research and pending work. Root `AGENTS.md` routes fresh/resumed chats automatically.

```powershell
.\tools\bootstrap.ps1
.\tools\caretakermods.ps1 doctor
.\tools\caretakermods.ps1 check
.\tools\caretakermods.ps1 build --mod dev-probe
.\tools\caretakermods.ps1 package --mod dev-probe
.\tools\test.ps1
.\deploy.ps1 -Mod dev-probe -DryRun
```

Bootstrap installs a checksum-pinned Lua 5.4 checker locally using bundled Python 3.12 x64. It does not alter the game. Steam manifest discovery finds `Voyage`; an override is available in `.caretakerdev.example.json` or `CARETAKER_GAME_ROOT`.

`DevProbe` is an original diagnostic starter, not a gameplay feature. Build validates Lua syntax and stages source scripts; it does not compile a native DLL. Packages contain only this mod's Lua, README, and enable marker.

Live loader installation and mod deployment are separate from setup. See [loader setup and fresh-launch validation](docs/DEVELOPMENT.md#loader-setup) before using `install-loader` or a real deployment. Runtime compatibility remains untested.

## Project map

| Path | Purpose |
| --- | --- |
| `caretakermods.json` | Registered mods and commit prefixes |
| `mods/DevProbe/` | Diagnostic starter and its two handoff notes |
| `tools/` | Local bootstrap, doctor, validation, build/package/deploy, tests |
| `.agents/skills/` | Refresh, mod work, ops work, deploy, handoff |
| `ops/` | Durable/working notes and topic router |
| `references/` | Provenance plus ignored samples and dumps |
| `artifacts/` | Ignored packages, tests, and deployment backups |

## First planned mod

Halve scrapping and repairing durations while preserving enhancement and tool-upgrade scaling. Requirements and investigation plan live in [scrapping and repair](ops/topics/scrapping-and-repair.md). This is a future mod, not implemented or registered as a completed feature during setup.
