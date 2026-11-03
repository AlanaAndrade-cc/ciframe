# coding: utf-8
"""Matching H2 (contíguo ordenado) para sequências novas.

Módulo puro: não conhece Flask nem o banco. A sequência casa quando aparece
como janela consecutiva e ordenada em `Musica.cifra` (`musica.py:16`), que
preserva ordem e repetição. Acordes antes ou depois da janela são permitidos;
um acorde de passagem entre dois acordes da sequência quebra o match.
"""


def normaliza(acordes):
    """trim + minúsculas, descartando tokens vazios; preserva ordem e repetição."""
    return [
        acorde.strip().lower()
        for acorde in acordes
        if acorde is not None and acorde.strip() != ''
    ]


def casa_contigua(seq, cifra):
    """True se `seq` é uma janela consecutiva de `cifra`."""
    seq = normaliza(seq)
    cifra = normaliza(cifra)

    if not seq or len(seq) > len(cifra):
        return False

    tamanho = len(seq)
    for inicio in range(len(cifra) - tamanho + 1):
        if cifra[inicio:inicio + tamanho] == seq:
            return True
    return False
