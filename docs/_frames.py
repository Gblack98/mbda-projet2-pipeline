import subprocess

ON_TEAL  = ('fillcolor="#0F766E", fontcolor="white", color="#0F766E"')
ON_AMBER = ('fillcolor="#B45309", fontcolor="white", color="#B45309"')
OFF      = ('fillcolor="white", fontcolor="#9AAAA3", color="#DDE5E1"')
DIM      = ('fillcolor="#F7FAF8", fontcolor="#B7C4BE", color="#E3EAE6"')

def graphe(etats):
    def s(k, on=ON_TEAL):
        return on if etats.get(k) else (DIM if etats.get(k) is None else OFF)
    return f'''digraph archi {{
  rankdir=LR; bgcolor="#F1F4F2"; fontname="DejaVu Sans"; dpi=110;
  node [fontname="DejaVu Sans", fontsize=11, shape=box, style="rounded,filled",
        penwidth=1.3, margin="0.18,0.12"];
  edge [color="#B7C4BE", penwidth=1.2];

  yahoo [label="Yahoo Finance\\n41 instruments", {s('src')}];
  frank [label="Frankfurter (BCE)\\n14 devises", {s('src')}];
  wb    [label="Banque Mondiale\\n8 pays", {s('src')}];
  airflow [label="AIRFLOW\\ningest_market_data\\nlun-ven 18h00", {s('air')}];
  raw   [label="BigQuery raw\\n5 tables\\ncopie fidele", {s('raw', ON_AMBER)}];
  dbt   [label="dbt\\nstaging - marts\\ntests qualite", {s('dbt')}];
  marts [label="BigQuery marts\\nschema en etoile", {s('marts', ON_AMBER)}];
  looker [label="Looker Studio", {s('bi')}];
  pbi    [label="Power BI\\n(export CSV)", {s('bi')}];

  yahoo -> airflow [{ 'color="#0F766E", penwidth=2' if etats.get('f1') else ''}];
  frank -> airflow [{ 'color="#0F766E", penwidth=2' if etats.get('f1') else ''}];
  wb -> airflow    [{ 'color="#0F766E", penwidth=2' if etats.get('f1') else ''}];
  airflow -> raw   [{ 'color="#B45309", penwidth=2' if etats.get('f2') else ''}];
  raw -> dbt       [{ 'color="#0F766E", penwidth=2' if etats.get('f3') else ''}];
  dbt -> marts     [{ 'color="#B45309", penwidth=2' if etats.get('f3') else ''}];
  marts -> looker  [{ 'color="#0F766E", penwidth=2' if etats.get('f4') else ''}];
  marts -> pbi     [{ 'color="#0F766E", penwidth=2' if etats.get('f4') else ''}];
}}'''

frames = [
  {},                                                        # tout eteint
  {'src':1},                                                 # les sources
  {'src':1,'air':1,'f1':1},                                  # airflow collecte
  {'air':1,'raw':1,'f2':1},                                  # chargement raw
  {'raw':1,'dbt':1,'marts':1,'f3':1},                        # dbt transforme
  {'marts':1,'bi':1,'f4':1},                                 # les dashboards
  {'src':1,'air':1,'raw':1,'dbt':1,'marts':1,'bi':1,
   'f1':1,'f2':1,'f3':1,'f4':1},                             # tout allume
]
for i, e in enumerate(frames):
    open(f"frame{i}.dot","w").write(graphe(e))
    subprocess.run(["dot","-Tpng",f"frame{i}.dot","-o",f"frame{i}.png"], check=True)
print("frames :", len(frames))
