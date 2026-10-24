# Durable knowledge

- ID `dev-probe`, prefix `probe`, GUID `com.ava.thelastcaretaker.devprobe`.
- Original UE4SS Lua starter. Emits namespaced startup/API diagnostics only. Never writes saves or installs gameplay hooks.
- Folder marker `enabled.txt` is generated during build; no shared mod-list edits. This activation mode is suitable for independent mods without load-order requirements.
- Syntax validation uses pinned Lupa 2.6's Lua 5.4 parser. This does not prove UE4SS or game compatibility.
