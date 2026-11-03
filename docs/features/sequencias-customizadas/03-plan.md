# Plano — Sequências de Acordes Customizadas

## Passos

1. [x] **Baseline antes de qualquer mudança de código.** Subir o código atual
   sem alterações (`python main.py`, porta 5000, ou `docker run -p 8080:8080
   ciframe`, porta 8080) e capturar o comportamento de hoje. Não reiniciar o
   servidor no meio da captura, para não misturar ordens.
   - Criar `tests/fixtures/capture_baseline.py` (script one-off, fora do
     `unittest`) que, para cada chave `BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`, `GmF`
     e `CC7FFm`, chama `/similares?sequencia=<chave>&pagina=N` até vir uma
     página vazia e coleta `id_unico_musica` de todas as páginas.
   - Gravar `tests/fixtures/sequencias_golden.json` no formato
     `{"<chave>": {"ids": [...], "paginas": [100, 99]}}`. A lista de ids é
     tratada como conjunto; a ordem não entra no fixture.
   - Conferir as contagens: `BmGDA` 100+99, `CGAmF` 100+100+96, `EmG` 4,
     `CA7DmG7` 5, `GmF` 7, `CC7FFm` 3 (`01-research.md:865-874`).
   - **Decisão:** o fixture é a única fonte de verdade do "antes" e é gravado
     antes de `main.py` ser tocado; depois do refactor o "antes" não é
     reproduzível com segurança.
   - **Correção (prompt de implementação):** o script usa apenas a stdlib
     (`urllib.request`, `json`); `requests` não é dependência do projeto.

2. [x] **Checkpoint 0 — baseline íntegro.** Validar o JSON e conferir as 6
   chaves e as contagens acima. Encerrar o servidor de captura. Só então
   seguir para o código.

3. [x] **Módulo de catálogo (`catalogo.py`) e schema.** Criar o banco antes de
   mexer nas rotas.
   - **Decisão de layout:** novo módulo na raiz, ao lado de `main.py`:
     `catalogo.py`, importável como `import catalogo`.
   - Funções: `conectar()`, `init_db()`, `listar()`, `criar(nome, acordes)`,
     `obter(id)`, `obter_por_legacy(key)`, `canonical(acordes)` e
     `verifica_legado(dict)`.
   - **Correção (prompt de implementação):** todas as funções de banco aceitam
     `path=None`. `main.py` usa o default; `test_catalogo` passa o próprio
     caminho. Isso resolve a inconsistência `init_db()` × `init_db(path)`.
   - Caminho do banco: `SEQUENCES_DB` se definido; senão `var/sequences.db`
     relativo ao cwd. Dentro do container o cwd é `/app` (`Dockerfile:3`),
     então o caminho efetivo é `/app/var/sequences.db`, como na proposta.
     `os.makedirs(dirname, exist_ok=True)` **apenas quando `dirname` não é
     vazio**, para que `SEQUENCES_DB=x.db` funcione; `PRAGMA
     journal_mode=WAL` e `PRAGMA busy_timeout=5000`.
   - **Correção (prompt de implementação):** manter sintaxe Python 3.9 (a
     imagem é `python:3.9-slim`): sem `match`, sem `X | Y` em tipos e sem APIs
     exclusivas de 3.10+.
   - Schema inicial:

```sql
CREATE TABLE IF NOT EXISTS sequences (
  id          INTEGER PRIMARY KEY,
  nome        TEXT NOT NULL,
  acordes     TEXT NOT NULL,
  canonical   TEXT NOT NULL UNIQUE,
  legacy_key  TEXT UNIQUE,
  match_mode  TEXT NOT NULL CHECK (match_mode IN ('tag', 'contiguous')),
  created_at  TEXT NOT NULL
);
PRAGMA user_version = 1;
```

   - `canonical`: tokens com `trim` e minúsculos, na ordem, unidos por `\x1f`;
     preserva repetição e impede duplicata entre caixas e modos.
   - `init_db()`: lê `PRAGMA user_version`; se 0, cria a tabela e seta 1; se 1,
     não faz nada; se outro valor, `RuntimeError`. Seed com `INSERT OR IGNORE`
     dos ids 0–5, `match_mode='tag'`, `legacy_key` e `acordes` JSON;
     `created_at` em ISO-8601 UTC.
   - **Onde roda:** em `main.py`, logo após `f.close()` (`main.py:98`) e antes
     das rotas, porque o gunicorn importa `main:app` (`Dockerfile:12`). Chamar
     `catalogo.init_db()` e `catalogo.verifica_legado(sequencias)`; o check
     compara `{legacy_key: id}` do banco com o dict de `main.py:40-45` e falha
     com `RuntimeError` se divergir.
   - Não tocar no parser do CSV (`main.py:49-98`).

