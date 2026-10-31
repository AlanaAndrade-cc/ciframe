# Proposta — Sequências de Acordes Customizadas

> Com base na pesquisa, declare a abordagem escolhida e por quê. Esta fase é sobre
> decidir, não sobre implementar. Apague este bloco de instruções antes de
> entregar.

## Abordagem escolhida

**Híbrido, como etapa de adaptação:** as 6 sequências originais continuam no
caminho de tag pré-computada, que é o comportamento histórico e equivale a H1
para elas; sequências novas usam H2 (contígua ordenada) ao vivo. O objetivo não
é eleger H2 como regra definitiva agora, e sim congelar o legado, experimentar
H2 apenas no catálogo novo e permitir que uma decisão futura migre as 6 sem
reescrever o sistema — o modo de matching fica gravado por linha no catálogo.

Duas precisões que valem para todo o documento:

- As 6 **não** passam a usar H1 ao vivo. Elas continuam usando
  `str(id_seq) in musica.seqs_famosas` (`main.py:203-223`). H1 é a regra que
  reproduz exatamente essas tags para as 6, com 0 falsos positivos e 0 falsos
  negativos (`01-research.md:865-874`); é essa equivalência que garante a
  regressão, não uma reimplementação de H1.
- A migração das 6 para H2 **não** faz parte desta entrega. Ela é uma evolução
  possível, que muda os resultados das 6 e por isso exigirá nova decisão
  explícita; o esquema desta proposta apenas deixa o caminho aberto.

### Algoritmo de matching

A regra é escolhida por linha do catálogo (`match_mode`), não inferida do id.

**Modo `tag` — ids 0–5 (originais):**

- Exatamente o caminho atual: `str(id_seq) in musica.seqs_famosas`
  (`main.py:203-223`), com `apply_filtro` (`main.py:266-272`) e paginação de 100
  (`main.py:35,226-228`).
- Nenhum recálculo, nenhuma normalização nova. A tag vem do CSV (`main.py:63`) e
  é tratada como dado estável.
- Resultado esperado, idêntico ao de hoje:

| Sequência | Id | Músicas |
|---|---:|---:|
| `BmGDA` | 0 | 199 |
| `CGAmF` | 1 | 296 |
| `EmG` | 2 | 4 |
| `CA7DmG7` | 3 | 5 |
| `GmF` | 4 | 7 |
| `CC7FFm` | 5 | 3 |

**Modo `contiguous` — sequências novas (H2):**

- A sequência aparece como **janela consecutiva e ordenada** em `Musica.cifra`
  (`musica.py:16`), que preserva ordem e repetição.
- Acordes antes ou depois da janela são permitidos. Um acorde de passagem
  **entre** dois acordes da sequência quebra o match.
- A ordem importa: `G, D, A` não casa com uma sequência `Bm, G, D, A`.
- Repetição é literal e consecutiva: `A, A, B` exige dois `A` seguidos. Não há
  colapso de runs (H8 descartado). Repetições na música são apenas ocorrências.
- Normalização: `trim`, minúsculas **na comparação** (a grafia original é
  preservada para exibição) e descarte de tokens vazios. Não há normalização
  enarmônica (`C#` ≠ `Db`), remoção de sufixos, unificação de grafias nem
  filtro de tokens não acordais.
- Acorde desconhecido é aceito e pode simplesmente devolver 0 resultados.
  Sequência vazia ou só com espaços → HTTP 400. Vírgula, ponto e vírgula ou
  espaço dentro de um token → 400 (a vírgula é separador no contrato legado,
  `main.py:191`).
- Limites: 1 a 32 acordes por sequência; nome de 1 a 80 caracteres. São
  decisões de produto, não achados da pesquisa.
- `Musica.acordes` (`musica.py:17`) **não** é usado: é `list(set(cifra))` e
  perde ordem e repetição.

**Dispatch e duplicatas:**

- O backend lê `match_mode` da linha e chama o caminho correspondente. Um modo
  inválido é erro de dados, não fallback silencioso.
