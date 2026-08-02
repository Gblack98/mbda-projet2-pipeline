"""Regenere les schemas de docs/img/. Requiert graphviz et Pillow.

    python docs/schemas.py
"""

import glob
import os
import subprocess
import sys

from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ICI, "img")
os.makedirs(IMG, exist_ok=True)

for nom, sortie in (("archi", "architecture.png"), ("etoile", "schema_etoile.png")):
    subprocess.run(["dot", "-Tpng", "-Gdpi=150",
                    os.path.join(ICI, f"{nom}.dot"),
                    "-o", os.path.join(IMG, sortie)], check=True)
    print(sortie)

sys.path.insert(0, ICI)
os.chdir(ICI)
import _frames  # noqa: E402  genere frame*.png

fichiers = sorted(glob.glob(os.path.join(ICI, "frame*.png")),
                  key=lambda p: int(os.path.basename(p)[5:-4]))
images = [Image.open(f).convert("RGBA") for f in fichiers]
largeur = max(i.width for i in images)
hauteur = max(i.height for i in images)

cadres = []
for im in images:
    fond = Image.new("RGBA", (largeur, hauteur), (241, 244, 242, 255))
    fond.paste(im, ((largeur - im.width) // 2, (hauteur - im.height) // 2), im)
    cadres.append(fond.convert("P", palette=Image.ADAPTIVE, colors=128))

cadres[0].save(os.path.join(IMG, "pipeline.gif"), save_all=True,
               append_images=cadres[1:],
               duration=[900, 1100, 1100, 1100, 1100, 1100, 2600],
               loop=0, optimize=True)
print("pipeline.gif")

for f in glob.glob(os.path.join(ICI, "frame*.png")) + glob.glob(os.path.join(ICI, "frame*.dot")):
    os.remove(f)
