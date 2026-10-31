# Propostas (rascunho) — Sequências de Acordes Customizadas

> **Rascunho para discussão, não decisão.** Este arquivo não é o `02-proposal.md`
> e não escolhe uma abordagem vencedora. Nada aqui foi implementado. O objetivo é
> comparar três desenhos possíveis antes da fase de proposta.
>
> **Ordem de leitura.** A ordem segue a aderência estrita às restrições fixas,
> com o eixo principal em matching + regressão: (1) H1 unificado, que reproduz
> exatamente as 6 tags; (2) híbrido, que mantém as 6 no caminho de tag e usa
> matching ao vivo só para sequências novas; (3) H2/H3 unificado, que muda os
> resultados das 6. O híbrido vem antes do H2/H3 porque preserva o resultado das
> 6; se o critério for “uma única semântica para todo o catálogo”, a ordem se
> inverte. Não há vencedor.
>
> **Correspondência com a numeração do pedido.** O pedido lista as abordagens
> como 1 = H1 unificado, 2 = H2/H3 unificado e 3 = híbrido. Aqui o híbrido sobe
> para a Proposta 2 e o H2/H3 desce para a Proposta 3, porque a ordenação pedida
> é “da mais aderente para a menos aderente às restrições” e o híbrido preserva as 6
> exatamente. Quem preferir a ordem literal do pedido deve ler a Proposta 3 antes
> da Proposta 2; o conteúdo não muda.

## Contexto

- **Pedido:** permitir que qualquer visitante cadastre uma sequência de acordes e
  busque músicas por ela, com o catálogo de sequências persistido em banco. O
  catálogo de músicas/gêneros continua no CSV em memória; a aplicação continua
  em um único container Docker local; as respostas continuam em `json.dumps`; as
  6 sequências originais precisam continuar produzindo os mesmos resultados.
- **Fonte de pesquisa:** `docs/features/sequencias-customizadas/00-enunciado.md`
  e `docs/features/sequencias-customizadas/01-research.md`, principalmente §1.5
  (hipóteses), §2.3 (contagens contra as tags), §3.3 (bancos candidatos), §4.5
  (frontend), “Trade-offs identificados” e “Questões abertas para a proposta”.
  As saídas brutas estão em `docs/features/sequencias-customizadas/evidence/`
  (`q2_report.out`, `hypotheses_metrics.out`, `extra_metrics.out`).

### Restrições fixas

| Restrição | Evidência |
|---|---|
| Músicas e gêneros continuam vindo do CSV em memória; só o catálogo de sequências vai para o banco. | `00-enunciado.md:60-62`; carga em `main.py:49-98`. |
| Aplicação em um único `Dockerfile` local, sem serviço externo. | `00-enunciado.md:63-65`; `Dockerfile:1-12`; `docs/adr/0001-local-only-docker-deploy.md:9-16`. |
| As 6 sequências originais mantêm os mesmos resultados de busca. | `00-enunciado.md:66-67`. |
| Endpoints continuam retornando `json.dumps(...)`, não `jsonify`. | `00-enunciado.md:68`; `main.py:197,201`. |
| Catálogo aberto e anônimo, sem login. | `00-enunciado.md:47-48`. |
| `#/porsequencia` reflete o catálogo real e permite cadastrar. | `00-enunciado.md:54-55`. |
| Stack do frontend continua AngularJS 1.4.9 + jQuery, sem build. | `AGENTS.md`; `docs/adr/0003-lift-frontend-freeze.md:17-20`. |

### Base compartilhada pelas três propostas

- **Contrato de busca preservado:** `GET /similares` continua devolvendo a mesma
  forma de objeto por música (`id_unico_musica`, `id_artista`, `id_musica`,
  `nome_artista`, `nome_musica`, `popularidade`, `acordes`, `genero`, `url`), sem
  `diferenca`/`intersecao` (`main.py:210-220`), com `json.dumps` (`main.py:197`) e
  paginação de 100 (`main.py:35,226-228`).
- **Filtro de gênero preservado:** `generos_tag.split(',')` e `apply_filtro`
  (`main.py:178-182,266-272`).
- **CSV intocado:** o parser de `main.py:49-74` não muda; a primeira linha
  continua sendo pulada (`main.py:50`), o `replace('NA','')` global continua
  (`main.py:53`) e cifras vazias continuam sem match.
- **Representação:** as três propostas ordenadas usam `Musica.cifra`
  (`musica.py:16`), que preserva ordem e repetição. `Musica.acordes`
  (`musica.py:17`) é `list(set(cifra))` e não serve para regras ordenadas.
- **Banco:** SQLite em arquivo, biblioteca padrão do Python 3.9, sem nova
  dependência (`requirements.txt:4-5`). Caminho `/app/var/sequences.db`, fora de
  `/app/data` para não arriscar esconder o CSV se um volume for montado.
- **Persistência:** o arquivo sobrevive a `docker restart` mesmo sem volume; para
  sobreviver a `docker rm`/recriação é preciso volume nomeado ou bind mount. O
  `Dockerfile` atual não tem `VOLUME` (`Dockerfile:1-12`) e o README não usa `-v`
  (`README.md:15-18`).
- **API compartilhada:** `GET /sequencias`, `POST /sequencias` e
  `GET /similares?sequencia_id=...`; o parâmetro legado `sequencia=` continua
  aceito. Todas as respostas usam `json.dumps`.
- **Frontend compartilhado:** o controller deixa de usar os quatro objetos fixos
  (`static/assets/js/controllers/sequencia.js:2-37`) e passa a carregar o
  catálogo por `$http`; o template ganha formulário de cadastro e paginação.
  `GENEROS` continua fixo (`static/assets/js/app.js:6-58`); trocar por
  `GET /generos` fica fora de escopo.
- **Testes:** hoje não há suíte (`AGENTS.md`). A proposta é criar `tests/` com
  `unittest` da biblioteca padrão, sem nova dependência, e documentar o comando
  `python3 -m unittest discover -s tests -v` no `AGENTS.md`.

### Custo medido do matching ao vivo

Benchmark descartável em `/tmp/bench_proposals.py`, uma passada completa sobre
67.585 músicas e 3.505.331 tokens, no host (Python 3.14, 8 núcleos), sem Docker:

| Regra | Tempo mediano por consulta | Observação |
|---|---:|---|
| H1 (contígua + vocabulário fechado) | 270–325 ms | Inclui a verificação de vocabulário em toda a música. |
| H2 (contígua ordenada) | 270–326 ms | Mesma varredura, sem o teste de vocabulário. |
| H3 (subsequência ordenada) | 125–135 ms | Para cedo quando encontra a subsequência; retorna muito mais músicas. |
| Caminho de tag atual | 4,5–6 ms | `str(id_seq) in musica.seqs_famosas` (`main.py:209`). |

