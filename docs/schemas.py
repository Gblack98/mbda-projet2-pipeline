# python docs/schemas.py -- requiert graphviz et Pillow

import glob
import os
import subprocess
import sys

from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ICI, "img")
os.makedirs(IMG, exist_ok=True)

subprocess.run(["dot", "-Tpng", "-Gdpi=150", os.path.join(ICI, "etoile.dot"),
                "-o", os.path.join(IMG, "schema_etoile.png")], check=True)
print("schema_etoile.png")

sys.path.insert(0, ICI)
os.chdir(ICI)
import _frames  # noqa: E402  genere frame*.png

fichiers = sorted(glob.glob(os.path.join(ICI, "frame*.png")),
                  key=lambda p: int(os.path.basename(p)[5:-4]))
images = [Image.open(f).convert("RGBA") for f in fichiers]
largeur = max(i.width for i in images)
hauteur = max(i.height for i in images)

fonds = []
for im in images:
    fond = Image.new("RGB", (largeur, hauteur), (255, 255, 255))
    fond.paste(im, ((largeur - im.width) // 2, (hauteur - im.height) // 2), im)
    fonds.append(fond)

# une palette commune a tous les cadres, sinon les couleurs sautent
palette = fonds[-1].quantize(colors=64)
cadres = [f.quantize(palette=palette) for f in fonds]

# le dernier cadre sert aussi de version statique
fonds[-1].save(os.path.join(IMG, "architecture.png"))
print("architecture.png")

cadres[0].save(os.path.join(IMG, "pipeline.gif"), save_all=True,
               append_images=cadres[1:],
               duration=[900, 1100, 1100, 1100, 1100, 1100, 2600],
               loop=0, optimize=True)
print("pipeline.gif")

for f in glob.glob(os.path.join(ICI, "frame*.png")) + glob.glob(os.path.join(ICI, "frame*.dot")):
    os.remove(f)
