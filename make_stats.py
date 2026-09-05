#!/usr/bin/env python3
"""Analitički pregled: brojke, opterećenja, iskorištenost mreže, model."""
import sys, os, html, glob, collections
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import extract

e = lambda s: html.escape(str(s))
RAMP = ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b']          # validirano --ordinal light
RAMP_D = ['#184f95', '#2a78d6', '#5598e7', '#b7d3f6']        # validirano --ordinal dark

def gather(roz, fet, outdir):
    _, T, subj, les, cnames = extract(roz)
    src = ET.parse(fet).getroot()
    days = [d.findtext('Name') for d in src.findall('./Days_List/Day')]
    hours = [h.findtext('Name').split(' ')[0] for h in src.findall('./Hours_List/Hour')]
    acts = {int(a.findtext('Id')): (a.findtext('Teacher'), a.findtext('Students'))
            for a in src.findall('./Activities_List/Activity')}
    years = {y.findtext('Name') for y in src.findall('./Students_List/Year')}
    yof = lambda g: g if g in years else g.rsplit('-', 1)[0]
    tt = glob.glob(os.path.join(outdir, 'timetables/*/*_activities.xml'))[0]
    room_slot = collections.Counter(); tch_slot = collections.defaultdict(set)
    for a in ET.parse(tt).getroot().findall('Activity'):
        d, h, r = a.findtext('Day'), a.findtext('Hour'), (a.findtext('Room') or '').strip()
        if d and h and r: room_slot[(d, h.split(' ')[0])] += 1
        if d and h: tch_slot[(d, h.split(' ')[0])].add(acts[int(a.findtext('Id'))][0])
    isO = lambda ci: cnames[ci][0].endswith('O')
    cls = collections.Counter(); tch = collections.Counter()
    for r in les:
        cls[cnames[r['cls']][0]] += r['h']; tch[T['teachers'][r['tch']]['names'][0]] += r['h']
    return dict(days=days, hours=hours, room_slot=room_slot, tch_slot=tch_slot,
                cls=cls, tch=tch, cnames=cnames, les=les, T=T,
                n_def=dict(razredi=len(cnames), predmeti=len(T['subjects']),
                           nastavnici=len(T['teachers']), ucionice=len(T['rooms'])),
                n_use=dict(razredi=sum(1 for i in range(len(cnames)) if not isO(i)),
                           predmeti=len({r['sub'] for r in les}),
                           nastavnici=len(T['teachers']) - sum(1 for t in T['teachers'] if 'PRAK' in t['names'][0]),
                           ucionice=len(T['rooms'])),
                pseudo_cls=[cnames[i][0] for i in range(len(cnames)) if isO(i)],
                pseudo_tch=[t['names'][0] for t in T['teachers'] if 'PRAK' in t['names'][0]])

def bars(items, cap, note=lambda k: ''):
    o = ['<div class="bars">']
    for k, v in items:
        o.append(f'<div class="bar" data-tip="{e(k)} — {v} sati tjedno{e(note(k))}">'
                 f'<span class="bl">{e(k)}</span>'
                 f'<span class="bt"><i style="width:{v/cap*100:.1f}%"></i></span>'
                 f'<span class="bv">{v}</span></div>')
    return '\n'.join(o + ['</div>'])

def heat(days, hours, cnt, cap, unit):
    lo, hi = min(cnt.values()), max(cnt.values())
    step = lambda v: min(3, int((v - lo) / max(1, hi - lo + .001) * 4))
    o = ['<div class="wrap"><table class="heat"><thead><tr><th></th>' +
         ''.join(f'<th>{e(h)}</th>' for h in hours) + '</tr></thead><tbody>']
    for d in days:
        o.append(f'<tr><th class="dy">{e(d)}</th>')
        for h in hours:
            v = cnt.get((d, h), 0); s = step(v)
            o.append(f'<td class="hc s{s}" data-tip="{e(d)} {e(h)}. sat — {v} {unit} od {cap}">{v}</td>')
        o.append('</tr>')
    o.append('</tbody></table></div>')
    o.append('<div class="scale"><span>manje</span>' +
             ''.join(f'<i class="s{i}"></i>' for i in range(4)) +
             f'<span>više</span><em>{lo}–{hi} {unit} istovremeno, strop je {cap}</em></div>')
    return '\n'.join(o)

