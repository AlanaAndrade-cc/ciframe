# coding: utf-8
"""Regressão exata das 6 sequências originais contra o fixture golden.

Critério: igualdade de **conjuntos** de `id_unico_musica` e contagens por
página. A ordem dentro da página não é comparada (vem de um `set` em
`main.py`).
"""

import json
import os
import sys
import unittest

import support

sys.path.insert(0, support.RAIZ)

FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'fixtures',
    'sequencias_golden.json',
)


class RegressaoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, 'r', encoding='utf-8') as arquivo:
            cls.golden = json.load(arquivo)

        cliente = support.app.test_client()
        resposta = cliente.get('/sequencias')
        catalogo = json.loads(resposta.data.decode('utf-8'))
        cls.id_por_legacy = {
            linha['legacy_key']: linha['id']
            for linha in catalogo
            if linha['legacy_key'] is not None
        }

    def setUp(self):
        support.limpar_catalogo()
        self.client = support.app.test_client()

    def _paginas(self, query):
        ids = set()
        paginas = []
        pagina = 1
        while True:
            resposta = self.client.get(
                '/similares?%s&pagina=%d' % (query, pagina))
            self.assertEqual(resposta.status_code, 200)
            self.assertTrue(resposta.content_type.startswith('text/html'))
            dados = json.loads(resposta.data.decode('utf-8'))
            self.assertIsInstance(dados, list)
            if not dados:
                break
            for musica in dados:
                ids.add(musica['id_unico_musica'])
            paginas.append(len(dados))
            pagina += 1
            self.assertLess(pagina, 100, 'paginacao nao terminou')
        return ids, paginas

    def _conferir(self, rotulo, ids, paginas, esperado):
        self.assertEqual(
            ids, set(esperado['ids']),
            '%s: conjunto de ids diverge do fixture' % rotulo)
        self.assertEqual(
            paginas, esperado['paginas'],
            '%s: contagem por pagina diverge do fixture' % rotulo)
        self.assertEqual(
            len(ids), sum(paginas),
            '%s: ids unicos != soma das paginas' % rotulo)

    def test_sequencia_id_bate_com_fixture(self):
        for chave, esperado in self.golden.items():
            with self.subTest(chave=chave):
                seq_id = self.id_por_legacy[chave]
                ids, paginas = self._paginas('sequencia_id=%d' % seq_id)
                self._conferir('sequencia_id=%d (%s)' % (seq_id, chave),
                               ids, paginas, esperado)

    def test_sequencia_legado_bate_com_fixture(self):
        for chave, esperado in self.golden.items():
            with self.subTest(chave=chave):
                ids, paginas = self._paginas('sequencia=%s' % chave)
                self._conferir('sequencia=%s' % chave, ids, paginas, esperado)

    def test_dois_caminhos_concordam(self):
        for chave in self.golden:
            with self.subTest(chave=chave):
                seq_id = self.id_por_legacy[chave]
                ids_id, paginas_id = self._paginas(
                    'sequencia_id=%d' % seq_id)
                ids_legado, paginas_legado = self._paginas(
                    'sequencia=%s' % chave)
                self.assertEqual(ids_id, ids_legado)
                self.assertEqual(paginas_id, paginas_legado)


if __name__ == '__main__':
    unittest.main()
