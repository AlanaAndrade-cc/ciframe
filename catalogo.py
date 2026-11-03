# coding: utf-8
"""Catálogo de sequências de acordes persistido em SQLite.

Só o catálogo de sequências vive no banco. Músicas e gêneros continuam no CSV
em memória carregado por `main.py`. O caminho do banco vem de `SEQUENCES_DB`
ou, por default, de `var/sequences.db` relativo ao cwd — dentro do container o
cwd é `/app`, então o caminho efetivo é `/app/var/sequences.db`.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

SCHEMA_VERSION = 1
DB_PADRAO = os.path.join('var', 'sequences.db')

# ids 0-5 são reservados para as sequências originais; o nome exibido é a
# própria chave legada.
SEED = [
    (0, 'BmGDA', 'BmGDA', ['Bm', 'G', 'D', 'A']),
    (1, 'CGAmF', 'CGAmF', ['C', 'G', 'Am', 'F']),
    (2, 'EmG', 'EmG', ['Em', 'G']),
    (3, 'CA7DmG7', 'CA7DmG7', ['C', 'A7', 'Dm', 'G7']),
    (4, 'GmF', 'GmF', ['Gm', 'F']),
    (5, 'CC7FFm', 'CC7FFm', ['C', 'C7', 'F', 'Fm']),
]

CAMPOS = 'id, nome, acordes, legacy_key, match_mode, created_at'


class Duplicada(Exception):
    """Já existe uma sequência com a mesma chave canônica."""

    def __init__(self, existente):
        super(Duplicada, self).__init__('sequencia ja cadastrada')
        self.existente = existente


def _db_path(path=None):
    if path is not None:
        return path
    return os.environ.get('SEQUENCES_DB') or DB_PADRAO


def conectar(path=None):
    caminho = _db_path(path)
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute('PRAGMA journal_mode=WAL')
    conexao.execute('PRAGMA busy_timeout=5000')
    return conexao


def canonical(acordes):
    """Chave única: tokens com trim e minúsculos, na ordem, preservando repetição."""
    return '\x1f'.join(
        acorde.strip().lower() for acorde in acordes if acorde.strip() != ''
    )


def _linha_para_dict(linha):
    dados = dict(linha)
    dados['acordes'] = json.loads(dados['acordes'])
    return dados


def _semear(conexao):
    agora = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for seq_id, nome, legacy_key, acordes in SEED:
        conexao.execute(
            'INSERT OR IGNORE INTO sequences '
            '(id, nome, acordes, canonical, legacy_key, match_mode, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                seq_id,
                nome,
                json.dumps(acordes),
                canonical(acordes),
                legacy_key,
                'tag',
                agora,
            ),
        )


def init_db(path=None):
    """Cria o schema (user_version 1) e semeia as 6 originais de forma idempotente."""
    conexao = conectar(path)
    try:
        versao = conexao.execute('PRAGMA user_version').fetchone()[0]
        if versao == 0:
            conexao.executescript(
                '''
                CREATE TABLE IF NOT EXISTS sequences (
                  id          INTEGER PRIMARY KEY,
                  nome        TEXT NOT NULL,
                  acordes     TEXT NOT NULL,
                  canonical   TEXT NOT NULL UNIQUE,
                  legacy_key  TEXT UNIQUE,
                  match_mode  TEXT NOT NULL CHECK (match_mode IN ('tag', 'contiguous')),
                  created_at  TEXT NOT NULL
                );
                '''
            )
            conexao.execute('PRAGMA user_version = %d' % SCHEMA_VERSION)
        elif versao != SCHEMA_VERSION:
            raise RuntimeError(
                'schema do catalogo desconhecido: user_version=%r' % (versao,)
            )

        _semear(conexao)
        conexao.commit()
    finally:
        conexao.close()


def listar(path=None):
    conexao = conectar(path)
    try:
        linhas = conexao.execute(
            'SELECT %s FROM sequences ORDER BY id' % CAMPOS
        ).fetchall()
    finally:
        conexao.close()
    return [_linha_para_dict(linha) for linha in linhas]


def obter(seq_id, path=None):
    conexao = conectar(path)
    try:
        linha = conexao.execute(
            'SELECT %s FROM sequences WHERE id = ?' % CAMPOS, (seq_id,)
        ).fetchone()
    finally:
        conexao.close()
    if linha is None:
        return None
    return _linha_para_dict(linha)


def obter_por_legacy(key, path=None):
    conexao = conectar(path)
    try:
        linha = conexao.execute(
            'SELECT %s FROM sequences WHERE legacy_key = ?' % CAMPOS, (key,)
        ).fetchone()
    finally:
        conexao.close()
    if linha is None:
        return None
    return _linha_para_dict(linha)


def criar(nome, acordes, path=None):
    """Insere uma sequência nova (sempre `contiguous`) e devolve a linha criada."""
    chave = canonical(acordes)
    conexao = conectar(path)
    try:
        existente = conexao.execute(
            'SELECT %s FROM sequences WHERE canonical = ?' % CAMPOS, (chave,)
        ).fetchone()
        if existente is not None:
            raise Duplicada(_linha_para_dict(existente))

        agora = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        try:
            cursor = conexao.execute(
                'INSERT INTO sequences '
                '(nome, acordes, canonical, legacy_key, match_mode, created_at) '
                "VALUES (?, ?, ?, NULL, 'contiguous', ?)",
                (nome, json.dumps(acordes), chave, agora),
            )
            conexao.commit()
        except sqlite3.IntegrityError:
            existente = conexao.execute(
                'SELECT %s FROM sequences WHERE canonical = ?' % CAMPOS, (chave,)
            ).fetchone()
            if existente is not None:
                raise Duplicada(_linha_para_dict(existente))
            raise
        seq_id = cursor.lastrowid
    finally:
        conexao.close()

    return obter(seq_id, path)


def verifica_legado(sequencias, path=None):
    """Falha se o seed do banco divergir do dict `sequencias` de `main.py`."""
    no_banco = {}
    for linha in listar(path):
        if linha['legacy_key'] is not None:
            no_banco[linha['legacy_key']] = linha['id']

    esperado = dict(sequencias)
    if no_banco != esperado:
        raise RuntimeError(
            'seed do catalogo diverge de main.sequencias: banco=%r main=%r'
            % (no_banco, esperado)
        )