- A chave canônica (tokens minúsculos, na ordem) é única em todo o catálogo,
  independentemente do modo. Recadastrar a mesma lista ordenada em qualquer
  caixa retorna 409.
- Consequência aceita: não é possível registrar um "gêmeo" H2 de uma sequência
  original pelo catálogo público. Comparar H2 com o comportamento das 6 é uma
  medição offline (as contagens já existem em `01-research.md:865-874`) ou um
  experimento com flag, não um cadastro.

**Critério de regressão:** igualdade exata de conjunto de músicas para cada id
0–5 contra as tags atuais, incluindo as contagens por página (100+99, 100+100+96,
4, 5, 7, 3). A ordem **não** é comparada: ela varia entre processos por causa do
`set` de gêneros (`main.py:38,92`; `01-research.md:275-288`). Tornar a ordem
determinística é mudança separada, fora desta proposta.

### Banco de dados

**SQLite em arquivo**, usando `sqlite3` da biblioteca padrão do Python 3.9.

- **Por quê:** atende ao requisito de persistência com transações e schema, sem
  serviço externo e sem nova dependência (`requirements.txt:4-5`). É o candidato
  de menor atrito no container único (`00-enunciado.md:63-65`;
  `docs/adr/0001-local-only-docker-deploy.md`).
- **Onde:** `/app/var/sequences.db`, fora de `/app/data`, que contém o CSV
  copiado em `Dockerfile:8`. Um volume montado em `/app/data` não deve arriscar
  esconder o CSV.
- **Persistência:** o arquivo sobrevive a `docker restart` pela camada gravável.
  Para sobreviver a `docker rm` e recriação, o README passa a documentar volume
  nomeado: `docker run -p 8080:8080 -v deciframe-data:/app/var ciframe`. Declarar
  `VOLUME` no `Dockerfile` é opcional; o requisito é atendido pelo volume
  nomeado. Sem volume, a perda em `docker rm` é esperada e documentada.
- **Inicialização:** o schema e o seed são criados no mesmo fluxo de import de
  `main.py` que já carrega o CSV (`main.py:49-98`), pois o gunicorn importa
  `main:app` (`Dockerfile:12`). O `Dockerfile` cria `/app/var`.
- **Concorrência:** `journal_mode=WAL` e `busy_timeout`; o gunicorn atual não
  fixa `--workers` (`Dockerfile:12`), então o cenário padrão é um worker.
- **Fora:** serviço externo, múltiplos containers, ORM e framework de migração.

### Esquema de dados (alto nível)

Uma única tabela, porque o catálogo é pequeno e a ordem dos acordes cabe em um
campo JSON:

| Campo | Papel |
|---|---|
| `id` | Chave primária; 0–5 reservados para as originais. |
| `nome` | Nome exibido da sequência (1–80 caracteres). |
| `acordes` | Lista JSON ordenada, preservando repetição; é a fonte da chave canônica e da exibição. |
| `canonical` | Chave única: tokens minúsculos unidos por um separador que não aparece em acorde; impede duplicatas entre modos e caixas. |
| `legacy_key` | `BmGDA`, `CGAmF`, etc. para as 6; `NULL` para novas. Mantém o parâmetro legado e o vínculo com as tags. |
| `match_mode` | `tag` para ids 0–5; `contiguous` para novas. É o que permite a migração futura ser mudança de dado. |
| `created_at` | Data de criação, para ordenação estável e auditoria simples. |

- **Seed:** as 6 são inseridas de forma idempotente com ids 0–5,
  `match_mode='tag'` e `legacy_key` preenchido. O dicionário `sequencias` de
  `main.py:40-45` deixa de ser fonte de verdade; no startup, os dois são
  conferidos para evitar divergência silenciosa.
- **Sem tabela filha de acordes:** não há consulta relacional por acorde; a
  ordem e a repetição são mais simples em JSON. Migrations e versionamento de
  schema ficam para o plano, não para esta proposta.

### API

Todas as respostas continuam `json.dumps(...)` como string, com
`Content-Type: text/html`; **não** usar `jsonify` (`00-enunciado.md:68`;
`main.py:197,201`).