4. [x] **Checkpoint 1 — banco sobe e o app continua servindo.** Rodar
   `SEQUENCES_DB=/tmp/deciframe.db .venv/bin/python -c "import main; import
   catalogo; print(catalogo.listar())"` e conferir 6 linhas com ids 0–5;
   repetir o comando e conferir que não duplica. Subir
   `.venv/bin/python main.py` e verificar
   `curl http://localhost:5000/generos` e
   `curl http://localhost:5000/similares?sequencia=BmGDA` (199, ainda no
   caminho de tag). **Correção:** o `python3` local é 3.14 e não tem Flask; o
   comando é sempre `.venv/bin/python`, a partir da raiz do repositório.

5. [x] **Matching H2 (`matching.py`) e dispatch por `match_mode`.** Manter a
   regra decidida na proposta; não reabrir a discussão.
   - **Decisão de layout:** novo módulo `matching.py`, puro (sem Flask e sem
     banco): `normaliza(acordes)` e `casa_contigua(seq, cifra)`.
   - `casa_contigua`: janela consecutiva e ordenada em `Musica.cifra`
     (`musica.py:16`); comparação em minúsculas; acordes antes/depois da janela
     são permitidos; acorde de passagem entre dois acordes da sequência quebra
     o match; repetição literal; `Musica.acordes` (`musica.py:17`) não é usado.
   - Em `main.py`, manter `get_similares_por_sequencia` (`main.py:203-223`)
     intacta e criar `get_similares_por_sequencia_contigua(acordes_seq,
     generos_key)` usando `apply_filtro` (`main.py:266-272`), o mesmo objeto de
     resposta (`main.py:210-220`) e `get_pagina` (`main.py:226-228`).
   - Dispatch: ler `match_mode` da linha; `tag` → função antiga com `row.id`;
     `contiguous` → função nova com `row.acordes`.
   - **Decisão:** `match_mode` inválido é `RuntimeError` no startup/teste, não
     fallback silencioso.

6. [x] **Checkpoint 2 — H2 isolado e as 6 intactas.** Exercitar
   `matching.casa_contigua` por `python3 -c` em casos sintéticos (bloco exato,
   acorde extra antes/depois, acorde de passagem, ordem trocada, repetição,
   caixa, cifra vazia). Conferir por `curl` que as 6 continuam com
   199/296/4/5/7/3; o caminho de tag ainda não foi alterado.

7. [x] **API.** Implementar o contrato da proposta sem mudar `json.dumps`.
   - `GET /sequencias`: lista do banco ordenada por `id`, com `id`, `nome`,
     `acordes` (array), `match_mode` e `legacy_key`; `json.dumps`.
   - `POST /sequencias`: `request.get_json(silent=True)`; `nome` de 1–80
     caracteres após `trim`; `acordes` lista de 1–32 strings, cada uma de 1–16,
     sem `,`, `;` ou espaço; calcula `canonical`; duplicata → 409 com `id` e
     `nome` existentes; sucesso → 201 com a linha criada e
     `match_mode='contiguous'`; erro → 400 com `json.dumps({"erro": "..."})`.
   - `GET /similares`: ler `sequencia_id` junto de `acordes`,
     `id_unico_musica` e `sequencia` (`main.py:170-201`). **Decisão de ordem:**
     inserir o ramo `sequencia_id` **depois** de `id_unico_musica`
     (`main.py:187-189`) e **antes** de `sequencia` (`main.py:190-196`),
     preservando a precedência atual de `acordes` e `id_unico_musica`. Id
     inexistente ou não numérico → `[]` com 200.
   - **Correção:** o id `0` é válido. Converter a string com `int()` e testar
     `is not None`; nunca `if id:`, senão `BmGDA` desaparece.
   - `sequencia=` legado: manter `replace(',','')` (`main.py:191`) e resolver
     por `legacy_key` no banco; desconhecida → `[]` com 200; não aceitar
     canonical nesse parâmetro.
   - A rota `get_similares` (`main.py:171`) e o helper homônimo
     (`main.py:230`) continuam como estão; o ramo novo fica na rota.
   - Todas as respostas continuam `json.dumps` com `Content-Type: text/html`
     (`main.py:197,201`); não usar `jsonify`. Não implementar edição/remoção.

