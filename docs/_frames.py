import subprocess

ON  = 'fillcolor="#333333", fontcolor="white", color="#333333"'
OFF = 'fillcolor="#F5F5F5", fontcolor="#AAAAAA", color="#DDDDDD"'


def graphe(etats):
    def s(k):
        return ON if etats.get(k) else OFF

    def fleche(k):
        return 'color="#333333", penwidth=2' if etats.get(k) else 'color="#DDDDDD"'

    return f'''digraph archi {{
  rankdir=LR; bgcolor="white"; dpi=110;
  node [fontname="DejaVu Sans", fontsize=11, shape=box, style=filled, margin="0.18,0.12"];
  edge [color="#DDDDDD"];

  yahoo [label="Yahoo Finance", {s('src')}];
  frank [label="Frankfurter (BCE)", {s('src')}];
  wb    [label="Banque Mondiale", {s('src')}];
  airflow [label="Airflow", {s('air')}];
  raw   [label="BigQuery\\nraw", {s('raw')}];
  dbt   [label="dbt", {s('dbt')}];
  marts [label="BigQuery\\nmarts", {s('marts')}];
  bi    [label="Looker Studio\\nPower BI", {s('bi')}];

  yahoo -> airflow [{fleche('f1')}];
  frank -> airflow [{fleche('f1')}];
  wb -> airflow [{fleche('f1')}];
  airflow -> raw [{fleche('f2')}];
  raw -> dbt [{fleche('f3')}];
  dbt -> marts [{fleche('f3')}];
  marts -> bi [{fleche('f4')}];
}}'''


frames = [
    {},
    {'src': 1},
    {'src': 1, 'air': 1, 'f1': 1},
    {'air': 1, 'raw': 1, 'f2': 1},
    {'raw': 1, 'dbt': 1, 'marts': 1, 'f3': 1},
    {'marts': 1, 'bi': 1, 'f4': 1},
    {'src': 1, 'air': 1, 'raw': 1, 'dbt': 1, 'marts': 1, 'bi': 1,
     'f1': 1, 'f2': 1, 'f3': 1, 'f4': 1},
]

for i, e in enumerate(frames):
    open(f"frame{i}.dot", "w").write(graphe(e))
    subprocess.run(["dot", "-Tpng", f"frame{i}.dot", "-o", f"frame{i}.png"], check=True)
