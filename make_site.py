#!/usr/bin/env python3
"""Gradi statičnu stranicu s rasporedom: naslovnica + pločice + svi rasporedi.
   Duboki linkovi: #razred/IVb, #nastavnik/Ana%20Colak, #ucionica/13a"""
import sys, os, html, glob, collections, datetime
import xml.etree.ElementTree as ET

SCHOOL = 'Srednja strukovna škola Široki Brijeg'
YEAR   = '2026 / 2027'
e = lambda s: html.escape(str(s))

def collect(fet_path, outdir):
    src = ET.parse(fet_path).getroot()
    days  = [d.findtext('Name') for d in src.findall('./Days_List/Day')]
    hours = [h.findtext('Name') for h in src.findall('./Hours_List/Hour')]
    acts  = {int(a.findtext('Id')): dict(t=a.findtext('Teacher'), s=a.findtext('Subject'),
                                         g=a.findtext('Students'))
             for a in src.findall('./Activities_List/Activity')}
    years = {y.findtext('Name'): (y.findtext('Comments') or '') for y in src.findall('./Students_List/Year')}
    yof = lambda g: g if g in years else g.rsplit('-', 1)[0]
    tt = glob.glob(os.path.join(outdir, 'timetables/*/*_activities.xml'))[0]
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    load  = collections.Counter()
    for a in ET.parse(tt).getroot().findall('Activity'):
        i = int(a.findtext('Id')); d, h = a.findtext('Day'), a.findtext('Hour')
        if not (d and h): continue
        r = (a.findtext('Room') or '').strip(); x = acts[i]
        grp = '' if x['g'] in years else x['g'].rsplit('-', 1)[1]
        cells[('razred', yof(x['g']))][(d, h)].append((x['s'], x['t'], r, f'gr.{grp}' if grp else ''))
        cells[('nastavnik', x['t'])][(d, h)].append(
            (x['s'], yof(x['g']) + (f' gr.{grp}' if grp else ''), r, ''))
        if r: cells[('ucionica', r)][(d, h)].append((x['s'], x['t'], yof(x['g']), ''))
        load[('razred', yof(x['g']))] += 1; load[('nastavnik', x['t'])] += 1
        if r: load[('ucionica', r)] += 1
    order = lambda s: (len(s), s)
    kinds = [('razred', 'Razredi', sorted(years, key=order), years),
             ('nastavnik', 'Nastavnici', sorted({a['t'] for a in acts.values()}), {}),
             ('ucionica', 'Učionice', sorted({k[1] for k in cells if k[0] == 'ucionica'}, key=order), {})]
    return days, hours, cells, load, kinds, len(acts), len({a['s'] for a in acts.values()})

def grid(days, hours, cell):
    o = ['<div class="wrap"><table><thead><tr><th class="corner"></th>' +
         ''.join(f'<th>{e(h)}</th>' for h in hours) + '</tr></thead><tbody>']
    for d in days:
        o.append(f'<tr><th class="dy">{e(d)}</th>')
        for h in hours:
            c = cell.get((d, h), [])
            if not c: o.append('<td class="free"></td>'); continue
            o.append('<td>' + ''.join(
                f'<div class="ev"><b>{e(a)}</b><span>{e(b)}'
                f'{" · " + e(r) if r else ""}{" · " + e(g) if g else ""}</span></div>'
                for a, b, r, g in c) + '</td>')
        o.append('</tr>')
    return '\n'.join(o + ['</tbody></table></div>'])

