import base64
import os
from xml.sax.saxutils import escape

ICI = os.path.dirname(os.path.abspath(__file__))


def icone(nom):
    donnees = base64.b64encode(open(os.path.join(ICI, "ico", nom), "rb").read()).decode()
    return f"data:image/svg+xml,{donnees}"


BLEU, VIOLET, GRIS = "#1D4ED8", "#6D28D9", "#475569"

cellules = []
n = [10]


def ident():
    n[0] += 1
    return f"c{n[0]}"


def carte(libelle, x, y, ico=None, w=190, h=54, sous=""):
    i = ident()
    brut = f"<b>{libelle}</b>" + (f"<br><font color='#64748B' style='font-size:10px'>{sous}</font>" if sous else "")
    texte = escape(brut, {'"': "&quot;"})
    style = ("rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
             "strokeColor=#E2E8F0;fontSize=12;fontColor=#0F172A;align=left;"
             "spacingLeft=44;verticalAlign=middle;shadow=1;")
    cellules.append(f'<mxCell id="{i}" value="{texte}" style="{style}" vertex="1" parent="1">'
                    f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    if ico:
        j = ident()
        s = f"shape=image;html=1;imageAspect=0;aspect=fixed;image={icone(ico)};"
        cellules.append(f'<mxCell id="{j}" style="{s}" vertex="1" parent="1">'
                        f'<mxGeometry x="{x+12}" y="{y+(h-22)//2}" width="22" height="22" as="geometry"/></mxCell>')
    return i


def bloc(titre, lignes, x, y, ico, couleur, w=210):
    """Conteneur empile facon table."""
    i = ident()
    h = 34 + len(lignes) * 24
    style = (f"swimlane;whiteSpace=wrap;html=1;startSize=34;rounded=1;arcSize=8;"
             f"fillColor=#FFFFFF;strokeColor=#E2E8F0;fontSize=12;fontStyle=1;"
             f"fontColor={couleur};align=left;spacingLeft=34;shadow=1;"
             f"childLayout=stackLayout;horizontalStack=0;resizeParent=0;"
             f"collapsible=0;marginBottom=0;")
    cellules.append(f'<mxCell id="{i}" value="{escape(titre)}" style="{style}" vertex="1" parent="1">'
                    f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    j = ident()
    s = f"shape=image;html=1;imageAspect=0;aspect=fixed;image={icone(ico)};"
    cellules.append(f'<mxCell id="{j}" style="{s}" vertex="1" parent="1">'
                    f'<mxGeometry x="{x+9}" y="{y+8}" width="18" height="18" as="geometry"/></mxCell>')
    for k, (nom, val) in enumerate(lignes):
        c = ident()
        st = ("text;html=1;strokeColor=none;fillColor=#F8FAFC;align=left;"
              "verticalAlign=middle;spacingLeft=10;fontSize=10;fontFamily=Courier New;"
              "fontColor=#334155;")
        v = escape(f"{nom}" + (f"<font color='#94A3B8'>  {val}</font>" if val else ""), {'"': "&quot;"})
        cellules.append(f'<mxCell id="{c}" value="{v}" style="{st}" vertex="1" parent="{i}">'
                        f'<mxGeometry y="{34+k*24}" width="{w}" height="24" as="geometry"/></mxCell>')
    return i


def fleche(source, cible, libelle=""):
    i = ident()
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;flowAnimation=1;"
             "strokeColor=#3B82F6;strokeWidth=2;fontSize=10;fontColor=#64748B;"
             "endArrow=blockThin;endFill=1;")
    cellules.append(f'<mxCell id="{i}" value="{escape(libelle)}" style="{style}" '
                    f'edge="1" parent="1" source="{source}" target="{cible}">'
                    f'<mxGeometry relative="1" as="geometry"/></mxCell>')


# --- sources
y0 = 60
s1 = carte("Yahoo Finance", 40, y0, "yahoo.svg", sous="41 instruments · OHLCV")
s2 = carte("Frankfurter · BCE", 40, y0 + 80, "bce.svg", sous="15 devises")
s3 = carte("Banque Mondiale", 40, y0 + 160, "worldbank.svg", sous="exportations, 8 pays")

# --- orchestration
a1 = carte("Airflow", 300, y0 + 40, "airflow.svg", sous="DAG quotidien · 18h")
a2 = carte("scripts/ingest.py", 300, y0 + 120, "python.svg", sous="sans ordonnanceur")

# --- entrepot
raw = bloc("raw", [("cotations", "103 071"), ("taux_change", "47 042"),
                   ("instruments", "41"), ("devises", "16"),
                   ("exportations", "300"), ("secteurs", "11")],
           560, y0 + 20, "bigquery.svg", BLEU)

# --- transformation
d = bloc("dbt", [("staging", "6 vues"), ("normalisation", "USX GBp ZAc"),
                 ("conversion", "→ EUR"), ("tests", "16")],
         830, y0 + 55, "dbt.svg", "#C2410C")

# --- marts
marts = bloc("marts", [("fct_cotation_journaliere", ""), ("dim_temps", ""),
                       ("dim_instrument", ""), ("dim_devise", ""),
                       ("dim_pays_exposition", "")],
             1100, y0 + 40, "bigquery.svg", VIOLET, w=230)

# --- restitution
b1 = carte("Looker Studio", 1390, y0 + 55, "looker.svg", sous="connexion native")
b2 = carte("Power BI", 1390, y0 + 135, "powerbi.svg", sous="export CSV")

for s in (s1, s2, s3):
    fleche(s, a1 if s is s1 else a2)
fleche(a1, raw, "chargement")
fleche(a2, raw)
fleche(raw, d, "transformation")
fleche(d, marts, "modèle")
fleche(marts, b1, "restitution")
fleche(marts, b2)

titre = ident()
cellules.insert(0, f'<mxCell id="{titre}" value="&lt;b&gt;Pipeline analytics&lt;/b&gt; — matières premières et devises ouest-africaines" '
                   f'style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=17;fontColor=#0F172A;" '
                   f'vertex="1" parent="1"><mxGeometry x="40" y="16" width="700" height="26" as="geometry"/></mxCell>')

xml = ('<mxfile host="app.diagrams.net">\n'
       '  <diagram name="Architecture" id="archi">\n'
       '    <mxGraphModel dx="1600" dy="900" grid="0" gridSize="10" guides="1" '
       'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
       'pageWidth="1700" pageHeight="420" math="0" shadow="0">\n'
       '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n        '
       + "\n        ".join(cellules) +
       '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')

sortie = os.path.join(ICI, "architecture.drawio")
open(sortie, "w", encoding="utf-8").write(xml)
print(f"{sortie} — {len(cellules)} cellules, {len(xml)//1024} Ko")
