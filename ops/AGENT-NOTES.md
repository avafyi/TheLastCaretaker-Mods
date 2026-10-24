# Durable project knowledge

- Canonical checkout: `C:\Users\avafy\repos\TheLastCaretaker-Mods`. Setup explicitly modeled on sibling `Flotsam-Mods`: registry, per-mod folders, five project skills, ops topic router, durable/working notes, guarded clean-source deployment, local Git commits.
- Target: The Last Caretaker, Steam app `1783560`. Installed at `C:\Program Files (x86)\Steam\steamapps\common\Voyage`; real executable `Voyage/Binaries/Win64/VoyageSteam-Win64-Shipping.exe`. Internal reflected module name `Voyage` appears in inspected sample source.
- Unreal/UE4SS Lua baseline; no Unity, BepInEx, Harmony, .NET SDK, or Flotsam gameplay code copied. See [research evidence](topics/modding-research.md).
- Shared tooling is Python standard library plus checksum-pinned Lupa 2.6/Lua 5.4 for syntax validation. PowerShell wrappers prefer Codex's bundled Python 3.12 x64. Dependencies and downloaded references remain ignored/local.
- `DevProbe` is the only registered mod: original startup diagnostics, no gameplay hooks or save mutations. Setup does not deploy it or install the loader.
- User wants future chats to begin mod work. First planned feature: halve all scrapping and repairing durations, preserving enhancement/tool-upgrade scaling. Requirements are recorded in [scrapping and repair](topics/scrapping-and-repair.md); implementation is deferred.
- Root `AGENTS.md` owns shared policy; `docs/DEVELOPMENT.md` owns commands; project-local skills route context. Future chats should use `$caretaker-refresh` first.

- Live mod setup authorized 2026-10-23; reviewed Nexus v1.3 loader installed through the pipeline. See the live-setup evidence in the research topic. The package DLL hash differs from the author description; both archive and actual DLL are now pinned.
