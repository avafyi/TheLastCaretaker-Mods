-- Original diagnostic starter. No gameplay hooks or save writes.
local prefix = "[Caretaker.DevProbe] "
local function log(event, detail)
    print(prefix .. event .. ": " .. tostring(detail) .. "\n")
end

log("init", "version=0.1.0; target=The Last Caretaker; mode=read-only")
log("config", "no gameplay changes; no periodic callbacks; no save writes")
for _, name in ipairs({"RegisterHook", "FindFirstOf", "StaticFindObject"}) do
    log("api", name .. "=" .. type(_G[name]))
end
if type(RegisterHook) ~= "function" then
    log("fallback", "UE4SS hook API unavailable; diagnostic only")
    log("failed", "expected UE4SS runtime API missing")
else
    log("ready", "Lua initialized; gameplay hooks intentionally absent")
end
