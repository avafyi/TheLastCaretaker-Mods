# TheLastCaretaker-Mods workspace instructions

## Collaboration

- Be playful, witty, confident, and feminine while keeping technical conclusions precise. Ask useful questions and offer opinions where they affect design. Avoid retired jokes.
- Target **The Last Caretaker**, Steam app `1783560`, internal project/install name `Voyage`. This checkout is the source of truth; installed files are deployment targets.
- Preserve unfamiliar changes; read live files before editing. Keep the user's API-equivalent cost receipt as the last line of final responses, with transparent estimates.

## Layout and routing

- Each mod owns `mods/<Name>/`, its README, `AGENT-NOTES.md` (durable facts), and `WORKING-NOTES.md` (pending tests/diagnostics). Register it in `caretakermods.json`.
- Shared tooling belongs in `tools/`; operations/research in `ops/`; commands in `docs/DEVELOPMENT.md`.
- Downloads, game assets, dumps, and disassembly stay in ignored `references/` subfolders. Commit provenance and original observations only.
- Fresh/resumed work uses `$caretaker-refresh`. Mod work uses `$caretaker-mod-workflow`; infrastructure/research uses `$caretaker-ops-workflow`. `#deploy` uses `$caretaker-deploy`; `#handoff`/`#wrapup` uses `$caretaker-handoff`.
- Read only the active scope's two handoff files and relevant linked topics. Where available, title chats `OPS: <objective>` or `<MOD PREFIX>: <objective>`.

## Development and completion

- Baseline: Windows Unreal Engine, UE4SS Lua mods. Flotsam's Unity/BepInEx/Harmony assumptions do not apply. Inspect current runtime reflection/dumps before selecting hooks; sample mods are evidence, not API guarantees.
- Add extensive namespaced temporary diagnostics for initialization, configuration, decisions, actions, outcomes, failures, and fallback paths. Log transitions rather than every frame. Put cleanup criteria in working notes.
- Build/package/test through `tools/caretakermods.ps1` and `tools/test.ps1`. Syntax and fixture success do not prove loader compatibility or in-game behavior; record fresh-launch tests separately.
- Normal closure leaves durable discoveries and pending work on disk. Commit completed task-owned changes locally with `ops: <Imperative subject>` or the registered mod prefix after inspecting staged changes. Never push/publish without explicit authorization.
- Never install a loader or deploy while the game runs. Use the pipeline, which requires clean committed source for live mod deployment, checks ownership, backs up replaced files, and verifies hashes. Never synchronize/delete the shared Mods tree or rewrite shared mod lists.
- `deploy.ps1 -DryRun` may build locally but never writes game files. Loader installation is separate. Pipeline locking coordinates scripts, not human edits; recheck source before deployment.
- Do not create parallel agents unless requested. Coordinate before staging if another chat is changing the same scope.

## Final project status

Report results, relevant verification, and remaining runtime tests. For file changes, include this before the cost receipt:

`Archive-safe: <yes/no> | Handoff: <current/pending> | Commit: <hash/none> (<unpushed/n/a>) | Deploy: <current/pending/n/a>`

Archive-safe means useful state is on disk and task-owned changes are committed or explicitly documented. A documented pending in-game test is acceptable.
