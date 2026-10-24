# Current work and handoff

## Project setup

- Implemented the Flotsam-style repository/workflows for The Last Caretaker, with Unreal-specific tooling and original diagnostic starter. User confirmed this chat's scope is setup for additional mod-development chats.
- Local Lua checker bootstrapped, registry validation and DevProbe build/package successful. Twenty initial meaningful tests passed: dry-run isolation, ownership/collision guards, current install, backup/config/list preservation, externally edited files, obsolete files, running-game guard, rollback/hash checks, path/archive containment, loader conflict preflight, lock, dirty source, Lua ready/fallback, invalid syntax, and ZIP contents.
- Lua sample and two author READMEs downloaded from pinned public GitHub commits and inspected read-only. Their hashes/provenance are in `references/manifest.json`. No third-party mod installed, executed, or copied into original source.
- Local Vortex scan found no Last Caretaker staging/download folder; reference research therefore used public author pages and GitHub source. No Vortex configuration changed.
- All five project skills passed the skill-creator validator. Local Markdown links and downloaded reference hashes passed verification. PowerShell wrappers parsed successfully, and a real-path DevProbe deployment dry run succeeded without creating a game loader/mod directory.

## Next chat

- Start with `$caretaker-refresh`. For the first gameplay mod, read [scrapping and repair](topics/scrapping-and-repair.md), choose a name, scaffold/register it, and inspect the current runtime types before selecting a hook.
- Loader ZIP acquisition/staging and live runtime validation remain pending. Nexus's game-specific loader may require login to download; see `docs/DEVELOPMENT.md`. The baseline DLL hash is pinned, but runtime compatibility with the current Steam build is not proven.
- No gameplay implementation, live loader installation, game-file writes, push, publication, or save edits performed during setup. Do not mistake source/syntax/fixture success for successful in-game execution.
- Shared tooling diagnostics log downloads/checksums, validation, build/source hash, package hash, deployment plans, backups, verified writes, rollback, and failures. Retain integrity/failure logging; reduce verbose successful-write/API diagnostics after the first live deployment is verified.

## Current live setup

- User authorized loader installation and complete mod setup. Verified and installed Nexus v1.3 file 1088 with the game closed (19 verified writes); no prior loader existed.
- Updated `tools/caretakermods.py`, `docs/DEVELOPMENT.md`, and `references/manifest.json` to pin the actual reviewed archive/DLL pair; prior author-quoted DLL hash did not match the authentic downloaded package. Shared guidance changed: refresh these files before further installs.
- All 20 existing disposable fixture/Lua tests pass after the pin update. Fresh game startup, DevProbe ready log, and runtime timing inspection remain pending.
- No push/publication or save edits. Mod implementation continues in its own scope once the reflected contract is established.
