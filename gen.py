from typing import Literal, Sequence, Tuple, Union, cast, Callable
import dataclasses
import math
import cairosvg
import io


from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageOps,
    PyAccess,
)

CHARS = [chr(x) for x in range(ord(" "), ord("_") + 1)]

TILE_WIDTH = 12 * 3
TILE_HEIGHT = 18 * 3

TILES_PER_ROW = 16
TILE_ROW_COUNT = math.ceil(len(CHARS) / TILES_PER_ROW)

FONT_PATH = "fonts/BebasNeue-Regular.ttf"
FONT = ImageFont.truetype(
    FONT_PATH,
    math.floor(TILE_HEIGHT * 0.85),
)

BACKGROUND = (0, 0, 0, 100)


def load_svg(
    path: str,
    width: int | None = None,
    height: int | None = None,
) -> Image.Image:
    svg_png = cairosvg.svg2png(
        url=path,
        parent_width=width,
        parent_height=height,
    )
    svg_png = io.BytesIO(cast(bytes, svg_png))
    svg_img = Image.open(svg_png)

    return svg_img


# @dataclasses.dataclass
# class IconImage:
#     index: int
#     material_icon: str
#     with_background: bool = True
#     scale: float = 1.0

#     def generate(self):
#         out_img = Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))

#         icon_path = get_path_to_material_icon(self.material_icon)

#         icon_img = Image.open(cast(str, icon_path))
#         icon_img = icon_img.convert("RGBA")
#         icon_img_a = icon_img.getchannel("A")
#         icon_img_l = Image.new("L", icon_img.size, 255)
#         icon_img = Image.merge(
#             "LA",
#             (
#                 icon_img_l,
#                 icon_img_a,
#             ),
#         )

#         icon_img = icon_img.resize(
#             (
#                 int(TILE_WIDTH * self.scale),
#                 int(TILE_WIDTH * self.scale),
#             ),
#             resample=Image.Resampling.BILINEAR,
#         )

#         scale_width_diff = TILE_WIDTH - icon_img.width
#         scale_height_diff = TILE_HEIGHT - icon_img.height

#         paste_x = scale_width_diff // 2
#         paste_y = scale_height_diff // 2

#         out_img.paste(
#             icon_img,
#             (paste_x, paste_y),
#             icon_img,
#         )

#         if self.with_background:
#             euclid = euclidean_distance_transform(out_img.getchannel("A"))
#             out_img = add_outline_via_euclidean_distance_transform(out_img, euclid)

#         return out_img


def apply_outline(img: Image.Image) -> Image.Image:
    euclid = euclidean_distance_transform(img.getchannel("A"))
    img = add_outline_via_euclidean_distance_transform(img, euclid)

    return img


@dataclasses.dataclass
class Icon:
    index: int

    def __post_init__(self):
        self.img = Image.new("RGBA", (TILE_WIDTH, TILE_HEIGHT), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)

    def generate(self) -> Image.Image:
        raise NotImplementedError()


@dataclasses.dataclass
class IconSvg(Icon):
    name: str
    scale: float = 1.0
    with_background: bool = True
    offset_x: float = 0
    offset_y: float = 0

    def generate(self):
        icon_path = f"./node_modules/@mdi/svg/svg/{self.name}.svg"
        icon_img = self._load_svg(icon_path)

        scale_width_diff = TILE_WIDTH - icon_img.width
        scale_height_diff = TILE_HEIGHT - icon_img.height

        paste_x = int(scale_width_diff / 2 + self.offset_x)
        paste_y = int(scale_height_diff / 2 + self.offset_y)

        self.img.paste(icon_img, (paste_x, paste_y))

        if self.with_background:
            self.img = apply_outline(self.img)

        return self.img

    def _load_svg(self, path: str) -> Image.Image:
        svg_img = load_svg(
            path,
            width=int(TILE_WIDTH * self.scale),
            height=int(TILE_WIDTH * self.scale),
        )
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
class IconEmpty(Icon):
    index: int

    def generate(self) -> Image.Image:
        return self.img


