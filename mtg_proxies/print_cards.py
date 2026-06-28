from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from tqdm import tqdm

from mtg_proxies.plotting import SplitPages

image_size = np.array([745, 1040])

BORDER_COLOR_RGB: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
}

# Pixels cropped off every edge of a bordered scan before it is placed under
# --bleed. Large enough to drop scan artifacts that cling to the very edge of the
# card, small enough to stay inside the ~26 px transparent rounded-corner zone of
# a Scryfall scan, so the rounded corners survive. ~1 mm on a 745x1040 scan.
EDGE_INSET = 12


def _normalize(img: np.ndarray) -> np.ndarray:
    """Return image data as float in ``[0, 1]`` regardless of source dtype."""
    arr = img.astype(float)
    if img.dtype.kind in "ui":
        arr = arr / 255.0
    return arr


def _opaque_mask(arr: np.ndarray) -> np.ndarray:
    """Boolean mask of non-transparent pixels (all-True when no alpha channel)."""
    if arr.shape[2] == 4:
        return arr[..., 3] > 0.5
    return np.ones(arr.shape[:2], dtype=bool)


def _central_band(length: int, fraction: float) -> tuple[int, int]:
    """Index range covering the central ``fraction`` of ``length``."""
    margin = int(length * (1 - fraction) / 2)
    return margin, length - margin


def _estimate_border_color(img: np.ndarray, band: int = 4, central_fraction: float = 0.6) -> np.ndarray:
    """Estimate the border color as the per-channel median of the outer ring.

    Samples only opaque pixels in thin edge bands over the central fraction of
    each side, dodging the transparent rounded corners and rejecting stray scan
    dots by majority. Returns normalized ``[0, 1]`` RGB.
    """
    arr = _normalize(img)
    height, width = arr.shape[:2]
    opaque = _opaque_mask(arr)
    cy0, cy1 = _central_band(height, central_fraction)
    cx0, cx1 = _central_band(width, central_fraction)
    regions = [
        (slice(0, band), slice(cx0, cx1)),
        (slice(height - band, height), slice(cx0, cx1)),
        (slice(cy0, cy1), slice(0, band)),
        (slice(cy0, cy1), slice(width - band, width)),
    ]
    samples = [arr[rs, cs][opaque[rs, cs]] for rs, cs in regions]
    stacked = np.concatenate(samples)
    return np.median(stacked[:, :3], axis=0)


def _bleed_fill_color(img: np.ndarray, border_color: str, borderless_fill: str) -> tuple[int, int, int]:
    """Resolve the bleed fill as a 0-255 RGB tuple.

    The fill paints both the bleed margin and the thin edge ring cropped from the
    scan. It is the per-channel median of the scanned border ring, so it matches
    each scan exactly: muddy non-digital scans stay muddy, genuinely clean digital
    borders stay pure. Borderless cards can instead force a solid fill.
    """
    if border_color == "borderless" and borderless_fill != "edge":
        return BORDER_COLOR_RGB[borderless_fill]
    r, g, b = (int(round(c * 255)) for c in _estimate_border_color(img))
    return (r, g, b)


def _edge_inset(border_color: str, full_art: bool) -> int:
    """Pixels to crop off every edge of a scan before placing it under --bleed.

    Bordered cards crop a thin uniform ring so scan artifacts at the very edge are
    replaced by the bleed fill, while the ring stays inside the rounded corner so
    it survives. Full-art and borderless cards keep their full image: their edge is
    artwork, not a border to clean away.
    """
    if full_art or border_color == "borderless":
        return 0
    return EDGE_INSET


def _inset_scan(image: str, img: np.ndarray, inset: int) -> str:
    """Path to a cached copy of ``img`` with ``inset`` px cropped off every edge.

    Returns the original path unchanged when no inset is needed.
    """
    if not inset:
        return image
    source = Path(image)
    cropped = source.parent / f"{source.stem}_inset{inset}{source.suffix}"
    if not cropped.is_file():
        plt.imsave(cropped, img[inset : img.shape[0] - inset, inset : img.shape[1] - inset])
    return str(cropped)


def _occupied_space(
    cardsize: np.ndarray,
    pos: np.ndarray,
    border_crop: int,
    gutter: float = 0.0,
    closed: bool = False,
) -> np.ndarray:
    image_term = cardsize * (pos * image_size - np.clip(2 * pos - 1 - closed, 0, None) * border_crop) / image_size
    gutter_term = np.clip(pos - closed, 0, None) * gutter
    return image_term + gutter_term


