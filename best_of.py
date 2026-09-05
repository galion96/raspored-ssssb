#!/usr/bin/env python3
"""Vrti FET s razlicitim sjemenima i zadrzi raspored s najmanje kratkih dana.
Ogranicenja su iscrpljena (minimum 6 je neizvediv iznad praga 33 sata),
pa se ostatak dobiva izborom medju ishodima."""
import subprocess, sys, os, glob, shutil, collections, random
import xml.etree.ElementTree as ET

BASE = os.path.expanduser('~/roz')
FET  = os.path.expanduser('~/.local/bin/fet-cl')

def score(fet, outdir):
    """blok traje vise sati -> aktivnost zauzima sve sate svog raspona"""
    src = ET.parse(fet).getroot()
    hours = [h.findtext('Name') for h in src.findall('./Hours_List/Hour')]
    hi = {h: i for i, h in enumerate(hours)}
    acts = {int(a.findtext('Id')): (a.findtext('Students'), a.findtext('Teacher'),
                                    int(a.findtext('Duration')))
            for a in src.findall('./Activities_List/Activity')}
    years = {y.findtext('Name') for y in src.findall('./Students_List/Year')}
    yof = lambda g: g if g in years else g.rsplit('-', 1)[0]
    tt = glob.glob(os.path.join(outdir, 'timetables/*/*_activities.xml'))
    if not tt: return None
    day = collections.defaultdict(set); tday = collections.defaultdict(set)
    for a in ET.parse(tt[0]).getroot().findall('Activity'):
        d, h = a.findtext('Day'), a.findtext('Hour')
        if not (d and h): continue
        s, t, du = acts[int(a.findtext('Id'))]
        for k in range(du):
            if hi[h] + k < len(hours):
                day[(yof(s), d)].add(hi[h] + k); tday[(t, d)].add(hi[h] + k)
    real = {k: v for k, v in day.items() if not k[0].endswith('O')}
    dist = collections.Counter(len(v) for v in real.values())
    gap = lambda v: (max(v) - min(v) + 1) - len(v)
    tgaps = sum(gap(v) for v in tday.values())
    sc = glob.glob(os.path.join(outdir, 'timetables/*/*_soft_conflicts.txt'))
    soft = 0
    if sc:
        for line in open(sc[0], encoding='utf-8-sig'):
            if line.startswith('Number of broken'): soft = int(line.split(':')[1])
    return dict(ispod5=sum(n for h, n in dist.items() if h < 5),
                kratki=sum(n for h, n in dist.items() if h <= 5),
                tgaps=tgaps, dist=dict(sorted(dist.items())),
                soft=soft, slobodni=len({k[0] for k in real}) * 5 - len(real))

if __name__ == '__main__':
    fet, n, tl = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    rnd = random.Random(20262027)
    best = None
    for i in range(n):
        s = [rnd.randrange(1, 4294944442) for _ in range(6)]
        out = f'{BASE}/bo-{i}'
        shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
        g = subprocess.run([FET, f'--inputfile={fet}', f'--outputdir={out}',
                            f'--timelimitseconds={tl}', '--writetimetablesxml=true',
                            '--embedcssinhtmlhead=true',
                            f'--randomseeds10={s[0]}', f'--randomseeds11={s[1]}',
                            f'--randomseeds12={s[2]}', f'--randomseeds20={s[3]}',
                            f'--randomseeds21={s[4]}', f'--randomseeds22={s[5]}'],
                           capture_output=True, text=True)
        if 'Generation successful' not in (g.stdout + g.stderr):
            print(f"  {i:2}  pao", flush=True); shutil.rmtree(out, ignore_errors=True); continue
        r = score(fet, out); r['seed'] = s; r['out'] = out
        print(f"  {i:2}  dana <5h: {r['ispod5']:2}  <=5h: {r['kratki']:3}  "
              f"pauze nastavnika: {r['tgaps']:4}  {r['dist']}  mekih: {r['soft']}", flush=True)
        # prioritet: nikad ispod 5h, pa sto manje petica, pa sto manje pauza
        key = lambda x: (x['ispod5'], x['kratki'], x['tgaps'], x['soft'])
        if best is None or key(r) < key(best):
            if best: shutil.rmtree(best['out'], ignore_errors=True)
            best = r
        else:
            shutil.rmtree(out, ignore_errors=True)
    if best:
        shutil.rmtree(f'{BASE}/fet-out', ignore_errors=True)
        shutil.move(best['out'], f'{BASE}/fet-out')
        print(f"\nNAJBOLJI: {best['ispod5']} dana ispod 5h, {best['kratki']} do 5h, "
              f"{best['tgaps']} pauza nastavnika, {best['dist']}, {best['soft']} mekih")
        print("sjeme:", best['seed'])
    sys.exit(0 if best else 1)
