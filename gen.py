from typing import cast, Callable
import dataclasses
import math
import cairosvg
import io


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

FONT_PATH = "fonts/BebasNeue-Regular.ttf"
FONT = ImageFont.truetype(
    # "fonts/roboto/RobotoMono-Regular.ttf",
    FONT_PATH,
    math.floor(TILE_HEIGHT * 0.85),
)

BACKGROUND = (0, 0, 0, 100)


@dataclasses.dataclass
class IconImage:
    index: int
    material_icon: str
    with_background: bool = True
    scale: float = 1.0

    def generate(self):
        out_img = Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))

        icon_path = get_path_to_material_icon(self.material_icon)

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
                int(TILE_WIDTH * self.scale),
                int(TILE_WIDTH * self.scale),
            ),
            resample=Image.Resampling.BILINEAR,
        )

        scale_width_diff = TILE_WIDTH - icon_img.width
        scale_height_diff = TILE_HEIGHT - icon_img.height

        paste_x = scale_width_diff // 2
        paste_y = scale_height_diff // 2

        out_img.paste(
            icon_img,
            (paste_x, paste_y),
            icon_img,
        )

        if self.with_background:
            euclid = euclidean_distance_transform(out_img.getchannel("A"))
            out_img = add_outline_via_euclidean_distance_transform(out_img, euclid)

        return out_img


@dataclasses.dataclass
class IconSvg:
    index: int
    name: str
    scale: float = 1.0
    with_background: bool = True

    def generate(self):
        out_img = Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))

        icon_path = f"./node_modules/@mdi/svg/svg/{self.name}.svg"
        icon_img = self._load_svg(icon_path)

        scale_width_diff = TILE_WIDTH - icon_img.width
        scale_height_diff = TILE_HEIGHT - icon_img.height

        paste_x = scale_width_diff // 2
        paste_y = scale_height_diff // 2

        out_img.paste(
            icon_img,
            (paste_x, paste_y),
            icon_img,
        )

        if self.with_background:
            euclid = euclidean_distance_transform(out_img.getchannel("A"))
            out_img = add_outline_via_euclidean_distance_transform(out_img, euclid)

        return out_img

    @staticmethod
    def _load_svg(path: str) -> Image.Image:
        svg_png = cairosvg.svg2png(
            url=path,
            parent_width=TILE_WIDTH,
            parent_height=TILE_WIDTH,
        )
        svg_png = io.BytesIO(cast(bytes, svg_png))
        svg_img = Image.open(svg_png)

        svg_img_a = svg_img.getchannel("A")
        icon_img_l = Image.new("L", svg_img.size, 255)

        icon_img = Image.merge(
            "LA",
            (
                icon_img_l,
                svg_img_a,
            ),
        )

        return icon_img


@dataclasses.dataclass
class IconEmpty:
    index: int


@dataclasses.dataclass
class IconCustom:
    index: int
    generator: Callable[[], Image.Image]


@dataclasses.dataclass
class IconText:
    index: int
    text: str
    center: bool = False
    scale: float = 0.5

    def generate(self):
        img = Image.new(
            "RGBA",
            (TILE_WIDTH, TILE_HEIGHT),
            (0, 0, 0, 0),
        )
        img_draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(
            FONT_PATH,
            math.floor(TILE_HEIGHT * self.scale),
        )

        anchor = "ms" if self.center else "ls"

        text_bbox = img_draw.textbbox(
            (0, 0),
            self.text,
            font=font,
            anchor=anchor,
            spacing=0,
        )

        text_xy = (
            (TILE_WIDTH / 2) if self.center else TILE_WIDTH * 0.1,
            (TILE_HEIGHT * 0.8) - text_bbox[3],
        )

        img_draw.multiline_text(
            text_xy,
            self.text,
            font=font,
            anchor=anchor,
            spacing=0,
            fill="white",
        )

        euclid = euclidean_distance_transform(img.getchannel("A"))
        img = add_outline_via_euclidean_distance_transform(img, euclid)

        return img


