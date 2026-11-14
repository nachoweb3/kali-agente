"""Reproducible README illustrations. No inference, screenshots or network access."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "story"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
CYAN, PURPLE, WHITE, MUTED = "#83edff", "#c0a2ff", "#eef4ff", "#a5b6d0"


def text(draw, xy, value, size=24, color=WHITE, font=FONT):
    draw.text(xy, value, font=ImageFont.truetype(font, size), fill=color)


def canvas(kicker, title, subtitle, height=760):
    image = Image.new("RGB", (1440, height), "#070b16")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / height
        draw.line((0, y, 1440, y), fill=(int(8 + 5 * t), int(14 + 4 * t), int(27 + 13 * t)))
    for x in range(0, 1440, 48):
        draw.line((x, 0, x, height), fill="#121e32")
    draw.rounded_rectangle((30, 28, 1410, height - 28), radius=28, outline="#2b405d", width=2)
    text(draw, (68, 56), kicker, 19, CYAN, MONO)
    text(draw, (68, 103), title, 48, WHITE, BOLD)
    text(draw, (70, 174), subtitle, 24, MUTED)
    text(draw, (70, height - 66), "NACHO_WEB3   /   KALI AGENTE", 18, CYAN, MONO)
    text(draw, (900, height - 66), "ILUSTRACIÓN · NO ES UNA SESIÓN REAL", 15, MUTED, MONO)
    return image, draw


def panel(draw, box, accent=CYAN):
    draw.rounded_rectangle(box, radius=20, fill="#111d31", outline="#30435e", width=2)
    x, y, _, _ = box
    draw.rounded_rectangle((x + 18, y + 21, x + 23, y + 58), radius=2, fill=accent)


def conversation():
    frames = []
    for stage in range(4):
        image, draw = canvas(
            "01 / UNA CONVERSACIÓN. MUCHAS CAPACIDADES.",
            "Tú explicas el objetivo.",
            "El agente decide qué recursos necesita en cada turno.",
            840,
        )
        panel(draw, (68, 245, 1372, 345))
        text(draw, (105, 263), "TÚ", 17, CYAN, BOLD)
        text(
            draw,
            (105, 295),
            "«Ayúdame a entender este error y crea una utilidad para procesar el registro».",
            25,
        )
        choices = [
            ("01", "ENTENDER", "Leer la salida compartida", "y situar el problema."),
            ("02", "ELEGIR", "Consultar la ayuda real", "y cargar skills pertinentes."),
            ("03", "ACTUAR", "Escribir código y ejecutar", "comprobaciones útiles."),
        ]
        for index, (number, label, first, second) in enumerate(choices):
            x = 68 + index * 443
            active = stage > index
            panel(draw, (x, 382, x + 418, 580), CYAN if active else PURPLE)
            text(draw, (x + 42, 405), number, 27, CYAN if active else MUTED, MONO)
            text(draw, (x + 99, 411), label, 22, WHITE if active else MUTED, BOLD)
            text(draw, (x + 34, 471), first, 22)
            text(draw, (x + 34, 508), second, 22, MUTED)
            if active:
                draw.ellipse((x + 365, 415, x + 379, 429), fill=CYAN)
        panel(draw, (68, 618, 1372, 727), PURPLE)
        text(draw, (104, 638), "SIGUIENTE TURNO", 17, PURPLE, BOLD)
        text(
            draw,
            (104, 675),
            "«Ahora comprueba el resultado y prepara un informe».  El contexto continúa.",
            25,
        )
        frames.append(image)
    frames[-1].save(DEST / "conversation.png", optimize=True)
    frames[0].save(
        DEST / "conversation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[1100, 950, 950, 2600],
        loop=0,
        optimize=True,
    )


def capabilities():
    image, draw = canvas(
        "02 / LAS SKILLS TRABAJAN POR DENTRO",
        "Un asistente, seis recursos especializados.",
        "No tienes que elegir un modo ni memorizar nombres.",
        930,
    )
    cards = [
        ("01", "HERRAMIENTAS", "Elegir utilidades instaladas.", "Consultar opciones y requisitos."),
        ("02", "INTERPRETACIÓN", "Entender errores y registros.", "Proponer el siguiente paso."),
        ("03", "DESARROLLO", "Crear y modificar archivos.", "Probar y compilar el código."),
        ("04", "VALIDACIÓN", "Contrastar posibles hallazgos.", "Separar indicios de pruebas."),
        ("05", "EVIDENCIAS", "Organizar lo observado.", "Preparar informes reproducibles."),
        ("06", "WEB / API", "Razonar sobre HTTP y accesos.", "Analizar y corregir aplicaciones."),
    ]
    for index, (number, title, first, second) in enumerate(cards):
        x, y = 68 + index % 3 * 443, 249 + index // 3 * 265
        panel(draw, (x, y, x + 418, y + 237), CYAN if index % 2 == 0 else PURPLE)
        text(draw, (x + 42, y + 24), number, 24, CYAN, MONO)
        text(draw, (x + 36, y + 81), title, 25, WHITE, BOLD)
        text(draw, (x + 36, y + 138), first, 21, MUTED)
        text(draw, (x + 36, y + 173), second, 21, MUTED)
    text(
        draw,
        (73, 806),
        "Carga selectiva · contexto de conversación · selección a cargo del modelo",
        23,
        PURPLE,
    )
    image.save(DEST / "capabilities.png", optimize=True)


def workflow():
    image, draw = canvas(
        "03 / DEL OBJETIVO A UN RESULTADO REVISABLE",
        "Conversar, construir, comprobar.",
        "Dos flujos complementarios sobre OpenCode + Ollama.",
        850,
    )
    rows = [
        (
            "CONVERSACIÓN",
            CYAN,
            ["Tu petición", "Contexto + skills", "Archivos / shell", "Respuesta + límites"],
        ),
        (
            "TAREA CON WORKTREE",
            PURPLE,
            ["Objetivo", "Worktree de Git", "Checks + parche", "Revisar y aplicar"],
        ),
    ]
    for row, (label, accent, cells) in enumerate(rows):
        y = 253 + row * 226
        text(draw, (72, y), label, 20, accent, BOLD)
        for index, label in enumerate(cells):
            x = 68 + index * 333
            panel(draw, (x, y + 48, x + 306, y + 162), accent)
            text(draw, (x + 36, y + 90), label, 21, WHITE, BOLD)
            if index < 3:
                text(draw, (x + 310, y + 90), "›", 26, accent, BOLD)
    text(
        draw,
        (73, 716),
        "Worktrees: separan cambios de Git. Docker opcional: aísla el comando indicado.",
        23,
        MUTED,
    )
    image.save(DEST / "workflow.png", optimize=True)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    conversation()
    capabilities()
    workflow()
    print(DEST)


if __name__ == "__main__":
    main()