O container usa Python 3.9 (`Dockerfile:1`), então esses números não são uma
promessa de produção; medir dentro do container é pré-requisito antes de fixar
qualquer meta de latência. A varredura é repetida a cada página; não há cache.

---

## Proposta 1 — Matching ao vivo unificado com H1

**Ideia:** todas as sequências, antigas e novas, usam a mesma regra H1 calculada
ao vivo sobre `musica.cifra`. É a única regra medida que reproduz exatamente as
tags das 6 (`01-research.md:865-886`), então a regressão é a mais simples das
três. O custo é uma semântica pouco intuitiva para sequências novas.

### 1.1 Regra exata

- **Canonicalização da sequência:** receber uma lista ordenada de tokens; aplicar
  `trim`, minúsculas e descartar tokens vazios; preservar a ordem; rejeitar
  vírgula dentro de um token (a vírgula é separador no contrato atual,
  `main.py:191`). A chave canônica é a lista de tokens minúsculos unida por um
  separador que não aparece em acorde (por exemplo `\x1f`), não a concatenação
  simples, para evitar colisões.
- **Lado da música:** usar `Musica.cifra` (`musica.py:16`), que preserva ordem e
  repetição, com os tokens já produzidos por `limpa_cifra` (`main.py:11-23`).
  Minúsculas são aplicadas na comparação, não no CSV.
- **Condição de match:** a sequência aparece como bloco **contíguo e ordenado**
  dentro da cifra **e** todo acorde da música pertence ao conjunto de acordes da
  sequência. Em fórmula: `contiguous(seq, cifra)` e `set(cifra) ⊆ set(seq)`.
- **Ordem e adjacência:** importam. Um acorde de passagem entre dois acordes da
  sequência quebra o match. Acordes antes ou depois do bloco são permitidos
  somente se pertencerem ao vocabulário da sequência; qualquer acorde fora
  desqualifica.
- **Repetição:** repetições da sequência são literais e consecutivas; não há
  colapso de runs (H8 não é usado). Repetições na música são permitidas desde que
  o vocabulário continue fechado.
- **Normalização:** minúsculas, `trim` e remoção de vazios. **Não** há
  normalização enarmônica (`C#` ≠ `Db`), remoção de sufixos, unificação de
  grafias ou filtro de tokens não acordais. Isso preserva a fidelidade ao gerador
  de tags (`scripts/generate_data_set.py:12-20`) e evita inventar equivalências
  que a pesquisa não mediu (`01-research.md:179-186`).
- **Tokens desconhecidos ou vazios:** sequência vazia ou só com espaços → HTTP
  400. Acorde desconhecido é aceito e armazenado; ele simplesmente produz 0
  resultados se nenhuma música tiver aquele token. Limite proposto: 1 a 32
  acordes por sequência (decisão de produto, não da pesquisa).
- **Tokens não acordais:** não são filtrados. Em H1 eles contam como acorde fora
  do vocabulário e desqualificam a música; isso é coerente com a tag atual. Há 13
  tokens sem letra em 21 músicas (`01-research.md:132-143`).
- **Duplicatas:** a chave canônica é única. Cadastrar a mesma lista ordenada de
  acordes, em qualquer caixa, retorna 409. As 6 originais são semeadas com ids
  0–5 e chaves legadas (`BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`, `GmF`, `CC7FFm`).

### 1.2 Regressão das 6

- **Critério:** igualdade exata de conjunto de músicas contra as tags atuais:
  199, 296, 4, 5, 7 e 3 (`01-research.md:865-874`). H1 foi a única hipótese com
  FP=0 e FN=0 para as 6 (`01-research.md:926-927`).
- **Como testar:** para cada id 0–5, percorrer todas as páginas de
  `GET /similares?sequencia_id=<id>` e comparar o conjunto de
  `id_unico_musica` com a lista de `evidence/q2_report.py`/`q2_report.out`.
  Também conferir as contagens por página: `BmGDA` 100+99, `CGAmF` 100+100+96,
  `EmG` 4, `CA7DmG7` 5, `GmF` 7, `CC7FFm` 3 (`01-research.md:245-264`).
- **Ordem:** comparar conjuntos, não a ordem. A ordem atual varia entre processos
  porque `generos` é um `set` (`main.py:38,92`) e `apply_filtro` concatena nessa
  ordem (`main.py:266-272`; `01-research.md:275-288`). Tornar a ordem
  determinística é uma mudança separada, fora do escopo desta proposta.
- **Forma da resposta:** mesmas chaves de `main.py:210-220`, `Content-Type:
  text/html` por causa do `json.dumps` (`main.py:197`; `01-research.md:268-273`).
- **Rollback:** manter o caminho de tag disponível por flag de ambiente durante
  a validação; se a regressão falhar, voltar ao caminho antigo sem reverter o
  banco. A flag não precisa ficar no produto final.

### 1.3 Banco, esquema e persistência

- **Tecnologia:** SQLite em arquivo, `sqlite3` da biblioteca padrão do CPython
  3.9. Não muda `requirements.txt` (`requirements.txt:4-5`) nem o passo de
  instalação (`Dockerfile:5-6`). É o candidato de menor atrito em §3.3
  (`01-research.md:1040-1067`).
- **Esquema inicial:**

```sql
CREATE TABLE IF NOT EXISTS sequences (
  id          INTEGER PRIMARY KEY,
  nome        TEXT NOT NULL,
  acordes     TEXT NOT NULL,              -- JSON array, ordem preservada
  canonical   TEXT NOT NULL UNIQUE,       -- tokens minúsculos unidos por \x1f
  legacy_key  TEXT UNIQUE,                -- 'BmGDA', ...; NULL para novas
  match_mode  TEXT NOT NULL CHECK (match_mode IN ('h1')),
  created_at  TEXT NOT NULL
);
PRAGMA user_version = 1;
```

- **Seed:** inserir as 6 com ids 0–5 e `legacy_key` preenchido, de forma
  idempotente (`INSERT OR IGNORE`). No startup, montar o dicionário
  `sequencias = {legacy_key: id}` a partir do banco para preservar o lookup de
  `main.py:194`; não manter duas fontes de verdade. Verificar que os ids 0–5
  continuam sendo exatamente os das 6 (`main.py:40-45`).
