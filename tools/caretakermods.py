"""Local UE4SS Lua workshop. Python 3.12 x64; game files change only on explicit install/deploy."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path("Voyage/Binaries/Win64")
EXE = "VoyageSteam-Win64-Shipping.exe"
INSTALL = ".caretakermods-install.json"
# Nexus file 1088: archive hash matches its linked VirusTotal record. The actual
# bundled DLL differs from the hash quoted in the author's description.
LOADER_HASH = "91d5444f41d19d0bb502f0fbdc15d76421e20359e898caa39e41e134c8f87958"
LOADER_ARCHIVE_HASH = "28b1e3b5c4efd6898cf1edc16b4118b2067bec94eda42fe8e53b026e235087a4"
WHEEL = "lupa-2.6-cp312-cp312-win_amd64.whl"
WHEEL_URL = "https://files.pythonhosted.org/packages/b8/15/5121e68aad3584e26e1425a5c9a79cd898f8a152292059e128c206ee817c/" + WHEEL
WHEEL_HASH = "c735a1ce8ee60edb0fe71d665f1e6b7c55c6021f1d340eb8c865952c602cd36f"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def within(parent, path):
    parent, path = Path(parent).resolve(), Path(path).resolve()
    if path == parent or not path.is_relative_to(parent):
        raise ValueError(f"Path must remain inside {parent}: {path}")
    return path


def run(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def registry(root=ROOT):
    data = read_json(root / "caretakermods.json")
    if data["schemaVersion"] != 1:
        raise ValueError("Unsupported registry schema")
    seen = {key: set() for key in ("id", "folder", "prefix", "guid")}
    for mod in data["mods"]:
        for key in seen:
            value = mod[key]
            pattern = r"[a-z][a-z0-9-]*" if key in ("id", "prefix") else r"[A-Za-z][A-Za-z0-9.]*"
            if not re.fullmatch(pattern, value) or value.lower() in seen[key]:
                raise ValueError(f"Invalid or duplicate {key}: {value}")
            seen[key].add(value.lower())
        if mod["kind"] != "ue4ss-lua":
            raise ValueError("Only ue4ss-lua mods are supported by this pipeline")
        folder = within(root / "mods", root / "mods" / mod["folder"])
        for name in ("scripts/main.lua", "README.md", "AGENT-NOTES.md", "WORKING-NOTES.md"):
            if not within(folder, folder / name).is_file():
                raise ValueError(f"Missing mod file: {folder / name}")
        script_files(folder)  # Validate all payload paths, including links.
    return data["mods"]


def game_root(root=ROOT):
    configured = os.environ.get("CARETAKER_GAME_ROOT")
    local = root / ".caretakerdev.local.json"
    if not configured and local.exists():
        configured = read_json(local).get("gameRoot")
    candidates = [Path(configured)] if configured else []
    if not configured:
        steam = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam"
        libraries = [steam]
        vdf = steam / "steamapps/libraryfolders.vdf"
        if vdf.exists():
            libraries += [Path(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8"))]
        for library in libraries:
            manifest = library / "steamapps/appmanifest_1783560.acf"
            directory = "Voyage"
            if manifest.exists():
                match = re.search(r'"installdir"\s+"([^"]+)"', manifest.read_text(encoding="utf-8"))
                if match:
                    directory = match[1]
            candidates.append(within(library / "steamapps/common", library / "steamapps/common" / directory))
    for candidate in candidates:
        if (candidate / "Voyage.exe").is_file() and within(candidate, candidate / BINARY / EXE).is_file():
            return candidate.resolve()
    raise ValueError("The Last Caretaker install not found; set CARETAKER_GAME_ROOT or .caretakerdev.local.json gameRoot")


def require_stopped():
    if os.name != "nt":
        raise ValueError("Live installation supports Windows only")
    for executable in ("Voyage.exe", EXE, "Voyage-Win64-Shipping.exe"):
        result = run(["tasklist", "/FI", f"IMAGENAME eq {executable}", "/FO", "CSV", "/NH"], capture_output=True, text=True)
        if f'"{executable.lower()}"' in result.stdout.lower():
            raise ValueError("The Last Caretaker is running; close it before installing/deploying, then freshly launch")


@contextmanager
def pipeline_lock(root=ROOT):
    path = root / ".cache/pipeline.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError(f"Another pipeline owns {path}; inspect the recorded PID before removing a stale lock")
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"pid": os.getpid(), "started": datetime.now(timezone.utc).isoformat()}, stream)
        yield
    finally:
        path.unlink()


def source_paths(mod):
    return [f'mods/{mod["folder"]}', "tools", "caretakermods.json", "deploy.ps1"]


def require_committed(root=ROOT):
    run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True)
    status = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, text=True).stdout
    if status.strip():
        raise ValueError(f"Commit source/tooling changes before deployment:\n{status}")


def fingerprint(mod, root=ROOT):
    accumulator = hashlib.sha256()
    for relative in source_paths(mod):
        path = root / relative
        for item in sorted(path.rglob("*")) if path.is_dir() else [path]:
            if not item.is_file() or "__pycache__" in item.parts:
                continue
            within(root, item)
            accumulator.update(item.relative_to(root).as_posix().encode())
            accumulator.update(item.read_bytes())
    return accumulator.hexdigest()


def lua_runtime(root=ROOT):
    sys.path.insert(0, str(root / ".tools/python"))
    try:
        from lupa.lua54 import LuaRuntime
    except ImportError as error:
        raise ValueError("Lua checker missing; run tools/bootstrap.ps1 (Python 3.12 x64)") from error
    return LuaRuntime(unpack_returned_tuples=True)


def extract_verified(archive, expected, destination):
    if digest(archive) != expected:
        raise ValueError(f"Archive checksum mismatch: {archive}")
    with zipfile.ZipFile(archive) as source:
        entries = []
        names = set()
        for info in source.infolist():
            name = info.filename.replace("\\", "/")
            if ":" in name or name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"Unsafe archive path: {name}")
            target = within(destination, destination / name)
            if name.lower() in names:
                raise ValueError(f"Duplicate archive path: {name}")
            names.add(name.lower())
            if info.file_size > 512 * 1024 * 1024 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Unsupported archive member: {name}")
            if not info.is_dir():
                entries.append((info, target))
        for info, target in entries:
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(info) as stream, target.open("wb") as output:
                shutil.copyfileobj(stream, output)


def bootstrap(root=ROOT, lua_wheel=None, loader_archive=None, archive_sha256=None):
    if sys.version_info[:2] != (3, 12) or sys.maxsize <= 2**32:
        raise ValueError("Pinned Lua wheel requires Python 3.12 x64; use the bundled Codex Python")
    if not lua_wheel:
        lua_wheel = root / ".tools/downloads" / WHEEL
        lua_wheel.parent.mkdir(parents=True, exist_ok=True)
        if not lua_wheel.exists():
            print(f"[bootstrap:download] {WHEEL_URL}", flush=True)
            urllib.request.urlretrieve(WHEEL_URL, lua_wheel)
    extract_verified(Path(lua_wheel), WHEEL_HASH, root / ".tools/python")
    lua = lua_runtime(root)
    print(f'[bootstrap:verified] Lupa 2.6; {lua.eval("_VERSION")}; wheel={WHEEL_HASH}')
    if loader_archive:
        if not archive_sha256 or not re.fullmatch(r"[a-fA-F0-9]{64}", archive_sha256):
            raise ValueError("Supply --archive-sha256 for the exact reviewed UE4SS ZIP")
        if archive_sha256.lower() != LOADER_ARCHIVE_HASH:
            raise ValueError("Expected reviewed Nexus v1.3 file 1088 archive checksum")
        destination = root / ".cache" / ("loader-" + uuid.uuid4().hex)
        extract_verified(Path(loader_archive), archive_sha256.lower(), destination)
        dll = destination / "ue4ss/UE4SS.dll"
        if not dll.is_file() or digest(dll) != LOADER_HASH or not (destination / "dwmapi.dll").is_file():
            raise ValueError("Expected the game-specific v1.3 loader ZIP with pinned ue4ss/UE4SS.dll and dwmapi.dll")
        target = root / ".tools/ue4ss"
        if target.exists():
            raise ValueError("Local loader already staged; inspect it before an explicit upgrade")
        shutil.copytree(destination, target)
        write_json(root / ".tools/loader-provenance.json", {
            "version": "UE4SS_v3.0.1-1125-g527a483b", "source": "https://www.nexusmods.com/thelastcaretaker/mods/4",
            "archiveSha256": archive_sha256.lower(), "dllSha256": LOADER_HASH,
            "files": {p.relative_to(target).as_posix(): digest(p) for p in target.rglob("*") if p.is_file()}})
        print("[bootstrap:loader] verified and staged locally")
    print("[bootstrap:ready] No game files modified")


def script_files(folder):
    scripts = folder / "scripts"
    files = []
    for item in sorted(scripts.rglob("*")):
        within(folder, item)
        if item.is_file():
            if item.suffix != ".lua":
                raise ValueError(f"Only Lua source is packaged from scripts/: {item}")
            files.append(item)
    if not files:
        raise ValueError(f"No Lua scripts: {folder}")
    return files


def build(mod, root=ROOT):
    before = fingerprint(mod, root)
    lua = lua_runtime(root)
    compile_only = lua.eval("function(code, name) local f,e=load(code,name,'t',{}); if not f then error(e) end; return true end")
    folder = root / "mods" / mod["folder"]
    output = root / "artifacts/build" / mod["id"] / uuid.uuid4().hex
    output.mkdir(parents=True, exist_ok=True)
    for script in script_files(folder):
        compile_only(script.read_text(encoding="utf-8"), script.relative_to(root).as_posix())
        target = output / script.relative_to(folder)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script, target)
        print(f"[build:syntax-ok] {script.relative_to(root)}")
    (output / "enabled.txt").write_bytes(b"")
    shutil.copy2(folder / "README.md", output / "README.md")
    if fingerprint(mod, root) != before:
        raise ValueError("Source changed during build; rerun")
    print(f'[build:ready] {mod["id"]}; source={before}; runtime=unverified')
    return output, before


def package(mod, root=ROOT):
    output, source_hash = build(mod, root)
    archive = root / "artifacts/packages" / f'{mod["id"]}.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                target.write(path, f'ue4ss/Mods/{mod["folder"]}/{path.relative_to(output).as_posix()}')
    print(f"[package:ready] {archive}; sha256={digest(archive)}")
    return output, source_hash


def apply_files(plan, root=ROOT):
    """Preflight elsewhere, then replace staged files with rollback and persistent backups."""
    require_stopped()
    transaction = uuid.uuid4().hex
    backup = root / "artifacts/backups" / transaction
    old = {}
    try:
        for index, (source, target) in enumerate(plan):
            require_stopped()
            previous = target.read_bytes() if target.exists() else None
            old[target] = previous
            if previous is not None:
                backup.mkdir(parents=True, exist_ok=True)
                (backup / str(index)).write_bytes(previous)
                write_json(backup / "index.json", {str(i): str(p) for i, p in enumerate(old)})
            target.parent.mkdir(parents=True, exist_ok=True)
            staged = target.with_name(f".{target.name}.{transaction}.tmp")
            try:
                shutil.copy2(source, staged)
                if digest(staged) != digest(source):
                    raise ValueError(f"Staged hash verification failed: {target}")
                os.replace(staged, target)
                if digest(target) != digest(source):
                    raise ValueError(f"Installed hash verification failed: {target}")
            finally:
                staged.unlink(missing_ok=True)
            print(f"[write:verified] {target}")
    except Exception:
        for target, previous in reversed(list(old.items())):
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(previous)
        print("[write:rollback] restored prior files", file=sys.stderr)
        raise
    print(f"[write:complete] files={len(plan)}; backup={backup if backup.exists() else 'none'}")


def deploy_files(mod, output, source_hash, game, root=ROOT, dry_run=False):
    target = within(game, game / BINARY / "ue4ss/Mods" / mod["folder"])
    manifest_path = within(game, target / INSTALL)
    manifest = read_json(manifest_path) if manifest_path.exists() else None
    if manifest and manifest.get("id") != mod["id"]:
        raise ValueError("Conflicting deployment ownership")
    if target.exists() and not manifest and any(target.iterdir()):
        raise ValueError(f"Unmanaged mod directory: {target}")
    expected = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob("*") if p.is_file()}
    previous = manifest.get("files", {}) if manifest else {}
    if set(previous) - set(expected):
        raise ValueError("Obsolete owned files need explicit reviewed removal; deployment never deletes them")
    plan = []
    for relative, file_hash in expected.items():
        destination = within(game, target / relative)
        if destination.exists() and relative not in previous:
            raise ValueError(f"Unmanaged payload collision: {destination}")
        if destination.exists() and digest(destination) not in (previous.get(relative), file_hash):
            raise ValueError(f"Installed file was edited externally: {destination}")
        if not destination.exists() or digest(destination) != file_hash:
            plan.append((output / relative, destination))
    if not plan and manifest and manifest.get("sourceSha256") == source_hash:
        print(f'[current] {mod["id"]}')
        return "current"
    print(f'[deploy:plan] {mod["id"]}; files={len(plan)}; dry-run={dry_run}; target={target}')
    if dry_run:
        return "pending"
    local_manifest = root / ".cache" / (uuid.uuid4().hex + ".json")
    write_json(local_manifest, {"id": mod["id"], "sourceSha256": source_hash, "files": expected, "installedUtc": datetime.now(timezone.utc).isoformat()})
    apply_files([*plan, (local_manifest, manifest_path)], root)
    return "deployed"


def loader_plan(game, root=ROOT):
    source = root / ".tools/ue4ss"
    provenance = root / ".tools/loader-provenance.json"
    if not provenance.is_file():
        raise ValueError("Loader not staged; see docs/DEVELOPMENT.md for checksum-verified local bootstrap")
    metadata = read_json(provenance)
    if metadata["dllSha256"] != LOADER_HASH or digest(source / "ue4ss/UE4SS.dll") != LOADER_HASH:
        raise ValueError("Staged UE4SS DLL does not match pinned baseline")
    plan = []
    for relative, expected in metadata["files"].items():
        src = within(source, source / relative)
        dst = within(game, game / BINARY / relative)
        if digest(src) != expected:
            raise ValueError(f"Staged loader file changed: {src}")
        if dst.exists() and digest(dst) != expected:
            raise ValueError(f"Refusing to overwrite a different loader file: {dst}")
        if not dst.exists():
            plan.append((src, dst))
    return plan


def doctor(root=ROOT):
    print(f"[doctor] Python {sys.version.split()[0]}; root={root}")
    try:
        lua = lua_runtime(root)
        print(f'[doctor] Lua checker: {lua.eval("_VERSION")}')
    except ValueError as error:
        print(f"[doctor] {error}")
    game = game_root(root)
    executable = game / BINARY / EXE
    print(f"[doctor] Game={game}; executable={executable}; sha256={digest(executable)}")
    for relative in ("dwmapi.dll", "ue4ss/UE4SS.dll", "ue4ss/UE4SS-settings.ini"):
        path = within(game, game / BINARY / relative)
        print(f"[doctor] {relative}: {digest(path) if path.is_file() else 'MISSING'}")
    print("[doctor] Runtime compatibility requires a fresh in-game test")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bootstrap", "doctor", "check", "build", "package", "deploy", "install-loader"])
    parser.add_argument("--mod")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lua-wheel", type=Path)
    parser.add_argument("--loader-archive", type=Path)
    parser.add_argument("--archive-sha256")
    args = parser.parse_args()
    if args.command == "bootstrap":
        with pipeline_lock():
            bootstrap(lua_wheel=args.lua_wheel, loader_archive=args.loader_archive, archive_sha256=args.archive_sha256)
        return
    mods = registry()
    if args.mod:
        mods = [mod for mod in mods if mod["id"] == args.mod]
        if not mods:
            raise ValueError(f"Unknown mod: {args.mod}")
    if args.command == "check":
        print(f"[check] Registry/handoff valid: {len(mods)} mods")
        return
    if args.command == "doctor":
        doctor()
        return
    with pipeline_lock():
        if args.command == "install-loader":
            if not args.dry_run:
                require_stopped()
            plan = loader_plan(game_root())
            print(f"[loader:plan] files={len(plan)}; dry-run={args.dry_run}")
            if not args.dry_run:
                apply_files(plan)
            return
        if args.command == "deploy":
            game = game_root()
            if not args.dry_run:
                require_stopped()
                require_committed()
            dll = within(game, game / BINARY / "ue4ss/UE4SS.dll")
            proxy = within(game, game / BINARY / "dwmapi.dll")
            if not dll.is_file() or not proxy.is_file() or digest(dll) != LOADER_HASH:
                if not args.dry_run:
                    raise ValueError("Pinned UE4SS loader missing/different; inspect before installing or upgrading")
                print("[deploy:plan] Pinned loader missing; install and verify it before live deployment")
        for mod in mods:
            if args.command == "build":
                build(mod)
            else:
                output, source_hash = package(mod)
                if args.command == "deploy":
                    if not args.dry_run:
                        require_committed()
                    if fingerprint(mod) != source_hash:
                        raise ValueError("Source changed after packaging")
                    deploy_files(mod, output, source_hash, game, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[error] {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