def _crop_mark_positions(
    N: np.ndarray,
    papersize: np.ndarray,
    cardsize: np.ndarray,
    border_crop: int,
    bleed: float,
    gutter: float,
    offset: np.ndarray,
) -> np.ndarray:
    """Positions of crop-mark crosses for a sheet, as an ``(M, 2)`` array.

    With no gutter, cards abut and marks sit on the shared grid lines. With a
    gutter, each card is cut individually, so marks sit at every card's four
    cut-box corners.
    """
    if gutter == 0:
        a = (cardsize * (image_size - 2 * border_crop) / image_size) + 2 * bleed
        b = papersize - N * a
        return np.array([b / 2 + a * np.array([cx, cy]) for cx in range(N[0] + 1) for cy in range(N[1] + 1)])

    occupied_cardsize = cardsize + 2 * bleed
    marks = []
    for gx in range(N[0]):
        for gy in range(N[1]):
            lower = offset + _occupied_space(occupied_cardsize, np.array([gx, gy]), border_crop, gutter=gutter)
            card_lower = lower + bleed
            card_upper = card_lower + cardsize
            for mx in (card_lower[0], card_upper[0]):
                for my in (card_lower[1], card_upper[1]):
                    marks.append(np.array([mx, my]))
    return np.array(marks)


def print_cards_matplotlib(
    images: Sequence[tuple[str, str, bool]],
    filepath: str | Path,
    papersize: np.ndarray = np.array([8.27, 11.69]),
    cardsize: np.ndarray = np.array([2.5, 3.5]),
    border_crop: int = 14,
    interpolation: str | None = "lanczos",
    dpi: int = 600,
    background_color: str | None = None,
    bleed_mm: float = 0.0,
    gutter_mm: float = 0.0,
    borderless_fill: str = "edge",
) -> None:
    """Print a list of cards to a pdf file.

    Args:
        images: List of ``(image_path, border_color, full_art)`` tuples.
        filepath: Name of the pdf file
        papersize: Size of the paper in inches. Defaults to A4.
        cardsize: Size of a card in inches.
        border_crop: How many pixels to crop from the border of each card.
        interpolation: Interpolation method for resizing images.
        dpi: Dots per inch for the output PDF.
        background_color: Background color of the PDF as name or hex code.
        bleed_mm: Extend each card outward by this many mm, filled with the card's
            own border tone; scan artifacts at the card edge are painted over.
        gutter_mm: Space cards apart on the sheet by this many mm.
        borderless_fill: Fill strategy for borderless cards.
    """
    bleed = bleed_mm / 25.4
    gutter = gutter_mm / 25.4
    occupied_cardsize = cardsize + 2 * bleed

    N = np.floor((papersize + gutter) / (occupied_cardsize + gutter)).astype(int)
    if N[0] == 0 or N[1] == 0:
        raise ValueError(f"Paper size too small: {papersize}")
    offset = (
        papersize - _occupied_space(occupied_cardsize, N, border_crop, gutter=gutter, closed=True)
    ) / 2

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    saver = PdfPages if filepath.suffix == ".pdf" else SplitPages

    with saver(filepath) as saver, tqdm(total=len(images), desc="Plotting cards") as pbar:
        idx = 0
        while idx < len(images):
            fig = plt.figure(figsize=papersize)
            ax = fig.add_axes((0, 0, 1, 1))
            if background_color is not None:
                plt.gca().add_patch(Rectangle((0, 0), 1, 1, color=background_color, zorder=-1000))

            for y in range(N[1]):
                for x in range(N[0]):
                    if idx < len(images):
                        image_path, border_color, full_art = images[idx]
                        img = plt.imread(image_path)
                        idx += 1

                        if bleed > 0:
                            fill = tuple(c / 255.0 for c in _bleed_fill_color(img, border_color, borderless_fill))
                            inset = _edge_inset(border_color, full_art)
                            if inset:
                                img = img[inset : img.shape[0] - inset, inset : img.shape[1] - inset]
                            left = top = 0
                        else:
                            left = border_crop if x > 0 and gutter == 0 else 0
                            top = border_crop if y > 0 and gutter == 0 else 0
                            img = img[top:, left:]

                        base = offset + _occupied_space(occupied_cardsize, np.array([x, y]), border_crop, gutter=gutter)
                        lower = base / papersize
                        card_upper = (
                            base + cardsize * (image_size - [left, top]) / image_size + 2 * bleed
                        ) / papersize

                        if bleed > 0:
                            plt.gca().add_patch(
                                Rectangle(
                                    (lower[0], 1 - card_upper[1]),
                                    card_upper[0] - lower[0],
                                    card_upper[1] - lower[1],
                                    color=fill,
                                    zorder=-500,
                                )
                            )

                        image_lower = lower + (bleed / papersize)
                        image_upper = card_upper - (bleed / papersize)
                        extent = (image_lower[0], image_upper[0], 1 - image_upper[1], 1 - image_lower[1])

                        plt.imshow(
                            img,
                            extent=extent,
                            aspect=papersize[1] / papersize[0],
                            interpolation=interpolation,
                        )
                        pbar.update(1)

            plt.xlim(0, 1)
            plt.ylim(0, 1)
            ax.axis("off")

            saver.savefig(dpi=dpi)
            plt.close()


