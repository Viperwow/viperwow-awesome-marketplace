# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Pick Claude Code plugins into apm.yml.

uv run migrate.py                      list enabled Claude plugins and the apm.yml set
uv run migrate.py add NAME@MP ...      add plugins to apm.yml
uv run migrate.py remove NAME@MP ...   remove plugins (or raw apm.yml refs) from apm.yml
uv run migrate.py sync                 rebuild the marketplace block from apm.yml and apm.lock.yaml
"""
import json
import sys
from pathlib import Path

import yaml

CLAUDE = Path.home() / ".claude"
MANIFEST = Path(__file__).with_name("apm.yml")


def github_slug(url):
    for prefix in ("https://github.com/", "git@github.com:"):
        if url.startswith(prefix):
            return url[len(prefix):].removesuffix(".git").rstrip("/")
    return None


def to_ref(mp_repo, source):
    """Marketplace plugin source -> apm.yml dependency entry, or None if unmappable."""
    if isinstance(source, str):
        sub = (source[2:] if source.startswith("./") else source).strip("/")
        return f"{mp_repo}/{sub}" if sub else mp_repo
    kind = source.get("source")
    if kind == "github":
        return source["repo"]
    if kind == "url":
        return {"git": source["url"].removesuffix(".git")}
    if kind == "git-subdir":
        slug = github_slug(source["url"]) or source["url"]
        return f"{slug}/{source['path'].strip('/')}"
    return None


def key(ref):
    """Comparable identity of an apm.yml entry, ignoring #ref pins, case and URL form."""
    if isinstance(ref, dict):
        base = ref.get("git", "")
        base = github_slug(base) or base.removesuffix(".git")
        return f"{base}/{ref['path']}".lower() if ref.get("path") else base.lower()
    ref = ref.split("#", 1)[0]
    return (github_slug(ref) or ref).lower()


def to_package(ref, commit):
    """apm.yml dependency entry -> marketplace package pinned to commit."""
    if isinstance(ref, dict):
        url, sub = ref["git"].removesuffix(".git"), ref.get("path", "")
    else:
        parts = ref.split("#", 1)[0].split("/")
        url, sub = "https://github.com/" + "/".join(parts[:2]), "/".join(parts[2:])
    # Claude Code clones git-subdir sources only from a full URL.
    pkg = {"name": (sub or url).rstrip("/").rsplit("/", 1)[-1], "source": url if sub else github_slug(url) or url}
    if sub:
        pkg["subdir"] = sub
    pkg["ref"] = commit
    return pkg


def sync(data, lock):
    """Rebuild marketplace.packages from dependencies.apm, pinned to the lockfile commits."""
    commits = {
        key(f"{d['repo_url']}/{d['virtual_path']}" if d.get("virtual_path") else d["repo_url"]): d["resolved_commit"]
        for d in lock.get("dependencies", [])
    }
    old = {p["name"]: p for p in data["marketplace"].get("packages") or []}
    packages, missing = [], []
    for ref in data["dependencies"]["apm"]:
        commit = commits.get(key(ref))
        if commit is None:
            missing.append(ref)
            continue
        pkg = to_package(ref, commit)
        kept = {k: v for k, v in old.get(pkg["name"], {}).items() if k not in ("source", "subdir", "ref")}
        packages.append({"category": "Productivity", **kept, **pkg})
    data["marketplace"]["packages"] = packages
    return missing


def claude_plugins():
    """Enabled plugin@marketplace -> apm ref (None when the source is not mappable)."""
    settings = json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8"))
    known = json.loads((CLAUDE / "plugins" / "known_marketplaces.json").read_text(encoding="utf-8"))
    out = {}
    for full, on in settings.get("enabledPlugins", {}).items():
        if not on:
            continue
        name, mp = full.rsplit("@", 1)
        src = known.get(mp, {}).get("source", {})
        mp_repo = src.get("repo") or github_slug(src.get("url", ""))
        manifest = CLAUDE / "plugins" / "marketplaces" / mp / ".claude-plugin" / "marketplace.json"
        if not mp_repo or not manifest.exists():
            out[full] = None
            continue
        plugins = json.loads(manifest.read_text(encoding="utf-8"))["plugins"]
        entry = next((p for p in plugins if p["name"] == name), None)
        out[full] = to_ref(mp_repo, entry["source"]) if entry else None
    return out


def load():
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    data.setdefault("dependencies", {})
    if data["dependencies"].get("apm") is None:
        data["dependencies"]["apm"] = []
    return data


def save(data):
    MANIFEST.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def show(plugins, deps):
    in_set = {key(d) for d in deps}
    mapped = set()
    print("Claude plugins:")
    for full, ref in sorted(plugins.items()):
        if ref is None:
            print(f"  [?] {full}  (source not mappable)")
            continue
        mapped.add(key(ref))
        mark = "x" if key(ref) in in_set else " "
        print(f"  [{mark}] {full}  ->  {ref}")
    extra = [d for d in deps if key(d) not in mapped]
    if extra:
        print("Only in apm.yml:")
        for d in extra:
            print(f"  [x] {d}")


def main(argv):
    plugins = claude_plugins()
    data = load()
    deps = data["dependencies"]["apm"]
    cmd, names = (argv[0], argv[1:]) if argv else ("list", [])
    if cmd == "list":
        show(plugins, deps)
        return 0
    if cmd == "sync":
        lock = MANIFEST.with_name("apm.lock.yaml")
        missing = sync(data, yaml.safe_load(lock.read_text(encoding="utf-8")) if lock.exists() else {})
        for ref in missing:
            print(f"not in apm.lock.yaml, run apm install: {ref}")
        if missing:
            return 1
        save(data)
        print(f"synced {len(data['marketplace']['packages'])} packages")
        return 0
    if cmd not in ("add", "remove") or not names:
        print(__doc__)
        return 2
    for name in names:
        ref = plugins.get(name, name if cmd == "remove" else None)
        if ref is None:
            print(f"skip {name}: not an enabled plugin with a mappable source")
            continue
        present = [d for d in deps if key(d) == key(ref)]
        if cmd == "add" and not present:
            deps.append(ref)
            print(f"added {name} -> {ref}")
        elif cmd == "remove" and present:
            deps.remove(present[0])
            print(f"removed {name}")
        else:
            print(f"unchanged {name}")
    save(data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
