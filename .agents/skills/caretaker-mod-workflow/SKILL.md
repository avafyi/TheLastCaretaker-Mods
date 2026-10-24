---
name: caretaker-mod-workflow
description: Develop or debug a registered The Last Caretaker UE4SS Lua mod, or scaffold a new mod in this repository.
---

Resolve the registry entry and read both handoff files in `mods/<Name>/`. For a new mod follow `docs/DEVELOPMENT.md`; register unique metadata and create the per-mod notes.

Inspect current-game reflected types/functions, signatures, lifecycle, and ownership before selecting hooks. Samples and old dumps do not establish current contracts. Keep extracted material ignored, with source build/hash and original observations recorded.

Prefer narrow event-driven behavior; use the game thread for UObject access, validity checks, and explicit failure/fallback logging. Follow root diagnostics policy. Build/package through the pipeline; separately record fresh-launch tests and diagnostic cleanup criteria. Syntax parsing proves neither hook validity nor engine compatibility.

First planned feature requirements are in `ops/topics/scrapping-and-repair.md`. Do not implement unrelated features solely because a sample does. Commit task-owned changes with the registered prefix; deployment follows caretaker-deploy.