- **Inicialização:** `init_db()` no import de `main.py`, depois da carga do CSV
  (`main.py:49-98`), como o gunicorn já importa `main:app` (`Dockerfile:12`).
  Criar o diretório `/app/var` no `Dockerfile` (`RUN mkdir -p /app/var`).
  `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000`; conexão curta por
  requisição ou uma conexão por worker. O gunicorn atual não fixa `--workers`
  (`Dockerfile:12`), então o cenário padrão é um worker; se `--workers` for
  adicionado, o WAL e o `busy_timeout` cobrem a concorrência de escrita.
- **Migrações:** `PRAGMA user_version` para versionar; mudanças futuras com
  `ALTER TABLE` manual. Não introduzir Alembic/ORM nesta fase (fora de escopo).
- **Persistência entre reinícios:**

| Cenário | Sem volume | `VOLUME /app/var` sem `-v` | Volume nomeado `-v deciframe-data:/app/var` |
|---|---|---|---|
| `docker restart` | sobrevive (camada gravável) | sobrevive | sobrevive |
| `docker rm` + recriar | perde | o volume anônimo permanece, mas um novo container não o reutiliza automaticamente | sobrevive |
| `docker rm -v` | perde | perde | sobrevive (volume nomeado não é removido por `-v`) |

  Declarar `VOLUME ["/app/var"]` é opcional; o requisito de recriação é atendido
  pelo volume nomeado documentado no README:
  `docker run -p 8080:8080 -v deciframe-data:/app/var ciframe`. Não montar sobre
  `/app/data`, que contém o CSV copiado em `Dockerfile:8`.

### 1.4 API, validação e duplicatas

| Método | Rota | Entrada | Saída | Status |
|---|---|---|---|---|
| GET | `/sequencias` | — | lista de sequências | 200 |
| POST | `/sequencias` | JSON `{nome, acordes}` | sequência criada | 201, 400 ou 409 |
| GET | `/similares?sequencia_id=<id>` | — | lista de músicas | 200; id desconhecido → `[]` |
| GET | `/similares?sequencia=<acordes>` | string legada | lista de músicas | 200; desconhecida → `[]` |

- **Validação do POST:** `nome` obrigatório, `trim`, 1–80 caracteres; `acordes`
  lista de 1–32 strings, cada uma com `trim`, 1–16 caracteres, sem vírgula,
  ponto e vírgula ou espaço; minúsculas só na chave canônica, preservando a
  grafia original para exibição. Corpo inválido → 400 com
  `json.dumps({"erro": "..."})`.
- **Duplicatas:** mesma lista canônica → 409 com o id e o nome existentes. Isso
  impede recadastrar `BmGDA` como `Bm,G,D,A`.
- **`json.dumps`:** todas as respostas, inclusive erros, usam `json.dumps` e
  continuam com `Content-Type: text/html`; não usar `jsonify`. Testar com
  `curl -D -` e `json.loads`.
- **Fora de escopo:** editar e remover sequências. O catálogo é anônimo e não há
  autenticação/CSRF; exclusão por qualquer visitante seria destrutiva. Também
  fora de escopo: rate limiting e moderação.

### 1.5 Frontend

- **Catálogo:** remover os objetos `sequencia1`..`sequencia4`
  (`static/assets/js/controllers/sequencia.js:2-37`) e carregar
  `GET /sequencias` no início do controller. Preencher
  `vm.sequenciasFamosas` com a resposta; estados `carregando`, `erro` e `vazio`.
  O `ng-repeat` de `static/templates/sequencia.html:5-8` já aceita uma lista.
- **Busca:** `pesquisarPorSequencia` passa a enviar
  `similares?sequencia_id=<id>` em vez de concatenar acordes
  (`sequencia.js:55-61,72-77`); mantém `&generos=` e acrescenta `&pagina=`.
- **Cadastro:** adicionar ao template um formulário com `nome` e uma lista
  editável de acordes (adicionar/remover), botão de envio e mensagens de erro.
  `$http.post('/sequencias', ...)`; em sucesso, recarregar o catálogo e
  selecionar a sequência criada; em 409, mostrar que já existe; em 400, mostrar
  a validação. Desabilitar o botão enquanto a requisição está em andamento.
- **Paginação:** controles anterior/próxima e estado `pagina`; enviar `pagina` e
  usar `data.length === 100` como heurística de “tem próxima” (o backend não
  devolve total). Isso é necessário para ver os 199/296 resultados completos; hoje
  a UI recebe no máximo 100 (`sequencia.js:72-77`; `main.py:35,226-228`).
- **Ordem e cores:** remover `orderBy:'-popularidade'` de
  `sequencia.html:42` ou aplicá-lo apenas dentro da página; o backend não ordena
  globalmente por popularidade (`01-research.md:275-295`). O catálogo não tem
  `cor`; manter uma paleta fixa no frontend e remover o `index` sempre `1`
  (`sequencia.js:3,11,19,25`). `df-hex` continua recebendo `acorde-color`
  (`sequencia.html:7`).
- **Gêneros:** manter `GENEROS` fixo (`sequencia.js:43`; `app.js:6-58`);
  `GET /generos` existe (`main.py:158-160`) mas não é usado pela página. Trocar
  para `/generos` fica fora de escopo.
- **Servir pelo Flask:** validar em `http://localhost:8080`, não por `file://`
  (`main.py:101-103`; `AGENTS.md`).

### 1.6 Desempenho

- **Custo dominante:** uma varredura completa de `musicas.values()` por
  requisição, como já ocorre em `main.py:203-209`, mas agora com a condição H1.
  Medido em ~270–325 ms por consulta no host; no container Python 3.9 pode ser
  diferente.
- **Paginação:** cada página repete a varredura; ver as 199/296 músicas custa 2–3
  varreduras. Não há cache. Um cache por sequência com TTL ou um índice
  pré-computado é otimização possível, mas fica fora do escopo desta proposta.
- **Concorrência:** com um worker de gunicorn (`Dockerfile:12`), requisições são
  serializadas; ~300 ms por busca limita o throughput a poucas buscas por
  segundo. Se `--workers` for adicionado, cada worker varre a base
  independentemente; o gargalo é CPU.
- **Banco:** leitura de uma linha por busca; irrelevante frente à varredura.
- **Meta sugerida para validação:** p95 abaixo de 1 s no container local para as
  6 sequências; medir antes de fixar.

### 1.7 Testes

- **Unitários de matching:** função pura nova (por exemplo `matching.py`) com
  `match_h1(seq, cifra)`; casos sintéticos de bloco exato, acorde extra que
  desqualifica, ordem trocada, repetição na música, repetição na sequência,
  caixa diferente, cifra vazia, token não acordal, acorde desconhecido e
  sequência vazia.
