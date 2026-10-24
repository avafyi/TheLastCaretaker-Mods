# First planned mod: halve scrapping and repairing time

## User requirement

"Making all scrapping and repairing take half as long (scaling appropriately with enhancements and tool upgrades)." Recorded 2026-10-23. This chat is project setup; gameplay implementation belongs to a subsequent mod chat.

## Intended behavior

- For each supported action/tool/enhancement combination, target `modded duration = vanilla effective duration * 0.5`. If the actual game API expresses work per second rather than duration, the equivalent rate is `vanilla effective rate * 2`.
- Preserve the original enhancement and upgrade relationships. Prefer applying the factor after vanilla computes effective duration, if there is a reliable hook; otherwise inspect the underlying rate/duration data flow first.
- Do not apply both a duration multiplier and a rate multiplier to the same path. Prevent compounded changes during reloads, repeated interactions, tool switching, and save/load.
- Preserve prerequisites, completion events, costs, yields, durability/energy behavior, cancellation, and progress UI unless changed timing inherently affects them. Inspect any time-based consumption before promising unchanged totals.
- "All" needs a current-game inventory of scrapping/repairing code paths and tools. Do not silently expand this to crafting, recycling, construction, or unrelated animations; resolve any gameplay ambiguity once the actual paths are known.

## Investigation plan

1. Establish loader compatibility using DevProbe with the game closed for installation and fresh restarts for verification.
2. Record game executable/build hashes and generate relevant runtime reflection/header/property dumps locally. Search for scrap, dismantle, repair, work rate, interaction duration, enhancements, and tool upgrade data.
3. Trace effective duration/rate calculations, native versus Blueprint ownership, method parameters, lifecycle, progress UI, and upgrade application. The inspected multiplayer sample demonstrates a `Voyage` reflected module but provides no verified scrapping/repair contracts.
4. Select a narrow hook/data change and namespace extensive temporary logs: base/effective values, enhancement/tool context, applied factor, decision/fallback, completion/cancel, invalid targets. Never mutate UObject state from a worker callback without the proper game-thread dispatch.
5. Implement an original mod with per-mod handoff notes and register it only when its scope/name is selected. Record unknowns rather than inventing function names or offsets.

## Runtime test matrix

Compare vanilla and modded timing for scrapping and repairing, starting tool and upgraded tools, no enhancements and available enhancement combinations, small/large jobs, cancellation/retry, tool switch, reload, and repeated interactions. Test repair of partly damaged objects and scrap completion/yields. Each combination should be approximately 50% of its own vanilla baseline, allowing measurement/tick granularity. Verify relative upgrade benefits, progress UI, completion events, resource/energy/durability effects, and fresh logs. Re-run after game or loader updates.
