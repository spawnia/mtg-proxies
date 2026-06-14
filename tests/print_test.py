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
