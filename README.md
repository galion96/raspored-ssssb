# Raspored 2026/27 — Srednja strukovna škola Široki Brijeg

Statična stranica s rasporedom sati. Jedan `index.html`, bez vanjskih ovisnosti — radi i offline.

- **Razredi** (36), **Nastavnici** (63), **Učionice** (31) — 890 sati tjedno
- Duboki linkovi: `#razred/IVb`, `#nastavnik/Ana%20Colak`, `#ucionica/13a`
- Prilagođeno mobitelu i ispisu (Cmd/Ctrl+P ispisuje odabrani raspored)

## Kako je nastalo

Podaci su izvučeni iz aSc TimeTables datoteke škole, raspored je izračunat
[FET-om](https://lalescu.ro/liviu/fet/) 7.10.3, a stranica je generirana skriptom.

## Napomene prije ozbiljne upotrebe

- **Dostupnost nastavnika nije modelirana** — netko može imati sat u terminu kad ne može raditi.
- **Učionice su dodijeljene automatski**, bez obzira treba li predmet praktikum ili radionicu.
- Kurikulum (tko što kome predaje) škola još nije potvrdila.

## Ponovno generiranje

```sh
python3 make_site.py <raspored.fet> <fet-izlazni-dir> index.html
```
