import base64
import os
import re
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


if __name__ == "__main__":
    capture("modele.html", "schema_etoile.png", 1200, 700)
    subprocess.run(["convert", os.path.join(IMG, "schema_etoile.png"),
                    "-crop", "1200x618+0+0", "+repage",
                    os.path.join(IMG, "schema_etoile.png")], check=True)
