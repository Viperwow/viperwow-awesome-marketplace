# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
from migrate import key, sync, to_package, to_ref

assert to_ref("JuliusBrussee/caveman", "./") == "JuliusBrussee/caveman"
assert to_ref("anthropics/claude-plugins-official", "./plugins/hookify") == "anthropics/claude-plugins-official/plugins/hookify"
assert to_ref("x/y", {"source": "github", "repo": "a/b"}) == "a/b"
assert to_ref("x/y", {"source": "url", "url": "https://github.com/obra/superpowers.git"}) == {"git": "https://github.com/obra/superpowers"}
assert to_ref("x/y", {"source": "git-subdir", "url": "https://github.com/adobe/skills.git", "path": "plugins/cc/"}) == "adobe/skills/plugins/cc"
assert to_ref("x/y", {"source": "npm", "package": "p"}) is None

assert key("JuliusBrussee/caveman#v1.0.0") == key("juliusbrussee/caveman")
assert key({"git": "https://github.com/obra/superpowers"}) == key("obra/superpowers")
assert key("https://github.com/a/b.git") == "a/b"
assert to_package("JuliusBrussee/caveman", "c1") == {"name": "caveman", "source": "JuliusBrussee/caveman", "ref": "c1"}
assert to_package("anthropics/claude-plugins-official/plugins/hookify", "c2") == {
    "name": "hookify", "source": "https://github.com/anthropics/claude-plugins-official", "subdir": "plugins/hookify", "ref": "c2"}
assert to_package({"git": "https://github.com/obra/superpowers"}, "c3") == {"name": "superpowers", "source": "obra/superpowers", "ref": "c3"}

data = {
    "dependencies": {"apm": ["JuliusBrussee/caveman", "anthropics/claude-plugins-official/plugins/hookify", "a/missing"]},
    "marketplace": {"packages": [{"name": "caveman", "category": "Style", "ref": "old", "subdir": "stale"}]},
}
lock = {"dependencies": [
    {"repo_url": "JuliusBrussee/caveman", "resolved_commit": "c1"},
    {"repo_url": "anthropics/claude-plugins-official", "virtual_path": "plugins/hookify", "resolved_commit": "c2"},
]}
assert sync(data, lock) == ["a/missing"]
assert data["marketplace"]["packages"] == [
    {"category": "Style", "name": "caveman", "source": "JuliusBrussee/caveman", "ref": "c1"},
    {"category": "Productivity", "name": "hookify", "source": "https://github.com/anthropics/claude-plugins-official",
     "subdir": "plugins/hookify", "ref": "c2"},
]
print("ok")
