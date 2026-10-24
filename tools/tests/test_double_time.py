"""Exercise final scrapping timing, repair writes, and reload protection."""
from pathlib import Path
import tempfile
import unittest
from test_pipeline import p, TEST_ROOT


class DoubleTimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()

    def runtime(self, setup='', engine=123):
        lua = p.lua_runtime()
        logs = []
        lua.globals().print = logs.append
        lua.globals().engineAddress = engine
        lua.execute('''
            items = {}
            pending = {}
            hooks = {}
            function StaticFindObject(path) return {IsValid=function() return true end} end
            function RegisterHook(path, pre, post)
                assert(hooks[path] == nil, 'duplicate hook')
                hooks[path]={pre=pre, post=post}
                return 1,2
            end
            function param(value)
                return {get=function() return value end, set=function(_, v) value=v end}
            end
            function scrapDuration(target, original)
                local result = param(original)
                for path, hook in pairs(hooks) do
                    if path:find(':GetActionDuration', 1, true) then
                        assert(hook.pre(nil, nil, param(target), result) == nil)
                    end
                end
                return result:get()
            end
            function asset(name, scrap, repair)
                local item = {DismantleDuration=scrap, RepairDuration=repair,
                    CraftTime=30, DismantleElectricityCost=7, RepairElectricityCost=9}
                item.GetFullName = function() return name end
                item.IsValid = function() return item.alive ~= false end
                return item
            end
            function FindFirstOf(name)
                return {IsValid=function() return true end,
                        GetAddress=function() return engineAddress end}
            end
            function FindAllOf(name) assert(name=='VoyageItem'); return items end
            function NotifyOnNewObject(path, callback)
                if path=='/Script/Voyage.VoyageItem' then newItem=callback
                else assert(path=='/Script/Voyage.EquipmentAbilityComponent'); newAbility=callback end
            end
            function RegisterLoadMapPostHook(callback) mapLoaded = callback end
            Key = {F10=121}
            ModifierKey = {CONTROL=1, SHIFT=2}
            function IsKeyBindRegistered() return false end
            function RegisterKeyBindAsync(key, modifiers, callback)
                assert(key==121 and modifiers[1]==1 and modifiers[2]==2)
                toggleTiming = callback
            end
            function ExecuteWithDelay(ms, callback)
                assert(ms==1000); pending[#pending+1] = callback
            end
            function ExecuteInGameThread(callback) callback() end
            function flushCallbacks()
                local callbacks = pending; pending = {}
                for _, callback in ipairs(callbacks) do callback() end
            end
        ''')
        lua.execute(setup)
        source = (p.ROOT / 'mods/DoubleTime/scripts/main.lua').read_text()
        lua.execute(source, name='@' + (self.root / 'scripts/main.lua').as_posix())
        return lua, logs

    def test_final_scrap_time_and_repair_scale_once_preserving_scrap_base(self):
        lua, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        lua.globals().flushCallbacks()
        item = lua.globals()["items"][1]
        self.assertEqual(item.DismantleDuration, 20)
        self.assertEqual(item.RepairDuration, 4)
        for tool in (1, .75, .4):
            for enhancer in (1, .8, .5):
                vanilla = 20 * tool * enhancer
                self.assertAlmostEqual(lua.globals().scrapDuration(item, vanilla), vanilla / 2)
        for _ in range(4):
            lua.globals().mapLoaded()
            lua.globals().flushCallbacks()
        self.assertEqual(item.DismantleDuration, 20)
        self.assertEqual(item.CraftTime, 30)
        self.assertEqual(item.DismantleElectricityCost, 7)
        self.assertEqual(item.RepairElectricityCost, 9)
        self.assertEqual(sum('applied:' in line for line in logs), 1)

    def test_new_assets_are_debounced_and_scanned_after_serialization(self):
        lua, _ = self.runtime()
        lua.globals().flushCallbacks()
        lua.execute('''
            items[1]=asset("VoyageItem /Game/New.A", 0, 0)
            for i=1,10 do newItem(items[1]) end
            assert(#pending==1)
            items[1].DismantleDuration=12
            items[1].RepairDuration=6
            flushCallbacks()
            assert(items[1].DismantleDuration==12 and items[1].RepairDuration==3)
        ''')

    def test_new_lua_state_recovers_originals_without_compounding(self):
        first, _ = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        first.globals().flushCallbacks()
        second, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 10, 4)}')
        second.globals().flushCallbacks()
        self.assertEqual(second.globals()["items"][1].DismantleDuration, 20)
        self.assertIn('recovered current session', ''.join(logs))
        # Reinstantiated asset in the same process starts with its vanilla base.
        second.execute('items={asset("VoyageItem /Game/Test.A", 20, 8)}; mapLoaded(); flushCallbacks()')
        self.assertEqual(second.globals()["items"][1].DismantleDuration, 20)

    def test_new_process_discards_old_session_and_accepts_changed_game_values(self):
        first, _ = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        first.globals().flushCallbacks()
        fresh, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 10, 6)}', engine=456)
        fresh.globals().flushCallbacks()
        self.assertEqual(fresh.globals()["items"][1].DismantleDuration, 10)
        self.assertEqual(fresh.globals()["items"][1].RepairDuration, 3)
        self.assertIn('new game session', ''.join(logs))

    def test_invalid_default_and_non_asset_objects_are_preserved(self):
        lua, _ = self.runtime('''
            items={asset("VoyageItem /Script/Voyage.Default__VoyageItem", 20, 8),
                   asset("VoyageItem /Engine/Test.A", 20, 8),
                   asset("VoyageItem /Game/Bad.A", -1, 0),
                   asset("VoyageItem /Game/Gone.A", 20, 8)}
            items[4].alive=false
        ''')
        lua.globals().flushCallbacks()
        self.assertEqual(lua.globals()["items"][1].DismantleDuration, 20)
        self.assertEqual(lua.globals()["items"][2].DismantleDuration, 20)
        self.assertEqual(lua.globals()["items"][3].DismantleDuration, -1)
        self.assertEqual(lua.globals()["items"][4].DismantleDuration, 20)

    def test_corrupt_reload_ledger_refuses_writes(self):
        (self.root / 'runtime-baselines.tsv').write_text('DoubleTime-v2\t7B\ncorrupted\n')
        lua, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 10, 4)}')
        lua.globals().flushCallbacks()
        self.assertEqual(lua.globals()["items"][1].DismantleDuration, 10)
        self.assertIn('invalid reload ledger', ''.join(logs))

    def test_missing_api_stays_inactive(self):
        lua, logs = self.runtime('NotifyOnNewObject=nil')
        self.assertIn('failed:', ''.join(logs))
        self.assertEqual(len(lua.globals().pending), 0)

    def test_diagnostic_toggle_restores_exact_originals_and_reapplies_once(self):
        lua, logs = self.runtime('items={asset("VoyageItem /Game/Cable.Extender", 2, 3)}')
        lua.globals().flushCallbacks()
        item = lua.globals()["items"][1]
        self.assertEqual(item.DismantleDuration, 2)
        self.assertEqual(lua.globals().scrapDuration(item, 2), 1)
        for _ in range(3):
            lua.globals().toggleTiming()
            lua.globals().flushCallbacks()
            self.assertEqual(item.DismantleDuration, 2)
            self.assertEqual(item.RepairDuration, 3)
            self.assertEqual(lua.globals().scrapDuration(item, 2), 2)
            lua.globals().mapLoaded()
            lua.globals().flushCallbacks()
            self.assertEqual(item.DismantleDuration, 2)
            lua.globals().toggleTiming()
            lua.globals().flushCallbacks()
            self.assertEqual(item.DismantleDuration, 2)
            self.assertEqual(item.RepairDuration, 1.5)
            self.assertEqual(lua.globals().scrapDuration(item, 2), 1)
        self.assertEqual(item.CraftTime, 30)
        self.assertEqual(item.DismantleElectricityCost, 7)
        self.assertIn('diagnostic-toggle', ''.join(logs))

    def test_assets_loaded_during_vanilla_mode_use_unscaled_baselines(self):
        lua, _ = self.runtime()
        lua.globals().flushCallbacks()
        lua.globals().toggleTiming()
        lua.globals().flushCallbacks()
        lua.execute('items={asset("VoyageItem /Game/Late.Extender", 2, 3)}; newItem(); flushCallbacks()')
        self.assertEqual(lua.globals()["items"][1].DismantleDuration, 2)
        lua.globals().toggleTiming()
        lua.globals().flushCallbacks()
        self.assertEqual(lua.globals()["items"][1].DismantleDuration, 2)
        self.assertEqual(lua.globals().scrapDuration(lua.globals()["items"][1], 2), 1)

    def test_diagnostic_hooks_observe_without_overriding_results(self):
        lua, logs = self.runtime('''
            hooks = {}
            function StaticFindObject(path) return {IsValid=function() return true end} end
            function RegisterHook(path, pre, post)
                hooks[path]={pre=pre, post=post}
                return 1,2
            end
        ''')
        lua.globals().flushCallbacks()
        lua.execute('''
            local function param(value) return {get=function() return value end} end
            local actor = asset("Extender /Game/Map.Extender", 2, 3)
            actor.bFoundConnection = false
            for path, hook in pairs(hooks) do
                if path:find("CanDismantle", 1, true) then
                    assert(hook.pre(param(actor)) == nil)
                    assert(hook.pre(param(actor)) == nil)
                    assert(actor.bFoundConnection == false)
                elseif not path:find('GetActionDuration', 1, true) then
                    assert(hook.pre(nil, nil, param(actor), param(0)) == nil)
                    assert(hook.post(nil, param(true), nil, param(actor)) == nil)
                end
            end
        ''')
        self.assertEqual(sum('extender-eligibility-query:' in line for line in logs), 1)
        self.assertIn('dismantle-return: success=true', ''.join(logs))

    def test_delayed_tool_class_load_registers_once_without_scrap_field_fallback(self):
        lua, logs = self.runtime('''
            classReady=false
            function StaticFindObject(path) return {IsValid=function() return classReady end} end
            items={asset("VoyageItem /Game/Cable.Extender", 2, 3)}
        ''')
        lua.globals().flushCallbacks()
        item = lua.globals()["items"][1]
        self.assertEqual(item.DismantleDuration, 2)
        self.assertEqual(lua.globals().scrapDuration(item, 2), 2)
        lua.execute('classReady=true; newAbility(); flushCallbacks(); newAbility(); flushCallbacks()')
        self.assertEqual(lua.globals().scrapDuration(item, 2), 1)
        self.assertEqual(sum('timing-hook:' in line for line in logs), 1)

    def test_final_duration_invalid_values_remain_unmodified(self):
        lua, _ = self.runtime('items={asset("VoyageItem /Game/Cable.Extender", 2, 3)}')
        lua.globals().flushCallbacks()
        item = lua.globals()["items"][1]
        for value in (0, -1, float('inf')):
            self.assertEqual(lua.globals().scrapDuration(item, value), value)
        item.alive = False
        self.assertEqual(lua.globals().scrapDuration(item, 2), 2)


if __name__ == '__main__':
    unittest.main()
