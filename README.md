# Raspored 2026/27 — Srednja strukovna škola Široki Brijeg

Statična stranica s rasporedom sati. Bez vanjskih ovisnosti — radi i offline.

**30 razreda · 58 nastavnika · 108 predmeta · 31 učionica · 890 sati tjedno**

- [Raspored](index.html) — razredi, nastavnici, učionice
- [Analiza](analiza.html) — kako je nastao, opterećenja, iskorištenost, granice modela
- Duboki linkovi: `#razred/IVb`, `#nastavnik/Ana%20Colak`, `#ucionica/13a`
- Prilagođeno mobitelu i ispisu

## Kako je nastalo

Podaci su izvučeni iz aSc TimeTables datoteke škole, raspored je izračunat
[FET-om](https://lalescu.ro/liviu/fet/) 7.10.3 (890 od 890 sati smješteno,
nula rupa, jedno prekršeno meko ograničenje), a stranice su generirane skriptama.

## Napomene prije ozbiljne upotrebe

- **Dostupnost nastavnika nije modelirana** — netko može imati sat u terminu kad ne može raditi.
- **Učionice su dodijeljene automatski**, bez obzira treba li predmet praktikum ili radionicu.
- Kurikulum (tko što kome predaje) škola još nije potvrdila — vidi `podaci/pregled.txt`.

## Podaci

`podaci/` sadrži izvučene tablice (CSV), pregled kurikuluma i FET model (`.fet`).

## Ponovno generiranje

```sh
python3 make_site.py  <model.fet> <fet-izlazni-dir> index.html
python3 make_stats.py <izvor.roz> <model.fet> <fet-izlazni-dir> analiza.html
```
