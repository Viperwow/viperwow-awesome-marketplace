# viperwow-awesome-marketplace

A curated set of third-party skills, plugins, hooks and MCP servers. [APM](https://github.com/microsoft/apm) installs the set into Claude Code, Codex and Cursor.

## Pick the set

`apm.yml` lists the set.

```bash
uv run migrate.py                       # enabled Claude plugins; [x] marks plugins in apm.yml
uv run migrate.py add caveman@caveman   # add a plugin to apm.yml
uv run migrate.py remove caveman@caveman
apm install                             # resolve and pin every entry in apm.lock.yaml
uv run migrate.py sync                  # copy the set into the marketplace block, pinned to the lockfile commits
apm pack                                # write .claude-plugin/marketplace.json and .agents/plugins/marketplace.json
```

Commit `apm.yml`, `apm.lock.yaml` and both `marketplace.json` files. `sync` keeps the `category` and `description` you set on a package.

You can also edit `apm.yml` by hand. An entry is `owner/repo`, `owner/repo/sub/dir`, `owner/repo#ref` or `git: <url>`.

## Install on a device

The whole set, through APM:

```bash
apm install -g Viperwow/viperwow-awesome-marketplace
```

Single plugins, through the marketplace:

```bash
/plugin marketplace add Viperwow/viperwow-awesome-marketplace     # Claude Code
codex plugin marketplace add Viperwow/viperwow-awesome-marketplace  # Codex
apm marketplace add Viperwow/viperwow-awesome-marketplace           # APM
```

Then install a plugin as `NAME@viperwow-awesome-marketplace`.

`apm.lock.yaml` pins each package to a commit and a content hash.

## Check

```bash
uv run test_migrate.py
```
