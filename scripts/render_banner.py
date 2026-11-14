"""Render the same ASCII frames as the terminal banner. Requires Pillow."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from kali_agente.cabecera_kali import scene, title


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    opts = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "assets"
    destination.mkdir(exist_ok=True)
    font = ImageFont.truetype(opts.font, 16)
    small = ImageFont.truetype(opts.font, 13)
    width, height = 960, 626
    stops = [(135, 255, 255), (35, 195, 255), (115, 110, 255), (220, 155, 255)]
    frames = []
    for step in range(28):
        base = Image.new("RGB", (width, height), "#050912")
        draw = ImageDraw.Draw(base)
        draw.rounded_rectangle(
            (12, 12, width - 12, height - 12), radius=18, fill="#0a1220", outline="#25364e", width=2
        )
        for x, color in [(36, "#48dbef"), (58, "#668eff"), (80, "#b397ff")]:
            draw.ellipse((x, 33, x + 10, 43), fill=color)
        draw.text((112, 31), "kali-agente  /  LOCAL CODING AGENT", font=small, fill="#adbed4")
        draw.line((28, 64, width - 28, 64), fill="#25364e", width=1)
        lines = [
            "KALI IA  /  NACHO_WEB3".center(76),
            "",
            *title("bloque", 76),
            "",
            "CULTIVANDO IDEAS. COSECHANDO CODIGO.".center(76),
            "",
            *scene(step, 76),
            "",
            "[ CODE ]    [ SHELL ]    [ BUILD ]    [ VERIFY ]".center(76),
        ]
        ink = Image.new("RGBA", base.size)
        writer = ImageDraw.Draw(ink)
        cell = font.getlength("M")
        left = (width - cell * 76) / 2
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == " ":
                    continue
                amount = min(2.999, x / 75 * 3)
                k = int(amount)
                rgb = tuple(
                    round(stops[k][j] * (1 - amount + k) + stops[k + 1][j] * (amount - k))
                    for j in range(3)
                )
                writer.text((left + x * cell, 81 + y * 19), char, font=font, fill=(*rgb, 255))
        glow = ink.filter(ImageFilter.GaussianBlur(2.2))
        composed = Image.alpha_composite(
            Image.alpha_composite(base.convert("RGBA"), glow), ink
        ).convert("RGB")
        frames.append(composed)
    frames[0].save(
        destination / "banner.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[110] * 27 + [1000],
        loop=0,
        optimize=False,
    )
    frames[14].save(destination / "banner.png")
    print(destination / "banner.gif")


if __name__ == "__main__":
    main()
