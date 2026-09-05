#!/usr/bin/env python3
"""Vrti FET s razlicitim sjemenima i zadrzi raspored s najmanje kratkih dana.
Ogranicenja su iscrpljena (minimum 6 je neizvediv iznad praga 33 sata),
pa se ostatak dobiva izborom medju ishodima."""
import subprocess, sys, os, glob, shutil, collections, random
import xml.etree.ElementTree as ET

BASE = os.path.expanduser('~/roz')
FET  = os.path.expanduser('~/.local/bin/fet-cl')

def score(fet, outdir):
    src = ET.parse(fet).getroot()
    hours = [h.findtext('Name') for h in src.findall('./Hours_List/Hour')]
    hi = {h: i for i, h in enumerate(hours)}
    acts = {int(a.findtext('Id')): a.findtext('Students')
            for a in src.findall('./Activities_List/Activity')}
    years = {y.findtext('Name') for y in src.findall('./Students_List/Year')}
    yof = lambda g: g if g in years else g.rsplit('-', 1)[0]
    tt = glob.glob(os.path.join(outdir, 'timetables/*/*_activities.xml'))
    if not tt: return None
    day = collections.defaultdict(set)
    for a in ET.parse(tt[0]).getroot().findall('Activity'):
        d, h = a.findtext('Day'), a.findtext('Hour')
        if d and h: day[(yof(acts[int(a.findtext('Id'))]), d)].add(hi[h])
    real = {k: v for k, v in day.items() if not k[0].endswith('O')}
    dist = collections.Counter(len(v) for v in real.values())
    sc = glob.glob(os.path.join(outdir, 'timetables/*/*_soft_conflicts.txt'))
    soft = 0
    if sc:
        for line in open(sc[0], encoding='utf-8-sig'):
            if line.startswith('Number of broken'): soft = int(line.split(':')[1])
    return dict(kratki=sum(n for h, n in dist.items() if h <= 5), dist=dict(sorted(dist.items())),
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
        print(f"  {i:2}  kratkih dana (<=5h): {r['kratki']:3}   {r['dist']}   mekih: {r['soft']}", flush=True)
        if best is None or (r['kratki'], r['soft']) < (best['kratki'], best['soft']):
            if best: shutil.rmtree(best['out'], ignore_errors=True)
            best = r
        else:
            shutil.rmtree(out, ignore_errors=True)
    if best:
        shutil.rmtree(f'{BASE}/fet-out', ignore_errors=True)
        shutil.move(best['out'], f'{BASE}/fet-out')
        print(f"\nNAJBOLJI: {best['kratki']} kratkih dana, {best['dist']}, "
              f"{best['soft']} mekih, {best['slobodni']} slobodnih dana")
        print("sjeme:", best['seed'])
    sys.exit(0 if best else 1)
