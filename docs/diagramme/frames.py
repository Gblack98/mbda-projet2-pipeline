import os
import subprocess

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "frames")
os.makedirs(SORTIE, exist_ok=True)

import base64
import re

BASE = open(os.path.join(ICI, "architecture.html"), encoding="utf-8").read()


def inline(page):
    def rempl(m):
        chemin = os.path.join(ICI, m.group(1))
        data = base64.b64encode(open(chemin, "rb").read()).decode()
        return f'src="data:image/svg+xml;base64,{data}"'
    return re.sub(r'src="(ico/[^"]+)"', rempl, page)


BASE = inline(BASE)

# ce qui est allume a chaque etape
ETAPES = [
    ["e-src"],
    ["e-src", "e-air", "f1", "l1"],
    ["e-air", "e-raw", "f2", "l2"],
    ["e-raw", "e-dbt", "f3", "l3"],
    ["e-dbt", "e-marts", "f4", "l4"],
    ["e-marts", "e-bi", "f5", "l5"],
    ["e-src", "e-air", "e-raw", "e-dbt", "e-marts", "e-bi",
     "f1", "f2", "f3", "f4", "f5", "l1", "l2", "l3", "l4", "l5"],
]

TOUS = ["e-src", "e-air", "e-raw", "e-dbt", "e-marts", "e-bi",
        "f1", "f2", "f3", "f4", "f5", "l1", "l2", "l3", "l4", "l5"]


def css(actifs):
    regles = []
    for cle in TOUS:
        if cle in actifs:
            if cle.startswith("f"):
                regles.append(f"#{cle} {{ background:#3B82F6 }} #{cle}::after {{ border-left-color:#3B82F6 }}")
            elif cle.startswith("l"):
                regles.append(f"#{cle} {{ color:#2563EB; font-weight:700 }}")
            else:
                regles.append(f"#{cle} .carte, #{cle}.bloc {{ border-color:#93C5FD;"
                              f" box-shadow:0 8px 22px rgba(59,130,246,.16) }}")
        else:
            if cle.startswith(("f", "l")):
                regles.append(f"#{cle} {{ opacity:.25 }}")
            else:
                regles.append(f"#{cle} {{ opacity:.18; filter:grayscale(1) }}")
    return "<style>" + "\n".join(regles) + "</style>"


for i, actifs in enumerate(ETAPES):
    page = BASE.replace("</style>", "</style>" + css(actifs), 1)
    chemin = os.path.join(SORTIE, f"e{i}.html")
    open(chemin, "w", encoding="utf-8").write(page)
    subprocess.run([
        "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--window-size=1960,700",
        f"--screenshot={SORTIE}/e{i}.png", f"file://{chemin}",
    ], check=True, capture_output=True)
    subprocess.run(["convert", f"{SORTIE}/e{i}.png", "-crop", "1960x478+0+0",
                    "+repage", f"{SORTIE}/e{i}.png"], check=True)
    print(f"  etape {i}")

from PIL import Image

images = [Image.open(os.path.join(SORTIE, f"e{i}.png")).convert("RGB")
          for i in range(len(ETAPES))]
LARGE = 1470
images = [im.resize((LARGE, round(im.height * LARGE / im.width)), Image.LANCZOS)
          for im in images]
palette = images[-1].quantize(colors=128)
cadres = [im.quantize(palette=palette) for im in images]

cadres[0].save(os.path.join(ICI, "..", "img", "pipeline.gif"), save_all=True,
               append_images=cadres[1:],
               duration=[1000, 1000, 1000, 1000, 1000, 1000, 2800],
               loop=0, optimize=True)
images[-1].save(os.path.join(ICI, "..", "img", "architecture.png"))
print("gif + png")
