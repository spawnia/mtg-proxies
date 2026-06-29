from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.pylab import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from mtg_proxies.decklists import Decklist


@pytest.fixture(scope="module")
def example_scans(example_decklist: Decklist) -> list[str]:
    from mtg_proxies import fetch_scans_scryfall

    example_scans = fetch_scans_scryfall(example_decklist)
    assert len(example_scans) == 7
    return example_scans


def test_fetch_scans_returns_paths(example_scans: list[str]) -> None:
    assert all(isinstance(scan, str) for scan in example_scans)


def test_print_cards_fpdf(example_scans: list[str], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist.pdf"
    print_cards_fpdf(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_pdf(
    example_scans: list[str], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.pdf"
    print_cards_matplotlib(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_png(
    example_scans: list[str], tmp_path: Path
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
    example_scans: list[str], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist_bleed.png"
    print_cards_matplotlib(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert (tmp_path / "decklist_bleed_000.png").is_file()


def test_print_cards_fpdf_with_bleed_and_gutter(
    example_scans: list[str], tmp_path: Path
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
