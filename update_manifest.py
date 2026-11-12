#!/usr/bin/env python3
"""Sync Library/manifest.json with the game files in Library/.

Usage:  python3 update_manifest.py [--library DIR] [--dry-run] [--check]

Per-game metadata goes in a comment at the top of the game file:
    <!-- microfeed: {"title":"Beat Tap","icon":"🥁","description":"Tap the lanes in time.","tags":{"Rhythm":1,"Music":0.8}} -->
Tags are interest names (see DIMS) with weights in (0, 1]. icon (an emoji) and description
(one short line, under 140 characters) are shown on the game's card in the Feed page.
  - New .html files are added (id = file name without extension).
  - Existing entries keep their id and tags unless the file carries a microfeed comment.
  - Entries whose file no longer exists are removed.
  - Files missing a required function are skipped with an error.
  --dry-run  show changes without writing.   --check  exit 1 if the manifest is out of date.
"""
import argparse, json, re, sys
from pathlib import Path

DIMS = ['Asymmetric','Chance','Competitive','Cooperative','Endless','Endurance','Memory','Minimal','Physics','Precision',
        'Puzzle','Racing','Reflex','Rhythm','Sorting','Spatial','Sports','Strategy','Survival','Turn-Based']
REQUIRED = ['getResult', 'updateGame', 'handleInput', 'renderAll']

def has_fn(text, name):
    return re.search(r'function\s+%s\s*\(|\b%s\s*=\s*(?:function|\()|window\.%s\s*=' % ((name,) * 3), text)

def read_game(path):
    """Return (entry_fields, errors, warnings) for one game file."""
    text, errs, warns = path.read_text(encoding='utf-8'), [], []
    errs += ['missing %s()' % n for n in REQUIRED if not has_fn(text, n)]
    if 'GameMeta' not in text:
        warns.append('no window.GameMeta (host will use the default 15 s)')
    meta = {}
    m = re.search(r'<!--\s*microfeed:\s*(\{.*?\})\s*-->', text, re.S)
    if m:
        try: meta = json.loads(m.group(1))
        except ValueError as e: errs.append('bad microfeed comment: %s' % e)
    if 'title' not in meta:
        t = re.search(r"GameMeta\s*=\s*\{[^}]*?title\s*:\s*['\"]([^'\"]+)['\"]", text)
        if t: meta['title'] = t.group(1)
    tags = {}
    for k, w in (meta.get('tags') or {}).items():
        if k not in DIMS: warns.append('unknown interest "%s" ignored' % k)
        elif not isinstance(w, (int, float)) or not 0 < w <= 1: errs.append('tag "%s" must be a number in (0, 1]' % k)
        else: tags[k] = w
    if 'tags' in meta: meta['tags'] = tags
    for k in ('icon', 'description'):
        if k in meta and not isinstance(meta[k], str): errs.append('%s must be a string' % k); meta.pop(k)
    if len(meta.get('description', '')) > 140: warns.append('description is over 140 characters')
    return meta, errs, warns

def main():
    ap = argparse.ArgumentParser(description='Sync Library/manifest.json with game files.')
    ap.add_argument('--library', type=Path, default=Path(__file__).resolve().parent / 'Library')
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    mpath = a.library / 'manifest.json'
    old = json.loads(mpath.read_text(encoding='utf-8')) if mpath.exists() else {'games': []}
    by_file = {g['file']: g for g in old.get('games', [])}
    files = sorted(p for p in a.library.glob('*.html'))
    games, ids, bad, log = [], set(), 0, []
    for p in files:
        meta, errs, warns = read_game(p)
        for w in warns: print('  warn  %s: %s' % (p.name, w))
        if errs:
            bad += 1; print('  SKIP  %s: %s' % (p.name, '; '.join(errs))); continue
        e = dict(by_file.get(p.name) or {'id': p.stem, 'file': p.name, 'title': p.stem.replace('-', ' ').title(), 'tags': {}})
        e.update({k: meta[k] for k in ('title', 'icon', 'description', 'tags') if k in meta})
        if not e.get('description'): print('  warn  %s: no description (its Feed card shows a placeholder)' % p.name)
        if not e.get('tags'): print('  warn  %s: no tags, so it gives no taste signal' % p.name)
        if e['id'] in ids: e['id'] = p.stem
        ids.add(e['id']); games.append(e)
        if p.name not in by_file: log.append('+ added   ' + p.name)
        elif e != by_file[p.name]: log.append('~ updated ' + p.name)
    log += ['- removed ' + f for f in by_file if not (a.library / f).exists()]
    new = {'games': games}
    print('\n'.join(log) if log else 'Manifest is up to date (%d games).' % len(games))
    if new != old:
        if a.check: sys.exit(1)
        if not a.dry_run:
            mpath.write_text(json.dumps(new, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print('Wrote %s (%d games).' % (mpath, len(games)))
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