| Método | Rota | Entrada | Saída | Status |
|---|---|---|---|---|
| GET | `/sequencias` | — | lista do catálogo com `id`, `nome`, `acordes`, `match_mode`/origem | 200 |
| POST | `/sequencias` | JSON `{nome, acordes: [...]}` | sequência criada, sempre `contiguous` | 201, 400, 409 |
| GET | `/similares?sequencia_id=<id>` | — | mesmas músicas/objetos de hoje (`main.py:210-220`) | 200; id desconhecido → `[]` |
| GET | `/similares?sequencia=<legacy_key>` | string legada | mesmas músicas de hoje | 200; desconhecida → `[]` |

- **Listagem:** ordenada por `id` crescente, para as originais aparecerem
  primeiro e a UI ter ordem estável.
- **Criação:** o cliente não escolhe `match_mode`; o servidor grava
  `contiguous`. Criar `tag` pelo POST fica fora de escopo.
- **Validação:** `nome` obrigatório, `trim`, 1–80 caracteres; `acordes` lista de
  1–32 strings, cada uma com `trim`, 1–16 caracteres, sem vírgula, ponto e
  vírgula ou espaço. Corpo inválido → 400 com `json.dumps({"erro": "..."})`.
- **Duplicata:** mesma chave canônica → 409, com `id` e `nome` existentes.
- **Compatibilidade:** `sequencia=` continua funcionando apenas para as 6
  (resolve por `legacy_key`); o frontend passa a usar `sequencia_id` para todas.
  Um id desconhecido devolve `[]` com 200, como hoje.
- **Fora:** editar, remover, autenticação, moderação e rate limiting. O catálogo
  é aberto e anônimo (`00-enunciado.md:47-48`); remoção por qualquer visitante
  seria destrutiva.

### Frontend

A página `#/porsequencia` passa a refletir o catálogo real e a permitir cadastro,
mantendo AngularJS 1.4.9 e sem build (`docs/adr/0003-lift-frontend-freeze.md`).

- **Catálogo:** remove os quatro objetos fixos de
  `static/assets/js/controllers/sequencia.js:2-37` e carrega `GET /sequencias`
  por `$http`. Estados de carregando, erro e vazio; `ng-repeat` do template
  (`static/templates/sequencia.html:5-8`) continua servindo.
- **Origem visível:** cada item mostra um selo `original`/`nova` derivado de
  `match_mode`/`legacy_key`, com uma explicação curta de que as originais usam a
  marcação histórica e as novas usam correspondência contígua. Sem isso, a
  diferença de volume (199 vs. centenas) parece bug.
- **Busca:** `pesquisarPorSequencia` envia `similares?sequencia_id=<id>`, mantém
  `&generos=` e acrescenta `&pagina=` (`sequencia.js:55-61,72-77`).
- **Cadastro:** formulário com `nome` e lista editável de acordes
  (adicionar/remover), `POST /sequencias`, mensagens de 400/409, botão
  desabilitado durante o envio e recarga do catálogo em caso de sucesso.
- **Paginação:** controles anterior/próxima e estado `pagina`; `data.length ===
  100` como heurística de "tem próxima", já que o backend não devolve total.
  Necessário porque H2 pode retornar milhares (por exemplo `Em,G` → 3.110).
- **Ordem, cores e `index`:** remover `orderBy:'-popularidade'` global
  (`sequencia.html:42`), que só ordena a página; usar paleta fixa no frontend e
  remover o `index` sempre `1` (`sequencia.js:3,11,19,25`).
- **Gêneros:** `GENEROS` continua fixo (`sequencia.js:43`;
  `static/assets/js/app.js:6-58`); trocar por `GET /generos` fica fora de escopo.
- **Servir pelo Flask:** validar em `http://localhost:8080`, não por `file://`
  (`main.py:101-103`).

## Alternativas consideradas e descartadas

