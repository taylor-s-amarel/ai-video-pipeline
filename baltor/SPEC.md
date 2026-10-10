# Baltor component format, v1

This directory holds components that a Baltor catalogue can ingest without
changes. It mirrors what the Baltor service describes: every item has one of
twelve kinds, an exact version, a licence, a source, declared effects and a
SHA-256 digest of its bytes. Harnesses find items with `intelligence_search`
and download one exact version with `provisioning_read`.

Nothing here talks to baltor.ai. `tools/baltor_catalog.py` implements the same
operations locally over this repository so the components can be checked,
searched, placed and locked today.

## Layout

```
baltor/
  SPEC.md                      this file
  schemas/                     JSON Schemas for manifests, feeds, locks, the index
  components/<kind-dir>/<name>/  one directory per component (a "package")
    baltor.json                the manifest (declared metadata)
    ...payload files           SKILL.md, module.py, schema.json, hook.py, ...
  feeds/<collection>.json      source collections (Agent Feeds input)
  generators/                  scripts + data tables that produce component families
  catalog/                     generated: index.json, release.json, feeds, CATALOG.md
  tools/baltor_catalog.py      validate | build | search | read | place | lock | stats
  tests/                       pytest suite for the format and the tools
```

`<name>` is the identity in kebab case. Directory names must be unique across
the whole tree; the validator enforces it.

## The twelve kinds

| `kind`                          | directory                    | What it is |
|---------------------------------|------------------------------|------------|
| `skill`                         | `skills/`                    | A `SKILL.md` (YAML front matter `name`, `description`) plus optional `scripts/`, `assets/`, `references/` |
| `instruction-file`              | `instruction-files/`         | A `CLAUDE.md` / `AGENTS.md` body for one kind of step |
| `rules`                         | `rules/`                     | A short, checkable rule set (`RULES.md`), optionally with a machine-readable `rules.json` |
| `subagent`                      | `subagents/`                 | An agent definition (`agent.md`, YAML front matter `name`, `description`, `tools`) |
| `command`                       | `commands/`                  | A slash command (`command.md`, front matter `description`, `argument-hint`) |
| `hook`                          | `hooks/`                     | A script the harness runs itself (`hook.py`) plus `hook.json` naming the event and matcher |
| `plugin-manifest`               | `plugin-manifests/`          | `plugin.json` describing a bundle of other components |
| `plugin-marketplace`            | `plugin-marketplaces/`       | `marketplace.json` listing plugins |
| `protocol-server-configuration` | `protocol-server-configs/`   | MCP server entries for each harness (`mcp.json`, `codex.toml`, `opencode.json`) |
| `harness-settings`              | `harness-settings/`          | Settings for one harness (`settings.json`, `config.toml`, ...) |
| `contract-schema`               | `contract-schemas/`          | A JSON Schema (`schema.json`) plus at least one valid `examples/*.json` |
| `code-module`                   | `code-modules/`              | Reusable code (`module.py`, `module.js`, `*.gd`, ...) with `test_*.py` where the language allows |

Work that is not one of these twelve keeps a canonical kind and adds a
`subkind`: a video style preset ships as a `skill` with `subkind:
"style-preset"`; a serverless handler ships as a `code-module` with `subkind:
"cloud-function"`; a media source list ships as a `contract-schema` instance
inside a skill or as a feed collection. Recognised subkinds are listed in
`schemas/component.schema.json`.

## The manifest: `baltor.json`

```json
{
  "spec": "baltor.component/v1",
  "identity": "find_duplicate_records_with_blocking_keys",
  "title": "Find duplicate records with blocking keys",
  "kind": "skill",
  "version": "1.0.0",
  "summary": "One sentence: what a step gets from this item.",
  "licence": "MIT",
  "source": { "type": "original", "url": "https://github.com/taylor-s-amarel/ai-video-pipeline" },
  "step_kinds": ["build", "verify"],
  "effects": { "filesystem": "read", "network": "none", "executes": "python", "secrets": [] },
  "harnesses": ["claude-code", "codex", "opencode", "pi", "baltor-harness"],
  "entry": "SKILL.md",
  "tags": ["data-cleaning", "deduplication"],
  "collection": "public-good"
}
```

