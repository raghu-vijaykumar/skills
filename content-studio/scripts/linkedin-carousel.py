"""Assemble reviewed portrait slide PNGs into an organic LinkedIn document post."""

import argparse
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slides", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    slides = sorted(Path(args.slides).glob("*.png"))
    if len(slides) < 2:
        parser.error("Carousel needs at least two numbered PNG slides")
    images = []
    for slide in slides:
        image = Image.open(slide)
        if image.size != (1080, 1350):
            parser.error(f"{slide.name} must be 1080x1350")
        images.append(image.convert("RGB"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # A PDF document, rather than a sponsored Carousel API payload, lets a
    # personal organic post present a sequence of swipeable information pages.
    images[0].save(output, "PDF", save_all=True, append_images=images[1:], resolution=72.0)
    print(f"Created {output} with {len(images)} pages")


if __name__ == "__main__":
    main()
