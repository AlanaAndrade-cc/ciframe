# coding: utf-8
"""Schema, seed, canonical e persistência do catálogo SQLite.

Este módulo usa sempre um caminho próprio (nunca o `SEQUENCES_DB` da suíte),
exceto no teste explícito de override por variável de ambiente.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import catalogo  # noqa: E402


class CatalogoTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='deciframe-catalogo-')
        self.path = os.path.join(self.tmp, 'sequences.db')

    def tearDown(self):
        shutil.rmtree(self.tmp, True)

    def _conexao(self):
        conexao = sqlite3.connect(self.path)
        try:
            return conexao.execute('PRAGMA user_version').fetchone()[0]
        finally:
            conexao.close()

    def test_user_version(self):
        catalogo.init_db(self.path)
        self.assertEqual(self._conexao(), catalogo.SCHEMA_VERSION)

    def test_seed_idempotente(self):
        catalogo.init_db(self.path)
        catalogo.init_db(self.path)

        linhas = catalogo.listar(self.path)
        self.assertEqual(len(linhas), 6)
        self.assertEqual([linha['id'] for linha in linhas], [0, 1, 2, 3, 4, 5])

    def test_seed_ids_originais(self):
        catalogo.init_db(self.path)

        por_id = {linha['id']: linha for linha in catalogo.listar(self.path)}
        self.assertEqual(por_id[0]['legacy_key'], 'BmGDA')
        self.assertEqual(por_id[0]['acordes'], ['Bm', 'G', 'D', 'A'])
        self.assertEqual(por_id[1]['legacy_key'], 'CGAmF')
        self.assertEqual(por_id[2]['legacy_key'], 'EmG')
        self.assertEqual(por_id[3]['legacy_key'], 'CA7DmG7')
        self.assertEqual(por_id[4]['legacy_key'], 'GmF')
        self.assertEqual(por_id[5]['legacy_key'], 'CC7FFm')
        for linha in por_id.values():
            self.assertEqual(linha['match_mode'], 'tag')

    def test_canonical_ignora_caixa_e_espacos(self):
        self.assertEqual(
            catalogo.canonical([' Em ', 'c', '', 'G']),
            catalogo.canonical(['em', 'C', 'g']),
        )

    def test_canonical_preserva_ordem_e_repeticao(self):
        self.assertNotEqual(
            catalogo.canonical(['Em', 'C']),
            catalogo.canonical(['C', 'Em']),
        )
        self.assertNotEqual(
            catalogo.canonical(['A', 'A', 'B']),
            catalogo.canonical(['A', 'B']),
        )

    def test_duplicada_devolve_existente(self):
        catalogo.init_db(self.path)
        criada = catalogo.criar('Minha sequencia', ['Em', 'C', 'G'], self.path)

        with self.assertRaises(catalogo.Duplicada) as contexto:
            catalogo.criar('Outro nome', [' em ', 'c', 'G'], self.path)

        self.assertEqual(contexto.exception.existente['id'], criada['id'])
        self.assertEqual(contexto.exception.existente['nome'], 'Minha sequencia')

    def test_ordem_diferente_nao_e_duplicata(self):
        catalogo.init_db(self.path)
        primeira = catalogo.criar('Primeira', ['Em', 'C'], self.path)
        segunda = catalogo.criar('Segunda', ['C', 'Em'], self.path)

        self.assertNotEqual(primeira['id'], segunda['id'])
        self.assertEqual(len(catalogo.listar(self.path)), 8)

    def test_criar_sempre_contigua(self):
        catalogo.init_db(self.path)
        criada = catalogo.criar('Nova', ['D', 'A', 'Bm'], self.path)

        self.assertEqual(criada['match_mode'], 'contiguous')
        self.assertIsNone(criada['legacy_key'])

    def test_reabrir_arquivo_persiste(self):
        catalogo.init_db(self.path)
        criada = catalogo.criar('Persistente', ['D', 'A', 'Bm'], self.path)

        catalogo.init_db(self.path)
        reaberta = catalogo.obter(criada['id'], self.path)

        self.assertIsNotNone(reaberta)
        self.assertEqual(reaberta['nome'], 'Persistente')
        self.assertEqual(reaberta['acordes'], ['D', 'A', 'Bm'])

    def test_obter_por_legacy(self):
        catalogo.init_db(self.path)

        self.assertEqual(catalogo.obter_por_legacy('BmGDA', self.path)['id'], 0)
        self.assertIsNone(catalogo.obter_por_legacy('NaoExiste', self.path))

    def test_obter_id_inexistente(self):
        catalogo.init_db(self.path)
        self.assertIsNone(catalogo.obter(999, self.path))

    def test_verifica_legado_aceita_seed(self):
        catalogo.init_db(self.path)
        catalogo.verifica_legado({
            'BmGDA': 0,
            'CGAmF': 1,
            'EmG': 2,
            'CA7DmG7': 3,
            'GmF': 4,
            'CC7FFm': 5,
        }, self.path)

    def test_verifica_legado_rejeita_divergencia(self):
        catalogo.init_db(self.path)
        with self.assertRaises(RuntimeError):
            catalogo.verifica_legado({'BmGDA': 9}, self.path)

    def test_override_por_sequences_db(self):
        caminho = os.path.join(self.tmp, 'via-env.db')
        anterior = os.environ.get('SEQUENCES_DB')
        os.environ['SEQUENCES_DB'] = caminho
        try:
            catalogo.init_db()
            self.assertEqual(len(catalogo.listar()), 6)
        finally:
            if anterior is None:
                del os.environ['SEQUENCES_DB']
            else:
                os.environ['SEQUENCES_DB'] = anterior

        self.assertTrue(os.path.exists(caminho))

    def test_sequences_db_sem_diretorio(self):
        anterior = os.environ.get('SEQUENCES_DB')
        anterior_cwd = os.getcwd()
        os.environ['SEQUENCES_DB'] = 'x.db'
        os.chdir(self.tmp)
        try:
            catalogo.init_db()
            self.assertTrue(os.path.exists(os.path.join(self.tmp, 'x.db')))
        finally:
            os.chdir(anterior_cwd)
            if anterior is None:
                del os.environ['SEQUENCES_DB']
            else:
                os.environ['SEQUENCES_DB'] = anterior


if __name__ == '__main__':
    unittest.main()
