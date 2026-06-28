# Border-synthesis manual testing

The `--bleed` feature replaces the noisy scanned border of retro-frame cards with a clean synthetic border and fills the bleed margin with it.
Synthesis engages for a card only when **all** of these hold: `--bleed` is greater than zero, the Scryfall `frame` is one of `1993` / `1997` / `2003`, and content-box detection returns a plausible inset on enough sides.
Every other card keeps the existing edge-sample (or `--borderless-fill`) path.

The synthetic color is always the per-channel median of the scanned border ring (`_resolve_synthetic_color`).
It deliberately keeps the muddy scanned tone rather than forcing pure black/white: the rectangular crop preserves a sliver of the scanned border at the rounded corners, and a muddy fill blends with it instead of clashing — and the aged tone reads as more natural on retro cards anyway.

This behavior is hard to unit-test for visual quality, so it is verified by printing.
The fixture `tests/data/border_synthesis_edge_cases.txt` packs one card per branch onto a single sheet.

## The fixture

| Card | Set | Frame | Border | Expected path |
| --- | --- | --- | --- | --- |
| Hypnotic Specter | LEB | 1993 | black | synthesize, muddy ring-median black |
| Serra Angel | 2ED | 1993 | white | synthesize, muddy ring-median white |
| Worn Powerstone | USG | 1997 | black | synthesize, muddy ring-median black |
| Llanowar Elves | 6ED | 1997 | white | synthesize, muddy ring-median white |
| Black Knight | WC97 | 1997 | gold | synthesize, ring-median gold (Worlds border) |
| Damnation | PLC | 2003 | black | synthesize, muddy ring-median black |
| Shock | 9ED | 2003 | white | synthesize, muddy ring-median white |
| Sorin Markov | M12 | 2003 | black | synthesize; muddy fill must blend with the corner border the crop preserves |
| Ass Whuppin' | UNH | 2003 | silver | synthesize, ring-median silver (Unhinged prints near-black) |
| Forest | ZEN | 2003 | black (full-art) | **no** synthesis — plausibility gate skips it — edge-sample |
| Lightning Bolt | 2X2 | 2015 | black | fallback edge-sample (already clean black) |
| Abrupt Decay | MB2 | 2015 | white | fallback edge-sample (real white border) |
| Black Lotus | VMA | 2015 | black | fallback (retro *look*, modern composition) |
| Adorable Kitten | UST | 2015 | silver | fallback (Unstable) |
| Rainbow Dash | SLD | 2015 | silver | fallback (Secret Lair, non-uniform border) |
| Ajani, Sleeper Agent | DMU | 2015 | borderless | fallback / `--borderless-fill` |

## Generating a sheet

From a checkout of this branch:

```bash
uv run mtg-proxies print --border_crop=0 --bleed=2 \
  tests/data/border_synthesis_edge_cases.txt /tmp/border-edge-cases.pdf
```

Or through the published `personal` branch the way the `mtg` consumer does:

```bash
uvx --refresh --from git+https://github.com/spawnia/mtg-proxies@personal mtg-proxies \
  print --border_crop=0 --bleed=2 \
  tests/data/border_synthesis_edge_cases.txt /tmp/border-edge-cases.pdf
```

`--refresh` is required after pushing to `personal`, otherwise `uvx` reuses the cached build.

## What to check on the print

- Retro-frame borders are a clean, uniform color out to the cut line, with no stray scan dots.
- No content is clipped — especially Sorin Markov's left-protruding loyalty badge and every collector/artist line.
- The synthetic fill blends seamlessly into the scanned border the crop preserves at the rounded corners, with no hard color seam (Sorin Markov is the clearest test).
- Retro borders keep their muddy aged tone — black is a soft near-black, white is a soft off-white — rather than a stark pure `#000` / `#fff`.
- Forest, the modern cards, the silver/borderless cards, and the retro-look Black Lotus are untouched by synthesis (fallback only).
- Gold (Black Knight) and silver (Ass Whuppin') borders match the scanned color without banding.
