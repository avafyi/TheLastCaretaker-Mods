---
name: caretaker-deploy
description: Deploy TheLastCaretaker-Mods Lua payloads locally when the user requests deploy or #deploy.
---

A deploy request authorizes local testing, not publication. Run `deploy.ps1` with `-Mod <registered-id>` only when scoped; use `-DryRun` when requested or testing the pipeline, not as a substitute for authorized live deployment.

The pipeline owns clean-source/process guards, build/package, backup/rollback, ownership, and hash checks. Do not bypass failures or manually recreate the copy loop. A missing loader follows the separate verified staging/install procedure in `docs/DEVELOPMENT.md`; differing loader/settings files need explicit maintenance rather than overwrite.

If the game is running, leave deployment pending and request closure; never kill it. Report actual per-mod results. Changed files need a fresh launch and log/behavior validation. Deploy does not stage, commit, push, or publish.