- **Regressão:** as 6 contra as tags, igualdade exata de conjunto e contagens por
  página; usar `evidence/q2_report.py`/`.out` como oráculo.
- **Banco:** seed idempotente; ids 0–5; criar/listar; duplicata 409; reabrir o
  arquivo; `docker restart`; `docker rm` + recriação com volume nomeado; sem
  volume, documentar a perda esperada.
- **API:** 200/201/400/409; `json.loads`; `Content-Type: text/html`; resposta de
  id desconhecido `[]`; corpo inválido; duplicata com caixa diferente.
- **Frontend:** smoke no browser via Flask; catálogo carrega; cadastro aparece na
  lista após reload; busca pela sequência nova; erro de catálogo; vazio;
  paginação; gênero.
- **Comando:** `python3 -m unittest discover -s tests -v`. Documentar no
  `AGENTS.md`; não inventar `pytest`/`npm test` sem adicionar dependência.
- **Docker:** `docker build -t ciframe .`; `docker run -p 8080:8080 -v
  deciframe-data:/app/var ciframe`; `curl` nos endpoints; `docker restart`;
  `docker rm` + novo `docker run` com o mesmo volume.

### 1.8 Trade-offs e sistemas impactados

| Prós | Contras | Riscos |
|---|---|---|
| Regressão exata das 6, com FP=0/FN=0. | H1 é um artefato do gerador de tags, não uma definição musical intuitiva: qualquer acorde extra na música desqualifica. | Usuários podem achar que a busca de sequências novas está “quebrada” por retornar pouco. |
| Uma única semântica para todo o catálogo. | Recall baixo para sequências novas; poucas músicas casam. | A equivalência H1 ao vivo × tag foi medida só para as 6; casos com `\|`, espaços e tokens vazios precisam de teste sintético (`01-research.md:942-944`). |
| Banco e API simples; sem dependência nova. | Varredura completa por requisição (~0,3 s) e por página. | Persistência depende de volume nomeado; sem ele, `docker rm` perde o catálogo. |
| Fácil de explicar como “a mesma regra das 6”. | Não atende à expectativa “a sequência aparece” para sequências novas. | Ordem de resultados continua não determinística; comparar por conjunto. |

**Sistemas impactados:** `main.py` (rotas novas, dispatch, init do banco),
`musica.py` (somente leitura), novo módulo de matching, novo módulo de banco,
`Dockerfile` (diretório/volume), `README.md` (comando com `-v`),
`static/assets/js/controllers/sequencia.js`,
`static/templates/sequencia.html`, `tests/` e `AGENTS.md` (comando de teste).
`requirements.txt` não muda.

### 1.9 Questões abertas (1–12)

| # | Pergunta | Resposta nesta proposta |
|---:|---|---|
| 1 | Definição de “a sequência aparece” | H1: bloco contíguo e ordenado + vocabulário fechado; minúsculas; repetição literal; sem normalização enarmônica. |
| 2 | Critério de regressão das 6 | Igualdade exata de conjunto com as tags (199/296/4/5/7/3); ordem não é comparada. |
| 3 | `cifra` ou `acordes` | `Musica.cifra` (`musica.py:16`); `acordes` (`musica.py:17`) não preserva ordem/repetição e fica fora. |
| 4 | Normalizações | Minúsculas, `trim`, remover vazios; sem enarmônicos/sufixos; não filtrar tokens não acordais; desconhecido aceito; vazio → 400. |
| 5 | Desempenho, tamanho e pré-cálculo | Ao vivo; ~0,3 s por consulta no host; catálogo pequeno; sem pré-cálculo nem invalidação; medir no container. |
| 6 | Banco e persistência | SQLite stdlib em `/app/var/sequences.db`; volume nomeado para `docker rm`; `restart` já sobrevive. |
| 7 | Esquema, seed e migrações | Tabela única com `acordes` JSON, `canonical` único, `legacy_key`, `match_mode='h1'`; seed 0–5; `user_version=1`; sem framework de migração. |
| 8 | Contrato da API | `GET/POST /sequencias`, `GET /similares?sequencia_id=`; 200/201/400/409; sem edição/remoção; `json.dumps` e `text/html`. |
| 9 | Frontend: catálogo e cadastro | XHR no load; estados carregando/erro/vazio; formulário + POST; lista e cadastro; sem render no servidor. |
| 10 | Paginação, ordem, cores, `index`, gêneros | Controles de página; remover `orderBy` global; paleta fixa; remover `index`; manter `GENEROS`; `/generos` fora de escopo. |
| 11 | Testes mínimos | Unitários de matching, regressão exata, banco/restart, API, smoke de frontend e medição de latência; `unittest`. |
| 12 | Tratamento do CSV | Parser intocado; cifra vazia sem match; caixa normalizada na comparação; tokens não acordais não filtrados; primeira linha/`NA` fora de escopo. |

---

## Proposta 2 — Híbrido: tag para as 6, matching ao vivo para novas

**Ideia:** as 6 sequências continuam usando o caminho de tag pré-computada
(`main.py:203-223`), preservando resultados e custo atuais; sequências novas usam
H2 (contígua ordenada) ao vivo. É a opção que preserva o legado e oferece uma
semântica intuitiva para o catálogo novo, ao preço de duas semânticas no mesmo
catálogo.

### 2.1 Regra exata

- **Sequências legadas (`match_mode='tag'`, ids 0–5):** exatamente o caminho
  atual: `str(id_seq) in musica.seqs_famosas` (`main.py:209`), com
  `apply_filtro` (`main.py:266-272`) e paginação (`main.py:226-228`). A tag vem
  do CSV (`main.py:63`) e não é recalculada.
- **Sequências novas (`match_mode='contiguous'`):** H2 ao vivo sobre
  `Musica.cifra` (`musica.py:16`).
  - **Ordem e adjacência:** a sequência aparece como janela consecutiva na ordem
    dada; acordes antes ou depois da janela são permitidos; um acorde de
    passagem entre dois acordes da sequência quebra o match.
  - **Repetição:** repetições na sequência são literais e consecutivas; não há
    colapso de runs. Repetições na música não importam além de formarem a janela.
  - **Normalização:** minúsculas, `trim`, remover vazios; sem enarmônicos,
    sufixos ou filtro de tokens não acordais.
  - **Desconhecido/vazio:** vazio → 400; acorde desconhecido aceito e pode
    retornar 0; limite de 32 acordes.
  - **Duplicatas:** a chave canônica é única em todo o catálogo; recadastrar
    `Bm,G,D,A` (legado `BmGDA`) retorna 409, mesmo sendo outra semântica. Isso
    evita duas entradas com os mesmos acordes e comportamentos diferentes.
