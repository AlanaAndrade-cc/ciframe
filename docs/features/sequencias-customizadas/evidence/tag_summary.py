# coding: utf-8
"""Reproduce the SEQ_FAMOSA summary quoted in 01-research.md §2.1.

Run from the repository root:

    python3 docs/features/sequencias-customizadas/evidence/tag_summary.py
"""
from collections import Counter

CSV = 'data/top/dataset_final.csv'

SEQS = [
    ('BmGDA', 0),
    ('CGAmF', 1),
    ('EmG', 2),
    ('CA7DmG7', 3),
    ('GmF', 4),
    ('CC7FFm', 5),
]


def load_tag_lists():
    tags_per_song = []
    with open(CSV, encoding='utf-8') as f:
        f.readline()
        for line in f:
            line = line.replace('"', '').replace('NA', '')[:-1]
            parts = line.split(',')
            if len(parts) < 9:
                continue
            tags_per_song.append(parts[7].split(';'))
    return tags_per_song


def main():
    tags_per_song = load_tag_lists()
    counter = Counter(tag for tags in tags_per_song for tag in tags)

    print('TOTAL loaded songs:', len(tags_per_song))
    print('Distinct SEQ_FAMOSA tokens:', len(counter))
    print('Token distribution:', dict(sorted(counter.items(), key=lambda kv: -kv[1])))
    for name, idx in SEQS:
        count = sum(1 for tags in tags_per_song if str(idx) in tags)
        print('%s id=%d count=%d' % (name, idx, count))


if __name__ == '__main__':
    main()
