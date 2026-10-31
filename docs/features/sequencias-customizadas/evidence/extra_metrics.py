# coding: utf-8
"""Extra throwaway metrics for the research document."""
from collections import Counter, defaultdict

CSV = 'data/top/dataset_final.csv'
SEQS = [
    ('BmGDA', 0, ['bm', 'g', 'd', 'a']),
    ('CGAmF', 1, ['c', 'g', 'am', 'f']),
    ('EmG', 2, ['em', 'g']),
    ('CA7DmG7', 3, ['c', 'a7', 'dm', 'g7']),
    ('GmF', 4, ['gm', 'f']),
    ('CC7FFm', 5, ['c', 'c7', 'f', 'fm']),
]


def limpa_cifra(raw_cifra):
    cifra = []
    for m in raw_cifra:
        if m.strip() != '':
            if '|' in m:
                acorde = m.split('|')[0].split()[0]
                cifra.append(acorde)
            else:
                cifra += m.split()
    return cifra


songs = []
with open(CSV, encoding='utf-8') as f:
    f.readline()
    for line in f:
        line = line.replace('"', '').replace('NA', '')[:-1]
        p = line.split(',')
        if len(p) < 9:
            continue
        tokens = limpa_cifra(p[8].split(';'))
        songs.append({
            'id': p[0] + '_' + p[1],
            'artist': p[2],
            'name': p[3],
            'pop': int(p[5].replace('.', '')),
            'tokens': tokens,
            'lower': [t.lower() for t in tokens],
            'tags': set(t for t in p[7].split(';') if t),
        })

all_tokens = [t for s in songs for t in s['tokens']]
distinct = set(all_tokens)
by_lower = defaultdict(set)
for t in distinct:
    by_lower[t.lower()].add(t)
collisions = {k: v for k, v in by_lower.items() if len(v) > 1}
non_chord = [t for t in distinct if not any(c.isalpha() for c in t)]
songs_non_chord = [s for s in songs if any(not any(c.isalpha() for c in t) for t in s['tokens'])]

print('tokens total', len(all_tokens), 'distinct', len(distinct),
      'distinct lowercase', len(by_lower), 'case-collision groups', len(collisions))
print('case collision examples:')
for k in sorted(collisions)[:15]:
    print(' ', k, sorted(collisions[k]))
print('non-chord distinct', len(non_chord), 'examples', sorted(non_chord)[:20])
print('songs with non-chord token', len(songs_non_chord))
print()

print('tag rule versus exact multiset:')
for name, sid, seq in SEQS:
    tagged = [s for s in songs if str(sid) in s['tags']]
    exact = [s for s in tagged if Counter(s['lower']) == Counter(seq)]
    print(' ', name, 'tagged', len(tagged), 'exact multiset', len(exact),
          'tagged with repeats/extra', len(tagged) - len(exact))
print()

print('set equality false positives (top popularity):')
for name, sid, seq in SEQS:
    tag = {s['id'] for s in songs if str(sid) in s['tags']}
    equal = {s['id'] for s in songs if set(s['lower']) == set(seq)}
    fp = equal - tag
    top = sorted((s for s in songs if s['id'] in fp), key=lambda x: -x['pop'])[:3]
    print(' ', name, 'set_equal', len(equal), 'fp', len(fp))
    for s in top:
        print('      ', s['artist'], '-', s['name'], '(%d)' % s['pop'],
              '|', ';'.join(s['tokens'][:16]))
print()

print('songs where sequence is contiguous but tag is absent, extra chord vocabulary:')
for name, sid, seq in SEQS:
    allowed = set(seq)
    contig = [s for s in songs if any(s['lower'][i:i + len(seq)] == seq
                                      for i in range(len(s['lower']) - len(seq) + 1))]
    extra = [s for s in contig if any(t not in allowed for t in s['lower'])]
    print(' ', name, 'contig', len(contig), 'extra', len(extra),
          'top extra chord tokens', Counter(t for s in extra for t in s['lower'] if t not in allowed).most_common(5))
