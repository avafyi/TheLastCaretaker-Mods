-- DoubleTime: native callers read these reflected base-duration fields directly.
local prefix = "[Caretaker.DoubleTime] "
local source = debug.getinfo(1, "S").source
local scriptFolder = source:match("^@(.+)[/\\][^/\\]+$")
local ledgerPath = scriptFolder and (scriptFolder .. "/../runtime-baselines.tsv")
local fields = {"DismantleDuration", "RepairDuration"}
local durationFactor = 0.5
local baselines, ledger, session
local queued = false
local lastFailure
local diagnosticHooks = {}
local diagnosticState = {}

local function log(event, detail)
    print(prefix .. event .. ": " .. tostring(detail) .. "\n")
end

local function finitePositive(value)
    return type(value) == "number" and value == value and value > 0 and value < math.huge
end

local function initializeLedger()
    if ledger then return end
    assert(ledgerPath, "cannot resolve this script's directory for reload protection")
    local engine = FindFirstOf("GameEngine")
    assert(engine and engine:IsValid(), "GameEngine not ready; waiting for a lifecycle rescan")
    -- The engine object is process-local and survives Lua mod reloads. A new
    -- game process gets a new session and freshly loaded vanilla asset values.
    session = "DoubleTime-v2\t" .. string.format("%X", engine:GetAddress())
    baselines = {}
    local input = io.open(ledgerPath, "r")
    local sameSession = false
    if input then
        sameSession = input:read("*l") == session
        if sameSession then
            for line in input:lines() do
                local name, field, textValue = line:match("^([^\t]+)\t([^\t]+)\t([^\t]+)$")
                local value = tonumber(textValue)
                if not name or (field ~= fields[1] and field ~= fields[2]) or not finitePositive(value) then
                    input:close()
                    error("invalid reload ledger; preserve it and restart the game before retrying")
                end
                baselines[name .. "\t" .. field] = value
            end
        end
        input:close()
    end
    local output, failure = io.open(ledgerPath, sameSession and "a" or "w")
    assert(output, "cannot open reload ledger: " .. tostring(failure))
    if not sameSession then
        assert(output:write(session .. "\n"))
        assert(output:flush())
    end
    ledger = output
    log("ledger", (sameSession and "recovered current session" or "new game session") .. "; file=" .. ledgerPath)
end

local function apply(item)
    if not item or not item:IsValid() then return 0 end
    local name = item:GetFullName()
    -- Default objects can seed new instances with already-scaled values, so
    -- touch asset instances only. No raw offsets or class defaults are edited.
    if name:find("Default__", 1, true) or not name:find(" /Game/", 1, true) then return 0 end
    assert(not name:find("[\t\r\n]"), "unsupported control character in asset name")
    local changed = 0
    for _, field in ipairs(fields) do
        local current = item[field]
        if finitePositive(current) then
            local key = name .. "\t" .. field
            local original = baselines[key]
            if original == nil or (current ~= original and current ~= original * 0.5) then
                -- A serialized/reloaded definition or another stat update has
                -- supplied a new base. Journal before mutation, including flush,
                -- so Lua reload cannot halve an already-scaled value again.
                original = current
                assert(ledger:write(name .. "\t" .. field .. "\t" .. string.format("%.17g", original) .. "\n"))
                assert(ledger:flush())
                baselines[key] = original
                log("baseline", string.format("asset=%s; field=%s; vanilla=%.9g", name, field, original))
            end
            local desired = original * durationFactor
            if current ~= desired then
                item[field] = desired
                assert(item[field] == desired, "duration write/readback mismatch: " .. name .. ":" .. field)
                changed = changed + 1
                log("applied", string.format("asset=%s; field=%s; vanilla=%.9g; modded=%.9g; factor=%.1f", name, field, original, desired, durationFactor))
            end
        end
    end
    return changed
end

