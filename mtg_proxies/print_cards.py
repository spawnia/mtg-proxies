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


def _flatten_corner_transparency(img: np.ndarray) -> np.ndarray:
    """Return opaque RGB with each transparent edge run replaced by its row's nearest opaque pixel.

    Scryfall scans fade to transparent in the rounded corners. Replicating that
    transparency outward would streak the bleed; instead each corner inherits its
    own side's tone (the black bottom row stays black, the light top row stays
    light) by copying the nearest opaque pixel along each row.
    """
    arr = _normalize(img)
    rgb = arr[..., :3].copy()
    if arr.shape[2] < 4:
        return rgb
    opaque = arr[..., 3] > 0.5
    for row in range(rgb.shape[0]):
        opaque_cols = np.flatnonzero(opaque[row])
        if opaque_cols.size == 0:
            continue
        first, last = opaque_cols[0], opaque_cols[-1]
        rgb[row, :first] = rgb[row, first]
        rgb[row, last + 1 :] = rgb[row, last]
    return rgb


def bleed_image(img: np.ndarray, inset_px: int, bleed_px: tuple[int, int]) -> np.ndarray:
    """Return an opaque float RGB image extended outward by ``bleed_px`` (rows, cols) per axis.

    Insets ``inset_px`` off every edge to drop the semi-transparent alpha rim and
    any edge scan artifact, flattens the rounded-corner transparency so each corner
    keeps its own side's tone, then replicates every edge and corner pixel into the
    margin with ``np.pad(mode="edge")``.
    """
    inset = img[inset_px : img.shape[0] - inset_px, inset_px : img.shape[1] - inset_px]
    flat = _flatten_corner_transparency(inset)
    bleed_rows, bleed_cols = bleed_px
    return np.pad(flat, ((bleed_rows, bleed_rows), (bleed_cols, bleed_cols), (0, 0)), mode="edge")


def _bleed_px(bleed_mm: float, cardsize_mm: np.ndarray) -> tuple[int, int]:
    """Bleed margin in scan pixels as ``(rows, cols)`` for the scan resolution.

    ``image_size`` is ``[width, height]``; ``cardsize_mm`` is ``[width, height]``,
    so per-mm resolution is ``image_size / cardsize_mm`` in ``[x, y]`` order.
    """
    px_per_mm = image_size / cardsize_mm
    return (round(bleed_mm * px_per_mm[1]), round(bleed_mm * px_per_mm[0]))


def _cached_bleed_png(image: str, img: np.ndarray, inset_px: int, bleed_px: tuple[int, int]) -> str:
    """Path to a cached bled PNG for ``image``, written on first use.

    Keyed by source path + inset + per-axis bleed so re-renders reuse the file.
    """
    source = Path(image)
    bleed_rows, bleed_cols = bleed_px
    cached = source.parent / f"{source.stem}_bleed{inset_px}_{bleed_rows}_{bleed_cols}{source.suffix}"
    if not cached.is_file():
        plt.imsave(cached, bleed_image(img, inset_px, bleed_px))
    return str(cached)


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
    images: Sequence[str],
    filepath: str | Path,
    papersize: np.ndarray = np.array([8.27, 11.69]),
    cardsize: np.ndarray = np.array([2.5, 3.5]),
    border_crop: int = 14,
    interpolation: str | None = "lanczos",
    dpi: int = 600,
    background_color: str | None = None,
    bleed_mm: float = 0.0,
    gutter_mm: float = 0.0,
) -> None:
    """Print a list of cards to a pdf file.

    Args:
        images: List of image paths.
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
                        image_path = images[idx]
                        img = plt.imread(image_path)
                        idx += 1

                        base = offset + _occupied_space(
                            occupied_cardsize, np.array([x, y]), border_crop, gutter=gutter
                        )
                        lower = base / papersize

                        if bleed > 0:
                            bled = bleed_image(img, EDGE_INSET, _bleed_px(bleed_mm, cardsize * 25.4))
                            card_upper = (base + cardsize + 2 * bleed) / papersize
                            extent = (lower[0], card_upper[0], 1 - card_upper[1], 1 - lower[1])
                            plt.imshow(
                                bled,
                                extent=extent,
                                aspect=papersize[1] / papersize[0],
                                interpolation=interpolation,
                            )
                        else:
                            left = border_crop if x > 0 and gutter == 0 else 0
                            top = border_crop if y > 0 and gutter == 0 else 0
                            img = img[top:, left:]
                            card_upper = (
                                base + cardsize * (image_size - [left, top]) / image_size
                            ) / papersize
                            extent = (lower[0], card_upper[0], 1 - card_upper[1], 1 - lower[1])
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
    images: Sequence[str],
    filepath: str | Path,
    papersize: np.ndarray = np.array([210, 297]),
    cardsize: np.ndarray = np.array([2.5 * 25.4, 3.5 * 25.4]),
    border_crop: int = 14,
    background_color: tuple[int, int, int] | None = None,
    cropmarks: bool = True,
    bleed_mm: float = 0.0,
    gutter_mm: float = 0.0,
) -> None:
    """Print a list of cards to a pdf file.

    Args:
        images: List of image paths.
        filepath: Name of the pdf file
        papersize: Size of the paper in mm. Defaults to A4.
        cardsize: Size of a card in mm.
        border_crop: How many pixels to crop from the border of each card.
        background_color: Background color of the PDF as an RGB tuple.
        cropmarks: Whether to add crop marks to the PDF.
        bleed_mm: Extend each card outward by this many mm, filled with the card's
            own border tone; scan artifacts at the card edge are painted over.
        gutter_mm: Space cards apart on the sheet by this many mm.
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

    for i, image in enumerate(tqdm(images, desc="Plotting cards")):
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
            bled_path = _cached_bleed_png(image, img, EDGE_INSET, _bleed_px(bleed, cardsize))
            pdf.image(
                bled_path,
                x=lower[0],
                y=lower[1],
                w=cardsize[0] + 2 * bleed,
                h=cardsize[1] + 2 * bleed,
            )
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