- **Por que não H1 para as novas:** H1 nas novas repetiria o problema de recall
  baixo; H2 é a leitura mais direta de “a sequência aparece” e inclui todas as
  tags das 6 (`01-research.md:928-932`). H3 fica como variante futura, não nesta
  proposta.
- **Inconsistência assumida:** a mesma tela mostra sequências com duas regras.
  A UI deve indicar `original` versus `nova` e explicar que as originais usam a
  tag histórica; sem isso, a diferença de volume de resultados parece bug.

### 2.2 Regressão das 6

- **Critério:** igualdade exata de conjunto e de contagens por página, porque o
  caminho de tag não muda. As 6 continuam com 199/296/4/5/7/3.
- **Como testar:** mesmos testes da P1 para os ids 0–5; adicionalmente, garantir
  que o dispatch nunca manda id 0–5 para a função H2 e que `match_mode='tag'` é
  lido do banco.
- **Sequências novas:** não há baseline histórico. Testar H2 com casos
  sintéticos e com um conjunto dourado pequeno (por exemplo `D,G,Em`) gerado na
  fase de testes; não comparar com tags.
- **Rollback:** como o caminho legado não muda, o risco de regressão é baixo; se
  o cadastro novo falhar, é possível desabilitar o formulário/POST e manter as 6
  funcionando.

### 2.3 Banco, esquema e persistência

- **Tecnologia:** a mesma SQLite stdlib, `/app/var/sequences.db`, sem nova
  dependência. A escolha de banco é ortogonal ao eixo de matching; se outro
  banco embarcado for preferido, o esquema e a API não mudam.
- **Esquema:**

```sql
CREATE TABLE IF NOT EXISTS sequences (
  id          INTEGER PRIMARY KEY,
  nome        TEXT NOT NULL,
  acordes     TEXT NOT NULL,              -- JSON array, ordem preservada
  canonical   TEXT NOT NULL UNIQUE,       -- tokens minúsculos unidos por \x1f
  legacy_key  TEXT UNIQUE,                -- 'BmGDA', ...; NULL para novas
  match_mode  TEXT NOT NULL CHECK (match_mode IN ('tag', 'contiguous')),
  created_at  TEXT NOT NULL
);
PRAGMA user_version = 1;
```

- **Seed:** as 6 com ids 0–5, `match_mode='tag'`, `legacy_key` preenchido;
  idempotente. O dicionário `sequencias` de `main.py:40-45` pode ser mantido como
  fallback, mas a fonte de verdade do catálogo passa a ser o banco; verificar no
  startup que os dois concordam.
- **Persistência:** mesma matriz da P1 (`restart` sobrevive; `docker rm` exige
  volume nomeado; `/app/var`, não `/app/data`). `RUN mkdir -p /app/var`;
  `VOLUME` opcional; README com `-v deciframe-data:/app/var`.
- **Concorrência:** WAL + `busy_timeout`; o caminho legado é somente leitura de
  memória e não toca o banco além de ler a linha da sequência.

### 2.4 API, validação e duplicatas

| Método | Rota | Entrada | Saída | Status |
|---|---|---|---|---|
| GET | `/sequencias` | — | lista com `match_mode`/origem | 200 |
| POST | `/sequencias` | JSON `{nome, acordes}` | sequência nova (`contiguous`) | 201, 400 ou 409 |
| GET | `/similares?sequencia_id=<id>` | — | lista de músicas | 200; desconhecido → `[]` |
| GET | `/similares?sequencia=<acordes>` | string legada | lista de músicas | 200; desconhecida → `[]` |

- **Dispatch:** ler `match_mode` da linha; `tag` → `get_similares_por_sequencia`
  atual (`main.py:203-223`); `contiguous` → nova função H2. O parâmetro
  `sequencia_id` é a forma nova; `sequencia=` continua aceito e resolve pelo
  `legacy_key` ou pela chave canônica.
- **POST:** sempre cria `match_mode='contiguous'`; o cliente não pode criar
  `tag`. Validação igual à P1 (nome 1–80; 1–32 acordes; sem vírgula/espaço;
  vazio → 400). Duplicata canônica em qualquer modo → 409.
- **`json.dumps`:** todas as respostas continuam `json.dumps` com
  `Content-Type: text/html`; não usar `jsonify`.
- **Fora de escopo:** editar/remover; rate limiting; moderação; criação de novas
  sequências com `match_mode='tag'`.

### 2.5 Frontend

- **Catálogo:** carregar `GET /sequencias`; exibir `nome`, acordes e um selo
  `original`/`nova` derivado de `match_mode`/`legacy_key`. Estado de carregando,
  erro e vazio.
- **Busca:** enviar `sequencia_id` e `pagina`; manter `&generos=`.
- **Cadastro:** formulário de `nome` + acordes; `POST /sequencias`; recarregar a
  lista; mostrar 400/409; desabilitar durante o envio.
- **Explicação da diferença:** um texto curto na página ou tooltip: “originais
  usam a marcação histórica; novas usam correspondência contígua”. Sem isso, o
  usuário vê volumes muito diferentes e não entende.
- **Paginação:** essencial para as novas: H2 pode retornar 866, 1.216 ou 3.110
  (por exemplo `Em,G`), ou seja, 9–32 páginas de 100. Controles
  anterior/próxima; remover `orderBy` global; paleta fixa; remover `index`;
  manter `GENEROS`.
- **Template/rotas:** mudanças em `sequencia.js` e `sequencia.html`; a rota
  `#/porsequencia` (`static/assets/js/routes.js:17-21`) e o `ng-view`
  (`static/index.html:123`) não mudam.

### 2.6 Desempenho

- **Legado:** ~4,5–6 ms por consulta no host (tag scan), sem regressão de custo.
- **Novas:** ~270–326 ms por consulta (H2), repetido por página; o volume de
  resultados é maior e a paginação importa mais.
- **Banco:** leitura de uma linha; irrelevante.
- **Concorrência:** um worker de gunicorn serializa; as 6 continuam rápidas, as
  novas competem por CPU. Se o catálogo novo crescer, considerar cache/índice
  (fora de escopo).
- **Meta:** manter as 6 no custo atual e aceitar ~0,3 s para novas; medir no
  container.

### 2.7 Testes

- **Regressão das 6:** igualdade exata de conjunto e páginas, como na P1.
- **H2:** unitários sintéticos de janela contígua, acorde de passagem que quebra,
  acordes antes/depois, repetição, caixa, cifra vazia, token não acordal,
  desconhecido e vazio.
