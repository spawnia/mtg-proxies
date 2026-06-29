from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.pylab import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from mtg_proxies.decklists import Decklist


@pytest.fixture(scope="module")
def example_scans(example_decklist: Decklist) -> list[tuple[str, str, bool]]:
    from mtg_proxies import fetch_scans_scryfall

    example_scans = fetch_scans_scryfall(example_decklist)
    assert len(example_scans) == 7
    return example_scans


@pytest.fixture(scope="module")
def example_images(example_scans: list[tuple[str, str, bool]]) -> list[str]:
    return [path for path, _, _ in example_scans]


def test_fetch_scans_returns_tuples(example_scans: list[tuple[str, str, bool]]) -> None:
    assert all(isinstance(t, tuple) and len(t) == 3 for t in example_scans)
    assert all(isinstance(t[0], str) and isinstance(t[1], str) and isinstance(t[2], bool) for t in example_scans)


def test_print_cards_fpdf(example_scans: list[tuple[str, str, bool]], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist.pdf"
    print_cards_fpdf(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_pdf(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.pdf"
    print_cards_matplotlib(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_png(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.png"
    print_cards_matplotlib(example_scans, out_file)

    assert (tmp_path / "decklist_000.png").is_file()


def test_occupied_space_zero_gutter_matches_current() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _occupied_space

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]), pos=np.array([2, 3]), border_crop=14
    )
    expected = _occupied_space(
        cardsize=np.array([2.5, 3.5]), pos=np.array([2, 3]), border_crop=14, gutter=0.0
    )
    assert np.allclose(result, expected)


def test_occupied_space_open_form_adds_pos_gutters() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _occupied_space

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]),
        pos=np.array([2, 0]),
        border_crop=0,
        gutter=0.5,
    )
    assert np.allclose(result, np.array([2 * 2.5 + 2 * 0.5, 0]))


def test_occupied_space_closed_form_adds_n_minus_1_gutters() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _occupied_space

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]),
        pos=np.array([3, 4]),
        border_crop=0,
        gutter=0.5,
        closed=True,
    )
    assert np.allclose(result, np.array([3 * 2.5 + 2 * 0.5, 4 * 3.5 + 3 * 0.5]))