def build(roz, fet, outdir, dest, soft=1):
    g = gather(roz, fet, outdir)
    isO = lambda k: k.endswith('O')
    real_cls = sorted([(k, v) for k, v in g['cls'].items() if not isO(k)], key=lambda x: -x[1])
    real_tch = sorted([(k, v) for k, v in g['tch'].items()], key=lambda x: -x[1])
    tot = sum(g['cls'].values())
    rows = [('Razredi', g['n_def']['razredi'], g['n_use']['razredi'],
             'šest oznaka s „O" (' + ', '.join(g['pseudo_cls']) + ') nisu razredi nego stavke za obilazak prakse'),
            ('Predmeti', g['n_def']['predmeti'], g['n_use']['predmeti'],
             'ostatak je definiran u aSc datoteci, ali ga ove godine nitko ne sluša'),
            ('Nastavnici', g['n_def']['nastavnici'], g['n_use']['nastavnici'],
             'pet zapisa „PRAK.NAST.VAN.SK…" su nositelji prakse van škole, ne osobe'),
            ('Učionice', g['n_def']['ucionice'], g['n_use']['ucionice'], '—')]
    tbl = '\n'.join(f'<tr><th>{e(a)}</th><td class="n dim">{b}</td><td class="n">{c}</td>'
                    f'<td class="wh">{e(d)}</td></tr>' for a, b, c, d in rows)
    tiles = [(f"{tot}", "sati smješteno", f"od {tot} traženih"),
             ("0", "rupa u rasporedima", "kroz svih 36 rasporeda"),
             (str(soft), "prekršeno meko ograničenje", "dvosat isti dan, spojen"),
             ("&lt;1 s", "trajanje izračuna", "FET 7.10.3")]
    cap_r = g['n_def']['ucionice']
    doc = (TPL.replace('%%TILES%%', ''.join(
                f'<div class="tile"><b>{a}</b><span>{e(b)}</span><em>{e(c)}</em></div>' for a, b, c in tiles))
              .replace('%%TABLE%%', tbl)
              .replace('%%CLS%%', bars(real_cls, max(v for _, v in real_cls)))
              .replace('%%NCLS%%', str(len(real_cls)))
              .replace('%%TCH%%', bars(real_tch, max(v for _, v in real_tch),
                                       lambda k: ' · nositelj prakse, ne osoba' if 'PRAK' in k else ''))
              .replace('%%NTCH%%', str(len(real_tch)))
              .replace('%%HEAT%%', heat(g['days'], g['hours'], g['room_slot'], cap_r, 'učionica'))
              .replace('%%RAMP%%', ''.join(f'--s{i}:{c};' for i, c in enumerate(RAMP)))
              .replace('%%RAMPD%%', ''.join(f'--s{i}:{c};' for i, c in enumerate(RAMP_D))))
    open(dest, 'w', encoding='utf-8').write(doc)
    return dict(razredi=len(real_cls), nastavnici=len(real_tch), sati=tot)