- **Dispatch:** ids 0–5 → tag; id ≥ 6 → H2; `match_mode` inválido → erro de
  inicialização/teste.
- **Duplicata entre modos:** `Bm,G,D,A` → 409; `D,G,Em` → 201.
- **Banco/API/frontend/perf:** mesmos da P1, com o selo de origem e a explicação
  das duas semânticas no smoke test.
- **Comando:** `python3 -m unittest discover -s tests -v`.

### 2.8 Trade-offs e sistemas impactados

| Prós | Contras | Riscos |
|---|---|---|
| As 6 ficam exatamente iguais e rápidas (~5 ms). | Duas semânticas no mesmo catálogo: o usuário vê comportamentos diferentes. | Confusão de UX; a diferença de resultados parece bug se não for explicada. |
| Matching novo intuitivo (H2) e com recall maior. | Duas funções, dois caminhos de teste e manutenção. | Duplicata canônica entre modos precisa ser rejeitada para não criar ambiguidade. |
| Rollout incremental: o caminho legado não muda. | H2 pode retornar milhares; paginação vira requisito forte. | Se o catálogo novo crescer, o custo por busca e a paginação pioram. |
| Banco simples e sem dependência nova. | A regra “cada sequência tem seu modo” fica gravada no dado; migrar depois exige mudança de schema. | Persistência depende de volume nomeado para `docker rm`. |

**Sistemas impactados:** `main.py` (dispatch, rotas novas, init do banco),
`main.py:203-223` (caminho legado preservado), novo módulo H2, novo módulo de
banco, `Dockerfile`/`README.md`, `sequencia.js`, `sequencia.html`, `tests/`,
`AGENTS.md`. `requirements.txt` não muda.

### 2.9 Questões abertas (1–12)

| # | Pergunta | Resposta nesta proposta |
|---:|---|---|
| 1 | Definição de “a sequência aparece” | H1 via tag para ids 0–5; H2 contígua ordenada ao vivo para novas; ordem/adjacência importam; repetição literal; minúsculas. |
| 2 | Critério de regressão das 6 | Igualdade exata de conjunto e páginas; o caminho de tag não muda. |
| 3 | `cifra` ou `acordes` | `cifra` para H2; `seqs_famosas` para o legado; `acordes` fora. |
| 4 | Normalizações | Minúsculas, `trim`, remover vazios; sem enarmônicos/sufixos; não filtrar não acordais; desconhecido aceito; vazio → 400. |
| 5 | Desempenho, tamanho e pré-cálculo | Legado ~5 ms; novas ~0,3 s; ao vivo; sem pré-cálculo; medir no container. |
| 6 | Banco e persistência | SQLite stdlib; `/app/var/sequences.db`; volume nomeado para `docker rm`. |
| 7 | Esquema, seed e migrações | Tabela com `match_mode` `tag`/`contiguous`, `canonical` único, `legacy_key`; seed 0–5; `user_version=1`. |
| 8 | Contrato da API | `GET/POST /sequencias`, `GET /similares?sequencia_id=`; dispatch por modo; 200/201/400/409; `json.dumps`. |
| 9 | Frontend: catálogo e cadastro | XHR; selo original/nova; formulário + POST; estados de erro/vazio; sem render no servidor. |
| 10 | Paginação, ordem, cores, `index`, gêneros | Paginação obrigatória; remover `orderBy` global; paleta fixa; remover `index`; manter `GENEROS`. |
| 11 | Testes mínimos | Regressão exata, unitários H2, dispatch, duplicata entre modos, banco/restart, API, frontend e latência. |
| 12 | Tratamento do CSV | Parser intocado; legado lê `seqs_famosas` (`main.py:63`); H2 lê `cifra`; cifra vazia sem match; caixa na comparação. |

---

## Proposta 3 — Matching ao vivo unificado com H2 (variante H3)

**Ideia:** todo o catálogo usa H2 (contígua ordenada) ao vivo, com H3
(subsequência ordenada) como modo opcional por sequência. É a semântica mais
intuitiva de “a sequência aparece” e a mais consistente entre antigas e novas,
mas muda os resultados das 6 e, portanto, conflita com o requisito de regressão
exata.

### 3.1 Regra exata

- **H2 (padrão, `match_mode='contiguous'`):** a sequência aparece como janela
  consecutiva de `Musica.cifra` (`musica.py:16`) na ordem dada; acordes antes ou
  depois da janela são permitidos; um acorde de passagem entre dois acordes da
  sequência quebra o match.
- **H3 (opcional, `match_mode='subsequence'`):** os acordes da sequência aparecem
  na ordem dada, mas não precisam ser consecutivos; outros acordes podem ficar
  entre eles. É a leitura “a sequência está espalhada pela música”.
- **Repetição:** em H2, repetições da sequência são literais e consecutivas; em
  H3, a subsequência pode usar ocorrências distintas da música, então repetições
  da sequência exigem ocorrências suficientes na ordem. Não há colapso de runs.
- **Normalização:** minúsculas, `trim`, remover vazios; sem enarmônicos,
  sufixos ou filtro de tokens não acordais. A filtragem de tokens não acordais é
  uma possível melhoria, mas mudaria as contagens e fica fora do baseline.
- **Desconhecido/vazio:** vazio → 400; desconhecido aceito e pode retornar 0;
  limite de 32 acordes.
- **Duplicatas:** chave canônica única; as 6 são semeadas com H2; recadastrar a
  mesma lista retorna 409. O modo não faz parte da chave: a mesma sequência não
  pode existir em H2 e H3 ao mesmo tempo.
- **Contagens esperadas:** H2 retorna 866/1.216/3.110/96/1.039/132 para as 6;
  H3 retorna 4.763/5.887/13.643/427/3.641/280 (`01-research.md:865-874`). Em
  ambos os casos, todas as músicas com tag continuam incluídas (0 FN), mas há
  milhares de novas músicas.

### 3.2 Regressão das 6

- **Conflito explícito:** esta proposta **não** preserva os mesmos resultados das
  6. H2 devolve um superconjunto (por exemplo `BmGDA` 199 → 866) e H3 devolve um
  superconjunto muito maior (`BmGDA` 4.763). O requisito `00-enunciado.md:66-67`
  teria que ser reinterpretado como “todas as músicas com tag continuam
  aparecendo, com matches adicionais”, e isso precisa de aprovação explícita.
- **Critério de teste:** para cada id 0–5, verificar `tag_set ⊆ live_set` e que a
  diferença é exatamente 667/920/3.106/91/1.032/129 em H2
  (`01-research.md:892-899`); para H3, as diferenças são
  4.564/5.591/13.639/422/3.634/277. Congelar conjuntos dourados (ou hashes) para
  detectar mudanças futuras.