def build(fet, outdir, dest):
    days, hours, cells, load, kinds, nact, nsub = collect(fet, outdir)
    tiles, sheets = [], []
    for kind, label, names, meta in kinds:
        t = [f'<div class="tiles" data-kind="{kind}" hidden>']
        for n in names:
            sub = meta.get(n, '') or f'{load[(kind, n)]} sati tjedno'
            t.append(f'<a class="tile" href="#{kind}/{e(n)}"><b>{e(n)}</b>'
                     f'<span>{e(sub[:44])}</span></a>')
        tiles.append('\n'.join(t + ['</div>']))
        for n in names:
            sheets.append(
                f'<section class="sheet" data-key="{kind}/{e(n)}" hidden>'
                f'<div class="shead"><a class="back" href="#{kind}">← {e(label)}</a>'
                f'<h2>{e(n)}</h2><p>{e(meta.get(n,"") or "")}</p></div>'
                f'{grid(days, hours, cells[(kind, n)])}</section>')
    # naslovne brojke broje samo ono što se stvarno predaje: bez 'O' oznaka za
    # obilazak prakse i bez PRAK.NAST.VAN.SK nositelja koji nisu osobe
    n_cls = sum(1 for n in kinds[0][2] if not n.endswith('O'))
    n_tch = sum(1 for n in kinds[1][2] if 'PRAK' not in n)
    n_sub = len({a['s'] for a in acts.values()}) if False else nsub
    stats = [(n_cls, 'razreda'), (n_tch, 'nastavnika'), (n_sub, 'predmeta'),
             (len(kinds[2][2]), 'učionica'), (nact, 'sati tjedno')]
    doc = (TPL.replace('%%SCHOOL%%', e(SCHOOL)).replace('%%YEAR%%', e(YEAR))
              .replace('%%STATS%%', ''.join(f'<div><b>{a}</b><span>{e(b)}</span></div>' for a, b in stats))
              .replace('%%TABS%%', ''.join(
                  f'<a class="tab" data-kind="{k}" href="#{k}">{e(l)}</a>' for k, l, _, _ in kinds))
              .replace('%%TILES%%', '\n'.join(tiles)).replace('%%SHEETS%%', '\n'.join(sheets))
              .replace('%%DATE%%', datetime.date.today().strftime('%d.%m.%Y.')))
    open(dest, 'w', encoding='utf-8').write(doc)
    return {l: len(n) for _, l, n, _ in kinds}

