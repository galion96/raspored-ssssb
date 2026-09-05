#!/usr/bin/env python3
"""Provjera SAMOG PRIKAZA: raspored koji je ispravan mora i izgledati ispravno.
Blok koji se crta samo u prvoj celiji ostavlja lazne rupe - ovaj test to hvata."""
import sys, re, collections

FAIL = []
def check(name, cond, detail=''):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{'' if cond else '  -> '+str(detail)}")
    if not cond: FAIL.append(name)

def sheets(h):
    for m in re.finditer(r'data-key="([^"]+)"', h):
        i = m.start(); yield m.group(1), h[i:h.index('</section>', i)]

def main(path):
    h = open(path, encoding='utf-8').read()
    nh = len(re.findall(r'<th>[^<]*</th>', h[:h.index('</thead>')]))
    holes, wide, bad_span = [], [], []
    n = 0
    for key, seg in sheets(h):
        kind = key.split('/')[0]
        kind = key.split('/')[0]
        for d, body in re.findall(r'<tr><th class="dy">([^<]+)</th>(.*?)</tr>', seg, re.S):
            n += 1
            cells = re.findall(r'<td([^>]*)>(.*?)</td>', body, re.S)
            cols = 0; occ = []
            for attr, c in cells:
                sp = re.search(r'colspan="(\d+)"', attr)
                w = int(sp.group(1)) if sp else 1
                cols += w
                occ += [bool(c.strip())] * w
                if w > 1 and not c.strip(): bad_span.append((key, d))
            if cols != nh: wide.append((key, d, cols))
            if kind == 'razred' and any(occ):
                a, b = occ.index(True), len(occ) - 1 - occ[::-1].index(True)
                if not all(occ[a:b + 1]): holes.append((key, d))
    print(f"== prikaz ({n} redaka, {nh} sati po danu) ==")
    check("svaki redak ima točno onoliko stupaca koliko ima sati", not wide, wide[:4])
    check("nijedan razred nema praznu ćeliju usred dana", not holes, holes[:6])
    check("nijedna spojena ćelija nije prazna", not bad_span, bad_span[:4])
    blocks = len(re.findall(r'colspan="[2-9]"', h))
    print(f"  INFO  spojenih ćelija (blok-nastava): {blocks}")
    print()
    if FAIL: print(f"NEUSPJEŠNO: {FAIL}"); sys.exit(1)
    print("SVE PROŠLO")

if __name__ == '__main__':
    main(sys.argv[1])