- **Páginas:** as contagens por página mudam; `BmGDA` passa a 9 páginas em H2 e
  `EmG` a 32; a UI precisa de paginação de verdade. Testar páginas 1, 2, última
  e uma além.
- **Ordem:** continua não determinística; comparar conjuntos, não ordem.
- **Rollback:** se a regressão exata for inegociável, esta proposta não é viável;
  manter o caminho de tag por flag permite voltar atrás sem reverter o banco.

### 3.3 Banco, esquema e persistência

- **Tecnologia:** SQLite stdlib, `/app/var/sequences.db`, sem nova dependência;
  mesma matriz de persistência da P1 (`restart` sobrevive; `docker rm` exige
  volume nomeado; `/app/var`, não `/app/data`).
- **Esquema:**

```sql
CREATE TABLE IF NOT EXISTS sequences (
  id          INTEGER PRIMARY KEY,
  nome        TEXT NOT NULL,
  acordes     TEXT NOT NULL,              -- JSON array, ordem preservada
  canonical   TEXT NOT NULL UNIQUE,       -- tokens minúsculos unidos por \x1f
  legacy_key  TEXT UNIQUE,                -- 'BmGDA', ...; NULL para novas
  match_mode  TEXT NOT NULL CHECK (match_mode IN ('contiguous', 'subsequence')),
  created_at  TEXT NOT NULL
);
PRAGMA user_version = 1;
```

- **Seed:** as 6 com ids 0–5 e `match_mode='contiguous'` (H2), para minimizar a
  mudança em relação às tags; H3 fica disponível para sequências novas. Se as 6
  fossem semeadas em H3, a mudança seria ainda maior.
- **Migrações:** `user_version=1`; `ALTER TABLE` manual no futuro; sem ORM.
- **Concorrência:** WAL + `busy_timeout`; o modo não muda o custo de escrita.

### 3.4 API, validação e duplicatas

| Método | Rota | Entrada | Saída | Status |
|---|---|---|---|---|
| GET | `/sequencias` | — | lista com `match_mode` | 200 |
| POST | `/sequencias` | JSON `{nome, acordes, match_mode?}` | sequência criada | 201, 400 ou 409 |
| GET | `/similares?sequencia_id=<id>` | — | lista de músicas | 200; desconhecido → `[]` |
| GET | `/similares?sequencia=<acordes>` | string legada | lista de músicas | 200; desconhecida → `[]` |

- **POST:** `match_mode` opcional, padrão `contiguous`; aceitar `subsequence`;
  qualquer outro valor → 400. `nome` 1–80; `acordes` 1–32; sem vírgula/espaço;
  vazio → 400. Duplicata canônica → 409.
- **Dispatch:** `contiguous` → H2; `subsequence` → H3; ids 0–5 também passam pelo
  matching ao vivo, não pela tag.
- **`json.dumps`:** todas as respostas continuam `json.dumps` com
  `Content-Type: text/html`; não usar `jsonify`.
- **Fora de escopo:** editar/remover; rate limiting; moderação; expor métricas de
  match por sequência.

### 3.5 Frontend

- **Catálogo:** carregar `GET /sequencias`; exibir `nome`, acordes, `match_mode`
  e um selo `contígua`/`subsequência`. Estados de carregando/erro/vazio.
- **Busca:** enviar `sequencia_id` e `pagina`; manter `&generos=`.
- **Cadastro:** formulário com `nome`, acordes e seletor de modo (padrão
  contígua), com texto explicando a diferença; `POST /sequencias`; recarregar;
  mostrar 400/409; desabilitar durante o envio.
- **Paginação:** obrigatória e mais visível que nas outras propostas: H2 chega a
  32 páginas para `EmG`; H3 chega a 137 páginas. Controles anterior/próxima;
  remover `orderBy` global; paleta fixa; remover `index`; manter `GENEROS`.
- **Aviso de volume:** mostrar a contagem aproximada ou pelo menos “muitos
  resultados” para o usuário não achar que a busca travou.
- **Template/rotas:** mudanças em `sequencia.js` e `sequencia.html`; rota e
  `ng-view` não mudam.

### 3.6 Desempenho

- **H2:** ~270–326 ms por consulta no host; H3 ~125–135 ms (para cedo), mas
  retorna muito mais músicas. O custo dominante continua sendo a varredura
  completa; a paginação repete a varredura.
- **Serialização:** só 100 itens por página; irrelevante frente à varredura.
- **Concorrência:** um worker de gunicorn serializa; H3 é mais rápido por
  consulta, mas o volume maior aumenta o custo de UI/paginação.
- **Pré-cálculo:** possível armazenar os ids de músicas por sequência no banco na
  criação (as músicas vêm do CSV e só mudam com restart), mas invalidação e
  tamanho ficam fora do escopo; medir antes.
- **Meta:** p95 abaixo de 1 s no container para H2; H3 idem, com paginação.

### 3.7 Testes

- **Unitários:** `match_h2` e `match_h3` com os mesmos casos sintéticos da P1,
  mais o caso “acorde de passagem” que H2 rejeita e H3 aceita.
- **Regressão das 6:** inclusão (`tag_set ⊆ live_set`) e delta exato em H2;
  para H3, inclusão e delta exato; conjuntos dourados/hashes.
- **API:** `match_mode` inválido → 400; default contígua; duplicata → 409;
  `json.dumps`/`text/html`.
- **Banco/restart:** seed 0–5, ids, persistência com volume nomeado.
- **Frontend:** cadastro com cada modo; paginação; busca; erro/vazio; reload.
- **Performance:** medir H2/H3 no container; páginas 1/2/última.
- **Comando:** `python3 -m unittest discover -s tests -v`.

### 3.8 Trade-offs e sistemas impactados

| Prós | Contras | Riscos |
|---|---|---|
| Uma única semântica para todo o catálogo. | Viola o requisito de mesmos resultados das 6; H2/H3 retornam superconjuntos grandes. | Sem aprovação explícita, a proposta não é aceitável. |
| H2 é intuitiva; H3 cobre “sequência espalhada”. | Volume de resultados e paginação muito maiores; UX precisa de contagem/aviso. | Usuários podem estranhar a mudança de 199 para 866 ou 4.763. |
| Sem dependência de tag para buscar; catálogo consistente. | Duas regras (H2/H3) e mais testes; performance por consulta. | H3 pode casar acordes muito distantes e perder precisão. |
| Banco/API simples e sem dependência nova. | Persistência depende de volume nomeado para `docker rm`. | Ordem continua não determinística; comparar por conjunto. |

