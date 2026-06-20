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


def test_print_cards_fpdf(example_images: list[str], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist.pdf"
    print_cards_fpdf(example_images, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_pdf(example_images: list[str], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.pdf"
    print_cards_matplotlib(example_images, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_png(example_images: list[str], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.png"
    print_cards_matplotlib(example_images, out_file)

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
