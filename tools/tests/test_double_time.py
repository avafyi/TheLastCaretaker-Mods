"""Exercise the shipped entry point with the native post-hook calling convention."""
import unittest
from test_pipeline import p


class DoubleTimeTests(unittest.TestCase):
    def runtime(self, setup=""):
        lua = p.lua_runtime()
        logs = []
        lua.globals().print = logs.append
        lua.execute('''
            function object(name, good)
                return {IsValid=function() return good ~= false end,
                        GetFullName=function() return name end}
            end
            function param(value) return {get=function() return value end} end
            function fname(value) return {ToString=function() return value end} end
            function StaticFindObject(path)
                local result = object(path)
                if path:find("GetPlayerItemActionTotalDuration", 1, true) then
                    result.ForEachProperty = function(self, callback)
                        for _, name in ipairs(signature or {"InPlayerController", "Item", "InAction", "ReturnValue"}) do
                            callback({GetFName=function() return fname(name) end,
                                      GetFullName=function() return name end})
                        end
                    end
                else
                    result.ForEachName = function(self, callback)
                        for name, value in pairs(enumValues or {Dismantle=0, Repair=1, Build=2, Craft=3}) do
                            callback(fname("EVoyagePlayerEnhancerItemActionType::" .. name), value)
                        end
                    end
                end
                return result
            end
            function RegisterHook(path, pre, post)
                hookPath, preHook, postHook = path, pre, post
                return 11, 12
            end
            function query(value, action, item, context)
                local original = param(value)
                local replacement = postHook(param(context or object("Library")), original,
                    param(object("Controller")), param(item or object("TestItem")), param(action))
                -- A native post hook returns an override; nil preserves the original.
                assert(original:get() == value or value ~= value, "modified original wrapper")
                if replacement == nil then return value end
                return replacement
            end
        ''')
        lua.execute(setup)
        lua.execute((p.ROOT / "mods/DoubleTime/scripts/main.lua").read_text())
        return lua, logs

    def test_tool_and_enhancement_matrix_uses_each_original_result(self):
        lua, logs = self.runtime()
        for base in (0.04, 1, 8, 90):
            for tool_factor in (1, 0.75, 0.4):
                for enhancement_factor in (1, 0.8, 0.5):
                    vanilla = base * tool_factor * enhancement_factor
                    for action in (0, 1):
                        for _ in range(3):
                            self.assertAlmostEqual(lua.globals().query(vanilla, action), vanilla / 2)
        self.assertIn("ready:", "".join(logs))

    def test_enum_names_drive_action_selection(self):
        lua, _ = self.runtime('enumValues = {Dismantle=7, Repair=9, Build=0, Craft=1}')
        for action in (7, 9):
            self.assertEqual(lua.globals().query(10, action), 5)
        for action in (0, 1, 2, 3, 99):
            self.assertEqual(lua.globals().query(10, action), 10)

    def test_invalid_values_and_objects_preserve_vanilla(self):
        lua, logs = self.runtime()
        for value in (0, -1, float("inf"), -float("inf"), "bad"):
            self.assertEqual(lua.globals().query(value, 0), value)
        self.assertNotEqual(lua.globals().query(float("nan"), 1), 0)
        invalid = lua.globals().object("Destroyed", False)
        self.assertEqual(lua.globals().query(10, 0, invalid), 10)
        self.assertEqual(lua.globals().query(10, 1, None, invalid), 10)
        self.assertIn("fallback-", "".join(logs))

    def test_reload_and_repeated_queries_do_not_mutate_item_or_original(self):
        for _ in range(2):
            lua, logs = self.runtime()
            item = lua.globals().object("SameItem")
            item.DismantleDuration = 20
            for _ in range(5):
                self.assertEqual(lua.globals().query(8, 0, item), 4)
            self.assertEqual(lua.globals().query(4, 0, item), 2)
            self.assertEqual(item.DismantleDuration, 20)
            self.assertEqual(sum("duration-Dismantle:" in line for line in logs), 2)

    def test_contract_or_missing_api_refuses_activation(self):
        for setup in (
            'RegisterHook=nil',
            'StaticFindObject=nil',
            'signature={"InPlayerController", "Item", "ReturnValue", "InAction"}',
            'enumValues={Build=0, Craft=1}',
            'function RegisterHook() error("fixture hook rejection") end',
        ):
            lua, logs = self.runtime(setup)
            text = "".join(logs)
            self.assertIn("failed:", text)
            self.assertNotIn("ready:", text)

    def test_callback_failure_leaves_original_and_reports_transition(self):
        lua, logs = self.runtime()
        lua.execute('''
            local broken = {get=function() error("expired param") end}
            assert(postHook(param(object("Library")), param(8), nil, nil, broken) == nil)
            assert(postHook(param(object("Library")), param(8), nil, nil, broken) == nil)
        ''')
        self.assertEqual(sum("failure:" in line for line in logs), 1)


if __name__ == "__main__":
    unittest.main()