@dataclasses.dataclass
class IconText(Icon):
    text: str
    center: bool = False
    scale: float = 0.5

    def generate(self):
        font = ImageFont.truetype(
            FONT_PATH,
            math.floor(TILE_HEIGHT * self.scale),
        )

        anchor = "ms" if self.center else "ls"

        text_bbox = self.draw.textbbox(
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

        self.draw.multiline_text(
            text_xy,
            self.text,
            font=font,
            anchor=anchor,
            spacing=0,
            fill="white",
        )

        return apply_outline(self.img)


@dataclasses.dataclass
class IconStickOverlay(Icon):
    position: Literal["high", "middle", "low"]

    def generate(self) -> Image.Image:
        x_middle = TILE_WIDTH // 2
        if self.position == "high":
            coords = (x_middle, TILE_HEIGHT * 0.2)
        elif self.position == "middle":
            coords = (x_middle, TILE_HEIGHT * 0.5)
        elif self.position == "low":
            coords = (x_middle, TILE_HEIGHT * 0.8)
        else:
            raise ValueError(f"Invalid position: {self.position}")

        self.draw.ellipse(
            (
                (coords[0] - 4, coords[1] - 4),
                (coords[0] + 4, coords[1] + 4),
            ),
            fill="white",
        )

        return apply_outline(self.img)


class IconStickCenterLine(Icon):
    def generate(self) -> Image.Image:
        self.draw.line(
            (
                (TILE_WIDTH // 2, 0),
                (TILE_WIDTH // 2, TILE_HEIGHT),
            ),
            fill="white",
            width=3,
        )

        self.draw.line(
            (
                (0, TILE_HEIGHT // 2),
                (TILE_WIDTH, TILE_HEIGHT // 2),
            ),
            fill="white",
            width=3,
        )

        return apply_outline(self.img)


class IconStickVerticalLine(Icon):
    def generate(self) -> Image.Image:
        self.draw.line(
            (
                (TILE_WIDTH // 2, 0),
                (TILE_WIDTH // 2, TILE_HEIGHT),
            ),
            fill="white",
            width=3,
        )

        return apply_outline(self.img)


class IconStickHorizontalLine(Icon):
    def generate(self) -> Image.Image:
        self.draw.line(
            (
                (0, TILE_HEIGHT // 2),
                (TILE_WIDTH, TILE_HEIGHT // 2),
            ),
            fill="white",
            width=3,
        )

        return apply_outline(self.img)


@dataclasses.dataclass
class IconHeading(Icon):
    divided: bool

    def generate(self) -> Image.Image:
        coords = (
            (TILE_WIDTH / 2, TILE_HEIGHT * 0.2),
            (TILE_WIDTH / 2, TILE_HEIGHT * (0.5 if self.divided else 0.8)),
        )

        self.draw.rounded_rectangle(
            (
                (coords[0][0] - 1.5, coords[0][1]),
                (coords[1][0] + 1.5, coords[1][1]),
            ),
            fill="white",
            radius=1,
        )

        return apply_outline(self.img)


@dataclasses.dataclass
class IconHeadingDecoration(Icon):
    def generate(self) -> Image.Image:
        width = 3
        width_2 = width / 2

        self.draw.rounded_rectangle(
            (
                (TILE_WIDTH * 0.45, -10),
                (TILE_WIDTH * 0.55, TILE_HEIGHT * 0.1),
            ),
            fill="white",
            radius=1,
        )

        self.draw.rounded_rectangle(
            (
                (TILE_WIDTH * 0.33, TILE_HEIGHT / 2 - width_2),
                (TILE_WIDTH * 0.66, TILE_HEIGHT / 2 + width_2),
            ),
            fill="white",
            radius=1,
        )

        self.draw.rounded_rectangle(
            (
                (TILE_WIDTH * 0.45, TILE_HEIGHT * 0.9),
                (TILE_WIDTH * 0.55, TILE_HEIGHT + 10),
            ),
            fill="white",
            radius=1,
        )

        return apply_outline(self.img)


@dataclasses.dataclass
class IconBarCap(Icon):
    side: Literal["left", "right"]

    def generate(self) -> Image.Image:
        if self.side == "left":
            coords = (
                (TILE_WIDTH - 1.5, TILE_HEIGHT * 0.25 - 1.5),
                (TILE_WIDTH - 1.5, TILE_HEIGHT * 0.75 + 1),
            )
        elif self.side == "right":
            coords = (
                (1.5, TILE_HEIGHT * 0.25 - 1.5),
                (1.5, TILE_HEIGHT * 0.75 + 1),
            )
        else:
            raise ValueError(f"Invalid side: {self.side}")

        self.draw.line(
            coords,
            fill="white",
            width=3,
        )

        return apply_outline(self.img)


@dataclasses.dataclass
class IconBar(Icon):
    section: Literal["full", "half_full", "empty", "end"]

    def generate(self) -> Image.Image:
        if self.section == "full":
            self.draw.rectangle(
                (
                    (-10, TILE_HEIGHT * 0.25),
                    (TILE_WIDTH + 10, TILE_HEIGHT * 0.75),
                ),
                fill="white",
            )
        elif self.section == "half_full":
            self.draw.rectangle(
                (
                    (-10, TILE_HEIGHT * 0.25),
                    (TILE_WIDTH / 2, TILE_HEIGHT * 0.75),
                ),
                fill="white",
            )
        elif self.section == "empty":
            pass
        elif self.section == "end":
            self.draw.rectangle(
                (
                    (-10, TILE_HEIGHT * 0.25),
                    (2, TILE_HEIGHT * 0.75),
                ),
                fill="white",
            )

        self.draw.line(
            (
                -10,
                TILE_HEIGHT * 0.25,
                TILE_WIDTH + 10,
                TILE_HEIGHT * 0.25,
            ),
            fill="white",
            width=3,
        )

        self.draw.line(
            (
                -10,
                TILE_HEIGHT * 0.75,
                TILE_WIDTH + 10,
                TILE_HEIGHT * 0.75,
            ),
            fill="white",
            width=3,
        )

        return apply_outline(self.img)


ICONS: Sequence[Icon] = [
    IconSvg(1, "signal"),  # RSSI
    IconSvg(2, "chevron-left", offset_x=TILE_WIDTH * 0.2),  # Horizon
    IconSvg(3, "chevron-right", offset_x=TILE_WIDTH * -0.2),  # Horizon
    IconSvg(4, "flash"),  # Throttle
    IconSvg(5, "home"),  # Home
    IconText(6, "v"),  # Voltage Unit
    IconText(7, "mah", scale=0.4),  # mAh
    IconText(12, "m"),  # Alt Unit (m)
    IconText(13, "°f"),  # Temp Unit (F)
    IconText(14, "°c"),  # Temp Unit (C)
    IconText(15, "ft"),  # Alt Unit (ft)
    IconSvg(16, "cube"),  # Blackbox
    IconSvg(17, "home-map-marker"),  # Home Marker
    IconEmpty(18),  # RPM? Unused.
    IconHeadingDecoration(19),  # Weird Heading Decoration Thing
    IconSvg(20, "axis-x-rotate-clockwise"),  # "Roll"
    IconSvg(21, "horizontal-rotate-clockwise"),  # "Pitch"
    # Headings (NSEW)
    IconText(24, "N", center=True, scale=0.8),
    IconText(25, "S", center=True, scale=0.8),
    IconText(26, "E", center=True, scale=0.8),
    IconText(27, "W", center=True, scale=0.8),
    IconHeading(28, True),
    IconHeading(29, False),
    # Satellite (2x1)
    IconEmpty(30),
    IconSvg(31, "satellite-variant", scale=0.9),
    IconSvg(112, "speedometer"),  # Speedometer
    IconSvg(113, "rotate-left"),  # Anti-clockwise ????
    # Crosshair (3x1)
    IconEmpty(114),
    IconSvg(115, "crosshairs", scale=0.9, with_background=True),
    IconEmpty(116),
    IconSvg(117, "chevron-double-up", offset_y=TILE_HEIGHT * -0.25),  # Up Chevron
    IconSvg(118, "chevron-double-down", offset_y=TILE_HEIGHT * 0.25),  # Down Chevron
    IconEmpty(119),  # Unused
    IconEmpty(120),  # Unused
    IconSvg(122, "thermometer"),  # Thermometer
    IconSvg(123, "signal"),  # RSSI (LQ)
    IconEmpty(124),  # Unused
    IconText(125, "km"),  # Dist Unit (km)
    IconText(126, "mi"),  # Dist Unit (mi)
    IconSvg(127, "altimeter"),  # "Alt" ???
    IconSvg(137, "latitude"),  # Longitude ("Lon")
    IconBarCap(138, "left"),  # Left Bar Cap
    IconBar(139, "full"),  # Full Bar
    IconBar(140, "half_full"),  # Half Full Bar
    IconBar(141, "empty"),  # Empty Bar
    IconBar(142, "end"),  # End Bar
    IconBarCap(143, "right"),  # Right Bar Cap
    # Battery
    IconSvg(144, "battery"),
    IconSvg(145, "battery-90"),
    IconSvg(146, "battery-80"),
    IconSvg(147, "battery-60"),
    IconSvg(148, "battery-40"),
    IconSvg(149, "battery-30"),
    IconSvg(150, "battery-20"),
    IconSvg(151, "battery-alert"),
    IconSvg(152, "longitude"),  # Longitude ("Lon")
    IconText(153, "ft/s", scale=0.4),  # Speed Unit (ft/s)
    IconText(154, "a"),  # Amps Unit
    IconSvg(155, "airplane-clock", scale=0.8),  # Timer (On) TODO: Clock graphic?
    IconSvg(156, "battery-clock", scale=0.8),  # Timer (On) TODO: Drone clock graphic?
    IconText(157, "mph", scale=0.4),  # Speed Unit (mph)
    IconText(158, "kph", scale=0.4),  # Speed Unit (kph)
    IconText(159, "m/s", scale=0.4),  # Speed Unit (m/s)
    # Stick Overlay
    IconStickOverlay(8, "high"),  # Stick High
    IconStickOverlay(9, "middle"),  # Stick Medium
    IconStickOverlay(10, "low"),  # Stick Low
    IconStickCenterLine(11),  # Stick Center
    IconStickVerticalLine(22),  # Stick Vertical
    IconStickHorizontalLine(23),  # Stick Vertical
    # Char Overrides
    IconText(36, "MAX", center=True, scale=0.4),  # Max
]


def get_icon_image(
    icon: Union[
        IconEmpty,
        IconSvg,
        IconText,
    ]
) -> Image.Image:
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

    return apply_outline(img)


def get_logo_image() -> Image.Image:
    logo_tile_width = 24
    logo_tile_height = 4
    logo_tile_count = logo_tile_width * logo_tile_height
    logo_tile_rows = logo_tile_count // TILES_PER_ROW

    logo_img_small = load_svg(
        "./icons/fpvwtf.svg",
        width=int(logo_tile_width * TILE_WIDTH * 0.8),
        height=int(logo_tile_height * TILE_HEIGHT * 0.8),
    )

    logo_img = Image.new(
        "RGBA",
        (logo_tile_width * TILE_WIDTH, logo_tile_height * TILE_HEIGHT),
        (0, 0, 0, 0),
    )

    logo_img.paste(
        logo_img_small,
        (
            (logo_img.width - logo_img_small.width) // 2,
            (logo_img.height - logo_img_small.height) // 2,
        ),
    )

    logo_img = apply_outline(logo_img)

    logo_tiled_img = Image.new(
        "RGBA",
        (TILE_WIDTH * TILES_PER_ROW, TILE_HEIGHT * logo_tile_rows),
        (0, 0, 0, 0),
    )

    for y in range(logo_tile_height):
        for x in range(logo_tile_width):
            logo_this_tile = logo_img.crop(
                (
                    x * TILE_WIDTH,
                    y * TILE_HEIGHT,
                    (x + 1) * TILE_WIDTH,
                    (y + 1) * TILE_HEIGHT,
                )
            )

            tile_index = y * logo_tile_width + x
            tile_x = tile_index % TILES_PER_ROW * TILE_WIDTH
            tile_y = tile_index // TILES_PER_ROW * TILE_HEIGHT

            logo_tiled_img.paste(logo_this_tile, (tile_x, tile_y))

    return logo_tiled_img


def get_horizon_image() -> Image.Image:
    horizon_width = 9
    line_width = 8

    img = Image.new(
        "RGBA",
        (TILE_WIDTH * horizon_width, TILE_HEIGHT),
        (0, 0, 0, 0),
    )

    for i in range(0, horizon_width):
        tile_img = Image.new(
            "RGBA",
            (TILE_WIDTH, TILE_HEIGHT),
            (0, 0, 0, 0),
        )

        tile_draw = ImageDraw.Draw(tile_img)
        line_y = (line_width / 2) + (TILE_HEIGHT - line_width / 2) * (i / horizon_width)
        tile_draw.line(
            (
                (0, line_y),
                (TILE_WIDTH, line_y),
            ),
            fill="white",
            width=line_width,
        )

        tile_img = apply_outline(tile_img)

        img.paste(tile_img, (i * TILE_WIDTH, 0))

    return img


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

    arrows_img = get_arrows_image()
    out.paste(arrows_img, (0, TILE_HEIGHT * 6))

    horizon_img = get_horizon_image()
    out.paste(horizon_img, (0, TILE_HEIGHT * 8))

    logo_img = get_logo_image()
    out.paste(logo_img, (0, TILE_HEIGHT * 10))

    for icon in ICONS:
        icon_img = icon.generate()
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