8. [x] **Checkpoint 3 — contrato HTTP.** Com `curl -D -`, conferir
   `GET /sequencias`, `POST` válido (201), duplicata (409), inválido (400),
   `GET /similares?sequencia_id=<novo>`, id inexistente (`[]`),
   `sequencia=BmGDA` (199) e `sequencia=CGAmF` (296). Confirmar com
   `json.loads` e `Content-Type: text/html`. Medir `time curl` de uma sequência
   nova (H2) e de `BmGDA` (tag) e registrar os números.

9. [x] **Frontend (`#/porsequencia`).** Manter AngularJS 1.4.9, sem build e com
   URLs relativas.
   - `sequencia.js`: remover os quatro objetos fixos (`sequencia.js:2-37`) e o
     `createChordsString` (`sequencia.js:55-61`); no início do controller,
     `$http.get('sequencias')` e preencher `vm.sequenciasFamosas`; estados
     `carregando`, `erro` e `vazio`.
   - Mapear `acordes` (strings) para `{acorde, cor}` com paleta fixa; remover o
     `index` sempre 1 (`sequencia.js:3,11,19,25`); selo `original`/`nova` por
     `match_mode`/`legacy_key`.
   - Cadastro: `vm.novaSequencia = {nome: '', acordes: ['']}` com
     adicionar/remover; `$http.post('sequencias', ...)`; 400/409 em `vm.erro`;
     desabilitar `vm.salvando`; recarregar o catálogo no 201.
   - Busca: `similares?sequencia_id=` + `&generos=` + `&pagina=`
     (`sequencia.js:72-77`); resetar `pagina` em nova busca.
   - Paginação: `vm.pagina` e `vm.temProxima = data.length === 100`;
     anterior/próxima.
   - `sequencia.html`: formulário, selo e controles; remover
     `orderBy:'-popularidade'` (`sequencia.html:42`); manter `df-hex`
     (`sequencia.html:7`).
   - `GENEROS` continua fixo (`sequencia.js:43`; `app.js:6-58`).

10. [x] **Checkpoint 4 — smoke no browser.** Abrir
    `http://localhost:5000/#/porsequencia` com o venv e
    `http://localhost:8080/#/porsequencia` com Docker (servido pelo Flask, não
    `file://`): catálogo com as 6, selo, cadastro, lista atualizada, busca nova,
    paginação, filtro de gênero e mensagens 400/409. **Correção:** não fixar
    8080 para o venv; cada origem usa a sua porta.

11. [x] **Docker e README.** Ajustar o caminho gravável e a execução.
    - `Dockerfile`: `RUN mkdir -p /app/var` após `COPY . .` (`Dockerfile:8`) e
      antes do `CMD` (`Dockerfile:12`). **Decisão:** não declarar `VOLUME`; o
      volume nomeado é o mecanismo documentado.
    - `README.md`: trocar o `docker run` (`README.md:15-18`) por
      `docker run -p 8080:8080 -v deciframe-data:/app/var ciframe`; nota de que
      sem `-v` o `docker rm` perde o catálogo.
    - `.gitignore` e `.dockerignore`: acrescentar `var/` para não versionar nem
      copiar para a imagem um banco local.

12. [x] **Checkpoint 5 — persistência no Docker.** `docker build -t ciframe .`;
    `docker run -p 8080:8080 -v deciframe-data:/app/var ciframe`; criar uma
    sequência; `docker restart` → ela continua; `docker rm` + novo `run` com o
    mesmo volume → continua; `docker rm` sem volume + `run` sem volume → volta
    ao seed (perda esperada e documentada).

