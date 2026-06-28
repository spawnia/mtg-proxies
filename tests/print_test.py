from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.pylab import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from mtg_proxies.decklists import Decklist


@pytest.fixture(scope="module")
def example_scans(example_decklist: Decklist) -> list[tuple[str, str, str]]:
    from mtg_proxies import fetch_scans_scryfall

    example_scans = fetch_scans_scryfall(example_decklist)
    assert len(example_scans) == 7
    return example_scans


@pytest.fixture(scope="module")
def example_images(example_scans: list[tuple[str, str, str]]) -> list[str]:
    return [path for path, _, _ in example_scans]


def test_fetch_scans_returns_tuples(example_scans: list[tuple[str, str, str]]) -> None:
    assert all(isinstance(t, tuple) and len(t) == 3 for t in example_scans)
    assert all(isinstance(t[0], str) and isinstance(t[1], str) and isinstance(t[2], str) for t in example_scans)


def test_print_cards_fpdf(example_scans: list[tuple[str, str, str]], tmp_path: Path) -> None:
    from mtg_proxies import print_cards_fpdf

    out_file = tmp_path / "decklist.pdf"
    print_cards_fpdf(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_pdf(
    example_scans: list[tuple[str, str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist.pdf"
    print_cards_matplotlib(example_scans, out_file)

    assert out_file.is_file()


def test_print_cards_matplotlib_png(
    example_scans: list[tuple[str, str, str]], tmp_path: Path
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
    example_scans: list[tuple[str, str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    out_file = tmp_path / "decklist_bleed.png"
    print_cards_matplotlib(example_scans, out_file, bleed_mm=3.0, gutter_mm=5.0)

    assert (tmp_path / "decklist_bleed_000.png").is_file()


def test_print_cards_matplotlib_with_borderless_fill_black(
    example_scans: list[tuple[str, str, str]], tmp_path: Path
) -> None:
    from mtg_proxies import print_cards_matplotlib

    fake_scans: list[tuple[str, str, str]] = [(path, "borderless", "2015") for path, _, _ in example_scans]
    out_file = tmp_path / "decklist_borderless.png"
    print_cards_matplotlib(fake_scans, out_file, bleed_mm=3.0, borderless_fill="black")

    assert (tmp_path / "decklist_borderless_000.png").is_file()


def test_print_cards_fpdf_with_bleed_and_gutter(
    example_scans: list[tuple[str, str, str]], tmp_path: Path
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
    from mtg_proxies.print_cards import BORDER_COLOR_RGB, _resolve_bleed_color

    assert _resolve_bleed_color("borderless", "edge") == "edge"
    assert _resolve_bleed_color("borderless", "black") == BORDER_COLOR_RGB["black"]
    assert _resolve_bleed_color("borderless", "white") == BORDER_COLOR_RGB["white"]


def test_should_synthesize_only_old_frames_with_bleed() -> None:
    from mtg_proxies.print_cards import _should_synthesize

    assert _should_synthesize("1993", 3.0)
    assert _should_synthesize("1997", 0.1)
    assert _should_synthesize("2003", 3.0)
    assert not _should_synthesize("2015", 3.0)
    assert not _should_synthesize("1993", 0.0)
    assert not _should_synthesize("future", 3.0)


def _bordered_array(height: int, width: int, inset: int) -> np.ndarray:
    import numpy as np

    img = np.zeros((height, width, 4), dtype=float)
    img[..., 3] = 1.0
    img[inset : height - inset, inset : width - inset, :3] = 1.0
    return img


def test_estimate_border_color_ignores_dots_and_transparent_corners() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _estimate_border_color

    img = np.full((20, 16, 4), 0.1, dtype=float)
    img[..., 3] = 1.0
    img[0, 0] = [1.0, 1.0, 1.0, 0.0]          # transparent corner
    img[19, 15] = [1.0, 1.0, 1.0, 0.0]        # transparent corner
    img[1, 8, :3] = 1.0                        # stray bright dot in top band

    assert np.allclose(_estimate_border_color(img), [0.1, 0.1, 0.1])


def test_detect_content_box_uniform_border() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _detect_content_box

    img = _bordered_array(20, 16, 3)
    assert _detect_content_box(img, reference=np.array([0.0, 0.0, 0.0])) == (3, 3, 3, 3)


def test_detect_content_box_ignores_isolated_dot() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _detect_content_box

    img = _bordered_array(20, 16, 3)
    img[1, 8, :3] = 1.0  # one bright pixel inside the top border

    assert _detect_content_box(img, reference=np.array([0.0, 0.0, 0.0])) == (3, 3, 3, 3)


def test_detect_content_box_keeps_protrusion() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _detect_content_box

    img = _bordered_array(20, 16, 3)
    img[8:12, 1:3, :3] = 1.0  # protrusion reaching left to column 1 over 4 rows

    assert _detect_content_box(img, reference=np.array([0.0, 0.0, 0.0])) == (1, 3, 3, 3)


def test_content_box_plausible_rejects_full_art() -> None:
    from mtg_proxies.print_cards import _content_box_plausible

    assert _content_box_plausible((30, 40, 30, 40), (1040, 745))
    assert not _content_box_plausible((2, 3, 1, 2), (1040, 745))


def test_resolve_synthetic_color_returns_ring_median() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _resolve_synthetic_color

    img = np.zeros((20, 16, 4), dtype=float)
    img[..., 3] = 1.0
    img[..., :3] = [0.8, 0.6, 0.2]

    assert _resolve_synthetic_color(img) == (204, 153, 51)


def test_resolve_synthetic_color_keeps_muddy_black() -> None:
    import numpy as np

    from mtg_proxies.print_cards import _resolve_synthetic_color

    img = np.full((20, 16, 4), 0.1, dtype=float)
    img[..., 3] = 1.0

    # A muddy scanned black stays muddy rather than being forced to pure (0, 0, 0),
    # so it blends with the scanned border preserved at the rounded corners.
    assert _resolve_synthetic_color(img) == (26, 26, 26)


def test_matplotlib_synthesizes_for_old_frame(
    example_scans: list[tuple[str, str, str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mtg_proxies.print_cards as pc
    from mtg_proxies import print_cards_matplotlib

    calls: list[tuple[int, int, int, int]] = []
    real_detect = pc._detect_content_box

    def spy(img, reference, **kwargs) -> tuple[int, int, int, int]:  # noqa: ANN001, ANN003
        box = real_detect(img, reference, **kwargs)
        calls.append(box)
        return box

    monkeypatch.setattr(pc, "_detect_content_box", spy)

    old_frame_scans = [(path, "black", "1993") for path, _, _ in example_scans]
    out_file = tmp_path / "synth.png"
    print_cards_matplotlib(old_frame_scans, out_file, bleed_mm=3.0)

    assert (tmp_path / "synth_000.png").is_file()
    assert len(calls) == len(old_frame_scans)


def test_fpdf_synthesizes_for_old_frame(
    example_scans: list[tuple[str, str, str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mtg_proxies.print_cards as pc
    from mtg_proxies import print_cards_fpdf

    calls: list[tuple[int, int, int, int]] = []
    real_detect = pc._detect_content_box

    def spy(img, reference, **kwargs) -> tuple[int, int, int, int]:  # noqa: ANN001, ANN003
        box = real_detect(img, reference, **kwargs)
        calls.append(box)
        return box

    monkeypatch.setattr(pc, "_detect_content_box", spy)

    old_frame_scans = [(path, "black", "1993") for path, _, _ in example_scans]
    out_file = tmp_path / "synth.pdf"
    print_cards_fpdf(old_frame_scans, out_file, bleed_mm=3.0)

    assert out_file.is_file()
    assert len(calls) == len(old_frame_scans)
