# coding: utf-8
"""Throwaway analysis for candidate matching rules. Does not modify the repo."""
from collections import Counter

CSV = 'data/top/dataset_final.csv'

SEQS = [
    ('BmGDA', 0, ['bm', 'g', 'd', 'a'], ['Bm', 'G', 'D', 'A']),
    ('CGAmF', 1, ['c', 'g', 'am', 'f'], ['C', 'G', 'Am', 'F']),
    ('EmG', 2, ['em', 'g'], ['Em', 'G']),
    ('CA7DmG7', 3, ['c', 'a7', 'dm', 'g7'], ['C', 'A7', 'Dm', 'G7']),
    ('GmF', 4, ['gm', 'f'], ['Gm', 'F']),
    ('CC7FFm', 5, ['c', 'c7', 'f', 'fm'], ['C', 'C7', 'F', 'Fm']),
]


def limpa_cifra(raw_cifra):
    cifra = []
    for m in raw_cifra:
        if m.strip() != '':
            if '|' in m:
                acorde = m.split('|')[0].split()[0]
                cifra.append(acorde)
            else:
                tokens = [token for token in m.split()]
                cifra += tokens
    return cifra


def is_sublist(pattern, values):
    n = len(pattern)
    if n == 0:
        return True
    for i in range(0, len(values) - n + 1):
        if values[i:i + n] == pattern:
            return True
    return False


def is_subsequence(pattern, values):
    it = iter(values)
    return all(any(x == p for x in it) for p in pattern)


def contiguous_subset(pattern, values, allowed):
    """The exact shape of generate_data_set.get_famosas for one sequence."""
    return is_sublist(pattern, values) and all(v in allowed for v in values)


def collapse_runs(values):
    out = []
    for v in values:
        if not out or out[-1] != v:
            out.append(v)
    return out


songs = []
with open(CSV, encoding='utf-8') as f:
    f.readline()  # same as main.py:50
    for line in f:
        line = line.replace('"', '').replace('NA', '')[:-1]
        parts = line.split(',')
        if len(parts) < 9:
            continue
        raw = parts[8]
        tokens = limpa_cifra(raw.split(';'))
        lower = [t.lower() for t in tokens]
        songs.append({
            'id': parts[0] + '_' + parts[1],
            'artist': parts[2],
            'name': parts[3],
            'pop': int(parts[5].replace('.', '')),
            'genre': parts[4],
            'raw': raw,
            'tokens': tokens,
            'lower': lower,
            'lower_set': set(lower),
            'tags': set(t for t in parts[7].split(';') if t),
        })

print('loaded', len(songs), 'songs')
print('empty cifra', sum(1 for s in songs if not s['lower']))
print()

rules = ['tag_rule', 'contig_ci', 'contig_cs', 'contig_collapse', 'subseq',
         'set_incl', 'multiset_incl', 'exact_multiset', 'set_equal']

summary = {}
examples = {}
for name, sid, lower_seq, original_seq in SEQS:
    sets = {}
    tag = {s['id'] for s in songs if str(sid) in s['tags']}
    sets['tag_rule'] = {
        s['id'] for s in songs
        if ';'.join(lower_seq) in s['raw'].lower()
        and all(t in set(lower_seq) for t in s['raw'].lower().split(';'))
    }
    sets['contig_ci'] = {s['id'] for s in songs if is_sublist(lower_seq, s['lower'])}
    sets['contig_cs'] = {s['id'] for s in songs if is_sublist(original_seq, s['tokens'])}
    sets['contig_collapse'] = {
        s['id'] for s in songs if is_sublist(lower_seq, collapse_runs(s['lower']))
    }
    sets['subseq'] = {s['id'] for s in songs if is_subsequence(lower_seq, s['lower'])}
    sets['set_incl'] = {s['id'] for s in songs if set(lower_seq) <= s['lower_set']}
    seq_counter = Counter(lower_seq)
    sets['multiset_incl'] = {
        s['id'] for s in songs if not (seq_counter - Counter(s['lower']))
    }
    sets['exact_multiset'] = {
        s['id'] for s in songs if Counter(s['lower']) == seq_counter
    }
    sets['set_equal'] = {s['id'] for s in songs if s['lower_set'] == set(lower_seq)}
    summary[name] = {}
    examples[name] = {}
    for rule in rules:
        cand = sets[rule]
        summary[name][rule] = {
            'count': len(cand),
            'tp': len(cand & tag),
            'fp': len(cand - tag),
            'fn': len(tag - cand),
        }
        fp = cand - tag
        fn = tag - cand
        examples[name][rule] = {
            'fp': sorted((s for s in songs if s['id'] in fp),
                         key=lambda x: -x['pop'])[:3],
            'fn': sorted((s for s in songs if s['id'] in fn),
                         key=lambda x: -x['pop'])[:3],
        }

