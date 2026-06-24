from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.pylab import TYPE_CHECKING

if TYPE_CHECKING:
    from mtg_proxies.decklists import Decklist


@pytest.fixture(scope="module")
def example_scans(example_decklist: Decklist) -> list[tuple[str, str]]:
    from mtg_proxies import fetch_scans_scryfall

    example_scans = fetch_scans_scryfall(example_decklist)
    assert len(example_scans) == 7
    return example_scans


@pytest.fixture(scope="module")
def example_images(example_scans: list[tuple[str, str]]) -> list[str]:
    return [path for path, _ in example_scans]


def test_fetch_scans_returns_tuples(example_scans: list[tuple[str, str]]) -> None:
    assert all(isinstance(t, tuple) and len(t) == 2 for t in example_scans)
    assert all(isinstance(t[0], str) and isinstance(t[1], str) for t in example_scans)


def test_print_cards_fpdf(example_scans: list[tuple[str, str]], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist.pdf"
    print_cards_fpdf(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_pdf(
    example_scans: list[tuple[str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.pdf"
    print_cards_matplotlib(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_png(
    example_scans: list[tuple[str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.png"
    print_cards_matplotlib(example_scans, out_file)

    assert (tmp_path / "decklist_000.png").is_file()


def test_occupied_space_zero_gutter_matches_current() -> None:
    from mtg_proxies.print_cards import _occupied_space
    import numpy as np

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]), pos=np.array([2, 3]), border_crop=14
    )
    expected = _occupied_space(
        cardsize=np.array([2.5, 3.5]), pos=np.array([2, 3]), border_crop=14, gutter=0.0
    )
    assert np.allclose(result, expected)


def test_occupied_space_open_form_adds_pos_gutters() -> None:
    from mtg_proxies.print_cards import _occupied_space
    import numpy as np

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]),
        pos=np.array([2, 0]),
        border_crop=0,
        gutter=0.5,
    )
    assert np.allclose(result, np.array([2 * 2.5 + 2 * 0.5, 0]))


def test_occupied_space_closed_form_adds_n_minus_1_gutters() -> None:
    from mtg_proxies.print_cards import _occupied_space
    import numpy as np

    result = _occupied_space(
        cardsize=np.array([2.5, 3.5]),
        pos=np.array([3, 4]),
        border_crop=0,
        gutter=0.5,
        closed=True,
    )
    assert np.allclose(result, np.array([3 * 2.5 + 2 * 0.5, 4 * 3.5 + 3 * 0.5]))


def test_print_cards_matplotlib_with_bleed_and_gutter(
    example_scans: list[tuple[str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist_bleed.png"
    print_cards_matplotlib(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert (tmp_path / "decklist_bleed_000.png").is_file()


def test_print_cards_matplotlib_with_borderless_fill_black(
    example_scans: list[tuple[str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    fake_scans: list[tuple[str, str]] = [(path, "borderless") for path, _ in example_scans]
    out_file = tmp_path / "decklist_borderless.png"
    print_cards_matplotlib(fake_scans, out_file, bleed_mm=3.0, borderless_fill="black")

    assert (tmp_path / "decklist_borderless_000.png").is_file()


def test_print_cards_fpdf_with_bleed_and_gutter(
    example_scans: list[tuple[str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist_bleed.pdf"
    print_cards_fpdf(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert out_file.is_file()


def test_crop_mark_positions_zero_gutter_grid() -> None:
    from mtg_proxies.print_cards import _crop_mark_positions
    import numpy as np

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
    from mtg_proxies.print_cards import _crop_mark_positions
    import numpy as np

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


def test_sample_edge_color_ignores_transparent_corner() -> None:
    import numpy as np
    from mtg_proxies.print_cards import _sample_edge_color

    img = np.ones((10, 8, 4), dtype=float)
    img[:, 0] = [0.086, 0.075, 0.055, 1.0]
    img[0, 0] = [1.0, 1.0, 1.0, 0.0]

    assert np.allclose(_sample_edge_color(img), [0.086, 0.075, 0.055])


def test_resolve_bleed_color_bordered_card_samples_edge() -> None:
    from mtg_proxies.print_cards import _resolve_bleed_color

    assert _resolve_bleed_color("black", "edge") == "edge"
    assert _resolve_bleed_color("white", "edge") == "edge"
    assert _resolve_bleed_color("gold", "black") == "edge"


def test_resolve_bleed_color_borderless_respects_fill() -> None:
    from mtg_proxies.print_cards import _resolve_bleed_color, BORDER_COLOR_RGB

    assert _resolve_bleed_color("borderless", "edge") == "edge"
    assert _resolve_bleed_color("borderless", "black") == BORDER_COLOR_RGB["black"]
    assert _resolve_bleed_color("borderless", "white") == BORDER_COLOR_RGB["white"]