13. [x] **Testes automatizados.** Criar a suíte em `tests/` com `unittest`.
    - Arquivos: `tests/test_matching.py`, `tests/test_catalogo.py`,
      `tests/test_api.py`, `tests/test_regression.py` e `tests/support.py`.
    - **Decisão de isolamento:** `tests/support.py` define
      `SEQUENCES_DB` para um arquivo em diretório temporário **antes** de
      `import main` e expõe `app`; `test_api` e `test_regression` importam
      `support`. `setUp` remove linhas com `id >= 6`. **Correção:** a limpeza do
      diretório temporário usa `atexit.register(shutil.rmtree, ...)`, não
      `tearDownModule`: o banco é compartilhado por `test_api` e
      `test_regression`, e o primeiro módulo apagaria o diretório do segundo.
      `test_catalogo` usa `catalogo.init_db(path)` com caminho próprio.
    - `test_matching`: bloco exato, acorde extra, passagem, ordem, repetição,
      caixa, vazio, desconhecido e token não acordal.
    - `test_catalogo`: `user_version`, seed idempotente, ids 0–5, canonical
      duplicado, reabrir arquivo e override por `SEQUENCES_DB`.
    - `test_api`: 200/201/400/409, `json.loads`, `text/html`, id inexistente
      `[]` e `sequencia=` legado.
    - `test_regression`: carregar `tests/fixtures/sequencias_golden.json`;
      para ids 0–5, percorrer as páginas via `sequencia_id`, comparar
      **conjuntos** de `id_unico_musica` e as contagens por página; repetir com
      `sequencia=<legacy_key>`.
    - Rodar `.venv/bin/python -m unittest discover -s tests -v` a partir da
      raiz do repositório (o `python3` local é 3.14 e não tem Flask); atualizar
      `AGENTS.md:46-48` (hoje afirma que não há suíte) com esse comando exato.

14. [x] **Checkpoint 6 — suíte verde.** O comando acima passa; nenhum teste
    cria arquivo em `/app/var`; a contagem de testes aparece na saída.

15. [x] **Verificação final manual e Docker.** Repetir a matriz dos checkpoints
    3, 4 e 5 com o build final; comparar as 6 com o fixture; conferir que
    `musica.py`, `data/top/*.csv`, `requirements.txt` e `GENEROS` não mudaram.

16. [x] **Checkpoint 7 — entrega verificável.** Todos os itens da "Definição de
    pronto" satisfeitos; `git diff` restrito aos arquivos da tabela abaixo.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `main.py` | `init_db()` + check de legado após `main.py:98`; dispatch por `match_mode`; rotas `GET/POST /sequencias`; ramo `sequencia_id` em `main.py:170-201`. |
| `catalogo.py` (novo) | Conexão SQLite, schema com `user_version`, seed 0–5, canonical e leitura/criação. |
| `matching.py` (novo) | `normaliza` e `casa_contigua` puros para H2 sobre `Musica.cifra`. |
| `Dockerfile` | `RUN mkdir -p /app/var`. |
| `README.md` | Comando com `-v deciframe-data:/app/var`, nota sobre `docker rm` e a linha 8-9 sobre o catálogo SQLite. |
| `AGENTS.md` | Stack (`main.py` + `catalogo.py`/`matching.py` + SQLite), comando de teste, `sequencia_id=` no catálogo, ADR 0002 decidida, frontend lendo a API. |
| `.gitignore` | Acrescentar `var/`. |
| `.dockerignore` | Acrescentar `var/` para não copiar banco local para a imagem. |
| `static/assets/js/controllers/sequencia.js` | Catálogo por XHR, selo, formulário, paginação e `sequencia_id`; remover hardcoded/index. |
| `static/templates/sequencia.html` | Formulário, selo e paginação; remover `orderBy` (`sequencia.html:42`). |
| `tests/support.py` (novo) | `SEQUENCES_DB` temporário antes de `import main`; expõe `app`. |
| `tests/test_matching.py` (novo) | Unitários de H2. |
| `tests/test_catalogo.py` (novo) | Schema, seed, canonical e persistência. |
| `tests/test_api.py` (novo) | Contrato dos endpoints e `json.dumps`. |
| `tests/test_regression.py` (novo) | Regressão exata das 6 contra o fixture. |
| `tests/fixtures/sequencias_golden.json` (novo) | Baseline capturado antes de qualquer mudança. |
| `tests/fixtures/capture_baseline.py` (novo) | Script one-off de captura do baseline. |
| `requirements.txt` | Sem mudança: SQLite é stdlib do Python 3.9. |
| `musica.py` | Sem mudança: `cifra` (`musica.py:16`) já preserva ordem e repetição. |
| `static/assets/js/app.js` / `routes.js` | Sem mudança: `GENEROS` e a rota `#/porsequencia` ficam como estão. |

