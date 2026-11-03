# coding: utf-8
"""Unitários da regra H2 (contígua ordenada), sem Flask e sem banco."""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from matching import casa_contigua, normaliza  # noqa: E402


class NormalizaTest(unittest.TestCase):

    def test_trim_e_minusculas(self):
        self.assertEqual(normaliza([' Bm ', 'g']), ['bm', 'g'])

    def test_descarta_vazios_preservando_ordem_e_repeticao(self):
        self.assertEqual(normaliza(['A', '', '  ', 'A', 'B']), ['a', 'a', 'b'])


class CasaContiguaTest(unittest.TestCase):

    def test_bloco_exato(self):
        self.assertTrue(casa_contigua(
            ['Bm', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A']))

    def test_acorde_extra_antes(self):
        self.assertTrue(casa_contigua(
            ['Bm', 'G', 'D', 'A'], ['X', 'Bm', 'G', 'D', 'A']))

    def test_acorde_extra_depois(self):
        self.assertTrue(casa_contigua(
            ['Bm', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A', 'Y']))

    def test_janela_no_meio(self):
        self.assertTrue(casa_contigua(
            ['G', 'D', 'A'], ['Bm', 'G', 'D', 'A']))

    def test_acorde_de_passagem_quebra(self):
        self.assertFalse(casa_contigua(
            ['Bm', 'G', 'D', 'A'], ['Bm', 'G', 'X', 'D', 'A']))

    def test_ordem_trocada_nao_casa(self):
        self.assertFalse(casa_contigua(
            ['Bm', 'G', 'D', 'A'], ['Bm', 'D', 'G', 'A']))

    def test_repeticao_literal_casa(self):
        self.assertTrue(casa_contigua(['A', 'A', 'B'], ['A', 'A', 'B']))

    def test_repeticao_exigida_nao_casa_quando_falta(self):
        self.assertFalse(casa_contigua(['A', 'A', 'B'], ['A', 'B']))

    def test_caixa_ignorada(self):
        self.assertTrue(casa_contigua(['bm', 'g'], ['Bm', 'G']))

    def test_sequencia_vazia_nao_casa(self):
        self.assertFalse(casa_contigua([], ['A']))

    def test_cifra_vazia_nao_casa(self):
        self.assertFalse(casa_contigua(['A'], []))

    def test_sequencia_maior_que_cifra_nao_casa(self):
        self.assertFalse(casa_contigua(['A', 'B'], ['A']))

    def test_acorde_desconhecido_casa_literalmente(self):
        self.assertTrue(casa_contigua(['Zzz'], ['A', 'Zzz', 'B']))

    def test_acorde_desconhecido_nao_casa_por_engano(self):
        self.assertFalse(casa_contigua(['Zzz'], ['A', 'B']))

    def test_token_nao_acordal_casa_literalmente(self):
        self.assertTrue(casa_contigua(['|', 'A'], ['|', 'A']))


if __name__ == '__main__':
    unittest.main()
