# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# mtg-proxies

Fork of `DiddiZ/mtg-proxies` (origin remote: `spawnia/mtg-proxies`, upstream: `DiddiZ/mtg-proxies`).
The `personal` branch bundles unmerged fixes plus a not-yet-upstreamed `--bleed` / `--gutter` / `--borderless-fill` print feature.
The `mtg` consumer project installs from it via `uvx --from git+https://github.com/spawnia/mtg-proxies@personal`.

## Testing

- Run tests with `uv run python -m pytest tests/` (CI runs plain `python -m pytest tests/` and does **not** run ruff).
- Plan/spec files are kept out of the repo, under `~/.local/share/superpowers/mtg-proxies/`.

## Border-synthesis test cases

`--bleed` synthesizes a clean border for retro-frame scans (Scryfall `frame` in `1993` / `1997` / `2003`); everything else uses the edge-sample / `--borderless-fill` fallback.
The visual behavior is verified by printing, not unit tests:

- `tests/data/border_synthesis_edge_cases.txt` — 16-card kitchen-sink deck, one card per branch (retro black/white/gold/silver borders, a full-art card that the plausibility gate skips, a planeswalker whose loyalty badge must not be clipped, plus modern black/white/silver/borderless and a retro-*look* reprint on the fallback path). Keep comment lines digit-free — the parser scans every line for a "number word" and would misread `1993 frame` as a card.
- `docs/border-synthesis-testing.md` — per-card expectation table, render/refresh commands, the `SYNTHETIC_COLOR_STRATEGY` (canonical vs sampled) A/B procedure, and a print-inspection checklist.

Render a sheet: `uv run mtg-proxies print --border_crop=0 --bleed=2 tests/data/border_synthesis_edge_cases.txt out.pdf`.
