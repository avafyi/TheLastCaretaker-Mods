"""Exercise actual asset writes, lifecycle scans, and cross-Lua reload journaling."""
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
            function NotifyOnNewObject(path, callback) newItem = callback end
            function RegisterLoadMapPostHook(callback) mapLoaded = callback end
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

    def test_base_fields_halved_once_across_lifecycle_and_upgrade_combinations(self):
        lua, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        lua.globals().flushCallbacks()
        item = lua.globals()["items"][1]
        self.assertEqual(item.DismantleDuration, 10)
        self.assertEqual(item.RepairDuration, 4)
        for tool in (1, .75, .4):
            for enhancer in (1, .8, .5):
                self.assertAlmostEqual(item.DismantleDuration * tool * enhancer, 20 * tool * enhancer / 2)
        for _ in range(4):
            lua.globals().mapLoaded()
            lua.globals().flushCallbacks()
        self.assertEqual(item.DismantleDuration, 10)
        self.assertEqual(item.CraftTime, 30)
        self.assertEqual(item.DismantleElectricityCost, 7)
        self.assertEqual(item.RepairElectricityCost, 9)
        self.assertEqual(sum('applied:' in line for line in logs), 2)

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
            assert(items[1].DismantleDuration==6 and items[1].RepairDuration==3)
        ''')

    def test_new_lua_state_recovers_originals_without_compounding(self):
        first, _ = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        first.globals().flushCallbacks()
        second, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 10, 4)}')
        second.globals().flushCallbacks()
        self.assertEqual(second.globals()["items"][1].DismantleDuration, 10)
        self.assertIn('recovered current session', ''.join(logs))
        # Reinstantiated asset in the same process starts with its vanilla base.
        second.execute('items={asset("VoyageItem /Game/Test.A", 20, 8)}; mapLoaded(); flushCallbacks()')
        self.assertEqual(second.globals()["items"][1].DismantleDuration, 10)

    def test_new_process_discards_old_session_and_accepts_changed_game_values(self):
        first, _ = self.runtime('items={asset("VoyageItem /Game/Test.A", 20, 8)}')
        first.globals().flushCallbacks()
        fresh, logs = self.runtime('items={asset("VoyageItem /Game/Test.A", 10, 6)}', engine=456)
        fresh.globals().flushCallbacks()
        self.assertEqual(fresh.globals()["items"][1].DismantleDuration, 5)
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


if __name__ == '__main__':
    unittest.main()