print('rule summary per sequence: count / tp / fp / fn')
for name, _, _, _ in SEQS:
    print(name)
    for rule in rules:
        m = summary[name][rule]
        print('  %-16s %5d / %4d / %4d / %3d' % (
            rule, m['count'], m['tp'], m['fp'], m['fn']))
print()

print('tag_rule equals contiguous_subset for all sequences?')
for name, _, lower_seq, _ in SEQS:
    tag = {s['id'] for s in songs if str(dict((x[0], x[1]) for x in SEQS)[name]) in s['tags']}
    cs = {s['id'] for s in songs if contiguous_subset(lower_seq, s['lower'], set(lower_seq))}
    print(' ', name, tag == cs, 'tag=%d cs=%d only_tag=%d only_cs=%d' % (
        len(tag), len(cs), len(tag - cs), len(cs - tag)))
print()

print('examples of false positives (top popularity):')
for name, _, _, _ in SEQS:
    print(name)
    for rule in ['contig_ci', 'subseq', 'set_incl', 'multiset_incl', 'exact_multiset']:
        fp = examples[name][rule]['fp']
        print('  %-16s' % rule, '; '.join(
            '%s - %s (%d)' % (s['artist'], s['name'], s['pop']) for s in fp))
print()

print('examples of false negatives (top popularity):')
for name, _, _, _ in SEQS:
    print(name)
    for rule in ['contig_cs', 'contig_collapse', 'set_incl', 'multiset_incl']:
        fn = examples[name][rule]['fn']
        print('  %-16s' % rule, '; '.join(
            '%s - %s (%d)' % (s['artist'], s['name'], s['pop']) for s in fn))
print()

# Exact tag-generator comparison, including raw string semantics.
print('raw-string tag generator check:')
for name, sid, lower_seq, _ in SEQS:
    tag = {s['id'] for s in songs if str(sid) in s['tags']}
    rule = {
        s['id'] for s in songs
        if ';'.join(lower_seq) in s['raw'].lower()
        and all(t in set(lower_seq) for t in s['raw'].lower().split(';'))
    }
    print(' ', name, 'equal=', tag == rule, 'only_tag=', len(tag - rule),
          'only_rule=', len(rule - tag))

# How many songs have extra chords outside the sequence, among contiguous hits.
print()
print('contiguous hits split by extra-chord vocabulary:')
for name, sid, lower_seq, _ in SEQS:
    allowed = set(lower_seq)
    contig = [s for s in songs if is_sublist(lower_seq, s['lower'])]
    extra = [s for s in contig if any(t not in allowed for t in s['lower'])]
    no_extra = [s for s in contig if all(t in allowed for t in s['lower'])]
    print(' ', name, 'contig=%d no_extra=%d extra=%d' % (
        len(contig), len(no_extra), len(extra)))
    top_extra = sorted(extra, key=lambda x: -x['pop'])[:2]
    for s in top_extra:
        print('      extra ex:', s['artist'], '-', s['name'], '|', ';'.join(s['tokens'][:18]))