**Sistemas impactados:** `main.py` (substituição do caminho de tag no
`/similares`, rotas novas, init), novo módulo H2/H3, novo módulo de banco,
`Dockerfile`/`README.md`, `sequencia.js`, `sequencia.html`, `tests/`,
`AGENTS.md`. `musica.py` só é lido; `requirements.txt` não muda.

### 3.9 Questões abertas (1–12)

| # | Pergunta | Resposta nesta proposta |
|---:|---|---|
| 1 | Definição de “a sequência aparece” | H2 contígua ordenada por padrão; H3 subsequência ordenada opcional; minúsculas; repetição literal; sem normalização enarmônica. |
| 2 | Critério de regressão das 6 | Não preserva igualdade; exige `tag_set ⊆ live_set` + delta exato (H2: 667/920/3.106/91/1.032/129) e aprovação explícita. |
| 3 | `cifra` ou `acordes` | `Musica.cifra` (`musica.py:16`) para H2/H3; `acordes` fora. |
| 4 | Normalizações | Minúsculas, `trim`, remover vazios; sem enarmônicos/sufixos; não filtrar não acordais no baseline; desconhecido aceito; vazio → 400. |
| 5 | Desempenho, tamanho e pré-cálculo | H2 ~0,3 s e H3 ~0,13 s no host; ao vivo; sem pré-cálculo; paginação; medir no container. |
| 6 | Banco e persistência | SQLite stdlib; `/app/var/sequences.db`; volume nomeado para `docker rm`. |
| 7 | Esquema, seed e migrações | Tabela com `match_mode` `contiguous`/`subsequence`, `canonical` único, `legacy_key`; seed 0–5 em H2; `user_version=1`. |
| 8 | Contrato da API | `GET/POST /sequencias`, `GET /similares?sequencia_id=`; `match_mode` opcional; 200/201/400/409; `json.dumps`. |
| 9 | Frontend: catálogo e cadastro | XHR; seletor de modo; formulário + POST; estados; sem render no servidor. |
| 10 | Paginação, ordem, cores, `index`, gêneros | Paginação obrigatória; remover `orderBy` global; paleta fixa; remover `index`; manter `GENEROS`. |
| 11 | Testes mínimos | Unitários H2/H3, inclusão + delta das 6, dourados, banco/restart, API, frontend e latência. |
| 12 | Tratamento do CSV | Parser intocado; cifra vazia sem match; caixa na comparação; não acordais não filtrados no baseline; primeira linha/`NA` fora de escopo. |

---

## Comparação rápida (sem vencedor)

| Critério | P1 — H1 unificado | P2 — Híbrido | P3 — H2/H3 unificado |
|---|---|---|---|
| Resultado das 6 | Exato (FP=0/FN=0) | Exato (caminho de tag intacto) | Superconjunto; muda os resultados |
| Semântica | Uma, mas pouco intuitiva | Duas: tag histórica + H2 | Uma (H2) + modo H3 |
| Recall para novas | Baixo | Alto | Alto |
| Complexidade de backend | Baixa/média | Média (dispatch) | Média (dois modos) |
| Custo por busca | ~0,3 s | ~5 ms (6) e ~0,3 s (novas) | ~0,3 s (H2) e ~0,13 s (H3) |
| Volume de resultados | Baixo | Alto para novas | Muito alto |
| Paginação na UI | Necessária | Muito necessária | Imprescindível |
| Risco de regressão | Baixo | Baixo | Alto (exige aprovação) |
| Esforço de testes | Médio | Médio/alto | Alto |

A leitura da tabela depende do critério que o time priorizar: aderência estrita
ao requisito das 6 (P1/P2), consistência semântica (P1/P3) ou intuitividade para
sequências novas (P2/P3). Nenhuma combinação vence em todos os critérios; por
isso a decisão fica para a fase de proposta.

## Lacunas de pesquisa e pré-requisitos

A pesquisa não responde diretamente a estes pontos; eles precisam de
experimento ou decisão antes da implementação:

1. **Latência no container:** o benchmark foi no host (Python 3.14). Medir H1,
   H2 e H3 no `python:3.9-slim` com gunicorn e o CSV real.
2. **Semântica de volume:** testar `docker restart`, `docker rm` e recriação com
   volume nomeado/anônimo neste `Dockerfile`; confirmar a matriz de persistência.
3. **Ordem determinística:** a ordem atual varia por causa do `set` de gêneros
   (`main.py:38,92`; `01-research.md:275-288`). Se o critério de regressão exigir
   ordem, é preciso antes tornar a ordenação determinística — mudança separada.
4. **Equivalência H1 × tag em casos de borda:** a igualdade foi medida só para as
   6; testar músicas com `|`, espaços, tokens vazios e tokens não acordais.
5. **Comportamento do AngularJS 1.4.9:** validar `$http.post` JSON, formulário,
   estados de erro e paginação no browser; não há suíte JS.
6. **Política de duplicatas e validação:** decidir se acorde desconhecido é aceito
   (proposta atual) ou rejeitado contra o vocabulário de `main.py:39,77-78`;
   decidir limite de acordes e de nome.
7. **Abuso do catálogo aberto:** sem login, qualquer pessoa pode criar sequências;
   rate limiting, moderação e limpeza ficam fora do escopo, mas são risco real.
8. **Concorrência SQLite:** testar POSTs simultâneos com um e com múltiplos
   workers de gunicorn; WAL/`busy_timeout` devem bastar, mas não foi medido.
9. **Migração/backup:** não há estratégia de backup do arquivo SQLite nem de
   migração versionada além de `user_version`; decidir antes de produção.
10. **Golden sets:** gerar e versionar os conjuntos esperados das 6 para P2/P3
    (H2/H3), incluindo hashes, para que a regressão não dependa de recalcular tudo
    a cada execução.

## Fora de escopo (nas três propostas)

- Migrar músicas/gêneros para o banco (`00-enunciado.md:60-62`).
- Serviço externo de banco, fila, cache distribuído ou múltiplos containers
  (`00-enunciado.md:63-65`).
- Editar/remover sequências, autenticação, moderação, rate limiting e CSRF.
- Trocar `GENEROS` por `GET /generos` (`main.py:158-160`; `app.js:6-58`).
- Renderizar o catálogo no servidor em vez de XHR.
- Modernizar AngularJS ou introduzir build step.
- Corrigir o parser do CSV (primeira linha pulada, `replace('NA','')` global) ou
  normalizar enarmônicos/sufixos.
- Pré-computar/armazenar matches por sequência ou cachear resultados.
