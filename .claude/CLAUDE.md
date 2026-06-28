# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# mtg-proxies

Fork of `DiddiZ/mtg-proxies` (origin remote: `spawnia/mtg-proxies`, upstream: `DiddiZ/mtg-proxies`).
The `personal` branch bundles unmerged fixes plus a not-yet-upstreamed `--bleed` / `--gutter` / `--borderless-fill` print feature.
The `mtg` consumer project installs from it via `uvx --from git+https://github.com/spawnia/mtg-proxies@personal`.

## Testing

- Run tests with `uv run python -m pytest tests/` (CI runs plain `python -m pytest tests/` and does **not** run ruff).
- Plan/spec files are kept out of the repo, under `~/.local/share/superpowers/mtg-proxies/`.

## --bleed integration test

`tests/data/bleed_edge_cases.txt` is THE regression fixture for `--bleed`: one deliberate representative of every edge case the feature must handle, on a single sheet.
Edge/corner quality is visual, so it is verified by **printing and inspecting**, not unit tests.
When a card misbehaves in the wild, add it (or a representative) to the fixture and the docs table first, then fix.

- `tests/data/bleed_edge_cases.txt` — the deck. Covers retro black/white/gold/silver scans, a planeswalker (protruding loyalty badge + corners), retro full-art, genuinely clean digital pure black/white, muddy modern scans (modern frame does NOT imply clean digital), a modern scan with a localized edge artifact (Blatant Thievery), modern full-art, silver, and borderless. Keep comment lines **digit-free** — the parser scans every line for a "number word" and would misread a digit-bearing comment as a card.
- `docs/bleed-testing.md` — per-card table (set, frame, border, measured border tone, rationale), render commands, and the print-inspection checklist.

Render a sheet (`.pdf` → fpdf renderer, other extension → matplotlib): `uv run mtg-proxies print --border_crop=0 --bleed=2 tests/data/bleed_edge_cases.txt out.pdf`.
