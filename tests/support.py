# coding: utf-8
"""Isolamento da suíte: banco temporário antes de importar `main`.

`test_api` e `test_regression` compartilham o mesmo processo e o mesmo banco,
então o diretório temporário só pode ser apagado no fim do processo
(`atexit`), não no `tearDownModule` de um dos módulos.
"""

import atexit
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix='deciframe-tests-')
os.environ['SEQUENCES_DB'] = os.path.join(_TMP, 'sequences.db')

atexit.register(shutil.rmtree, _TMP, True)

import main  # noqa: E402  (precisa vir depois de SEQUENCES_DB)

app = main.app


def limpar_catalogo():
    """Remove sequências criadas pelos testes (ids >= 6)."""
    import catalogo

    conexao = catalogo.conectar()
    try:
        conexao.execute('DELETE FROM sequences WHERE id >= 6')
        conexao.commit()
    finally:
        conexao.close()
