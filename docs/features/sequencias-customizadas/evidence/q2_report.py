import sys
sys.path.insert(0,'.')
from musica import Musica
AID,MID,ART,MUS,GEN,POP,TOM,SEQ,CIF = range(9)
def limpa(raw):
    out=[]
    for m in raw:
        if m.strip()!='':
            if '|' in m: out.append(m.split('|')[0].split()[0])
            else: out += m.split()
    return out
ms={}
f=open('data/top/dataset_final.csv'); f.readline()
for line in f:
    line=line.replace('"','').replace('NA','')[:-1]
    m=line.split(',')
    m[POP]=int(m[POP].replace('.',''))
    m[CIF]=limpa(m[CIF].split(';')) if m[CIF]!='' else []
    m[SEQ]=m[SEQ].split(';')
    o=Musica(m[AID],m[ART],m[MID],m[MUS],m[GEN],int(m[POP]),m[SEQ],m[TOM],m[CIF])
    ms[o.id_unico_musica]=o
f.close()
seqs=[('BmGDA',0,['bm','g','d','a']),('CGAmF',1,['c','g','am','f']),('EmG',2,['em','g']),
      ('CA7DmG7',3,['c','a7','dm','g7']),('GmF',4,['gm','f']),('CC7FFm',5,['c','c7','f','fm'])]
def contig(hay,needle):
    n=len(needle)
    return any(hay[i:i+n]==needle for i in range(len(hay)-n+1))
print('| Sequência | id_seq | Tag-based matches | Ocorrências contíguas na `cifra` | Subsequência (não contígua) |')
print('|---|---|---|---|---|')
for name,idx,p in seqs:
    hits=[x for x in ms.values() if str(idx) in x.seqs_famosas]
    allc=[x for x in ms.values() if x.cifra]
    contig_all=[x for x in allc if contig([c.lower() for c in x.cifra],p)]
    # subsequence
    def subseq(hay,needle):
        it=iter(hay); return all(any(x==y for x in it) for y in needle)
    sub_all=[x for x in allc if subseq([c.lower() for c in x.cifra],p)]
    print('| %s | %d | %d | %d | %d |' % (name,idx,len(hits),len(contig_all),len(sub_all)))
print()
for name,idx,p in seqs:
    hits=sorted([x for x in ms.values() if str(idx) in x.seqs_famosas], key=lambda x:(-x.popularidade,x.id_unico_musica))
    print('\n### %s (`id_seq=%d`) — %d músicas\n' % (name,idx,len(hits)))
    print('| # | Artista | Música | Popularidade | `id_unico_musica` |')
    print('|---|---|---|---|---|')
    for i,x in enumerate(hits,1):
        print('| %d | %s | %s | %d | `%s` |' % (i,x.nome_artista.replace('|','/'),x.nome_musica.replace('|','/'),x.popularidade,x.id_unico_musica))
