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
    "silver": (192, 192, 192),
    "gold": (212, 175, 55),
}


def _resolve_bleed_color(
    border_color: str,
    borderless_fill: str,
) -> tuple[int, int, int] | str:
    """Resolve bleed color for a card.

    Returns an (r,g,b) tuple for solid fills, or the literal string ``"edge"``
    when the caller should sample the source image's outermost pixel.
    """
    if border_color in BORDER_COLOR_RGB:
        return BORDER_COLOR_RGB[border_color]
    if borderless_fill == "edge":
        return "edge"
    return BORDER_COLOR_RGB[borderless_fill]


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


def print_cards_matplotlib(
    images: Sequence[tuple[str, str]],
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
        images: List of ``(image_path, border_color)`` tuples.
        filepath: Name of the pdf file
        papersize: Size of the paper in inches. Defaults to A4.
        cardsize: Size of a card in inches.
        border_crop: How many pixel to crop from the border of each card.
        interpolation: Interpolation method for resizing images.
        dpi: Dots per inch for the output PDF.
        background_color: Background color of the PDF as name or hex code.
        bleed_mm: Extend each card outward by this many mm, painted in the
            card's border color.
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
                        image_path, border_color = images[idx]
                        img = plt.imread(image_path)
                        idx += 1

                        left = border_crop if x > 0 and gutter == 0 else 0
                        top = border_crop if y > 0 and gutter == 0 else 0
                        img = img[top:, left:]

                        lower = (
                            offset
                            + _occupied_space(occupied_cardsize, np.array([x, y]), border_crop, gutter=gutter)
                        ) / papersize
                        card_upper = (
                            offset
                            + _occupied_space(occupied_cardsize, np.array([x, y]), border_crop, gutter=gutter)
                            + cardsize * (image_size - [left, top]) / image_size
                            + 2 * bleed
                        ) / papersize

                        if bleed > 0:
                            bleed_color = _resolve_bleed_color(border_color, borderless_fill)
                            bleed_lower = lower
                            bleed_upper = card_upper
                            if bleed_color == "edge":
                                edge_pixel = img[0, 0] / 255.0 if img.dtype.kind == "u" else img[0, 0]
                                rect_color = tuple(float(c) for c in edge_pixel[:3])
                            else:
                                rect_color = tuple(c / 255.0 for c in bleed_color)
                            plt.gca().add_patch(
                                Rectangle(
                                    (bleed_lower[0], 1 - bleed_upper[1]),
                                    bleed_upper[0] - bleed_lower[0],
                                    bleed_upper[1] - bleed_lower[1],
                                    color=rect_color,
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
    images: Sequence[str | Path],
    filepath: str | Path,
    papersize: np.ndarray = np.array([210, 297]),
    cardsize: np.ndarray = np.array([2.5 * 25.4, 3.5 * 25.4]),
    border_crop: int = 14,
    background_color: tuple[int, int, int] | None = None,
    cropmarks: bool = True,
) -> None:
    """Print a list of cards to a pdf file.

    Args:
        images: List of image files
        filepath: Name of the pdf file
        papersize: Size of the paper in inches. Defaults to A4.
        cardsize: Size of a card in inches.
        border_crop: How many pixel to crop from the border of each card.
        background_color: Background color of the PDF as an RGB tuple.
        cropmarks: Whether to add crop marks to the PDF.
    """
    from fpdf import FPDF

    # Cards per sheet
    N = np.floor(papersize / cardsize).astype(int)
    if N[0] == 0 or N[1] == 0:
        raise ValueError(f"Paper size too small: {papersize}")
    cards_per_sheet = np.prod(N)
    offset = (papersize - _occupied_space(cardsize, N, border_crop, closed=True)) / 2

    # Ensure directory exists
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Initialize PDF
    pdf = FPDF(orientation="P", unit="mm", format="A4")

    for i, image in enumerate(tqdm(images, desc="Plotting cards")):
        if i % cards_per_sheet == 0:  # Startign a new sheet
            pdf.add_page()
            if background_color is not None:
                pdf.set_fill_color(*background_color)
                pdf.rect(0, 0, papersize[0], papersize[1], "F")

        x = (i % cards_per_sheet) % N[0]
        y = (i % cards_per_sheet) // N[0]

        # Crop left and top if not on border of sheet
        left = border_crop if x > 0 else 0
        top = border_crop if y > 0 else 0

        if left == 0 and top == 0:
            cropped_image = image
        else:
            path = Path(image)
            cropped_image = str(path.parent / (path.stem + f"_{left}_{top}" + path.suffix))
            if not Path(cropped_image).is_file():
                # Crop image
                plt.imsave(cropped_image, plt.imread(image)[top:, left:])

        # Compute extent
        lower = offset + _occupied_space(cardsize, np.array([x, y]), border_crop)
        size = cardsize * (image_size - [left, top]) / image_size

        # Plot image
        pdf.image(cropped_image, x=lower[0], y=lower[1], w=size[0], h=size[1])

        if cropmarks and ((i + 1) % cards_per_sheet == 0 or i + 1 == len(images)):
            # If this was the last card on a page, add crop marks
            pdf.set_line_width(0.05)
            pdf.set_draw_color(255, 255, 255)
            a = cardsize * (image_size - 2 * border_crop) / image_size
            b = papersize - N * a
            for x in range(N[0] + 1):
                for y in range(N[1] + 1):
                    mark = b / 2 + a * [x, y]
                    pdf.line(mark[0] - 0.5, mark[1], mark[0] + 0.5, mark[1])
                    pdf.line(mark[0], mark[1] - 0.5, mark[0], mark[1] + 0.5)

    tqdm.write(f"Writing to {filepath}")
    pdf.output(filepath)