local function installDiagnostics()
    if type(RegisterHook) ~= "function" or type(StaticFindObject) ~= "function" then return end
    local path = "/Script/Voyage.VoyageGameplayBlueprintFunctionLibrary:DismantleDestructible"
    if not diagnosticHooks[path] then
        local func = StaticFindObject(path)
        if func and func:IsValid() then
            local ok, failure = pcall(function()
                local preId, postId = RegisterHook(path, function(_, _, actorParam, delayParam)
                    local good, detail = pcall(function()
                        local actor = actorParam:get()
                        if actor and actor:IsValid() then
                            log("dismantle-enter", string.format("actor=%s; delay=%s; duration-factor=%.1f",
                                actor:GetFullName(), tostring(delayParam:get()), durationFactor))
                        end
                    end)
                    if not good then log("diagnostic-failure", tostring(detail)) end
                end, function(_, result, _, actorParam)
                    local good, detail = pcall(function()
                        local actor = actorParam:get()
                        log("dismantle-return", "success=" .. tostring(result:get()) .. "; actor=" ..
                            ((actor and actor:IsValid()) and actor:GetFullName() or "invalid/removed"))
                    end)
                    if not good then log("diagnostic-failure", tostring(detail)) end
                end)
                diagnosticHooks[path] = {preId, postId}
                log("diagnostic-hook", path .. "; observation only; native direct calls may bypass")
            end)
            if not ok then log("diagnostic-failure", tostring(failure)) end
        end
    end
    local cablePath = "/Game/Blueprints/Cables/BP_Cable_Extender_Socket_Base.BP_Cable_Extender_Socket_Base_C:CanDismantle"
    if not diagnosticHooks[cablePath] then
        local func = StaticFindObject(cablePath)
        if func and func:IsValid() then
            local ok, failure = pcall(function()
                local preId, postId = RegisterHook(cablePath, function(context)
                    local good, detail = pcall(function()
                        local actor = context:get()
                        if not actor or not actor:IsValid() then return end
                        local name = actor:GetFullName()
                        local state = tostring(actor.bFoundConnection) .. "; factor=" .. durationFactor
                        if diagnosticState[name] ~= state then
                            diagnosticState[name] = state
                            log("extender-eligibility-query", "actor=" .. name .. "; cached-connection=" .. state)
                        end
                    end)
                    if not good then log("diagnostic-failure", tostring(detail)) end
                    -- A Blueprint hook's return value is left entirely untouched.
                end)
                diagnosticHooks[cablePath] = {preId, postId}
                log("diagnostic-hook", cablePath .. "; observation only")
            end)
            if not ok then log("diagnostic-failure", tostring(failure)) end
        end
    end
end

local function scan(reason)
    local ok, failure = pcall(function()
        initializeLedger()
        installDiagnostics()
        local items = FindAllOf("VoyageItem") or {}
        local changed, failed = 0, 0
        for _, item in ipairs(items) do
            local good, count = pcall(apply, item)
            if good then changed = changed + count else
                failed = failed + 1
                log("failure", "asset skipped: " .. tostring(count))
            end
        end
        log("scan", string.format("reason=%s; found=%d; fields-changed=%d; failures=%d; factor=%.1f", reason, #items, changed, failed, durationFactor))
        if #items > 0 and failed == 0 then
            log("ready", "version=0.2.1; item duration fields verified; duration-factor=" .. durationFactor)
        else
            log("fallback", "no complete asset scan yet; waiting for next load event")
        end
    end)
    if ledger then
        ledger:close()
        ledger = nil
    end
    if not ok and lastFailure ~= tostring(failure) then
        lastFailure = tostring(failure)
        log("failure", "scan deferred: " .. lastFailure)
    end
end

local function queueScan(reason)
    if queued then return end
    queued = true
    ExecuteWithDelay(1000, function()
        ExecuteInGameThread(function()
            queued = false
            scan(reason)
        end)
    end)
end

log("init", "version=0.2.1; target=The Last Caretaker; native item-duration data path")
log("config", "DismantleDuration/RepairDuration factor=0.5; enhancement/tool calculations retained; reload ledger enabled")
local ok, failure = pcall(function()
    for _, name in ipairs({"FindFirstOf", "FindAllOf", "NotifyOnNewObject", "ExecuteWithDelay", "ExecuteInGameThread", "RegisterLoadMapPostHook"}) do
        assert(type(_G[name]) == "function", name .. " unavailable")
    end
    NotifyOnNewObject("/Script/Voyage.VoyageItem", function() queueScan("item-loaded") end)
    RegisterLoadMapPostHook(function() queueScan("map-loaded") end)
    if type(RegisterKeyBindAsync) == "function" and type(IsKeyBindRegistered) == "function" and Key and ModifierKey then
        local modifiers = {ModifierKey.CONTROL, ModifierKey.SHIFT}
        if not IsKeyBindRegistered(Key.F10, modifiers) then
            RegisterKeyBindAsync(Key.F10, modifiers, function()
                -- Async input callback changes Lua state only; UObject access
                -- remains in the debounced game-thread scan.
                durationFactor = durationFactor == 0.5 and 1.0 or 0.5
                log("diagnostic-mode", "duration-factor=" .. durationFactor .. "; apply pending; wait for ready log")
                queueScan("diagnostic-toggle")
            end)
            log("diagnostic-key", "Ctrl+Shift+F10 toggles vanilla/2x duration; wait one second for scan")
        else
            log("diagnostic-failure", "Ctrl+Shift+F10 already bound; diagnostic toggle not registered")
        end
    end
    queueScan("startup")
    log("watching", "startup + debounced item construction + map load; no duration query hook")
end)
if not ok then
    log("failed", tostring(failure))
    log("fallback", "DoubleTime inactive; no asset durations changed")
end