## Riscos e mitigação

| Risco | Como detectar | Mitigação |
|---|---|---|
| `/app/var` não gravável no import | `sqlite3.OperationalError: unable to open database file` no startup | `mkdir -p /app/var` no `Dockerfile`; `os.makedirs` no módulo; erro claro; testes usam diretório temporário. |
| Seed divergir do dict de `main.py:40-45` | `RuntimeError` no check de startup | `INSERT OR IGNORE` idempotente + `verifica_legado` comparando `{legacy_key: id}`. |
| Quebrar `sequencia=` ou o ramo `acordes` | Regressão das 6 falha ou `curl` de `acordes`/`id_unico_musica` muda | Não reordenar ramos existentes; inserir `sequencia_id` entre `id_unico_musica` e `sequencia`; manter `replace(',','')` (`main.py:191`); testes de regressão. |
| Ordem não determinística | Conjuntos iguais, listas diferentes | Comparar conjuntos de `id_unico_musica`; fixture sem ordem; nunca assertar ordem. |
| Latência H2 em 67.585 músicas | `time curl` de ~0,3 s por página no host | Sem cache nesta fase; medir no container; se p95 passar de 1 s, registrar como otimização futura (fora do escopo). |
| Testes vazarem para o banco real | Arquivo criado em `/app/var` durante a suíte | `SEQUENCES_DB` temporário definido em `tests/support.py` antes de `import main`; `setUp` limpa `id >= 6`. |
| Erros no AngularJS (400/409/rede) | Tela vazia, botão travado ou erro silencioso | `$http` `.error`, `vm.erro`, `vm.salvando` e estados carregando/erro/vazio. |
| Volume ausente no `docker rm` | Catálogo volta ao seed após recriar | README documenta `-v`; matriz de verificação; perda esperada e explícita. |
| Duplicata canônica entre modos | `POST` com `Bm,G,D,A` tenta criar linha | UNIQUE em `canonical`; pré-checagem + `IntegrityError` → 409. |
| Corpo JSON inválido | Flask devolve 415/HTML em vez do contrato | `get_json(silent=True)`; 400 com `json.dumps({"erro": ...})`. |
| Parser do CSV alterado por engano | Contagens das 6 mudam | Não tocar em `main.py:49-98`; regressão no Checkpoint 6. |

Observabilidade e segurança não geram seção própria: não há métricas novas além
dos erros do Flask, e o catálogo é anônimo por requisito
(`00-enunciado.md:47-48`); rate limiting, moderação e autenticação ficam fora de
escopo. O rollout é o próprio `docker build`/`run` local; não há ambiente de
produção.

## Definição de pronto

- [x] `tests/fixtures/sequencias_golden.json` existe e as 6 chaves batem:
      100+99, 100+100+96, 4, 5, 7, 3.
- [x] Para cada id 0–5, o conjunto de `id_unico_musica` de
      `/similares?sequencia_id=<id>` é **exatamente** igual ao fixture, com as
      mesmas contagens por página; o mesmo vale para `sequencia=<legacy_key>`.
- [x] `GET /sequencias` lista as 6 semeadas (ids 0–5) e as novas;
      `POST /sequencias` válido → 201, duplicata → 409, inválido → 400.
- [x] Sequência nova é buscável por `sequencia_id` com H2; id inexistente ou
      não numérico → `[]` com 200.
- [x] Todas as respostas continuam `json.dumps` com `Content-Type: text/html`;
      nenhum `jsonify`.
- [x] `#/porsequencia` carrega o catálogo real, mostra selo original/nova,
      cadastra, busca, pagina, filtra por gênero e exibe 400/409; sem
      `index`/`orderBy`, paleta fixa, AngularJS 1.4.9 sem build.
- [x] `docker restart` mantém sequência criada; `docker rm` + `run` com
      `-v deciframe-data:/app/var` mantém; sem volume, a perda está documentada.
- [x] `python3 -m unittest discover -s tests -v` verde; `AGENTS.md` atualizado
      com o comando.
- [x] `musica.py`, `data/top/*.csv`, `requirements.txt` e `GENEROS` inalterados;
      `git diff` restrito aos arquivos da tabela.
