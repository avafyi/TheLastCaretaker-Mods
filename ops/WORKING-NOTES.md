# Current work and handoff

## GitHub and commit workflow (2026-10-24)

- User authorized creating a GitHub repository and publishing committed history. GitHub CLI is authenticated as `avafyi`; restricted-network auth checks can falsely report an invalid token, so verify with network access before requesting a login.
- Created public `https://github.com/avafyi/TheLastCaretaker-Mods` and configured `origin`; user explicitly selected public visibility. Initial publication is scoped to committed source/history; downloaded/game material and unfinished concurrent changes remain local.
- Root `AGENTS.md` and `docs/DEVELOPMENT.md` now require proactive commits at meaningful validated checkpoints, before live deployment preparation, and at task closure.
- Concurrent Reel changes in `caretakermods.json` and `mods/Reel/` belong to the active Reel chat. This ops change stages only its own documentation; uncommitted concurrent work is not part of the initial publication.

## Live mod setup (2026-10-23)

- User authorized loader installation and everything needed for mods. Verified Nexus v1.3 file 1088 archive and installed 19 absent files through the guarded pipeline with the game closed. Bundled Lua helpers/Blueprint loader are present; no existing shared list overwritten.
- The genuine archive's DLL differs from the author's description-quoted DLL hash. Pinned both reviewed archive and actual DLL in `tools/caretakermods.py`; evidence is in [modding research](topics/modding-research.md) and `references/manifest.json`. No integrity guard was bypassed.
- Fresh loader launch identifies commit `527a483b`, detects engine 5.8, and logs DevProbe 0.1.0 ready. User confirmed the main menu worked. DevProbe was deployed via pipeline; payload hashes verified.
- DoubleTime 0.1.0 was registered/deployed and initialized, but the user found gameplay timing unchanged. The 0.2.0 replacement scales reflected native item-duration fields; fresh 18:14 deployment/launch verified 911 assets / 1,822 duration fields and a subsequent zero-change scan. Follow mod notes for gameplay test status. See `mods/DoubleTime/AGENT-NOTES.md` and `WORKING-NOTES.md` for gameplay coverage and pending timing matrix.
- Registry/build/package pass; 27 tests pass (20 pipeline/probe fixtures plus 7 DoubleTime behavioral tests). Syntax/fixture/startup success does not establish every gameplay code path.

## Shared guidance and pending work

- Changed shared guidance: `docs/DEVELOPMENT.md`, `references/manifest.json`, loader constants in `tools/caretakermods.py`, and mod registry. Refresh these before more setup/deployment.
- User generated a Ctrl+J reflection dump (69,467,988 bytes), retained/hash-recorded under ignored `references/dumps/`. Keep raw dumps, game assets/disassembly, and downloaded sources ignored.
- Initial scaffold/workflows, pinned Lua checker, reference provenance, and skill validation were completed earlier. No publication, push, Vortex configuration changes, or direct save edits.
- Retain integrity/failure diagnostics. DoubleTime's temporary diagnostics cleanup criteria and exact runtime matrix live in its working notes.
