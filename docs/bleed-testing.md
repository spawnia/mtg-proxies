# --bleed integration test

`tests/data/bleed_edge_cases.txt` is the regression fixture for the `--bleed` feature.
It packs one deliberate representative of every edge case `--bleed` must handle onto a single sheet.

Edge and corner quality is a visual property, so this fixture is verified by **printing and inspecting**, not by unit tests.
When a card misbehaves in the wild, add it (or a representative) to the fixture and to the table below, then fix — that turns each real-world failure into a permanent regression guard.

## What `--bleed` must do

`--bleed` extends every card outward by the requested margin so a print-and-cut workflow has ink past the cut line.
At the very edge it must:

- paint the bleed in the card's own border tone, sampled per card, so muddy scans stay muddy and genuinely clean digital borders stay pure;
- paint over scan artifacts on the outermost ring of the card; and
- preserve the rounded corners and any content that protrudes toward the edge (loyalty badges, collector and artist lines).

It must do this whether the scan is an aged retro image or a modern frame.
Modern frames are **not** guaranteed to be clean digital images — most are muddy scans, and some carry edge artifacts (see Blatant Thievery below).

## The fixture

Border tone is the per-channel median of the scanned border ring, measured from the actual scan.
It is the single most telling number: pure `(0,0,0)` / `(255,255,255)` means a clean digital image, anything muddier is a scan.

| Card | Set | # | Frame | Border | Border tone | Why it is in the fixture |
| --- | --- | --- | --- | --- | --- | --- |
| Hypnotic Specter | LEB | 113 | 1993 | black | (27,27,27) | earliest retro black scan; bleed must be muddy near-black, not stark `#000`, with no scan ring |
| Worn Powerstone | USG | 318 | 1997 | black | (24,21,16) | mid-era retro black scan |
| Damnation | PLC | 85 | 2003 | black | (24,21,16) | late retro black scan |
| Serra Angel | 2ED | 40 | 1993 | white | (237,237,239) | retro white scan; bleed must be soft off-white that matches, with no grey seam |
| Llanowar Elves | 6ED | 239 | 1997 | white | (237,237,238) | mid-era retro white scan |
| Shock | 9ED | 220 | 2003 | white | (237,236,234) | late retro white scan |
| Black Knight | WC97 | js143 | 1997 | gold | (167,137,77) | Worlds gold border; sampled gold must match without banding |
| Ass Whuppin' | UNH | 117 | 2003 | silver | (128,128,128) | Unhinged silver that prints near-black; sampled tone, not a canonical guess |
| Sorin Markov | M12 | 109 | 2003 | black | (24,21,16) | planeswalker — protruding loyalty badge and the rounded corners must survive the edge clean |
| Forest | ZEN | 246 | 2003 | black | (24,21,16) | retro full-art (`full_art=True`); no border to clean, art must reach the cut untouched |
| Black Lotus | VMA | 4 | 2015 | black | (0,0,0) | genuinely clean digital pure black; must stay perfectly seamless |
| Abrupt Decay | MB2 | 78 | 2015 | white | (255,255,255) | genuinely clean digital pure white; must stay perfectly seamless |
| Lightning Bolt | 2X2 | 117 | 2015 | black | (22,19,14) | modern frame but a muddy scan — proves "modern frame" does not imply pure black; bleed must match the muddy tone |
| Blatant Thievery | E02 | 8 | 2015 | black | (23,20,15) | modern muddy scan with a localized light edge artifact at the bottom-left; the artifact must be painted over |
| Island | ZNR | 271 | 2015 | black | (23,20,15) | modern full-art (`full_art=True`); edge is art, must not gain a border ring |
| Adorable Kitten | UST | 1 | 2015 | silver | (162,174,182) | Unstable silver border |
| Rainbow Dash | SLD | 1540 | 2015 | silver | (137,141,144) | Secret Lair with a non-uniform edge |
| Ajani, Sleeper Agent | DMU | 375 | 2015 | borderless | (164,150,80) | borderless; edge replication or `--borderless-fill` |

## Generating a sheet

`.pdf` output uses the fpdf renderer (the default for the consumer); a non-`.pdf` extension uses the matplotlib renderer.
Render both when a change could affect either path.

```bash
uv run mtg-proxies print --border_crop=0 --bleed=2 \
  tests/data/bleed_edge_cases.txt /tmp/bleed-edge-cases.pdf
```

Or through the published `personal` branch the way the `mtg` consumer does:

```bash
uvx --refresh --from git+https://github.com/spawnia/mtg-proxies@personal mtg-proxies \
  print --border_crop=0 --bleed=2 \
  tests/data/bleed_edge_cases.txt /tmp/bleed-edge-cases.pdf
```

`--refresh` is required after pushing to `personal`, otherwise `uvx` reuses the cached build.

## What to check on the print

- Each card's bleed matches its own border tone: muddy scans stay muddy, the clean digital cards (Black Lotus, Abrupt Decay) stay pure black / pure white, gold and silver match their sampled tone.
- No hard color seam at the cut line, and no squared-off corners — the rounded corners survive (Sorin Markov is the clearest test).
- Blatant Thievery's bottom-left edge artifact is gone.
- No content is clipped — Sorin Markov's loyalty badge and every collector / artist line stay intact.
- Full-art and borderless cards (Forest, Island, Ajani) gain no border ring; their art reaches the cut.
