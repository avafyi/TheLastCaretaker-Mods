-- DoubleTime: scale the original effective duration, never a stored/upgraded value.
local prefix = "[Caretaker.DoubleTime] "
local durationPath = "/Script/Voyage.VoyageItemBlueprintFunctionLibrary:GetPlayerItemActionTotalDuration"
local enumPath = "/Script/Voyage.EVoyagePlayerEnhancerItemActionType"
local durationFactor = 0.5
local lastDecision = {}

local function log(event, detail)
    print(prefix .. event .. ": " .. tostring(detail) .. "\n")
end

local function transition(key, detail)
    if lastDecision[key] ~= detail then
        lastDecision[key] = detail
        log(key, detail)
    end
end

local function valid(object)
    return object ~= nil and object:IsValid()
end

log("init", "version=0.1.0; target=The Last Caretaker")
log("config", "effective-duration-factor=0.5; scrap/repair only; temporary transition diagnostics enabled")

local ok, failure = pcall(function()
    assert(type(RegisterHook) == "function", "RegisterHook unavailable")
    assert(type(StaticFindObject) == "function", "StaticFindObject unavailable")
    local durationFunction = StaticFindObject(durationPath)
    assert(valid(durationFunction), "effective-duration function unavailable: " .. durationPath)

    -- Refuse a changed contract instead of assigning meaning to the wrong argument.
    local expected = {"InPlayerController", "Item", "InAction", "ReturnValue"}
    local properties = {}
    durationFunction:ForEachProperty(function(property)
        properties[#properties + 1] = property:GetFName():ToString()
        log("signature", property:GetFullName())
    end)
    assert(#properties == #expected, "effective-duration parameter count changed")
    for index, name in ipairs(expected) do
        assert(properties[index] == name, "effective-duration parameter order changed at " .. index)
    end

    local actionEnum = StaticFindObject(enumPath)
    assert(valid(actionEnum), "action enum unavailable: " .. enumPath)
    local actions = {}
    actionEnum:ForEachName(function(name, value)
        local action = name:ToString():match("::([^:]+)$")
        log("enum", name:ToString() .. "=" .. tostring(value))
        if action == "Dismantle" or action == "Repair" then
            actions[value] = action
        end
    end)
    local count = 0
    for _ in pairs(actions) do count = count + 1 end
    assert(count == 2, "Dismantle/Repair enum contract changed")

    local function postDuration(context, originalResult, controllerParam, itemParam, actionParam)
        -- Native post-hook ABI: Context, original return value, original parameters.
        -- Returning nil preserves vanilla on unsupported actions or any Lua failure.
        local worked, replacement = pcall(function()
            local actionValue = actionParam:get()
            local action = actions[actionValue]
            if not action then
                transition("skip-" .. tostring(actionValue), "unrelated action; duration unchanged")
                return nil
            end
            local item = itemParam:get()
            if not valid(context:get()) or not valid(item) then
                transition("fallback-" .. action, "invalid context/item; original duration preserved")
                return nil
            end
            local original = originalResult:get()
            if type(original) ~= "number" or original ~= original or original <= 0 or original == math.huge then
                transition("fallback-" .. action, "non-positive/non-finite duration=" .. tostring(original) .. "; unchanged")
                return nil
            end
            local scaled = original * durationFactor
            transition("duration-" .. action, string.format(
                "item=%s; vanilla-effective=%.9g; modded=%.9g; factor=0.5; source=current-query",
                item:GetFullName(), original, scaled))
            return scaled
        end)
        if not worked then
            transition("failure", "duration callback failed; original preserved: " .. tostring(replacement))
            return nil
        end
        return replacement
    end

    local preId, postId = RegisterHook(durationPath, function() end, postDuration)
    assert(type(preId) == "number" and type(postId) == "number", "hook registration returned no IDs")
    log("hook", durationPath .. "; pre=" .. preId .. "; post=" .. postId)
end)

if ok then
    log("ready", "duration hook installed; fresh gameplay coverage/timing verification required")
else
    log("failed", tostring(failure))
    log("fallback", "DoubleTime inactive; no stored values or save data changed")
end