TPL = r"""<!doctype html><html lang="hr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Raspored %%YEAR%% — %%SCHOOL%%</title>
<meta name="robots" content="noindex,nofollow">
<style>
:root{
 --bg:#faf8f5; --panel:#fff; --fg:#1c1a17; --mut:#6f6a62; --line:#e6e1d9;
 --acc:#9a5b2d; --acc-soft:#f2e7dc; --shadow:0 1px 2px rgba(0,0,0,.04),0 6px 20px rgba(0,0,0,.05);
}
@media (prefers-color-scheme:dark){:root{
 --bg:#15140f; --panel:#1d1b17; --fg:#ece7de; --mut:#9b948a; --line:#332f28;
 --acc:#d99a5e; --acc-soft:#2b2318; --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
 font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
 -webkit-text-size-adjust:100%}
a{color:inherit;text-decoration:none}
.hero{padding:52px 24px 30px;max-width:1180px;margin:0 auto}
.kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);font-weight:640}
h1{font-size:clamp(28px,5vw,44px);line-height:1.1;margin:10px 0 6px;font-weight:660;letter-spacing:-.02em}
.sub{color:var(--mut);font-size:16px;margin:0}
.lnk{color:var(--acc);font-weight:550}.lnk:hover{text-decoration:underline}
.stats{display:flex;gap:30px;flex-wrap:wrap;margin-top:26px;padding-top:22px;border-top:1px solid var(--line)}
.stats div{display:flex;flex-direction:column}
.stats b{font-size:24px;font-weight:660;font-variant-numeric:tabular-nums}
.stats span{font-size:12px;color:var(--mut);letter-spacing:.03em}
.bar{position:sticky;top:0;z-index:9;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar .in{max-width:1180px;margin:0 auto;padding:0 24px;display:flex;gap:4px;align-items:center;flex-wrap:wrap}
.tab{padding:13px 14px;font-size:14px;color:var(--mut);border-bottom:2px solid transparent;font-weight:550}
.tab[aria-current=true]{color:var(--fg);border-bottom-color:var(--acc)}
.tab:hover{color:var(--fg)}
#find{margin-left:auto;font:inherit;font-size:13px;padding:7px 11px;border:1px solid var(--line);
 border-radius:8px;background:var(--panel);color:var(--fg);width:190px}
main{max-width:1180px;margin:0 auto;padding:26px 24px 70px}
.tiles{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(168px,1fr))}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 14px;
 box-shadow:var(--shadow);transition:transform .12s ease,border-color .12s ease}
.tile:hover{transform:translateY(-2px);border-color:var(--acc)}
.tile b{display:block;font-size:15px;font-weight:640;margin-bottom:3px}
.tile span{display:block;font-size:11.5px;color:var(--mut);line-height:1.35}
.shead{margin-bottom:18px}
.back{font-size:13px;color:var(--mut)}.back:hover{color:var(--acc)}
.shead h2{font-size:26px;margin:8px 0 2px;font-weight:660;letter-spacing:-.01em}
.shead p{margin:0;color:var(--mut);font-size:14px}
.wrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line);
 border-radius:12px;box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;min-width:780px}
th,td{border-right:1px solid var(--line);border-bottom:1px solid var(--line);
 padding:7px 9px;text-align:left;vertical-align:top}
tr:last-child th,tr:last-child td{border-bottom:0}
th:last-child,td:last-child{border-right:0}
thead th{font-size:11px;font-weight:600;color:var(--mut);letter-spacing:.03em;white-space:nowrap;
 background:var(--acc-soft)}
.corner{width:56px}
th.dy{width:56px;font-size:12.5px;font-weight:600;color:var(--mut);background:var(--acc-soft)}
td{width:13.4%}
td.free{background:repeating-linear-gradient(45deg,transparent,transparent 6px,
 color-mix(in srgb,var(--line) 45%,transparent) 6px,color-mix(in srgb,var(--line) 45%,transparent) 7px)}
.ev+.ev{margin-top:5px;padding-top:5px;border-top:1px dashed var(--line)}
.ev b{display:block;font-size:12.5px;font-weight:620;line-height:1.25}
.ev span{display:block;font-size:11px;color:var(--mut);margin-top:1px;line-height:1.3}
footer{max-width:1180px;margin:0 auto;padding:0 24px 50px;color:var(--mut);font-size:12px;line-height:1.6}
footer b{color:var(--fg);font-weight:600}
@media print{
 .bar,.hero .stats,#find,.back,footer{display:none}
 .sheet{page-break-after:always}body{background:#fff}
 .wrap{box-shadow:none;border-color:#999}
}
</style></head><body>
<div class="hero">
  <div class="kicker">Raspored sati · %%YEAR%%</div>
  <h1>%%SCHOOL%%</h1>
  <p class="sub">Odaberi razred, nastavnika ili učionicu. &nbsp;·&nbsp; <a href="analiza.html" class="lnk">Kako je nastao →</a></p>
  <div class="stats">%%STATS%%</div>
</div>
<div class="bar"><div class="in">%%TABS%%<input id="find" type="search" placeholder="Traži…" autocomplete="off"></div></div>
<main>%%TILES%%%%SHEETS%%</main>
<footer>
  Generirano %%DATE%% iz podataka škole.
  <b>Napomena:</b> dostupnost nastavnika nije uključena u izradu, a učionice su dodijeljene
  automatski bez posebnih zahtjeva pojedinih predmeta — prije objave provjeriti.
  Detalji na <a href="analiza.html">stranici s analizom</a>.
</footer>
<script>
var tiles=[].slice.call(document.querySelectorAll('.tiles')),
    sheets=[].slice.call(document.querySelectorAll('.sheet')),
    tabs=[].slice.call(document.querySelectorAll('.tab')),
    find=document.getElementById('find');
function route(){
  var h=decodeURIComponent(location.hash.replace(/^#/,'')) || 'razred';
  var kind=h.split('/')[0], isSheet=h.indexOf('/')>0;
  if(!tiles.some(function(t){return t.dataset.kind===kind})) {kind='razred';h='razred';isSheet=false;}
  tiles.forEach(function(t){t.hidden=isSheet||t.dataset.kind!==kind});
  sheets.forEach(function(s){s.hidden=!(isSheet&&s.dataset.key===h)});
  if(isSheet&&!sheets.some(function(s){return !s.hidden})){location.hash=kind;return}
  tabs.forEach(function(t){t.setAttribute('aria-current',String(t.dataset.kind===kind))});
  find.style.visibility=isSheet?'hidden':'visible';
  if(!isSheet){find.value='';filter()}
  window.scrollTo(0,0);
}
function filter(){
  var q=find.value.trim().toLowerCase();
  tiles.forEach(function(t){
    if(t.hidden)return;
    [].slice.call(t.children).forEach(function(a){
      a.style.display=!q||a.textContent.toLowerCase().indexOf(q)>-1?'':'none';
    });
  });
}
find.addEventListener('input',filter);
window.addEventListener('hashchange',route);
route();
</script></body></html>"""

if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2], sys.argv[3]))
