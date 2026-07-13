#!/usr/bin/env python3
"""Render V4 mascot previews from the anchor data in manifest.json."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
CANVAS = MANIFEST["canvas"]["width"]
PADDING = 256
LARGE = CANVAS + PADDING * 2
FONT = ImageFont.load_default()

LAYERS = {item["id"]: item for item in MANIFEST["layers"]}
IMAGES = {
    layer_id: Image.open(ROOT / layer["file"]).convert("RGBA")
    for layer_id, layer in LAYERS.items()
}

FIT = MANIFEST["viewportFit"]
HEAD = LAYERS["head"]
TORSO = LAYERS["torso"]
HEAD_OFFSET = (
    HEAD["restTransform"]["translateX"],
    HEAD["restTransform"]["translateY"],
)
HEAD_PIVOT = (HEAD["pivot"]["x"], HEAD["pivot"]["y"])
WING_PIVOT = (
    LAYERS["left_wing"]["pivot"]["x"],
    LAYERS["left_wing"]["pivot"]["y"],
)


def composite_clipped(target: Image.Image, source: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    left = max(0, x)
    top = max(0, y)
    right = min(target.width, x + source.width)
    bottom = min(target.height, y + source.height)
    if left >= right or top >= bottom:
        return
    crop = source.crop((left - x, top - y, right - x, bottom - y))
    target.alpha_composite(crop, (left, top))


def positioned_layer(
    image: Image.Image,
    offset: tuple[int, int] = (0, 0),
    angle: float = 0,
    pivot: tuple[int, int] = (256, 256),
) -> Image.Image:
    layer = Image.new("RGBA", (LARGE, LARGE), (0, 0, 0, 0))
    x = PADDING + offset[0]
    y = PADDING + offset[1]
    layer.alpha_composite(image, (x, y))
    if angle:
        layer = layer.rotate(
            -angle,
            resample=Image.Resampling.BICUBIC,
            center=(x + pivot[0], y + pivot[1]),
        )
    return layer


def fit_to_canvas(scene: Image.Image) -> Image.Image:
    scale = FIT["scale"]
    size = round(LARGE * scale)
    fitted = scene.resize((size, size), Image.Resampling.LANCZOS)
    origin = FIT["transformOrigin"]
    x = round(origin["x"] + FIT["translateX"] - scale * (PADDING + origin["x"]))
    y = round(origin["y"] + FIT["translateY"] - scale * (PADDING + origin["y"]))
    output = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    composite_clipped(output, fitted, (x, y))
    return output


def render_scene(
    head_angle: float = 0,
    wing_angle: float = -8,
    include: tuple[str, ...] = ("left_wing", "torso", "head"),
) -> Image.Image:
    scene = Image.new("RGBA", (LARGE, LARGE), (0, 0, 0, 0))
    if "left_wing" in include:
        scene.alpha_composite(
            positioned_layer(IMAGES["left_wing"], angle=wing_angle, pivot=WING_PIVOT)
        )
    if "torso" in include:
        scene.alpha_composite(positioned_layer(IMAGES["torso"]))
    if "head" in include:
        scene.alpha_composite(
            positioned_layer(
                IMAGES["head"],
                offset=HEAD_OFFSET,
                angle=head_angle,
                pivot=HEAD_PIVOT,
            )
        )
    return fit_to_canvas(scene)


def map_point(point: tuple[int, int], offset: tuple[int, int] = (0, 0)) -> tuple[int, int]:
    origin = FIT["transformOrigin"]
    return (
        round(origin["x"] + FIT["translateX"] + FIT["scale"] * (point[0] + offset[0] - origin["x"])),
        round(origin["y"] + FIT["translateY"] + FIT["scale"] * (point[1] + offset[1] - origin["y"])),
    )


def draw_cross(draw: ImageDraw.ImageDraw, point: tuple[int, int], color: str, radius: int) -> None:
    x, y = point
    draw.line((x - radius, y, x + radius, y), fill=color, width=2)
    draw.line((x, y - radius, x, y + radius), fill=color, width=2)
    draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)


def save_gif(path: Path, frames: list[Image.Image], size: int, duration: int) -> None:
    rendered = [frame.resize((size, size), Image.Resampling.LANCZOS) for frame in frames]
    rendered[0].save(
        path,
        save_all=True,
        append_images=rendered[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=True,
    )


def render_angle_strip() -> None:
    angles = [-6, -3, 0, 3, 6]
    strip = Image.new("RGB", (256 * len(angles), 256), "white")
    for index, angle in enumerate(angles):
        frame = render_scene(head_angle=angle).resize((256, 256), Image.Resampling.LANCZOS)
        panel = Image.new("RGB", (256, 256), "white")
        panel.paste(frame, (0, 0), frame)
        ImageDraw.Draw(panel).text((10, 10), f"{angle:+d} deg", fill="#1d2c30", font=FONT)
        strip.paste(panel, (index * 256, 0))
    strip.save(ROOT / "head-angle-preview.png")


def render_anchor_calibration() -> None:
    torso_anchor = (
        TORSO["anchors"]["neckSeat"]["x"],
        TORSO["anchors"]["neckSeat"]["y"],
    )
    head_anchor = (
        HEAD["anchors"]["neckBase"]["x"],
        HEAD["anchors"]["neckBase"]["y"],
    )
    torso_point = map_point(torso_anchor)
    head_point = map_point(head_anchor, HEAD_OFFSET)

    panels = [
        ("1. Torso neckSeat (220, 270)", render_scene(include=("torso",))),
        ("2. Head neckBase + rest transform", render_scene(include=("head",))),
        ("3. Snapped anchors: delta (0, 0)", render_scene()),
    ]
    sheet = Image.new("RGB", (CANVAS * 3, CANVAS), "white")
    for index, (label, frame) in enumerate(panels):
        panel = Image.new("RGB", (CANVAS, CANVAS), "white")
        panel.paste(frame, (0, 0), frame)
        draw = ImageDraw.Draw(panel)
        draw.rectangle((0, 0, CANVAS - 1, CANVAS - 1), outline="#d9e1e2")
        draw.rectangle((0, 0, CANVAS, 34), fill="#ffffff")
        draw.text((14, 12), label, fill="#1d2c30", font=FONT)
        if index != 1:
            draw_cross(draw, torso_point, "#ff3b30", 12)
        if index != 0:
            draw_cross(draw, head_point, "#168d96", 7)
        if index == 2:
            draw.rectangle((105, 185, 350, 325), outline="#627176", width=1)
        sheet.paste(panel, (index * CANVAS, 0))
    sheet.save(ROOT / "anchor-calibration.png")


def main() -> None:
    render_scene().save(ROOT / "composite-preview.png")
    render_angle_strip()
    render_anchor_calibration()

    frame_count = 32
    turn_frames = []
    combined_frames = []
    for index in range(frame_count):
        phase = index / (frame_count - 1)
        head_angle = 6 * math.sin(phase * math.tau)
        turn_frames.append(render_scene(head_angle=head_angle))
        wing_angle = -8 + 18 * math.sin(phase * math.tau * 2)
        combined_frames.append(render_scene(head_angle=head_angle, wing_angle=wing_angle))

    save_gif(ROOT / "head-turn-preview.gif", turn_frames, 512, 55)
    save_gif(ROOT / "combined-preview.gif", combined_frames, 384, 55)


if __name__ == "__main__":
    main()