Required: `spec`, `identity`, `title`, `kind`, `version`, `summary`,
`licence`, `source`, `step_kinds`, `effects`, `harnesses`, `entry`, `tags`,
`collection`.

Optional: `subkind`, `description`, `domain`, `depends_on`, `variant_of`,
`provenance`, `attribution`, `review`, `install`, `examples`.

Rules the validator checks beyond the schema:

- `identity` is snake case and unique across the tree; the directory name is the
  same identity in kebab case.
- `entry` and every path mentioned in `install` exist in the package.
- A `licence` that requires attribution (`CC-BY-*`) has an `attribution` string.
- `effects.network: "declared"` lists every host in `effects.hosts`.
- `effects.secrets` lists environment variable names only, never values. No
  file in a package may contain something that looks like a live credential.
- `variant_of` names an identity that exists. Variants are generated
  parameterisations of one base item; a catalogue can group them.
- Kind-specific payload checks: a skill has front matter with `name` and
  `description`; a contract schema is a valid JSON Schema and its examples
  validate against it; a hook has `hook.json` with a known event; a protocol
  server configuration parses in every format it ships; a Python code module
  compiles.
- No package exceeds 512 KB and no file exceeds 256 KB. Large media never goes
  in a package: ship a manifest that points at the source with its licence.

Computed by `build`, never written by hand: each file's `size` and `sha256`,
the package `digest`, and the package `size`. The package digest is the
SHA-256 of the UTF-8 text formed by one line per file, sorted by path:
`<path>\0<sha256>\n`. `baltor.json` is part of the package.

## Collections

`public-good`: free with an account. Everything original in this repository
defaults to it. `library`: needs the stated access. Third-party material keeps
its upstream licence and is only included when that licence allows
redistribution.

## Releases

`build` writes `catalog/index.json` (every package, its files and digests) and
`catalog/release.json`. The release id is the first 12 hex characters of the
SHA-256 of the sorted list of `identity@version#digest` lines. When a previous
`release.json` exists, the new one records `added`, `changed` and `withdrawn`
identities. A withdrawn identity is never reused for different content.

## Step locks

`lock` writes `.baltor/step.lock.json` for a step folder: every placed item's
identity, version, digest, kind and where it was placed. A harness can verify
a step by recomputing the digests. Schema: `schemas/step-lock.schema.json`.

## Feeds

`feeds/<collection>.json` follows `schemas/feed-collection.schema.json`. `build`
renders each collection as JSON Feed 1.1, RSS 2.0 and Markdown under
`catalog/feeds/`, and adds a `components` feed listing the latest release.

## Placement

`place <identity> <step-dir> --harness claude-code` copies a package to where
that harness reads it:

| kind | claude-code | codex / opencode / pi |
|------|-------------|------------------------|
| skill | `.claude/skills/<name>/` | `.agents/skills/<name>/` |
| instruction-file | appended to `CLAUDE.md` | appended to `AGENTS.md` |
| rules | `.baltor/rules/<name>.md` | same |
| subagent | `.claude/agents/<name>.md` | `.opencode/agent/<name>.md` (opencode) |
| command | `.claude/commands/<name>.md` | `.opencode/command/<name>.md` (opencode) |
| hook | `.baltor/hooks/<name>/` and a settings fragment to merge | same |
| protocol-server-configuration | merged into `.mcp.json` | `codex.toml` fragment / `opencode.json` |
| harness-settings | `.baltor/settings/<name>/` fragment to merge | same |
| plugin-manifest, plugin-marketplace | `.claude-plugin/` | same |
| code-module | `.baltor/lib/<name>/` | same |
| contract-schema | `.baltor/schemas/<name>/` | same |

Settings and server entries are never overwritten silently: `place` writes the
fragment next to the target and prints the merge it would make, unless
`--merge` is given.
