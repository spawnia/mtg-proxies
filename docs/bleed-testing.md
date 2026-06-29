# --bleed integration test

`tests/data/bleed_edge_cases.txt` is the regression fixture for the `--bleed` feature.
It packs one deliberate representative of every edge case `--bleed` must handle onto a single sheet.

Edge and corner quality is a visual property, so this fixture is verified by **printing and inspecting**, not by unit tests.
When a card misbehaves in the wild, add it (or a representative) to the fixture and to the table below, then fix — that turns each real-world failure into a permanent regression guard.

## What `--bleed` must do

`--bleed` extends every card outward by the requested margin so a print-and-cut workflow has ink past the cut line.
It uses one metadata-free pipeline for every card — no Scryfall `full_art` or `border_color` is read:

- inset a thin uniform ring off every edge, dropping the semi-transparent scan rim and any artifact clinging to the outermost pixels, while staying inside the rounded-corner zone so the corners survive;
- flatten the rounded-corner transparency per row, so each corner inherits its own side's tone (a black bottom stays black, a light top stays light);
- replicate the resulting edge and corner pixels outward into the margin (`np.pad(mode="edge")`), so each edge continues its own colour instead of a single sampled fill.

It must do this whether the scan is an aged retro image or a modern frame.
Modern frames are **not** guaranteed to be clean digital images — most are muddy scans, and some carry edge artifacts (see Blatant Thievery below).

Because the margin replicates the card's own outermost pixels, an edge that varies along its length (busy borderless showcases) produces mild streaks in the margin.
This is inherent to replication and acceptable: the streaks continue the card's own colours and sit entirely in the trimmed margin.

## The fixture

The **border tone** column is the per-channel median of the scanned border ring, measured from the actual scan.
It no longer drives the fill — replication does — but it stays the single most telling diagnostic: pure `(0,0,0)` / `(255,255,255)` means a clean digital image, anything muddier is a scan.

| Card | Set | # | Frame | Border | Border tone | Why it is in the fixture |
| --- | --- | --- | --- | --- | --- | --- |
| Hypnotic Specter | LEB | 113 | 1993 | black | (27,27,27) | earliest retro black scan; replicated margin must be muddy near-black, not stark `#000`, with no scan ring |
| Worn Powerstone | USG | 318 | 1997 | black | (24,21,16) | mid-era retro black scan |
| Damnation | PLC | 85 | 2003 | black | (24,21,16) | late retro black scan |
| Serra Angel | 2ED | 40 | 1993 | white | (237,237,239) | retro white scan; replicated margin must be soft off-white that matches, with no grey seam |
| Llanowar Elves | 6ED | 239 | 1997 | white | (237,237,238) | mid-era retro white scan |
| Shock | 9ED | 220 | 2003 | white | (237,236,234) | late retro white scan |
| Black Knight | WC97 | js143 | 1997 | gold | (167,137,77) | Worlds gold border; replicated metallic gold must continue without banding |
| Ass Whuppin' | UNH | 117 | 2003 | silver | (128,128,128) | Unhinged silver that prints near-black; replicated from its own edge, not a canonical guess |
| Sorin Markov | M12 | 109 | 2003 | black | (24,21,16) | planeswalker — protruding loyalty badge and the rounded corners must survive the edge clean |
| Forest | ZEN | 246 | 2003 | black | (24,21,16) | retro `full_art=True` but a uniform black border — proves Full Art != Borderless; the alpha rim must not survive at the cut |
| Black Lotus | VMA | 4 | 2015 | black | (0,0,0) | genuinely clean digital pure black; must stay perfectly seamless |
| Abrupt Decay | MB2 | 78 | 2015 | white | (255,255,255) | genuinely clean digital pure white; must stay perfectly seamless |
| Lightning Bolt | 2X2 | 117 | 2015 | black | (22,19,14) | modern frame but a muddy scan — proves "modern frame" does not imply pure black; replicated margin must match the muddy tone |
| Blatant Thievery | E02 | 8 | 2015 | black | (23,20,15) | modern muddy scan with a localized light edge artifact at the bottom-left; the inset must drop it |
| Island | ZNR | 271 | 2015 | black | (23,20,15) | modern `full_art=True` uniform black border; edge must not gain a border ring nor keep the alpha rim |
| Adorable Kitten | UST | 1 | 2015 | silver | (162,174,182) | Unstable silver: light silver sides with a black bottom border and rounded black corner — each edge must extend in its own tone from one pass |
| Rainbow Dash | SLD | 1540 | 2015 | silver | (137,141,144) | Secret Lair with a non-uniform silver edge; replication follows the variation, a single fill cannot |
| Ajani, Sleeper Agent | DMU | 375 | 2015 | borderless | (164,150,80) | borderless; replication continues the art to the cut — no border ring, no median fill |
| Aatchik, Emerald Radian | DFT | 360 | 2015 | borderless | (110,108,84) | borderless with a dark vignette edge — a solid edge replicates cleanly |
| Adeline, Resplendent Cathar | FCA | 1 | 2015 | borderless | (208,214,210) | Final Fantasy full-art borderless — light painterly edge, mild acceptable streaks |
| Aesi, Tyrant of Gyre Strait | SLD | 1873 | 2015 | borderless | (48,45,43) | Secret Lair "yearbook" borderless — cream photo edge replicates light |
| Aether Vial | SLD | 1640 | 2015 | borderless | (219,210,195) | Secret Lair showcase — pale edge, mild streaks where the art varies |
| Agonasaur Rex | DFT | 542 | 2015 | borderless | (162,120,181) | Aetherdrift borderless — purple frame edge replicates |
| Ajani Goldmane | SLD | 1453 | 2015 | borderless | (215,211,62) | Secret Lair trading-card frame — holo-gradient edge, mild streaks |
| Black Lotus | CEI | 233 | 1993 | black | (27,27,27) | Collectors' Edition square-corner card — muddy retro border extends; no rounded alpha rim to flatten |
| Jaxis, the Troublemaker | SNC | 461 | 2015 | black | (22,19,14) | extended-art — red art bleeds to the sides while a black border stays top and bottom; adjacent edges disagree |
| Drivnod, Carnage Dominus | ONE | 305 | 2015 | borderless | (28,32,52) | Phyrexian borderless with a dark bottom strip — bottom extends dark, top and sides extend art |
| Putrefy | STA | 63 | 2015 | borderless | (218,209,170) | Mystical Archive showcase — cream and gold filigree edge, streak-prone but cream dominates |
| Daybreak Ranger (back) | ISD | 176 | 2003 | black | (24,21,16) | transform back face (Nightfall Predator) — non-black olive-brown border tone must extend, not assume black |
| Agatha's Champion | AWOE | 22 | 2015 | borderless | (76,79,57) | Art Series full-bleed painting — no frame at all, painterly edge, mild streaks |

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

- Each card's margin continues its own edge: muddy scans stay muddy, the clean digital cards (Black Lotus, Abrupt Decay) stay pure black / pure white, gold and silver keep their metallic tone.
- No hard colour seam at the cut line, and no squared-off corners — the rounded corners survive (Sorin Markov is the clearest test).
- Blatant Thievery's bottom-left edge artifact is gone.
- No content is clipped — Sorin Markov's loyalty badge and every collector / artist line stay intact.
- Full-art and borderless cards (Forest, Island, Ajani) gain no border ring and keep no alpha rim; their art reaches the cut.
- Multi-edge cards (Adorable Kitten): the black bottom border and its curvature extend as black while the silver sides stay light.
- Busy borderless showcases may show mild streaks in the trimmed margin — acceptable.
