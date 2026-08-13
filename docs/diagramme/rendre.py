import base64
import os
import re
import shutil
import subprocess

ICI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ICI, "..", "img")


def inline(page):
    def rempl(m):
        data = base64.b64encode(open(os.path.join(ICI, m.group(1)), "rb").read()).decode()
        return f'src="data:image/svg+xml;base64,{data}"'
    return re.sub(r'src="(ico/[^"]+)"', rempl, page)


def capture(source, sortie, largeur, hauteur):
    page = inline(open(os.path.join(ICI, source), encoding="utf-8").read())
    tmp = os.path.join(ICI, "_tmp.html")
    open(tmp, "w", encoding="utf-8").write(page)
    subprocess.run([
        "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", f"--window-size={largeur},{hauteur}",
        f"--screenshot={os.path.join(IMG, sortie)}", f"file://{tmp}",
    ], check=True, capture_output=True)
    os.remove(tmp)
    print(sortie)


def recadrer(image, geometrie):
    subprocess.run(["convert", os.path.join(IMG, image), "-crop", geometrie,
                    "+repage", os.path.join(IMG, image)], check=True)


CAPTURES = os.path.join(ICI, "..", "captures")

# Les captures du rapport reprennent les memes images, numerotees. On recopie
# a chaque rendu, sinon les deux dossiers divergent.
NUMEROTATION = {
    "architecture.png": "01-architecture.png",
    "datasets.png": "02-datasets.png",
    "schema_etoile.png": "04-schema-etoile.png",
}


def alimenter_captures():
    for source, cible in NUMEROTATION.items():
        chemin = os.path.join(IMG, source)
        if os.path.exists(chemin):
            shutil.copyfile(chemin, os.path.join(CAPTURES, cible))
            print(f"captures/{cible}")


if __name__ == "__main__":
    capture("modele.html", "schema_etoile.png", 1200, 700)
    recadrer("schema_etoile.png", "1200x640+0+0")

    capture("datasets.html", "datasets.png", 1440, 620)
    recadrer("datasets.png", "1440x497+0+0")

    alimenter_captures()