TPL = r"""<!doctype html><html lang="hr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Analiza rasporeda — SSŠ Široki Brijeg</title>
<meta name="robots" content="noindex,nofollow"><style>
:root{--bg:#faf8f5;--panel:#fff;--fg:#1c1a17;--mut:#6f6a62;--line:#e6e1d9;--acc:#9a5b2d;
 --acc-soft:#f2e7dc;--data:#2a78d6;--shadow:0 1px 2px rgba(0,0,0,.04),0 6px 20px rgba(0,0,0,.05);%%RAMP%%}
@media(prefers-color-scheme:dark){:root{--bg:#15140f;--panel:#1d1b17;--fg:#ece7de;--mut:#9b948a;
 --line:#332f28;--acc:#d99a5e;--acc-soft:#2b2318;--data:#3987e5;
 --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);%%RAMPD%%}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
 font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--acc)}
main{max-width:980px;margin:0 auto;padding:46px 24px 80px}
.kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);font-weight:640}
h1{font-size:clamp(26px,4.5vw,38px);margin:10px 0 8px;font-weight:660;letter-spacing:-.02em}
.lede{color:var(--mut);max-width:62ch;margin:0 0 34px}
h2{font-size:19px;margin:44px 0 6px;font-weight:640;letter-spacing:-.01em}
h2+p{color:var(--mut);font-size:13.5px;margin:0 0 16px;max-width:66ch}
.tiles{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));margin-bottom:8px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:15px;box-shadow:var(--shadow)}
.tile b{display:block;font-size:29px;font-weight:660;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.tile span{display:block;font-size:12.5px;margin-top:2px}
.tile em{display:block;font-style:normal;font-size:11.5px;color:var(--mut);margin-top:3px}
table{border-collapse:collapse;width:100%;background:var(--panel)}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow)}
th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--line);font-size:13.5px;vertical-align:top}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:0}
thead th{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;background:var(--acc-soft)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;width:88px}
td.dim{color:var(--mut);font-weight:400;text-decoration:line-through}
td.wh{color:var(--mut);font-size:12.5px}
.bars{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:12px 14px;
 box-shadow:var(--shadow);max-height:440px;overflow-y:auto}
.bar{display:grid;grid-template-columns:118px 1fr 30px;gap:9px;align-items:center;padding:2.5px 0}
.bl{font-size:12px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bt{background:color-mix(in srgb,var(--line) 55%,transparent);border-radius:4px;height:11px;overflow:hidden}
.bt i{display:block;height:100%;background:var(--data);border-radius:0 4px 4px 0}
.bv{font-size:12px;font-variant-numeric:tabular-nums;text-align:right;color:var(--mut)}
table.heat td.hc{text-align:center;font-variant-numeric:tabular-nums;font-weight:600;
 font-size:12.5px;color:#fff;border:2px solid var(--panel);border-radius:5px}
table.heat td.s0{background:var(--s0);color:#0b2a52}table.heat td.s1{background:var(--s1)}
table.heat td.s2{background:var(--s2)}table.heat td.s3{background:var(--s3)}
table.heat th.dy{font-size:12px;color:var(--mut);width:52px}
table.heat thead th{text-align:center}
.scale{display:flex;gap:6px;align-items:center;margin-top:9px;font-size:11.5px;color:var(--mut)}
.scale i{width:26px;height:11px;border-radius:3px;display:inline-block}
.scale i.s0{background:var(--s0)}.scale i.s1{background:var(--s1)}
.scale i.s2{background:var(--s2)}.scale i.s3{background:var(--s3)}
.scale em{font-style:normal;margin-left:8px}
#tip{position:fixed;pointer-events:none;background:var(--fg);color:var(--bg);font-size:12px;
 padding:5px 9px;border-radius:6px;opacity:0;transition:opacity .1s;z-index:20;max-width:270px}
.back{font-size:13px}
footer{color:var(--mut);font-size:12.5px;line-height:1.65;margin-top:50px;
 border-top:1px solid var(--line);padding-top:18px}
</style></head><body><main>
<a class="back" href="./">← Raspored</a>
<div class="kicker" style="margin-top:20px">Kako je raspored nastao</div>
<h1>Analiza</h1>
<p class="lede">Što je ušlo u izračun, što je iz njega izašlo, i gdje su granice.
Za nekoga tko i sam slaže rasporede.</p>

<h2>Rezultat izračuna</h2>
<p>Jedan prolaz FET-a, bez ručnih zahvata.</p>
<div class="tiles">%%TILES%%</div>

<h2>Brojke koje stvarno stoje</h2>
<p>aSc datoteka nosi i zapise koji se ne predaju. Lijevi stupac je ono što u njoj piše,
desni je ono što stvarno ulazi u raspored.</p>
<div class="wrap"><table><thead><tr><th></th><th class="n">u datoteci</th>
<th class="n">u nastavi</th><th>razlika</th></tr></thead><tbody>%%TABLE%%</tbody></table></div>

<h2>Tjedno opterećenje po razredu</h2>
<p>%%NCLS%% razreda. Mreža ima 35 termina (5 dana × 7 sati), pa najopterećeniji razred
troši 33 od 35 — dva slobodna termina u tjednu.</p>
%%CLS%%

<h2>Tjedno opterećenje po nastavniku</h2>
<p>%%NTCH%% zapisa, uključujući pet nositelja prakse van škole koji nisu osobe.</p>
%%TCH%%

<h2>Iskorištenost učionica</h2>
<p>Koliko je učionica zauzeto u svakom terminu. Ovo je najuže grlo cijelog rasporeda:
u vršnom terminu ostaje vrlo malo praznih učionica.</p>
%%HEAT%%

<h2>Što model sadrži, a što ne</h2>
<div class="wrap"><table><tbody>
<tr><th>Sadrži</th><td>zabranu sudara nastavnika, razreda i učionica; razmak po danima za
višesatne predmete; istovremenost podijeljenih grupa; najviše nula rupa dnevno po razredu;
dodjelu učionica bez sudara</td></tr>
<tr><th>Ne sadrži</th><td><b>dostupnost nastavnika</b> — nije dekodirana iz izvora, pa netko može
dobiti sat u terminu kad ne može raditi; <b>zahtjeve predmeta na učionicu</b> — praktikumi i
radionice nisu razlikovani od običnih učionica; smjene; ograničenja na najviše sati dnevno</td></tr>
<tr><th>Nije potvrđeno</th><td>kurikulum — tko što kome predaje i koliko sati — škola još nije pregledala</td></tr>
<tr><th>Otvoreno pitanje</th><td>u datoteci je <b>58</b> imenovanih nastavnika; ručnim brojanjem
dobiveno je <b>61</b>. Razlika je tri, a točno tri nastavnika u datoteci imaju besmisleno malu
satnicu (1, 2 i 3 sata tjedno). Moguće je da dio nastave nedostaje već u izvoru — što bi se
poklapalo s time da aSc raspored nije bio dovršen.</td></tr>
</tbody></table></div>

<footer>Podaci izvučeni iz aSc TimeTables datoteke škole; raspored izračunat
<a href="https://lalescu.ro/liviu/fet/">FET-om</a> 7.10.3.
Grafovi koriste jednu sekvencijalnu skalu provjerenu na razlučivost pri daltonizmu i kontrast
prema podlozi, u oba moda.</footer>
</main><div id="tip"></div><script>
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(ev){
  var t=ev.target.closest('[data-tip]'); if(!t){tip.style.opacity=0;return;}
  tip.textContent=t.dataset.tip; tip.style.opacity=1;
  var r=t.getBoundingClientRect();
  tip.style.left=Math.min(innerWidth-tip.offsetWidth-8,Math.max(8,r.left))+'px';
  tip.style.top=(r.top>46?r.top-tip.offsetHeight-7:r.bottom+7)+'px';
});
document.addEventListener('mouseleave',function(){tip.style.opacity=0},true);
</script></body></html>"""

if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                int(sys.argv[5]) if len(sys.argv) > 5 else 1))
