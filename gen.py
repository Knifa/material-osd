from typing import cast
import dataclasses
import math

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    PyAccess,
)

CHARS = [chr(x) for x in range(ord(" "), ord("_") + 1)]

TILE_WIDTH = 12 * 3
TILE_HEIGHT = 18 * 3

TILES_PER_ROW = 16
TILE_ROW_COUNT = math.ceil(len(CHARS) / TILES_PER_ROW)

FONT = ImageFont.truetype(
    # "fonts/roboto/RobotoMono-Regular.ttf",
    "fonts/BebasNeue-Regular.ttf",
    math.floor(TILE_HEIGHT * 0.85),
)

BACKGROUND = (0, 0, 0, 100)


@dataclasses.dataclass
class IconImage:
    index: int
    material_icon: str
    with_background: bool = True


@dataclasses.dataclass
class IconEmpty:
    index: int


ICONS = [
    IconImage(1, "signal"),
    IconImage(2, "left"),
    IconImage(3, "right"),
    IconEmpty(6),
    IconImage(60, "left"),
    IconImage(62, "right"),
    IconEmpty(114),
    IconImage(115, "crosshair", False),
    IconEmpty(116),
    IconImage(123, "signal"),
    IconImage(144, "battery_full"),
    IconImage(145, "battery_5_bar"),
    IconImage(146, "battery_4_bar"),
    IconImage(147, "battery_3_bar"),
    IconImage(148, "battery_2_bar"),
    IconImage(149, "battery_1_bar"),
    IconImage(150, "battery_0_bar"),
    IconImage(151, "battery_alert"),
]


def get_path_to_material_icon(
    icon_name: str,
) -> str | None:
    return f"icons/material/{icon_name}.png"


def get_icon_image(icon: IconImage) -> Image.Image:
    if isinstance(icon, IconEmpty):
        return Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))

    out_img = Image.new(
        "RGBA",
        (TILE_WIDTH, TILE_HEIGHT),
        (0, 0, 0, 0)
        # BACKGROUND if icon.with_background else (0, 0, 0, 0),
    )

    icon_path = get_path_to_material_icon(icon.material_icon)

    icon_img = Image.open(cast(str, icon_path))
    icon_img = icon_img.convert("RGBA")
    icon_img_a = icon_img.getchannel("A")
    icon_img_l = Image.new("L", icon_img.size, 255)
    icon_img = Image.merge(
        "LA",
        (
            icon_img_l,
            icon_img_a,
        ),
    )

    icon_img = icon_img.resize(
        (
            TILE_WIDTH,
            TILE_WIDTH,
        ),
        resample=Image.Resampling.BILINEAR,
    )

    out_img.paste(
        icon_img,
        (0, (TILE_HEIGHT // 2) - (TILE_WIDTH // 2)),
        icon_img,
    )

    euclid = euclidean_distance_transform(out_img.getchannel("A"))
    outline = add_outline_via_euclidean_distance_transform(out_img, euclid)

    return outline


def get_char_image() -> Image.Image:
    img = Image.new(
        "RGBA",
        (TILE_WIDTH * TILES_PER_ROW, TILE_HEIGHT * TILE_ROW_COUNT),
        (0, 0, 0, 0),
    )

    img_draw = ImageDraw.Draw(img)

    for i, char in enumerate(CHARS):
        tile_x = i % TILES_PER_ROW * TILE_WIDTH
        tile_y = i // TILES_PER_ROW * TILE_HEIGHT

        text_x = tile_x + TILE_WIDTH // 2
        text_y = tile_y + (TILE_HEIGHT * 0.8)

        img_draw.text(
            (text_x, text_y),
            char,
            fill="white",
            font=FONT,
            # stroke_fill=(0, 0, 0, 127),
            # stroke_width=3,
            anchor="ms",
        )

    euclid = euclidean_distance_transform(img.getchannel("A"))
    outline = add_outline_via_euclidean_distance_transform(img, euclid)

    return outline


def add_outline_via_euclidean_distance_transform(
    img: Image.Image, euclid: Image.Image, radius=3
) -> Image.Image:
    img = img.copy()
    outline = Image.new("L", img.size, 0)

    euclid_px = PyAccess.new(euclid)
    outline_px = PyAccess.new(outline)

    radius2 = radius**2

    for y in range(img.height):
        for x in range(img.width):
            if euclid_px[x, y] == 255:
                continue

            if euclid_px[x, y] <= radius2:
                outline_px[x, y] = 255
            else:
                dist = math.sqrt(euclid_px[x, y])

                if dist < radius + 1:
                    outline_px[x, y] = int((1 - (dist - radius)) * 255)

    outline = Image.merge(
        "LA",
        (
            Image.new("L", outline.size, 0),
            Image.eval(outline, lambda x: x * 0.33),
        ),
    )

    outline = outline.convert("RGBA")

    outline.alpha_composite(img)

    return outline


OCTAGON_PATTERN_9x9 = [
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
]


def euclidean_distance_transform(img: Image.Image) -> Image.Image:
    img = Image.eval(img, lambda x: 255 if x > 100 else 0)
    ed_img = Image.new("L", img.size, 0)

    img_px = PyAccess.new(img)
    ed_img_px = PyAccess.new(ed_img)

    for y in range(img.height):
        for x in range(img.width):
            min_dist: float | None = None

            for y2 in range(len(OCTAGON_PATTERN_9x9)):
                for x2 in range(len(OCTAGON_PATTERN_9x9)):
                    if OCTAGON_PATTERN_9x9[y2][x2] == 0:
                        continue

                    pixel_x = x + x2 - 4
                    pixel_y = y + y2 - 4

                    if pixel_x < 0 or pixel_x >= img.width:
                        continue
                    if pixel_y < 0 or pixel_y >= img.height:
                        continue

                    if img_px[pixel_x, pixel_y] == 0:
                        continue

                    dist = (x2 - 4) ** 2 + (y2 - 4) ** 2

                    if min_dist is None or dist < min_dist:
                        min_dist = dist

            if min_dist:
                ed_img_px[x, y] = min_dist
            else:
                ed_img_px[x, y] = 255

    return ed_img


def main():
    overlay = Image.open("template_overlay.png")
    overlay = overlay.convert("RGB")
    overlay = Image.eval(overlay, lambda x: x * 0.25 + 128)

    template = Image.open("betaflight_template.png")
    out = template.copy()

    chars_img = get_char_image()
    out.paste(chars_img, (0, TILE_HEIGHT * 2))

    for icon in ICONS:
        icon_img = get_icon_image(icon)
        tile_x = icon.index % TILES_PER_ROW * TILE_WIDTH
        tile_y = icon.index // TILES_PER_ROW * TILE_HEIGHT

        out.paste(icon_img, (tile_x, tile_y))

    # overlay.paste(out, (0, 0), out)
    # out = overlay.copy()

    out.save("text.png")


if __name__ == "__main__":
    main()