1. **H1 unificado ao vivo (Proposta 1).** Preservaria as 6 com uma única regra,
   mas H1 é um artefato do gerador de tags: qualquer acorde extra na música
   desqualifica, e o recall para sequências novas é baixíssimo (`Em,G` retorna
   4 músicas, contra 3.110 em H2). Além disso, exigiria provar a equivalência
   H1 × tag em casos de borda (`|`, espaços, tokens vazios) que a pesquisa só
   mediu para as 6 (`01-research.md:942-944`). Seria fiel ao legado e ruim como
   produto para o catálogo novo.

2. **H2/H3 unificado (Proposta 3).** É a semântica mais intuitiva, mas muda os
   resultados das 6 — `BmGDA` passaria de 199 para 866 em H2 e 4.763 em H3 — e
   viola diretamente `00-enunciado.md:66-67`. H3, além disso, tem precisão baixa
   para sequências curtas (`Em,G` → 13.643). Só seria aceitável com uma
   reinterpretação explícita do requisito, o que não é o caso nesta entrega.

3. **H3 como padrão para as novas.** Descartado por precisão: tolera acordes
   espalhados pela música e transforma sequências curtas em quase "qualquer
   música". H2 é o meio-termo intuitivo; H3 pode voltar como modo opcional no
   futuro, com decisão própria.

4. **H4/H6/H7 (conjunto/multiconjunto).** Ignoram ordem ou repetição, que é
   justamente o que define uma sequência; H7 perde quase todas as tags
   (`01-research.md:865-874`). Não servem como regra de descoberta.

5. **JSON em arquivo, TinyDB, DuckDB ou PostgreSQL.** JSON não tem transações
   nem unicidade declarativa; TinyDB e DuckDB adicionam dependência e wheel
   binária sem necessidade para dezenas de registros; PostgreSQL exige serviço
   externo e conflita com o container único (`00-enunciado.md:63-65`).

6. **Frontend hardcoded alinhado às 6, sem cadastro.** Menor mudança, mas
   mantém duas fontes de verdade, não reflete o catálogo real e não atende ao
   requisito de cadastro (`00-enunciado.md:54-55`).

7. **Renderizar o catálogo no servidor.** Evitaria o XHR inicial, mas acoplaria
   template e Flask; o controller Angular continuaria precisando dos dados para
   cadastrar e atualizar a lista.

## Escopo explícito

**Dentro do escopo:**

- Matching híbrido: caminho de tag preservado para os ids 0–5; H2 ao vivo para
  sequências novas, com `match_mode` por linha.
- Catálogo de sequências em SQLite, com seed idempotente das 6, chave canônica
  única e persistência via volume nomeado documentado.
- Endpoints `GET /sequencias`, `POST /sequencias` e
  `GET /similares?sequencia_id=`, com o parâmetro legado `sequencia=` mantido
  para as 6; respostas em `json.dumps`.
- Frontend `#/porsequencia` lendo o catálogo, exibindo origem, cadastrando
  sequência nova e paginando resultados.
- Testes de regressão exata das 6, unitários de H2, persistência
  restart/recriação, contrato da API e smoke test no browser; comando
  `python3 -m unittest discover -s tests -v` documentado no `AGENTS.md`.
- Atualização do `README.md` com o comando de execução usando volume nomeado.

**Fora do escopo (e por quê):**

- **Aplicar H2 às 6 originais.** É a evolução futura, não esta entrega: mudaria
  os resultados das 6 e exige nova decisão explícita. O esquema deixa o caminho
  aberto, mas não o percorre.
- **Editar ou remover sequências.** O catálogo é anônimo e sem autenticação;
  exclusão por qualquer visitante seria destrutiva. Fica para quando houver
  moderação/autoria.
- **Autenticação, moderação, rate limiting e CSRF.** O requisito é catálogo
  aberto e anônimo; os riscos de abuso são aceitos nesta fase.
- **Migrar músicas/gêneros para o banco.** O catálogo de músicas e gêneros
  continua no CSV em memória (`00-enunciado.md:60-62`).
