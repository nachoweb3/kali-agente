"""Identidad ASCII animada: robot cosechador y degradado electrico."""

import os
import shutil
import sys
import time

FONT = {
    "N": ["#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"],
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "C": [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "_": ["     ", "     ", "     ", "     ", "     ", "     ", "#####"],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "3": ["#### ", "    #", "    #", " ### ", "    #", "    #", "#### "],
}
MINI = {
    "N": ["#  #", "## #", "# ##", "#  #", "#  #"],
    "A": [" ## ", "#  #", "####", "#  #", "#  #"],
    "C": [" ###", "#   ", "#   ", "#   ", " ###"],
    "H": ["#  #", "#  #", "####", "#  #", "#  #"],
    "O": [" ## ", "#  #", "#  #", "#  #", " ## "],
    "_": ["    ", "    ", "    ", "    ", "####"],
    "W": ["#  #", "#  #", "#  #", "####", "#  #"],
    "E": ["####", "#   ", "### ", "#   ", "####"],
    "B": ["### ", "#  #", "### ", "#  #", "### "],
    "3": ["### ", "   #", " ## ", "   #", "### "],
}


def title(font="bloque", width=76):
    glyphs = MINI if font == "compacta" else FONT
    chars = "NACHO_WEB3"
    groups = (
        [chars] if width >= (len(chars) * (len(glyphs["N"][0]) + 1) - 1) else ["NACHO", "_WEB3"]
    )
    result = []
    for group in groups:
        for row in range(len(glyphs["N"])):
            result.append(" ".join(glyphs[c][row] for c in group).center(width).rstrip())
    return result


def scene(frame, width=76):
    width = max(40, width)
    canvas = [[" "] * width for _ in range(12)]

    def put(x, y, text, opaque=False):
        for j, char in enumerate(text):
            if 0 <= x + j < width and 0 <= y < 12 and (char != " " or opaque):
                canvas[y][x + j] = char

    t = min(frame, 27)
    x = 2 + int(t * (width - 35) / 27)
    put(width - 14, 0, r"\  |  /")
    put(width - 14, 1, " -- * --")
    put(width - 14, 2, "/  |  \\")
    for crop in range(width // 2, width - 14, 5):
        cut = t > 9 and crop < x + 17
        if not cut:
            put(crop, 5, r"\|/")
            put(crop, 6, "-|-")
            put(crop, 7, " | ")
            put(crop, 8, " | ")
        put(crop, 9, "_|_")
    robot = [
        "    .----.",
        "  __|____|__",
        "    [o_o]",
        "   /|[_]|\\___" if t % 4 < 2 else "   /|[_]|\\",
        "  /_|___|    \\" if t % 4 < 2 else "  /_|___| \\____",
        "    /   \\",
        "   _|   |_" if t % 4 < 2 else "  _/     \\_",
    ]
    for y, row in enumerate(robot, 3):
        put(x, y, row.ljust(14), opaque=True)
    if t % 4 < 2:
        put(x + 14, 6, "---)")
        put(x + 17, 7, "/")
    else:
        put(x + 14, 7, "---)")
        put(x + 17, 8, "/")
    if t > 9:
        put(min(x + 18, width - 8), 4 + (t % 3), "+")
        put(width - 7, 7, r"\|/")
    put(width - 8, 8, r"\====/")
    put(width - 8, 9, r" \__/")
    put(0, 10, "_" * width)
    for p in range(1, width - 2, 5):
        put(p, 11, " .")
    return ["".join(row).rstrip() for row in canvas]


def gradient(text, width, row=0):
    # Solo dos familias de color: hielo/cian -> azul electrico -> violeta.
    stops = [(135, 255, 255), (35, 195, 255), (115, 110, 255), (220, 155, 255)]
    out = []
    for i, char in enumerate(text):
        q = min(2.999, max(0, (i / max(1, width - 1)) * 3))
        k = int(q)
        rgb = tuple(
            round(stops[k][j] * (1 - (q - k)) + stops[k + 1][j] * (q - k)) for j in range(3)
        )
        out.append("\033[1;38;2;%d;%d;%dm%s" % (*rgb, char) if char != " " else " ")
    return "".join(out) + "\033[0m"


def show(color_mode="auto", font="bloque", animate=True):
    color = color_mode == "always" or (
        color_mode == "auto" and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    )
    if color and os.name == "nt":
        try:
            import ctypes

            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 4)
        except (OSError, AttributeError):
            pass
    width = min(76, max(40, shutil.get_terminal_size((80, 30)).columns - 2))

    def paint(text, row=0):
        return gradient(text, width, row) if color else text

    print()
    print(paint("  / KALI IA /                    ROBOT HARVESTER v1".center(width)))
    print()
    for i, line in enumerate(title(font, width)):
        print(paint(line, i))
    print(paint(("  " + "-" * (width - 4)).center(width)))
    print(paint("CULTIVANDO IDEAS. COSECHANDO CODIGO.".center(width)))
    frames = range(28) if animate and color else [27]
    if animate and color:
        print("\033[?25l", end="", flush=True)
    try:
        first = True
        for frame in frames:
            if not first:
                print("\033[12A", end="")
            for y, line in enumerate(scene(frame, width)):
                print(("\033[2K" if color else "") + paint(line, y))
            sys.stdout.flush()
            first = False
            if animate and color:
                time.sleep(0.11)
    finally:
        if animate and color:
            print("\033[0m\033[?25h", end="", flush=True)
    print(paint("  [ CODIGO ]    [ SHELL ]    [ CREAR ]    [ APRENDER ]".center(width)))
    print(flush=True)