ICONS = [
    IconImage(1, "signal", scale=1.2),  # RSSI
    IconSvg(2, "chevron-left"),
    IconSvg(3, "chevron-right"),
    IconSvg(4, "speedometer"),
    IconSvg(5, "home"),  # Home
    IconText(6, "v"),  # Voltage Unit
    IconText(7, "mah", scale=0.4),  # mAh
    IconText(12, "m"),  # Alt Unit (m)
    IconText(13, "°f"),  # Temp Unit (F)
    IconText(14, "°c"),  # Temp Unit (C)
    IconText(15, "ft"),  # Alt Unit (ft)
    IconSvg(20, "axis-z-rotate-clockwise"),  # "Roll" ???  TODO: Graphic?
    IconSvg(21, "horizontal-rotate-clockwise"),  # "Pitch" ???  TODO: Graphic?
    # Cardinal Directions (NSEW)
    IconText(24, "N"),
    IconText(25, "S"),
    IconText(26, "E"),
    IconText(27, "W"),
    # IconImage(60, "left"),  # Override < Char
    # IconImage(62, "right"),  # Override > Char
    IconSvg(112, "speedometer"),  # Speedometer
    IconSvg(113, "rotate-left"),  # Anti-clockwise ????
    # Crosshair (3x1)
    IconEmpty(114),
    IconSvg(115, "crosshairs-gps", False),
    IconEmpty(116),
    IconSvg(117, "chevron-double-up"),  # Up Chevron
    IconSvg(118, "chevron-double-down"),  # Down Chevron
    IconSvg(119, "chevron-double-right"),  # Right Chevron
    IconSvg(120, "chevron-double-left"),  # Left Chevron
    IconSvg(122, "thermometer"),  # Thermometer
    IconImage(123, "signal", scale=1.2),  # RSSI (LQ)
    IconText(125, "km"),  # Dist Unit (km)
    IconText(126, "mi"),  # Dist Unit (mi)
    IconSvg(127, "altimeter"),  # "Alt" ???
    IconSvg(137, "latitude"),  # Longitude ("Lon")
    # Battery
    IconImage(144, "battery_full", scale=1.25),
    IconImage(145, "battery_5_bar", scale=1.25),
    IconImage(146, "battery_4_bar", scale=1.25),
    IconImage(147, "battery_3_bar", scale=1.25),
    IconImage(148, "battery_2_bar", scale=1.25),
    IconImage(149, "battery_1_bar", scale=1.25),
    IconImage(150, "battery_0_bar", scale=1.25),
    IconImage(151, "battery_alert", scale=1.25),
    IconSvg(152, "longitude"),  # Longitude ("Lon")
    IconText(153, "ft/s", scale=0.4),  # Speed Unit (ft/s)
    IconText(154, "a"),  # Amps Unit
    IconSvg(155, "airplane-clock"),  # Timer (On) TODO: Clock graphic?
    IconSvg(156, "battery-clock"),  # Timer (On) TODO: Drone clock graphic?
    IconText(157, "mph", scale=0.4),  # Speed Unit (mph)
    IconText(158, "kph", scale=0.4),  # Speed Unit (kph)
    IconText(159, "m/s", scale=0.4),  # Speed Unit (m/s)
]


def get_path_to_material_icon(
    icon_name: str,
) -> str | None:
    return f"icons/material/{icon_name}.png"


def get_icon_image(icon: IconImage) -> Image.Image:
    print(icon)
    if isinstance(icon, IconEmpty):
        return Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))
    else:
        return icon.generate()


def get_arrows_image() -> Image.Image:
    img = Image.new(
        "RGBA",
        (TILE_WIDTH * TILES_PER_ROW, TILE_HEIGHT),
        (0, 0, 0, 0),
    )

    arrow_icon = IconSvg(0, "arrow-down-bold").generate()

    for i in range(0, TILES_PER_ROW):
        rotated_arrow_icon = arrow_icon.rotate(
            i * 22.5, resample=Image.Resampling.BICUBIC
        )
        img.paste(rotated_arrow_icon, (i * TILE_WIDTH, 0))

    return img


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
    return img
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
    return img
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

    arrows_img = get_arrows_image()
    out.paste(arrows_img, (0, TILE_HEIGHT * 6))

    for icon in ICONS:
        icon_img = get_icon_image(icon)
        tile_x = icon.index % TILES_PER_ROW * TILE_WIDTH
        tile_y = icon.index // TILES_PER_ROW * TILE_HEIGHT

        out.paste(icon_img, (tile_x, tile_y))

    preview = out.copy()
    overlay.paste(preview, (0, 0), preview)
    preview = overlay

    out.save("template.png")
    preview.save("preview.png")


if __name__ == "__main__":
    main()