def test_print_cards_matplotlib_with_bleed_and_gutter(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist_bleed.png"
    print_cards_matplotlib(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert (tmp_path / "decklist_bleed_000.png").is_file()


def test_print_cards_matplotlib_with_borderless_fill_black(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    fake_scans: list[tuple[str, str, bool]] = [(path, "borderless", False) for path, _, _ in example_scans]
    out_file = tmp_path / "decklist_borderless.png"
    print_cards_matplotlib(fake_scans, out_file, bleed_mm=3.0, borderless_fill="black")

    assert (tmp_path / "decklist_borderless_000.png").is_file()


def test_print_cards_fpdf_with_bleed_and_gutter(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist_bleed.pdf"
    print_cards_fpdf(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert out_file.is_file()


def test_crop_mark_positions_zero_gutter_grid() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _crop_mark_positions

    marks = _crop_mark_positions(
        N=np.array([1, 1]),
        papersize=np.array([210.0, 297.0]),
        cardsize=np.array([63.5, 88.9]),
        border_crop=0,
        bleed=0.0,
        gutter=0.0,
        offset=np.array([0.0, 0.0]),
    )
    expected = np.array(
        [
            [73.25, 104.05],
            [73.25, 192.95],
            [136.75, 104.05],
            [136.75, 192.95],
        ]
    )
    assert np.allclose(marks, expected)


def test_crop_mark_positions_with_gutter_per_card_corners() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _crop_mark_positions

    marks = _crop_mark_positions(
        N=np.array([2, 1]),
        papersize=np.array([210.0, 297.0]),
        cardsize=np.array([63.5, 88.9]),
        border_crop=0,
        bleed=3.0,
        gutter=5.0,
        offset=np.array([33.0, 101.05]),
    )
    expected = np.array(
        [
            [36.0, 104.05],
            [36.0, 192.95],
            [99.5, 104.05],
            [99.5, 192.95],
            [110.5, 104.05],
            [110.5, 192.95],
            [174.0, 104.05],
            [174.0, 192.95],
        ]
    )
    assert np.allclose(marks, expected)


def test_estimate_border_color_ignores_dots_and_transparent_corners() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _estimate_border_color

    img = np.full((20, 16, 4), 0.1, dtype=float)
    img[..., 3] = 1.0
    img[0, 0] = [1.0, 1.0, 1.0, 0.0]          # transparent corner
    img[19, 15] = [1.0, 1.0, 1.0, 0.0]        # transparent corner
    img[1, 8, :3] = 1.0                        # stray bright dot in top band

    assert np.allclose(_estimate_border_color(img), [0.1, 0.1, 0.1])


def test_bleed_fill_color_bordered_uses_ring_median() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _bleed_fill_color

    img = np.zeros((20, 16, 4), dtype=float)
    img[..., 3] = 1.0
    img[..., :3] = [0.8, 0.6, 0.2]

    assert _bleed_fill_color(img, "gold", "edge") == (204, 153, 51)


def test_bleed_fill_color_keeps_muddy_black() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _bleed_fill_color

    img = np.full((20, 16, 4), 0.1, dtype=float)
    img[..., 3] = 1.0

    # A muddy scanned black stays muddy rather than being forced to pure (0, 0, 0).
    assert _bleed_fill_color(img, "black", "edge") == (26, 26, 26)


def test_bleed_fill_color_borderless_respects_fill() -> None:
    import numpy as np

    from mtg_proxies.print_cards import BORDER_COLOR_RGB, _bleed_fill_color

    img = np.full((20, 16, 4), 0.5, dtype=float)
    img[..., 3] = 1.0

    assert _bleed_fill_color(img, "borderless", "black") == BORDER_COLOR_RGB["black"]
    assert _bleed_fill_color(img, "borderless", "white") == BORDER_COLOR_RGB["white"]
    # "edge" means replicate the scan, so it falls back to the ring median.
    assert _bleed_fill_color(img, "borderless", "edge") == (128, 128, 128)


def test_edge_inset_crops_bordered_cards_only() -> None:
    from mtg_proxies.print_cards import EDGE_INSET, _edge_inset

    assert _edge_inset("black", full_art=False) == EDGE_INSET
    assert _edge_inset("white", full_art=False) == EDGE_INSET
    # Full-art and borderless edges are artwork, not a border to crop away.
    assert _edge_inset("black", full_art=True) == 0
    assert _edge_inset("borderless", full_art=False) == 0


def test_edge_inset_stays_inside_rounded_corner() -> None:
    from mtg_proxies.print_cards import EDGE_INSET

    # The Scryfall rounded-corner transparency reaches ~26 px in; the inset must
    # stay below that so the corners survive, while covering edge scan artifacts.
    assert 0 < EDGE_INSET < 26


def test_matplotlib_cleans_edge_per_card_with_bleed(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mtg_proxies.print_cards as pc
    from mtg_proxies import print_cards_matplotlib

    calls: list[int] = []
    real_inset = pc._edge_inset

    def spy(border_color, full_art) -> int:  # noqa: ANN001
        inset = real_inset(border_color, full_art)
        calls.append(inset)
        return inset

    monkeypatch.setattr(pc, "_edge_inset", spy)

    bordered_scans = [(path, "black", False) for path, _, _ in example_scans]
    out_file = tmp_path / "bleed.png"
    print_cards_matplotlib(bordered_scans, out_file, bleed_mm=3.0)

    assert (tmp_path / "bleed_000.png").is_file()
    assert calls == [pc.EDGE_INSET] * len(bordered_scans)


def test_fpdf_cleans_edge_per_card_with_bleed(
    example_scans: list[tuple[str, str, bool]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mtg_proxies.print_cards as pc
    from mtg_proxies import print_cards_fpdf

    calls: list[int] = []
    real_inset = pc._edge_inset

    def spy(border_color, full_art) -> int:  # noqa: ANN001
        inset = real_inset(border_color, full_art)
        calls.append(inset)
        return inset

    monkeypatch.setattr(pc, "_edge_inset", spy)

    bordered_scans = [(path, "black", False) for path, _, _ in example_scans]
    out_file = tmp_path / "bleed.pdf"
    print_cards_fpdf(bordered_scans, out_file, bleed_mm=3.0)

    assert out_file.is_file()
    assert calls == [pc.EDGE_INSET] * len(bordered_scans)


def test_flatten_corner_transparency_fills_runs_with_row_edge_pixel() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _flatten_corner_transparency

    img = np.zeros((2, 4, 4), dtype=float)
    img[..., 3] = 1.0
    img[0, :, :3] = 0.8        # light top row
    img[0, 0] = [0.5, 0.5, 0.5, 0.0]   # transparent top-left corner with junk colour
    img[1, :, :3] = 0.0        # black bottom row
    img[1, 3] = [0.5, 0.5, 0.5, 0.0]   # transparent bottom-right corner with junk colour

    result = _flatten_corner_transparency(img)

    assert np.allclose(result[0, 0], [0.8, 0.8, 0.8])   # took the row's first opaque pixel
    assert np.allclose(result[1, 3], [0.0, 0.0, 0.0])   # took the row's last opaque pixel
    assert result.shape == (2, 4, 3)


def test_bleed_image_dimensions() -> None:
    import numpy as np

    from mtg_proxies.print_cards import bleed_image

    img = np.ones((20, 16, 4), dtype=float)

    result = bleed_image(img, inset_px=2, bleed_px=(3, 5))

    # inset removes 2 px per edge (20->16 rows, 16->12 cols); pad adds 2*bleed per axis.
    assert result.shape == (22, 22, 3)


def test_bleed_image_replicates_edge_outward() -> None:
    import numpy as np

    from mtg_proxies.print_cards import bleed_image

    img = np.zeros((10, 10, 4), dtype=float)
    img[..., 3] = 1.0
    img[..., :3] = 0.3
    img[0, :, :3] = 0.9        # brighter top edge

    result = bleed_image(img, inset_px=0, bleed_px=(2, 2))

    assert np.allclose(result[0, 2], [0.9, 0.9, 0.9])


def test_bleed_image_extends_each_edge_with_its_own_tone() -> None:
    import numpy as np

    from mtg_proxies.print_cards import bleed_image

    img = np.full((6, 6, 4), 0.5, dtype=float)
    img[..., 3] = 1.0
    img[0, :, :3] = 1.0        # light top
    img[5, :, :3] = 0.0        # black bottom

    result = bleed_image(img, inset_px=0, bleed_px=(2, 0))

    assert np.allclose(result[0], 1.0)     # top margin replicates the light top
    assert np.allclose(result[-1], 0.0)    # bottom margin replicates the black bottom


def test_bleed_px_resolves_each_axis_from_its_own_resolution() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _bleed_px

    # 745x1040 scan over a deliberately non-square 60x90 mm card separates the axes.
    rows, cols = _bleed_px(3.0, np.array([60.0, 90.0]))

    assert (rows, cols) == (35, 37)
