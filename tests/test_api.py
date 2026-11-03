# coding: utf-8
"""Contrato HTTP dos endpoints, com o banco temporário de `support`."""

import json
import sys
import unittest

import support

sys.path.insert(0, support.RAIZ)


class ApiTest(unittest.TestCase):

    def setUp(self):
        support.limpar_catalogo()
        self.client = support.app.test_client()

    def tearDown(self):
        support.limpar_catalogo()

    def _json(self, resposta):
        return json.loads(resposta.data.decode('utf-8'))

    def _paginas(self, query):
        ids = set()
        paginas = []
        pagina = 1
        while True:
            resposta = self.client.get(
                '/similares?%s&pagina=%d' % (query, pagina))
            self.assertEqual(resposta.status_code, 200)
            self.assertTrue(resposta.content_type.startswith('text/html'))
            dados = self._json(resposta)
            self.assertIsInstance(dados, list)
            if not dados:
                break
            for musica in dados:
                ids.add(musica['id_unico_musica'])
            paginas.append(len(dados))
            pagina += 1
            self.assertLess(pagina, 100, 'paginacao nao terminou')
        return ids, paginas

    def test_get_sequencias_200_text_html(self):
        resposta = self.client.get('/sequencias')

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.content_type.startswith('text/html'))
        dados = self._json(resposta)
        self.assertEqual([linha['id'] for linha in dados], [0, 1, 2, 3, 4, 5])
        for linha in dados:
            self.assertEqual(linha['match_mode'], 'tag')

    def test_post_cria_201(self):
        resposta = self.client.post('/sequencias', json={
            'nome': '  Nova sequencia  ',
            'acordes': [' Em ', 'C', 'G', 'D'],
        })

        self.assertEqual(resposta.status_code, 201)
        self.assertTrue(resposta.content_type.startswith('text/html'))
        dados = self._json(resposta)
        self.assertGreaterEqual(dados['id'], 6)
        self.assertEqual(dados['nome'], 'Nova sequencia')
        self.assertEqual(dados['acordes'], ['Em', 'C', 'G', 'D'])
        self.assertEqual(dados['match_mode'], 'contiguous')
        self.assertIsNone(dados['legacy_key'])

        catalogo = self._json(self.client.get('/sequencias'))
        self.assertIn(dados['id'], [linha['id'] for linha in catalogo])

    def test_post_duplicata_409(self):
        primeira = self._json(self.client.post('/sequencias', json={
            'nome': 'Primeira',
            'acordes': ['Em', 'C', 'G'],
        }))
        resposta = self.client.post('/sequencias', json={
            'nome': 'Outro nome',
            'acordes': ['em', 'c', 'G'],
        })

        self.assertEqual(resposta.status_code, 409)
        self.assertTrue(resposta.content_type.startswith('text/html'))
        dados = self._json(resposta)
        self.assertEqual(dados['id'], primeira['id'])
        self.assertEqual(dados['nome'], 'Primeira')

    def test_post_invalido_400(self):
        casos = [
            ('corpo nao json', None),
            ('sem nome', {'acordes': ['C']}),
            ('nome vazio', {'nome': '   ', 'acordes': ['C']}),
            ('nome longo', {'nome': 'x' * 81, 'acordes': ['C']}),
            ('acordes nao lista', {'nome': 'x', 'acordes': 'C'}),
            ('acordes vazio', {'nome': 'x', 'acordes': []}),
            ('acorde nao string', {'nome': 'x', 'acordes': ['C', 1]}),
            ('acorde vazio', {'nome': 'x', 'acordes': ['C', '  ']}),
            ('acorde com virgula', {'nome': 'x', 'acordes': ['C,G']}),
            ('acorde com ponto e virgula', {'nome': 'x', 'acordes': ['C;G']}),
            ('acorde com espaco', {'nome': 'x', 'acordes': ['C G']}),
            ('acorde longo', {'nome': 'x', 'acordes': ['C' * 17]}),
            ('acordes demais', {
                'nome': 'x', 'acordes': ['C'] * 33}),
        ]
        for rotulo, corpo in casos:
            with self.subTest(rotulo):
                if corpo is None:
                    resposta = self.client.post(
                        '/sequencias', data='nao e json',
                        content_type='application/json')
                else:
                    resposta = self.client.post('/sequencias', json=corpo)
                self.assertEqual(resposta.status_code, 400)
                self.assertTrue(
                    resposta.content_type.startswith('text/html'))
                self.assertIn('erro', self._json(resposta))

    def test_sequencia_id_0_paginas(self):
        ids, paginas = self._paginas('sequencia_id=0')

        self.assertEqual(paginas, [100, 99])
        self.assertEqual(len(ids), 199)

    def test_sequencia_id_inexistente_e_vazio(self):
        self.assertEqual(self._json(self.client.get(
            '/similares?sequencia_id=999999')), [])

    def test_sequencia_id_nao_numerico_e_vazio(self):
        self.assertEqual(self._json(self.client.get(
            '/similares?sequencia_id=abc')), [])

    def test_sequencia_legado(self):
        ids, paginas = self._paginas('sequencia=BmGDA')

        self.assertEqual(paginas, [100, 99])
        self.assertEqual(len(ids), 199)

    def test_sequencia_legado_desconhecida_e_vazia(self):
        self.assertEqual(self._json(self.client.get(
            '/similares?sequencia=NaoExiste')), [])

    def test_sequencia_nova_usa_contigua(self):
        criada = self._json(self.client.post('/sequencias', json={
            'nome': 'Contigua',
            'acordes': ['Em', 'C', 'G', 'D'],
        }))
        ids, paginas = self._paginas('sequencia_id=%d' % criada['id'])

        self.assertTrue(paginas)
        self.assertEqual(len(ids), sum(paginas))


if __name__ == '__main__':
    unittest.main()