def print_cards_fpdf(
    images: Sequence[tuple[str, str, bool]],
    filepath: str | Path,
    papersize: np.ndarray = np.array([210, 297]),
    cardsize: np.ndarray = np.array([2.5 * 25.4, 3.5 * 25.4]),
    border_crop: int = 14,
    background_color: tuple[int, int, int] | None = None,
    cropmarks: bool = True,
    bleed_mm: float = 0.0,
    gutter_mm: float = 0.0,
    borderless_fill: str = "edge",
) -> None:
    """Print a list of cards to a pdf file.

    Args:
        images: List of ``(image_path, border_color, full_art)`` tuples.
        filepath: Name of the pdf file
        papersize: Size of the paper in mm. Defaults to A4.
        cardsize: Size of a card in mm.
        border_crop: How many pixels to crop from the border of each card.
        background_color: Background color of the PDF as an RGB tuple.
        cropmarks: Whether to add crop marks to the PDF.
        bleed_mm: Extend each card outward by this many mm, filled with the card's
            own border tone; scan artifacts at the card edge are painted over.
        gutter_mm: Space cards apart on the sheet by this many mm.
        borderless_fill: Fill strategy for borderless cards.
    """
    from fpdf import FPDF

    bleed = float(bleed_mm)
    gutter = float(gutter_mm)
    occupied_cardsize = cardsize + 2 * bleed

    N = np.floor((papersize + gutter) / (occupied_cardsize + gutter)).astype(int)
    if N[0] == 0 or N[1] == 0:
        raise ValueError(f"Paper size too small: {papersize}")
    cards_per_sheet = np.prod(N)
    offset = (
        papersize - _occupied_space(occupied_cardsize, N, border_crop, gutter=gutter, closed=True)
    ) / 2

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF(orientation="P", unit="mm", format="A4")

    for i, (image, border_color, full_art) in enumerate(tqdm(images, desc="Plotting cards")):
        if i % cards_per_sheet == 0:
            pdf.add_page()
            if background_color is not None:
                pdf.set_fill_color(*background_color)
                pdf.rect(0, 0, papersize[0], papersize[1], "F")

        x = (i % cards_per_sheet) % N[0]
        y = (i % cards_per_sheet) // N[0]
        lower = offset + _occupied_space(occupied_cardsize, np.array([x, y]), border_crop, gutter=gutter)

        if bleed > 0:
            img = plt.imread(image)
            pdf.set_fill_color(*_bleed_fill_color(img, border_color, borderless_fill))
            pdf.rect(lower[0], lower[1], cardsize[0] + 2 * bleed, cardsize[1] + 2 * bleed, "F")
            card_image = _inset_scan(image, img, _edge_inset(border_color, full_art))
            pdf.image(card_image, x=lower[0] + bleed, y=lower[1] + bleed, w=cardsize[0], h=cardsize[1])
        else:
            left = border_crop if x > 0 and gutter == 0 else 0
            top = border_crop if y > 0 and gutter == 0 else 0
            if left == 0 and top == 0:
                cropped_image = image
            else:
                path = Path(image)
                cropped_image = str(path.parent / (path.stem + f"_{left}_{top}" + path.suffix))
                if not Path(cropped_image).is_file():
                    plt.imsave(cropped_image, plt.imread(image)[top:, left:])
            size = cardsize * (image_size - [left, top]) / image_size
            pdf.image(cropped_image, x=lower[0], y=lower[1], w=size[0], h=size[1])

        if cropmarks and ((i + 1) % cards_per_sheet == 0 or i + 1 == len(images)):
            pdf.set_line_width(0.05)
            pdf.set_draw_color(255, 255, 255)
            for mark in _crop_mark_positions(N, papersize, cardsize, border_crop, bleed, gutter, offset):
                pdf.line(mark[0] - 0.5, mark[1], mark[0] + 0.5, mark[1])
                pdf.line(mark[0], mark[1] - 0.5, mark[0], mark[1] + 0.5)

    tqdm.write(f"Writing to {filepath}")
    pdf.output(filepath)