- **Serviço externo de banco, fila, cache distribuído ou múltiplos containers.**
  Conflita com o deploy local de container único
  (`docs/adr/0001-local-only-docker-deploy.md`).
- **Trocar `GENEROS` por `GET /generos`.** Existe endpoint, mas a página nunca o
  usou; mudança independente e sem relação com o cadastro.
- **Renderizar o catálogo no servidor.** A página continua consumindo a API.
- **Modernizar AngularJS ou introduzir build step.** O stack permanece o mesmo
  (`docs/adr/0003-lift-frontend-freeze.md`).
- **Corrigir o parser do CSV** (primeira linha pulada, `replace('NA','')`
  global) ou normalizar enarmônicos/sufixos. São comportamentos pré-existentes;
  mudá-los alteraria resultados e mascararia a regressão.
- **Pré-computar ou cachear matches por sequência.** O catálogo é pequeno e a
  medição no container ainda não existe; otimização sem evidência fica para
  depois.
- **Framework de migração e política de backup.** O plano cobre a evolução do
  schema; backup/migração versionada não é requisito desta entrega.

## Questões abertas resolvidas

| # | Questão | Decisão |
|---:|---|---|
| 1 | Definição de "a sequência aparece" | Duas regras por modo: `tag` para ids 0–5 (equivalente a H1, sem recálculo) e H2 contígua ordenada para novas. Ordem e adjacência importam; acorde de passagem quebra H2; repetição é literal. |
| 2 | Critério de regressão das 6 | Igualdade exata de conjunto e de contagens por página contra as tags (199/296/4/5/7/3). Não é "superconjunto"; ordem não é comparada. |
| 3 | `cifra` ou `acordes` | `Musica.cifra` (`musica.py:16`) para H2; `seqs_famosas` para as 6; `Musica.acordes` (`musica.py:17`) descartado por perder ordem e repetição. |
| 4 | Normalizações | `trim`, minúsculas na comparação, descarte de vazios; sem enarmônicos, sufixos ou filtro de não acordais; desconhecido aceito; vazio → 400; vírgula/ponto e vírgula/espaço no token → 400. |
| 5 | Desempenho, tamanho e pré-cálculo | Busca ao vivo; ~0,3 s por consulta H2 e ~5 ms no caminho de tag, medidos no host, a confirmar no container. Catálogo pequeno; sem pré-cálculo, cache ou índice nesta fase. Limite de tamanho do catálogo: fora de escopo, revisar com uso real. |
| 6 | Banco e persistência | SQLite em arquivo, `/app/var/sequences.db`; sobrevive a `docker restart`; `docker rm` exige volume nomeado documentado. `VOLUME` opcional; não montar sobre `/app/data`. |
| 7 | Modelagem, seed e migrações | Tabela única com `acordes` JSON, `canonical` único, `legacy_key` e `match_mode`; seed idempotente 0–5; versionamento de schema fica para o plano, sem ORM. |
| 8 | Contrato da API | `GET/POST /sequencias` e `GET /similares?sequencia_id=`; 200/201/400/409; erros `{"erro": ...}`; lista por `id`; sem edição/remoção; `json.dumps` e `text/html` preservados; `sequencia=` legado só para as 6. |
| 9 | Carregamento do catálogo no frontend | XHR em `#/porsequencia`, com estados carregando/erro/vazio; a página lista e cadastra; sem render no servidor e sem fallback hardcoded. |
| 10 | Paginação, ordem, cores, `index`, gêneros | Paginação obrigatória com `pagina`; remover `orderBy` global; paleta fixa no frontend; remover `index`; `GENEROS` continua fixo; `/generos` fora de escopo. |
| 11 | Testes mínimos | Regressão exata das 6, unitários de H2 (ordem, passagem, repetição, caixa, vazio, desconhecido), persistência restart/recriação, contrato da API, smoke no browser e medição de latência no container. |
| 12 | Tratamento do CSV | Parser intocado; cifra vazia não casa; caixa normalizada só na comparação; tokens não acordais não filtrados; primeira linha e `replace('NA','')` são pré-existentes e ficam fora de escopo. |
