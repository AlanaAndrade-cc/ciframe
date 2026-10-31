# Pesquisa — Sequências de Acordes Customizadas

> Preencha esta fase antes de propor qualquer solução. O objetivo é investigar as
> perguntas abaixo com evidência real (código, dados, testes rápidos que você mesmo
> rodou), não chutar. Apague este bloco de instruções antes de entregar.

## Perguntas que você precisa responder

1. **Algoritmo de matching**: hoje, as 6 sequências hardcoded em `main.py` (linhas
   40-45) são comparadas contra músicas via uma tag pré-computada
   (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário
   não têm essa tag — o matching precisa ser calculado em tempo real a partir da
   lista de acordes de cada música (`musica.acordes`/`musica.cifra`). O que vai
   definir "a sequência X aparece na música Y"? A ordem dos acordes importa?
   Repetições de acorde dentro da música importam? É preciso normalizar (ex.:
   maiúsculas/minúsculas, variações de escrita do mesmo acorde)?
2. **Validação da hipótese**: rode o algoritmo que você está considerando contra os
   dados reais em `data/top/dataset_final.csv`, para as 6 sequências hoje
   hardcoded, e confirme (ou refute) que ele reproduz os mesmos matches que o
   código atual produz via `seqs_famosas`. Esse é o bar mínimo de correção que
   você vai usar na fase de testes.
3. **Banco de dados**: quais bancos embarcados (sem serviço externo adicional) são
   viáveis dentro do container Docker único e local-only já documentado em
   `docs/adr/0001-local-only-docker-deploy.md`? O que cada opção implica para o
   `Dockerfile` atual e para a persistência dos dados entre reinícios do
   container?
4. **Frontend existente**: o que a página `#/porsequencia`
   (`static/templates/sequencia.html` +
   `static/assets/js/controllers/sequencia.js`) já faz? Repare que ela tem hoje uma
   lista *hardcoded no JavaScript* de 4 sequências (`sequencia1`..`sequencia4`),
   diferente das 6 que existem no backend — um detalhe real e pré-existente do
   código, não um erro seu, que vale entender antes de decidir o que precisa
   mudar.

## Registro das descobertas

> Estado observado no commit `749bc21da9f8d19cbfff25a46e1ac789ce5bb125`. Nenhum
> arquivo de `main.py`, `musica.py`, `data/` ou `scripts/` foi alterado durante a
> pesquisa. Os scripts descartáveis usados para caracterizar os dados ficaram em
> `/tmp` (`tag_summary.py`, `tag_semantics.py`, `q2_report.py`, `chord_vocab.py`).
> O servidor Flask foi executado a partir de uma venv descartável em
> `/tmp/deciframe-venv` e encerrado ao final.
>
> O HEAD atual (`bb6c785`) apenas acrescenta o template de feedback RePPIT; o
> código observado continua sendo o de `749bc21`. A segunda passagem acrescentou
> os scripts descartáveis `/tmp/hypotheses_metrics.py` e
> `/tmp/extra_metrics.py`, com saídas em `/tmp/hypotheses_metrics.out` e
> `/tmp/extra_metrics.out`.

### 1. Algoritmo de matching hoje

#### 1.1 Fluxo de uma busca por sequência

- A rota é `GET /similares` (`main.py:170-201`). Os parâmetros lidos são
  `acordes`, `id_unico_musica`, `sequencia`, `pagina` e `generos`
  (`main.py:172-182`).
- Quando `sequencia` está presente, o backend remove todas as vírgulas com
  `sequencia_tag.replace(',','')` (`main.py:191`) e faz uma busca exata no
  dicionário literal `sequencias` (`main.py:40-45`, consultado em
  `main.py:194`). Se a chave existir, chama
  `get_similares_por_sequencia(id_seq, generos_key)` (`main.py:195-196`); se não
  existir, `similares` permanece `[]` e a resposta é `[]`
  (`main.py:192,197`).
- O ramo de sequência está em um `elif` (`main.py:185-197`): quando
  `sequencia` é usada, os parâmetros `acordes` e `id_unico_musica` não são
  consultados.
- `get_similares_por_sequencia` (`main.py:203-223`) percorre
  `apply_filtro(musicas.values(), generos_key)` (`main.py:205`) e seleciona a
  música quando `str(id_seq) in musica.seqs_famosas` (`main.py:209`). É
  comparação exata de string contra a lista de tags da música, não uma varredura
  de `musica.cifra` nem de `musica.acordes`.
- O resultado de sequência contém `id_unico_musica`, `id_artista`,
  `id_musica`, `nome_artista`, `nome_musica`, `popularidade`, `acordes`,
  `genero` e `url` (`main.py:210-220`); não contém `diferenca` nem `intersecao`.
- A paginação é um slice de `TAM_PAGINA = 100` (`main.py:35`, `main.py:226-228`),
  aplicado depois do filtro (`main.py:196`).
- O filtro de gênero usa `generos_tag.split(',')` ou todos os gêneros
  (`main.py:178-182`) e `apply_filtro` concatena as listas de
  `genero_musicas` (`main.py:266-272`).
- A resposta é `json.dumps(...)` (`main.py:197`), portanto sai com
  `Content-Type: text/html` (verificado com `curl -D -`).

#### 1.2 De onde vêm as tags `seqs_famosas`

- No carregamento do CSV, a coluna 7 (`SEQ_FAMOSA`, `main.py:33`) é dividida por
  `;` (`main.py:63`) e entregue ao construtor de `Musica`
  (`main.py:69-72`); `Musica` apenas guarda a lista em `self.seqs_famosas`
  (`musica.py:18`).
- As tags não são recalculadas em tempo de requisição. O cálculo offline está em
  `scripts/generate_data_set.py:7-24`: a lista `seqs` contém as seis sequências
  em minúsculas separadas por `;` (`scripts/generate_data_set.py:8`); o código
  lowercasa a string inteira de acordes da música (`scripts/generate_data_set.py:12`),
  testa `if s in acorde` (`scripts/generate_data_set.py:13`) e depois percorre
  os tokens da música, exigindo que cada um pertença ao conjunto de acordes da
  sequência (`scripts/generate_data_set.py:16-20`); o índice da sequência é
  convertido em string e acumulado (`scripts/generate_data_set.py:21-23`).
  A releitura do laço é importante: `l` é um acorde da música e `tokens` é a
  sequência; portanto a tag não exige apenas a ocorrência contígua, mas também
  que a música não tenha nenhum acorde fora do vocabulário da sequência. Essa
  condição é reproduzida e medida em §2.3.
- Na geração do CSV, `famosas = ''.join(get_famosas(str_notas))`
  (`scripts/generate_data_set.py:86-88`) concatena os índices sem separador. Se
  mais de uma sequência casasse, o resultado seria algo como `"01"`, e
  `main.py:63` o transformaria em um único token `"01"`, não em `"0"` e `"1"`.
  No CSV atual não existe nenhum token multi-dígito: os valores distintos são
  `''`, `'0'`, `'1'`, `'2'`, `'3'`, `'4'`, `'5'` (ver §2.1).
- O script gera a coluna a partir de `str_notas`
  (`scripts/generate_data_set.py:70-74,89`), que é a mesma sequência de acordes
  exportada como coluna `CIFRA` (`main.py:34`). Apesar disso, as tags presentes
  no CSV não equivalem a uma varredura contígua ao vivo da `cifra` atual: toda
  música com tag contém o padrão como subsequência contígua e ordenada da
  `cifra` em minúsculas, mas há muito mais músicas com essa ocorrência contígua
  do que músicas com tag (números em §2.2).

#### 1.3 Representações de acordes disponíveis no runtime

- `Musica.cifra` é a lista ordenada de acordes, preservando repetições
  (`musica.py:16`).
- `Musica.acordes` é `list(set(cifra))` (`musica.py:17`): remove duplicatas e
  perde ordem e repetição.
- `limpa_cifra` (`main.py:11-23`) percorre os tokens separados por `;`
  (`main.py:59`), descarta tokens vazios (`main.py:14`), para tokens com `|`
  pega o texto antes do primeiro `|` e o primeiro token separado por espaço
  (`main.py:16-18`), e para os demais divide por espaço (`main.py:20-22`).
  Não há lowercasing, normalização enarmônica, remoção de sufixos ou deduplicação
  nessa função.
- O parser do CSV (`main.py:49-74`) pula a primeira linha (`main.py:50`), aplica
  `replace('"','').replace('NA','')[:-1]` na linha inteira (`main.py:53`),
  divide por vírgula (`main.py:55`), converte popularidade (`main.py:56`),
  processa a cifra (`main.py:58-61`) e divide a coluna de tags por `;`
  (`main.py:63`). O `replace('NA','')` é global na linha.
- O vocabulário de acordes observado no CSV tem 6.653 tokens distintos e
  3.505.331 ocorrências. Desses tokens, 4.015 têm alguma letra minúscula, 2.713
  são totalmente maiúsculos, 3.808 contêm `/`, 2.170 contêm `#`, 1.972 contêm
  `b`, 2.278 contêm parênteses e nenhum contém espaço. Há colisões de caixa como
  `Am7`/`AM7`, `Cm7`/`CM7`, `G/B`/`G/b` e `C#m7`/`C#M7`. Há também pares
  enarmônicos com contagens diferentes: `C#` 23.911 vs. `Db` 4.090, `D#` 12.147
  vs. `Eb` 23.626, `F#` 49.300 vs. `Gb` 1.407, `G#` 21.349 vs. `Ab` 12.259,
  `A#` 10.135 vs. `Bb` 59.759. O vocabulário inclui tokens não acordais como
  `1a.vez`, `2x`, `:`, `4`, `11`, `13)`.
- Como `musica.acordes` usa igualdade exata de string em um `set`, variações de
  caixa e de grafia são tokens diferentes nessa estrutura. `musica.cifra`
  mantém a grafia original e a ordem.

#### 1.4 O que existe hoje em termos de normalização/validação da sequência

- A única transformação da sequência recebida é a remoção de vírgulas
  (`main.py:191`); não há trim de espaços, lowercasing, normalização
  enarmônica, remoção de sufixos ou tratamento de duplicatas.
- A chave precisa bater exatamente com uma das seis strings de `main.py:40-45`.
  Uma sequência desconhecida retorna `[]` com HTTP 200 (verificado).
- Não existe endpoint de criação, listagem ou validação de sequências. O
  catálogo é o literal `sequencias` (`main.py:40-45`).
- Não existe banco de dados, esquema, migração ou arquivo de persistência para
  sequências no repositório.

#### 1.5 Hipóteses candidatas de matching (Q1)

As hipóteses abaixo são regras possíveis; nenhuma foi escolhida. Salvo indicação
contrária, a comparação é feita sobre `musica.cifra` (`musica.py:16`) com tokens
em minúsculas, e a sequência é uma lista ordenada de tokens. A representação
`musica.acordes` (`musica.py:17`) só permite regras sem ordem e sem repetição,
porque é `list(set(cifra))`.

| # | Hipótese | O que casaria | Casos de borda | Como validar contra as tags |
|---|---|---|---|---|
| H1 | **Tag-like / legado** | A sequência aparece como bloco contíguo **e** todo acorde da música pertence ao vocabulário da sequência. É a condição que o gerador de tags tenta expressar (`scripts/generate_data_set.py:12-20`). | Qualquer acorde extra na música desqualifica, mesmo que a sequência apareça; repetições de acordes da sequência são permitidas; a ordem e a adjacência importam. | É a única hipótese testada que reproduz exatamente as tags das 6 sequências (FP=0, FN=0 em §2.3). |
| H2 | **Contígua ordenada** | A sequência aparece como uma janela consecutiva de `musica.cifra`, na ordem dada; acordes antes ou depois da janela são permitidos. | Um acorde de passagem entre dois acordes da sequência quebra o match; a sequência pode aparecer mais de uma vez; repetição dentro da janela conta. | Contém todas as músicas com tag, mas adiciona centenas ou milhares de falsos positivos (§2.3). |
| H3 | **Subsequência ordenada** | Os acordes da sequência aparecem na ordem dada, mas não precisam ser consecutivos; outros acordes podem ficar entre eles. | Aceita uma sequência “espalhada” pela música; a ordem ainda importa; repetições da música podem ser usadas como parte da subsequência. | Contém todas as tags e amplia muito o conjunto; mede o custo de ignorar a adjacência (§2.3). |
| H4 | **Inclusão de conjunto** | Todos os acordes da sequência aparecem em qualquer posição da música; usa `musica.acordes` ou um `set` da cifra. | Ignora ordem e repetição; permite acordes extras; sem normalização, `Am7` e `AM7` são tokens diferentes. | Contém todas as tags; é a hipótese mais permissiva entre as que ainda exigem todos os acordes (§2.3). |
| H5 | **Inclusão de multiconjunto** | Como H4, mas exige que a música tenha pelo menos a multiplicidade de cada acorde da sequência. | Para as 6 atuais, o resultado é igual a H4 porque nenhuma sequência repete acorde; para uma sequência com repetição, exige repetição na música. | Comparar H5 com H4; a diferença só aparece em consultas com acorde repetido, que precisam de teste sintético. |
| H6 | **Igualdade de conjunto** | O vocabulário da música é exatamente o vocabulário da sequência, em qualquer ordem. | Não exige adjacência; permite ordem trocada; ignora repetição; não permite acorde extra. | Reproduz as tags de `EmG`, `GmF` e `CC7FFm`, mas não as de `BmGDA`, `CGAmF` e `CA7DmG7` (§2.3). |
| H7 | **Igualdade de multiconjunto** | A música tem exatamente os mesmos acordes da sequência, com as mesmas multiplicidades, em qualquer ordem. | Muito restritiva; repetição e acordes extras contam; a ordem não importa. | Tem recall baixo contra as tags: a maioria das músicas com tag repete acordes ou usa acordes do vocabulário além da sequência (§2.3). |
| H8 | **Contígua com colapso de repetições imediatas** | Antes de procurar o bloco, colapsa runs consecutivos iguais (`A;A;B` vira `A;B`). | Só afeta repetições imediatas; repetições separadas continuam contando; pode unir duas ocorrências vizinhas. | Contém todas as tags; muda pouco os totais das 6 (§2.3). |

**Variações transversais às hipóteses.** Elas não são regras completas; são
decisões de normalização que podem ser combinadas com H1-H8.

| Variação | O que mudaria | Evidência atual | Como validar |
|---|---|---|---|
| Caixa (maiúsculas/minúsculas) | Comparar tokens em minúsculas ou exatamente como escritos. O gerador já lowercasa (`scripts/generate_data_set.py:12`), mas `limpa_cifra` preserva a caixa (`main.py:11-23`). | O vocabulário tem 6.653 tokens distintos e 6.500 formas em minúsculas, com 151 grupos de colisão, como `Am7`/`AM7`, `Cm7`/`CM7` e `G/B`/`G/b`. Nas 6 sequências, a contagem case-sensitive é igual à case-insensitive. | Comparar as duas contagens e usar os pares de colisão como casos sintéticos. |
| Enarmônicos | Tratar `C#`/`Db`, `D#`/`Eb`, `F#`/`Gb`, `G#`/`Ab` e `A#`/`Bb` como o mesmo acorde. | Hoje não há normalização; as contagens de cada grafia diferem (§1.3), então a escolha muda o conjunto de matches. | Criar uma tabela de equivalência e comparar os resultados com e sem ela. |
| Tokens não acordais | Filtrar tokens como `1a.vez`, `2x`, `:`, `4`, `11` e `13)` antes de procurar a sequência. | Há 13 tokens distintos sem letra e 21 músicas que os contêm (§1.3); eles podem quebrar uma janela contígua. | Medir os matches antes e depois do filtro e inspecionar as músicas afetadas. |
| Repetição | Ignorar repetições, colapsar apenas runs consecutivos ou exigir multiplicidade. | As 6 sequências não repetem acordes, então H4 e H5 coincidem; H7 perde quase todas as tags; H8 muda pouco. | Usar sequências sintéticas com acordes repetidos e músicas com repetições imediatas e separadas. |
| String bruta vs. tokens | O gerador testa a string bruta separada por `;` (`scripts/generate_data_set.py:12-20`); o runtime usa `limpa_cifra` (`main.py:11-23`), que remove vazios, lida com `\|` e separa por espaço. | Para as 6 atuais, a regra sobre a string bruta e a regra sobre tokens limpos produzem o mesmo conjunto de tags (§2.3). | Comparar as duas implementações em músicas com `\|`, espaços e tokens vazios. |
| Sequência vazia/desconhecida | Definir se vazio, só espaços, acorde inexistente ou caixa errada retornam `[]`, erro ou match vazio. | Hoje a única transformação é remover vírgulas (`main.py:191`); chave desconhecida retorna `[]` com HTTP 200. | Testar entradas vazias, com espaços, com vírgulas, com acorde inexistente e com caixa trocada. |

### 2. Validação com os dados reais (`data/top/dataset_final.csv`) — Q2

#### 2.1 Contagem por tag

O script `/tmp/q2_report.py` replica o carregamento de `main.py` (incluindo
`f.readline()` em `main.py:50`, os `replace` de `main.py:53`, o split por `,` de
`main.py:55`, o processamento de cifra de `main.py:58-61` e o split de tags de
`main.py:63`) e aplica exatamente a condição de `main.py:209`
(`str(id_seq) in musica.seqs_famosas`). Comando executado:

```bash
python3 /tmp/q2_report.py
```

Resultado bruto do resumo (`/tmp/tag_summary.py`):

```text
TOTAL loaded songs: 67585
Distinct SEQ_FAMOSA tokens: 7
Token distribution: {'': 67071, '1': 296, '0': 199, '4': 7, '3': 5, '2': 4, '5': 3}
BmGDA id=0 count=199
CGAmF id=1 count=296
EmG id=2 count=4
CA7DmG7 id=3 count=5
GmF id=4 count=7
CC7FFm id=5 count=3
```

| Sequência | `id_seq` | Matches por tag | Ocorrências contíguas na `cifra` | Subsequência (não contígua) |
|---|---:|---:|---:|---:|
| `BmGDA` | 0 | 199 | 866 | 4763 |
| `CGAmF` | 1 | 296 | 1216 | 5887 |
| `EmG` | 2 | 4 | 3110 | 13643 |
| `CA7DmG7` | 3 | 5 | 96 | 427 |
| `GmF` | 4 | 7 | 1039 | 3641 |
| `CC7FFm` | 5 | 3 | 132 | 280 |

Denominador das colunas de ocorrência: 59.444 músicas com `cifra` não vazia
(67.585 linhas carregadas menos 8.141 com cifra vazia). A coluna “contígua” usa
a lista `musica.cifra` em minúsculas e exige o padrão na ordem exata e sem
interrupção; a coluna “subsequência” exige a ordem, mas permite outros acordes
entre os acordes do padrão. Para as seis sequências, o conjunto de músicas com
tag é subconjunto estrito do conjunto com ocorrência contígua: não há nenhuma
música com tag que não tenha a ocorrência contígua, e há 667, 920, 3.106, 91,
1.032 e 129 músicas, respectivamente, com ocorrência contígua e sem tag.

Verificação ao vivo com o servidor real (`python main.py` na venv descartável,
porta 5000):

```bash
curl -s -o /tmp/seq.json -w '%{http_code}' 'http://127.0.0.1:5000/similares?sequencia=BmGDA'
curl -s 'http://127.0.0.1:5000/similares?sequencia=BmGDA&pagina=2'
curl -s 'http://127.0.0.1:5000/similares?sequencia=CGAmF&pagina=2'
curl -s 'http://127.0.0.1:5000/similares?sequencia=CGAmF&pagina=3'
curl -s 'http://127.0.0.1:5000/similares?sequencia=NOPE'
```

Resultados brutos de contagem:

```text
BmGDA          -> HTTP 200, count=100
CGAmF          -> HTTP 200, count=100
EmG            -> HTTP 200, count=4
CA7DmG7        -> HTTP 200, count=5
GmF            -> HTTP 200, count=7
CC7FFm         -> HTTP 200, count=3
Bm,G,D,A       -> HTTP 200, count=100
C,G,Am,F       -> HTTP 200, count=100
Gm,F           -> HTTP 200, count=7
C,C7,F,Fm      -> HTTP 200, count=3
NOPE           -> HTTP 200, count=0
BmGDA&pagina=1 -> HTTP 200, count=100
BmGDA&pagina=2 -> HTTP 200, count=99
BmGDA&pagina=3 -> HTTP 200, count=0
CGAmF&pagina=2 -> HTTP 200, count=100
CGAmF&pagina=3 -> HTTP 200, count=96
```

Os totais por tag (199 e 296) só aparecem completos ao percorrer as páginas;
`BmGDA` tem 100 na página 1 e 99 na página 2, e `CGAmF` tem 100 + 100 + 96.
A resposta de `BmGDA` tem `Content-Type: text/html; charset=utf-8` e o primeiro
item retornado nessa execução foi:

```json
{"id_unico_musica": "vedder-eddie_society", "id_artista": "vedder-eddie", "id_musica": "society", "nome_artista": "Eddie Vedder", "nome_musica": "Society", "popularidade": 243700, "acordes": ["A", "Bm", "G", "D"], "genero": "Folk", "url": "http://www.cifraclub.com.br/vedder-eddie/society"}
```

A ordem da lista de sequência não é popularidade global. `musicas` é ordenado
por popularidade (`main.py:87-89`) e cada lista de `genero_musicas` também
(`main.py:94-96`), mas `apply_filtro` concatena gêneros na ordem de
`generos_key` (`main.py:266-272`). Sem filtro, `generos_key` é a lista
`generos`, construída a partir de um `set` (`main.py:38,92`). Duas execuções
separadas do carregamento produziram ordens diferentes de gêneros e primeiros
resultados diferentes para `BmGDA`:

```text
run 1: generos[:8] = ['Heavy Metal', 'Rock', 'Guarânia', 'Power-Pop', 'Velha Guarda', 'Rockabilly', 'Samba', 'Surf Music']
       BmGDA first 3: [('Bon Jovi', 'Bang a drum', 10856, 'Rock'), ('Tenacious D', "I'm The Only Gay Eskimo", 3077, 'Rock'), ('Fall Out Boy', 'Disloyal Order Of Water Buffaloes', 2087, 'Rock')]
run 2: generos[:8] = ['Alternativo', 'Indie', 'Marchas/Hinos', 'Soft Rock', 'Power-Pop', 'Bolero', 'Brega', 'Sertanejo']
       BmGDA first 3: [('30 Seconds To Mars', 'City Of Angels', 16307, 'Alternativo'), ('Keane', 'With Or Without You', 5390, 'Alternativo'), ("Plain White T's", 'Fireworks', 1786, 'Indie')]
```

Com filtro de um único gênero, a ordem é a da lista daquele gênero, que é
ordenada por popularidade (`main.py:95-96`). Exemplo verificado:
`BmGDA&generos=Rock` retornou 5 músicas, começando por Bon Jovi — “Bang a drum”
(10.856), Tenacious D — “I'm The Only Gay Eskimo” (3.077) e Fall Out Boy —
“Disloyal Order Of Water Buffaloes” (2.087). `BmGDA&generos=Folk` também
retornou 5; `NOPE&generos=Rock` retornou 0.

#### 2.2 Músicas retornadas por tag

As listas abaixo foram geradas por `/tmp/q2_report.py` a partir da condição
`str(id_seq) in musica.seqs_famosas`. Para legibilidade, estão ordenadas por
popularidade decrescente e incluem o `id_unico_musica`; essa não é
necessariamente a ordem em que o endpoint pagina (ver §2.1). O total de cada
seção é o total real de músicas com a tag; o endpoint mostra no máximo 100 por
página (`main.py:35,226-228`).

##### `BmGDA` (`id_seq=0`) — 199 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Capital Inicial | À Sua Maneira | 2489447 | `capital-inicial_a-sua-maneira` |
| 2 | Gusttavo Lima | Balada (Tchê Tchê Rere) | 1219444 | `gusttavo-lima_balada-boa-tche-tche-rere` |
| 3 | João Neto e Frederico | Tá Combinado | 314696 | `joao-neto-frederico_ta-combinado` |
| 4 | Fernando e Sorocaba | Juliana | 279523 | `fernando-sorocaba_juliana` |
| 5 | Shakira | Waka Waka (This Time For Africa) | 261480 | `shakira_waka-waka` |
| 6 | Eddie Vedder | Society | 243700 | `vedder-eddie_society` |
| 7 | Maria Cecília e Rodolfo | Vou Jogar a Chave Fora | 218138 | `maria-cecilia-rodolfo_vou-jogar-chave-fora` |
| 8 | Guilherme & Santiago | Só de Você | 215440 | `guilherme-e-santiago_so-de-voce` |
| 9 | Taylor Swift | I Knew You Were Trouble | 210164 | `taylor-swift_i-knew-you-were-trouble` |
| 10 | Projota | A Rezadeira | 151677 | `projota_a-rezadeira` |
| 11 | João Bosco e Vinícius | Colo Colo | 141705 | `joao-bosco-viniciusacustico_colo-colo` |
| 12 | Hinos Avulsos CCB | Ester | 132819 | `hinos-avulsos-ccb_ester` |
| 13 | Luan Santana | À Sua Maneira | 131534 | `luan-santana_a-sua-maneira` |
| 14 | Guilherme & Santiago | Bolo Doido | 131441 | `guilherme-e-santiago_bolo-doido` |
| 15 | RBD | Enseñame | 127290 | `rbd_enseame` |
| 16 | Lucas Lucco | Pac-Man | 126940 | `lucas-lucco_pac-man` |
| 17 | Katy Perry | California Gurls | 119956 | `katy-perry_california-gurls` |
| 18 | João Neto e Frederico | Chuva de Verão | 109980 | `joao-neto-frederico_chuva-de-verao` |
| 19 | Wesley Safadão | Sou Ciumento Mesmo(Part: Fernando & Sorocaba) | 100108 | `wesley-safadao_sou-ciumento-mesmopart-fernando-e-sorocaba` |
| 20 | U2 | With or Without you (Live Elevation Tour) | 98229 | `u2_with-or-without-you-live-elevation-tour` |
| 21 | Justin Bieber | Down To Earth | 97388 | `justin-bieber_down-to-earth` |
| 22 | Leandro & Leonardo | Cumpade e Cumade | 87715 | `leandro-e-leonardo_cumpade-cumade` |
| 23 | Thaeme e Thiago | Perdeu | 78755 | `thaeme-thiago_perdeu` |
| 24 | Léo Magalhães | Alô | 75172 | `leo-magalhaes_alo` |
| 25 | Thaeme e Thiago | Arrocha | 75164 | `thaeme-thiago_arrocha` |
| 26 | Thaeme e Thiago | Tchá Tchá Tchá | 74670 | `thaeme-thiago_tcha-tcha-tcha` |
| 27 | One Direction | Live While We're Young | 74053 | `one-direction_live-while-were-young` |
| 28 | João Neto e Frederico | Enquanto o Sol Brilhar | 72603 | `joao-neto-frederico_enquanto-sol-brilhar` |
| 29 | Fernando e Sorocaba | Força de Um Furacão | 69242 | `fernando-sorocaba_forca-de-um-furacao-194548` |
| 30 | Hillsong United | Oceans (Tradução) | 68893 | `hillsong-united_oceans-traducao` |
| 31 | One Direction | Moments | 67575 | `one-direction_moments` |
| 32 | RBD | Ensina-me | 67137 | `rbd_ensina-me` |
| 33 | Marcus Salles | Vem Senhor Jesus | 66238 | `marcus-salles_vem-senhor-jesus` |
| 34 | Cristiano Araújo | Frases de Fogo | 61073 | `cristiano-araujo_frases-de-fogo` |
| 35 | Banda Calypso | Chamo por Você | 59530 | `banda-calypso_chamo-por-voce` |
| 36 | Cristiano Araújo | Arrocha Com Tequila | 55299 | `cristiano-araujo_arrocha-com-tequila` |
| 37 | Fred & Gustavo | Armadilha | 51032 | `fred-gustavo_armadilha` |
| 38 | João Neto e Frederico | Sai Pra Lá! | 48764 | `joao-neto-frederico_sai-pra-la` |
| 39 | Jotta A | Faz Chover | 48617 | `jotta-a_faz-chover` |
| 40 | Jorge e Mateus | Armadilha | 48439 | `jorge-mateus_armadilha` |
| 41 | Calvin Harris | I Need Your Love | 46914 | `calvin-harris_i-need-your-love` |
| 42 | Gusttavo Lima | Agua de Bar | 45201 | `gusttavo-lima_agua-de-bar` |
| 43 | Marcos e Belutti | Um Dia A Gente Se Encontra | 42627 | `marcos-belutti_um-dia-a-gente-se-encontra` |
| 44 | Zé Ricardo e Thiago | Pode Ou Nao Pode | 39384 | `ze-ricardo-thiago_pode-ou-nao-pode` |
| 45 | Rionegro e Solimões | À sua maneira | 38884 | `rio-negro-e-solimoes_a-sua-maneira` |
| 46 | Gusttavo Lima | À Sua Maneira | 38646 | `gusttavo-lima_a-sua-maneira` |
| 47 | Wesley Safadão | Segunda Opção | 34756 | `wesley-safadao_segunda-opcao` |
| 48 | Hinos Avulsos CCB | Orgulho de Deus | 34725 | `hinos-avulsos-ccb_orgulho-de-deus` |
| 49 | Glee | Get It Right | 34439 | `glee_get-it-right` |
| 50 | Humberto e Ronaldo | Canção Perfeita | 34437 | `humberto-ronaldo_cancao-perfeita` |
| 51 | Léo Magalhães | Fala Comigo | 32952 | `leo-magalhaes_fala-comigo` |
| 52 | Projota | Deixa Rolar | 32651 | `projota_deixa-rolar` |
| 53 | Ouvir e Crer | E Eu Vou | 32604 | `ouvir-e-crer_e-eu-vou` |
| 54 | Gabriel Gava | Bala Na Boquinha | 30917 | `gabriel-gava_bala-na-boquinha` |
| 55 | Henrique e Juliano | Ciumento Mesmo | 29978 | `henrique-e-juliano_ciumento-mesmo` |
| 56 | Catedral | Dona do Meu Coração | 29151 | `catedral_dona-do-meu-coracao` |
| 57 | One Direction | Over Again | 27820 | `one-direction_over-again` |
| 58 | Gerson Rufino | Filho de Leão | 27731 | `gerson-rufino_filho-de-leao` |
| 59 | Matheus e Kauan | Ciumento Mesmo | 26753 | `matheus-kauan_ciumento-mesmo` |
| 60 | One Direction | Change My Mind | 25935 | `one-direction_change-my-mind` |
| 61 | Wesley Safadão | Lapada Lapada | 25368 | `wesley-safadao_lapada-lapada` |
| 62 | Israel Novaes | Minhas Emoções | 24448 | `israel-novaes_minhas-emocoes` |
| 63 | Banda Calypso | Dudu | 24041 | `banda-calypso_dudu` |
| 64 | Wesley Safadão | Vida de Play Boy | 21872 | `wesley-safadao_vida-de-play-boy` |
| 65 | Antônio Cirilo | Cetro de Justiça | 21730 | `antonio-cirilo_cetro-de-justica` |
| 66 | João Lucas e Marcelo | Vuco Vuco | 21560 | `joao-lucas-marcelo_vuco-vuco` |
| 67 | Harpa Cristã | Hino 36 | 20390 | `harpa-crista_hino-36` |
| 68 | Marcos e Belutti | Você Não Me Faz Bem | 19571 | `marcos-belutti_voce-nao-me-faz-bem` |
| 69 | OneRepublic | If I Lose Myself | 19445 | `one-republic_if-i-lose-myself` |
| 70 | One Direction | Taken | 19395 | `one-direction_taken` |
| 71 | Taylor Swift | Haunted | 19094 | `taylor-swift_haunted` |
| 72 | Lázaro | Como Uma Criança | 18410 | `lazaro_como-uma-crianca` |
| 73 | Humberto e Ronaldo | Rascunho | 18406 | `humberto-ronaldo_rascunho` |
| 74 | Chris Brown | Yeah 3x | 17501 | `chris-brown_yeah-3x` |
| 75 | Hillsong United | Relentless | 16948 | `hillsong-united_relentless` |
| 76 | Wesley Safadão | Como Num Filme | 16394 | `wesley-safadao_como-num-filme` |
| 77 | 30 Seconds To Mars | City Of Angels | 16307 | `30-seconds-to-mars_city-of-angels` |
| 78 | RBD | De Musica Ligeira | 15015 | `rbd_de-musica-ligeira` |
| 79 | Wesley Safadão | O Pegador | 13494 | `wesley-safadao_o-pegador` |
| 80 | Soja | Not Done Yet | 13295 | `soja_not-done-yet` |
| 81 | Damares | Derrama Shekinah | 13282 | `damares_derrama-shekinah` |
| 82 | Simple Plan | This Song Saved My Life | 13257 | `simple-plan_this-song-saved-my-life` |
| 83 | Wesley Safadão | Desce Piriguete | 11876 | `wesley-safadao_desce-piriguete` |
| 84 | Taylor Swift | Innocent | 11789 | `taylor-swift_innocent` |
| 85 | Thiago Brava | Manda Nudes | 11404 | `thiago-brava_manda-nudes` |
| 86 | Carrossel (2012) | Todo Mundo | 11388 | `carrossel-2012_todo-mundo` |
| 87 | Ben Harper | When She Believes | 11194 | `ben-harper_when-she-believes` |
| 88 | Luan Santana | Vergonha Na Cara | 10965 | `luan-santana_vergonha-na-cara` |
| 89 | Aviões do Forró | Pensa Em Mim | 10956 | `avioes-do-forro_pensa-em-mim` |
| 90 | Bon Jovi | Bang a drum | 10856 | `bon-jovi_bang-drum` |
| 91 | Aviões do Forró | Vai a Pé | 10603 | `avioes-do-forro_vai-a-pe` |
| 92 | Léo Magalhães | Alô Fala Comigo | 10556 | `leo-magalhaes_alo-fala-comigo` |
| 93 | Oswaldo Montenegro | Espelho Das Águas | 10154 | `oswaldo-montenegro_espelho-das-aguas` |
| 94 | Maneva | Segura o Som | 9899 | `maneva_segura-som` |
| 95 | Aviões do Forró | Balada Boa | 9860 | `avioes-do-forro_balada-boa` |
| 96 | Jeann e Julio | Creme do Verão | 9289 | `jeann-julio_creme-do-verao` |
| 97 | Desejo de Menina | Mundo Inteiro | 9276 | `desejo-de-menina_mundo-inteiro` |
| 98 | Colbie Caillat | Fearless | 9032 | `colbie-caillat_fearless` |
| 99 | Pedro Paulo e Alex | Eu Voltei | 9024 | `pedro-paulo-alex_eu-voltei` |
| 100 | Cristiano Araújo | Sabe Me Prender | 8907 | `cristiano-araujo_sabe-me-prender` |
| 101 | Aviões do Forró | Da Água Pro Vinho | 8848 | `avioes-do-forro_da-agua-pro-vinho` |
| 102 | Conde do Forró | Chorar Todo Dia | 8503 | `conde-do-forro_chorar-todo-dia` |
| 103 | Ministério Fonte da Vida de Adoração | Fala Comigo | 8452 | `ministerio-fonte-da-vida-de-adoracao_fala-comigo` |
| 104 | Thaeme e Thiago | Eu Te Avisei | 8387 | `thaeme-thiago_eu-te-avisei` |
| 105 | Fred & Gustavo | Boca Louca | 7812 | `fred-gustavo_boca-louca` |
| 106 | Novo Tom | Testemunhar | 7701 | `novo-tom_testemunhar` |
| 107 | One Direction | Over Again | 7683 | `one-direction_over-again-` |
| 108 | Taylor Swift | All You Had To do Was Stay | 7672 | `taylor-swift_all-you-had-to-do-was-stay` |
| 109 | Demi Lovato | Never Been Hurt | 7241 | `demi-lovato_never-been-hurt` |
| 110 | Catedral | Amo Tanto Amar Você | 7238 | `catedral_amo-tanto-amar-voce` |
| 111 | Humberto e Ronaldo | Sensação Estranha | 7115 | `humberto-ronaldo_sensacao-estranha` |
| 112 | Wesley Safadão | Dança Kuduro | 7075 | `wesley-safadao_danca-kuduro` |
| 113 | Wesley Safadão | Farra Das Amigas | 6751 | `wesley-safadao_farra-das-amigas` |
| 114 | Humberto e Ronaldo | A Chinela Vai Cantar | 6406 | `humberto-ronaldo_a-chinela-vai-cantar` |
| 115 | Jonas Brothers | Fall | 5994 | `jonas-brothers_fall` |
| 116 | Arena Louvor | O Maior Milagre | 5738 | `arena-louvor_o-maior-milagre` |
| 117 | Priscilla Alcântara | Podemos Fingir | 5583 | `priscilla-alcantara_podemos-fingir` |
| 118 | João Lucas e Marcelo | De Janeiro a Janeiro | 5462 | `joao-lucas-marcelo_de-janeiro-a-janeiro` |
| 119 | Cristiano Araújo | Tchá Tchá Tchá | 5426 | `cristiano-araujo_tcha-tcha-tcha` |
| 120 | Taylor Swift | The Lucky One | 5393 | `taylor-swift_the-lucky-one` |
| 121 | Keane | With Or Without You | 5390 | `keane_with-or-without-you` |
| 122 | Laura Pausini | El no está por tí | 5362 | `laura-pausini_el-no-esta-por-ti` |
| 123 | Beirut | Scenic World | 5359 | `beirut_scenic-world` |
| 124 | Guilherme & Santiago | Nosso Amor Acabou | 5154 | `guilherme-e-santiago_nosso-amor-acabou` |
| 125 | Wesley Safadão | Balada | 5075 | `wesley-safadao_balada` |
| 126 | Aviões do Forró | Eu Tava Te Amando | 5058 | `avioes-do-forro_eu-tava-te-amando` |
| 127 | Wesley Safadão | Fiat Uno | 4954 | `wesley-safadao_fiat-uno` |
| 128 | Gabriel Gava | Papapapow | 4949 | `gabriel-gava_papapapow` |
| 129 | Zé Ricardo e Thiago | Vem Correndo | 4600 | `ze-ricardo-thiago_vem-correndo` |
| 130 | Gabriel Gava | O Pegador | 4561 | `gabriel-gava_o-pegador` |
| 131 | Hugo e Tiago | Mexe Devagar | 4511 | `hugo-e-tiago_mexe-devagar` |
| 132 | Gabriel Gava | Vai Bonitinha | 4259 | `gabriel-gava_vai-bonitinha` |
| 133 | Ed Sheeran | Moments | 4147 | `ed-sheeran_moments` |
| 134 | Wesley Safadão | Descendo e Rebolando | 3961 | `wesley-safadao_descendo-e-rebolando` |
| 135 | Catedral | Asfixia | 3931 | `catedral_asfixia` |
| 136 | Conrado e Aleksandro | Tinta Seca | 3767 | `conrado-aleksandro_tinta-seca` |
| 137 | Wesley Safadão | Eu Só Sei Dançar Beijando Na Boca | 3674 | `wesley-safadao_eu-so-sei-dancar-beijando-na-boca` |
| 138 | RBD | Desesperadamente Sola | 3555 | `rbd_desesperadamente-sola` |
| 139 | Thaeme e Thiago | Cê Endoidou Foi ? | 3438 | `thaeme-thiago_ce-endoidou-foi-` |
| 140 | Taylor Swift | This Love | 3342 | `taylor-swift_this-love` |
| 141 | Aviões do Forró | Tô Solteiro | 3327 | `avioes-do-forro_to-solteiro` |
| 142 | Leonardo | Se Entrega Amor | 3286 | `leonardo_se-entrega-amor` |
| 143 | Hillsong Music Australia | To Know Your Name | 3269 | `hillsong-music-australia_to-know-your-name` |
| 144 | One Direction | Why Don't We Go There | 3209 | `one-direction_why-dont-we-go-there` |
| 145 | Jeann e Julio | Nem Na Bala | 3118 | `jeann-julio_nem-na-bala` |
| 146 | Hugo e Tiago | Insanidade | 3090 | `hugo-e-tiago_insanidade` |
| 147 | Tenacious D | I'm The Only Gay Eskimo | 3077 | `tenacious-d_im-the-only-gay-eskimo` |
| 148 | Mayck e Lyan | Flecha Envenenada | 3004 | `mayck-lyan_flecha-envenenada` |
| 149 | Katy Perry | Hook Up | 2961 | `katy-perry_hook-up` |
| 150 | Calcinha Preta | Eu Amo Você  Eu Amo | 2931 | `calcinha-preta_eu-amo-voce--eu-amo` |
| 151 | Michel Teló | Me Chama Pra Sorrir | 2917 | `michel-telo_me-chama-pra-sorrir` |
| 152 | Deigma Marques | Só Tu És Deus (You Alone Are God) | 2744 | `deigma-marques_so-tu-es-deus-you-alone-are-god` |
| 153 | Grupo Tradição | Tô Solteiro | 2697 | `grupo-tradicao_to-solteiro` |
| 154 | Wesley Safadão | Me Libera | 2675 | `wesley-safadao_me-libera` |
| 155 | ABBA | Hey Hey Helen | 2663 | `abba_hey-hey-helen` |
| 156 | Munhoz & Mariano | Nunca Desista | 2610 | `munhoz-mariano_nunca-desista` |
| 157 | Chicabana | Farra Das Amigas | 2511 | `chicabana_farra-das-amigas` |
| 158 | Bob Dylan | Moonshiner | 2486 | `bob-dylan_moonshiner` |
| 159 | Aviões do Forró | Vai Lembrar | 2394 | `avioes-do-forro_vai-lembrar` |
| 160 | Hillsong United | Uneding Love | 2392 | `hillsong-united_uneding-love` |
| 161 | Hugo e Tiago | Então Tó | 2311 | `hugo-e-tiago_entao-to` |
| 162 | Wesley Safadão | Vai Lembrar | 2242 | `wesley-safadao_vai-lembrar` |
| 163 | Conrado e Aleksandro | Quando Eu Tocar No Seu Radin | 2228 | `conrado-aleksandro_quando-eu-tocar-no-seu-radin` |
| 164 | Simple Plan | Just Around The Corner | 2217 | `simple-plan_just-around-the-corner` |
| 165 | Beyoncé | Jealous | 2199 | `beyonce_jealous` |
| 166 | Fall Out Boy | Disloyal Order Of Water Buffaloes | 2087 | `fall-out-boy_disloyal-order-of-water-buffaloes` |
| 167 | Gabriel Gava | Beijo Roubado | 2084 | `gabriel-gava_beijo-roubado` |
| 168 | Malta | Cinderela | 2077 | `banda-malta_cinderela` |
| 169 | Fernando e Sorocaba | Porto da Paixão | 2013 | `fernando-sorocaba_porto-da-paixao` |
| 170 | Plain White T's | Fireworks | 1786 | `plain-white-ts_fireworks` |
| 171 | Zé Ricardo e Thiago | Pelas Ruas | 1746 | `ze-ricardo-thiago_pelas-ruas` |
| 172 | Zé Ricardo e Thiago | Beijo | 1727 | `ze-ricardo-thiago_beijo` |
| 173 | Thiago Brava | Ui Que Maravilia | 1637 | `thiago-brava_ui-que-maravilia` |
| 174 | Maria Cecília e Rodolfo | Voa Voa | 1546 | `maria-cecilia-rodolfo_voa-voa` |
| 175 | Raquel Mello | Lembre de Mim | 1485 | `raquel-mello_lembre-de-mim` |
| 176 | Selena Gomez | Sad Serenade | 1432 | `selena-gomez_sad-serenade` |
| 177 | Maná | Me Voy A Convertir En Un Ave | 1422 | `mana_me-voy-convertir-en-un-ave` |
| 178 | Henrique e Juliano | Sai do Meio | 1241 | `henrique-e-juliano_sai-do-meio` |
| 179 | Michel Teló | Jurerê | 1195 | `michel-telo_jurere` |
| 180 | Munhoz & Mariano | Voa Voa | 1190 | `munhoz-mariano_voa-voa` |
| 181 | Johnny Cash | The Wanderer | 1139 | `johnny-cash_the-wanderer` |
| 182 | He Is We | Love Life | 1049 | `he-is-we_love-life` |
| 183 | Voz da Verdade | Fé | 944 | `voz-da-verdade_fe` |
| 184 | 5 Seconds Of Summer | Heartache On The Big Screen | 906 | `5-seconds-of-summer_heartache-on-the-big-screen` |
| 185 | Strike | Em Êxtase | 815 | `strike_em-extase` |
| 186 | George Henrique e Rodrigo | Fogo Na Roupa | 683 | `george-henrique-rodrigo_fogo-na-roupa` |
| 187 | Missionário Shalom | Ele É Tudo | 643 | `missionario-shalom_ele-e-tudo` |
| 188 | 5 Seconds Of Summer | Independence Day | 613 | `5-seconds-of-summer_independence-day` |
| 189 | Tche Garotos | Fiel | 551 | `tche-garotos_fiel` |
| 190 | Sam Smith | Money On My Mind | 408 | `sam-smith_money-on-my-mind` |
| 191 | Pedro Paulo e Alex | Quando Eu Acordar | 398 | `pedro-paulo-alex_quando-eu-acordar` |
| 192 | Hillsong United | My Only Cry | 349 | `hillsong-united_my-only-cry` |
| 193 | Darvin | Fica Pronto Pra Mim | 236 | `darvin_fica-pronto-pra-mim` |
| 194 | Soja | Not Done | 88 | `soja_not-done` |
| 195 | Hillsong United | Narrow Road | 74 | `hillsong-united_narrow-road` |
| 196 | Europe | Normal | 65 | `europe_normal` |
| 197 | Limão Com Mel | Na Contra Mao do Tempo | 27 | `limao-com-mel_na-contra-mao-do-tempo` |
| 198 | Laura Pausini | He Creído En Mí | 0 | `laura-pausini_he-creido-en-mi` |
| 199 | One Direction | A.M. | 0 | `one-direction_am` |

##### `CGAmF` (`id_seq=1`) — 296 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Fernando e Sorocaba | A Casa Caiu | 914999 | `fernando-sorocaba_a-casa-caiu` |
| 2 | Pedra Letícia | Em Plena Lua de Mel | 669474 | `pedra-leticia_em-plena-lua-de-mel` |
| 3 | Israel Novaes | Vem Ni Mim Dodge Ram (part. Gusttavo Lima) | 547253 | `israel-novaes_vem-ni-mim-dodge-ram` |
| 4 | João Neto e Frederico | Só de Você | 535856 | `joao-neto-frederico_so-de-voce` |
| 5 | Livres Para Adorar | Quando o Mundo Cai Ao Meu Redor | 360543 | `livres-para-adorar_quando-o-mundo-cai-ao-meu-redor` |
| 6 | Fernandinho | Há Um  Rio | 319436 | `fernandinho_ha-um-rio` |
| 7 | Fernandinho | Eu Vejo Uma Pequena Nuvem | 319218 | `fernandinho_eu-vejo-uma-pequena-nuvem` |
| 8 | Jorge e Mateus | Eu Quero Ser Teu Sol | 277535 | `jorge-mateus_eu-quero-ser-teu-sol` |
| 9 | Humberto e Ronaldo | Só Vou Beber Mais Hoje | 256037 | `humberto-ronaldo_so-vou-beber-mais-hoje` |
| 10 | Marcos e Belutti | Nova Namorada | 249133 | `marcos-belutti_nova-namorada` |
| 11 | Jorge e Mateus | Invasões | 209986 | `jorge-mateus_invasoes` |
| 12 | Temas Infantis | Ciranda cirandinha | 151837 | `temas-infantis_ciranda-cirandinha` |
| 13 | Fernando e Sorocaba | Estrela Solitária | 149454 | `fernando-sorocaba_estrela-solitaria` |
| 14 | Charlie Brown Jr. | Proibida Pra Mim | 105232 | `charlie-brown-jr_proibida-pra-mim-` |
| 15 | Gusttavo Lima | Vem Ne Mim Dodge Ram | 100950 | `gusttavo-lima_vem-ne-mim-dodge-ram` |
| 16 | Justin Bieber | Love Me | 94575 | `justin-bieber_love-me` |
| 17 | Bruno e Marrone | Só de Você | 89163 | `bruno-e-marrone_so-de-voce` |
| 18 | Henrique e Juliano | A Dona do Meu Coração | 88766 | `henrique-e-juliano_a-dona-do-meu-coracao` |
| 19 | Henrique e Juliano | Na Hora da Raiva | 88025 | `henrique-e-juliano_na-hora-da-raiva` |
| 20 | Fresno | Ainda Te Amo | 84256 | `fresno_ainda-te-amo` |
| 21 | Victor e Leo | Lágrimas | 84101 | `victor-leo_lagrimas` |
| 22 | Of Monsters and Men | Little Talks | 80542 | `of-monsters-and-men_little-talks` |
| 23 | Diante do Trono | Meu filho não temas | 76178 | `diante-do-trono_meu-filho-nao-temas` |
| 24 | Cleber e Cauan | Mel Nesse Trem | 74979 | `cleber-cauan_mel-nesse-trem` |
| 25 | Luan Santana | Loira Linda | 72969 | `luan-santana_loira-linda` |
| 26 | Léo Magalhães | 24 Horas (Pensando Em Você) | 69476 | `leo-magalhaes_24-horas-pensando-em-voce` |
| 27 | Justin Bieber | Eenie Meenie | 67726 | `justin-bieber_eenie-meenie` |
| 28 | Cassiane | 500º | 63732 | `cassiane_500o` |
| 29 | Aline Barros | Faz Chover | 63429 | `aline-barros_faz-chover-202854` |
| 30 | Leonardo | Baby Fala Pra Mim | 61053 | `leonardo_baby-fala-pra-mim` |
| 31 | Maria Cecília e Rodolfo | Me Dê Uma Chance | 59156 | `maria-cecilia-rodolfo_me-de-uma-chance` |
| 32 | Thaeme e Thiago | Cafajeste | 57983 | `thaeme-thiago_cafajeste` |
| 33 | Pedro Paulo e Alex | Ta Calor | 56963 | `pedro-paulo-alex_ta-calor` |
| 34 | Henrique e Diego | Me Liga | 54523 | `henrique-diego_me-liga` |
| 35 | Snow Patrol | Run | 53603 | `snow-patrol_run` |
| 36 | Leandro & Leonardo | Água de coco | 52603 | `leandro-e-leonardo_agua-de-coco` |
| 37 | João Neto e Frederico | Eu e Você | 52136 | `joao-neto-frederico_eu-voce` |
| 38 | Os Paralamas do Sucesso | De Música Ligeira | 50514 | `os-paralamas-do-sucesso_de-musica-ligeira` |
| 39 | André Valadão | Quando o Mundo Cai Ao Meu Redor | 49833 | `andre-valadao_quando-o-mundo-cai-ao-meu-redor` |
| 40 | One Direction | They Don't Know About Us | 49772 | `one-direction_they-dont-know-about-us` |
| 41 | Avril Lavigne | Darlin | 48998 | `avril-lavigne_darlin` |
| 42 | Aviões do Forró | Eu Ela e a Amiga Dela (Menage) | 46740 | `avioes-do-forro_eu-ela-e-a-amiga-dela-menage` |
| 43 | Taylor Swift | Sparks Fly | 42982 | `taylor-swift_sparks-fly` |
| 44 | Israel Novaes | Dodge Ram | 42489 | `israel-novaes_dodge-ram` |
| 45 | Leonardo | Água de coco | 39953 | `leonardo_agua-de-coco` |
| 46 | Asa de Águia | Gladiador | 38613 | `asa-de-aguia_gladiador` |
| 47 | Gusttavo Lima | Chovendo Paixão | 38110 | `gusttavo-lima_chovendo-paixao` |
| 48 | Henrique e Diego | Vida Mais ou Menos | 37355 | `henrique-diego_vida-mais-ou-menos` |
| 49 | Damien Rice | 9 Crimes | 37192 | `damien-rice_9-crimes` |
| 50 | Luan Santana | Uma Noite | 37173 | `luan-santana_uma-noite` |
| 51 | Justin Bieber | Nothing Like Us | 36885 | `justin-bieber_nothing-like-us` |
| 52 | Taylor Swift | Bad Blood | 36297 | `taylor-swift_bad-blood` |
| 53 | Capital Inicial | Gratidão | 35928 | `capital-inicial_gratidao` |
| 54 | Paula Fernandes | Aos Olhos Do Tempo | 35606 | `paula-fernandes_aos-olhos-do-tempo` |
| 55 | Chris Brown | Next 2 You | 33410 | `chris-brown_next-2-you` |
| 56 | Stone Sour | Zzyxz Rd. | 33231 | `stone-sour_zzyxz-rd` |
| 57 | Catedral | Estações | 33028 | `catedral_estacoes` |
| 58 | Aviões do Forró | Só Se For Gelada | 31998 | `avioes-do-forro_so-se-for-gelada` |
| 59 | Bob Marley | Zion Train | 31482 | `bob-marley_zion-train` |
| 60 | Leonardo | Quem É o Dono Dos Seus Olhos | 31320 | `leonardo_quem-o-dono-dos-seus-olhos` |
| 61 | The Lumineers | Stubborn Love | 30656 | `the-lumineers_stubborn-love` |
| 62 | Harpa Cristã | O Exilado | 29451 | `harpa-crista_o-exilado` |
| 63 | Clamor pelas Nações | Eu Me Alegrarei | 29196 | `clamor-pelas-nacoes_eu-me-alegrarei` |
| 64 | Zezé Di Camargo e Luciano | Eu Sou Desejo Você É Paixão | 28289 | `zeze-di-camargo-e-luciano_eu-sou-desejo-voce-paixao` |
| 65 | Aviões do Forró | Saia e Bicicletinha | 27727 | `avioes-do-forro_saia-bicicletinha` |
| 66 | One Direction | Last First Kiss | 27564 | `one-direction_last-first-kiss` |
| 67 | One Direction | Half a Heart | 27346 | `one-direction_half-a-heart` |
| 68 | Leonardo | Tudo me lembra você | 27281 | `leonardo_tudo-me-lembra-voce` |
| 69 | Bonde do Brasil | Fala Comigo | 27073 | `bonde-do-brasil_fala-comigo` |
| 70 | Avril Lavigne | I Can do Better | 26949 | `avril-lavigne_i-can-do-better` |
| 71 | Justin Bieber | Up | 26173 | `justin-bieber_up` |
| 72 | Rod Stewart | Baby Jane | 25204 | `rod-stewart_baby-jane` |
| 73 | Resgate | O nome da Paz (acústico) | 24774 | `resgate_o-nome-da-paz-acustico` |
| 74 | João Neto e Frederico | Nossos Sonhos | 24539 | `joao-neto-frederico_nossos-sonhos` |
| 75 | Livres Para Adorar | Eu Amo Seu Coração | 24472 | `livres-para-adorar_eu-amo-seu-coracao` |
| 76 | Daniel | Memórias de Uma Paixão | 24381 | `daniel_memorias-de-uma-paixao` |
| 77 | Strike | A Última Chance | 23667 | `strike_a-ultima-chance` |
| 78 | Avril Lavigne | Remember When | 23432 | `avril-lavigne_remember-when` |
| 79 | Zé Neto e Cristiano | Tem Que Ter Pegada | 22800 | `ze-neto-cristiano_tem-que-ter-pegada` |
| 80 | Léo Magalhães | Amores Imortais | 22544 | `leo-magalhaes_amores-imortais` |
| 81 | Aviões do Forró | Vamos Sair Pra Algum Lugar | 22532 | `avioes-do-forro_vamos-sair-pra-algum-lugar` |
| 82 | Chicabana | Ai Se Eu Te Pego | 22371 | `chicabana_ai-se-eu-te-pego` |
| 83 | Ventania | Comer Você | 21707 | `ventania_comer-voce` |
| 84 | Avril Lavigne | Black Star | 20196 | `avril-lavigne_black-star` |
| 85 | Birdy | Not About Angels | 20172 | `birdy_not-about-angels` |
| 86 | Demi Lovato | Stop The World | 19778 | `demi-lovato_stop-the-word` |
| 87 | Secos & Molhados | Preto Velho | 19737 | `secos-molhados_preto-velho` |
| 88 | Gabriel Gava | E Tome Amor | 19499 | `gabriel-gava_e-tome-amor` |
| 89 | Boyce Avenue | Perfect | 19346 | `boyce-avenue_perfect` |
| 90 | Voz da Verdade | Avivamento | 19340 | `voz-da-verdade_avivamento` |
| 91 | João Lucas e Marcelo | Se Beijar Na Boca Dá Sapinho | 18503 | `joao-lucas-marcelo_se-beijar-na-boca-da-sapinho` |
| 92 | Calcinha Preta | Sonho Lindo | 18412 | `calcinha-preta_sonho-lindo` |
| 93 | João Neto e Frederico | Se Entrega | 18380 | `joao-neto-frederico_se-entrega` |
| 94 | Heloísa Rosa | Jesus Eu Te Amo (Nem o Céu Nem o Mar) | 17989 | `heloisa-rosa_jesus-eu-te-amo-nem-ceu-nem-mar` |
| 95 | Vander Lee | Subindo a ladeira | 17721 | `vander-lee_subindo-ladeira` |
| 96 | Bryan Adams | I Will Be Right Here Waiting | 17715 | `bryan-adams_i-will-be-right-here-waiting` |
| 97 | Lana Del Rey | Radio | 17514 | `lana-del-rey_radio` |
| 98 | Skid Row | Breakin' Down | 17183 | `skid-row_breakin-down` |
| 99 | Glee | Umbrella / Singin' In The Rain | 17082 | `glee_umbrella-singin-in-the-rain` |
| 100 | David Quinlan | Pequena Nuvem | 16451 | `david-quinlan_faz-chover-199369` |
| 101 | 5 Seconds Of Summer | Wherever You Are | 15710 | `5-seconds-of-summer_wherever-you-are` |
| 102 | Thaeme e Thiago | 29 de Agosto | 15596 | `thaeme-thiago_29-de-agosto` |
| 103 | Beyoncé | Si Yo Fuera Un Chico | 15260 | `beyonce_si-yo-fuera-un-chico` |
| 104 | Lucas Lucco | Vem Nimim Mulherada | 14532 | `lucas-lucco_vem-nimim-mulherada` |
| 105 | Colbie Caillat | One fine wire | 14500 | `colbie-caillat_one-fine-wire` |
| 106 | Cristiano Araújo | Não Sei Me Controlar | 14390 | `cristiano-araujo_nao-sei-me-controlar` |
| 107 | Eminem | Lighters | 14370 | `eminem_lighters` |
| 108 | Bonde do Brasil | Então Volta | 14283 | `bonde-do-brasil_entao-volta` |
| 109 | Mayck e Lyan | Querida | 14258 | `mayck-lyan_querida` |
| 110 | Boyce Avenue | Every Breath | 14133 | `boyce-avenue_every-breath` |
| 111 | Henrique e Juliano | Aqui Tem Fogo | 14017 | `henrique-e-juliano_aqui-tem-fogo` |
| 112 | Conrado e Aleksandro | No Lombo Das Prima | 14001 | `conrado-aleksandro_no-lombo-das-prima` |
| 113 | Conrado e Aleksandro | Caso de Descaso | 13750 | `conrado-aleksandro_caso-de-descaso` |
| 114 | Lorde | Tennis Court | 13722 | `lorde_tennis-court` |
| 115 | Aviões do Forró | A Onça Bebe Leite | 13715 | `avioes-do-forro_a-onca-bebe-leite` |
| 116 | Britney Spears | If You Seek Amy | 13531 | `britney-spears_if-you-seek-amy` |
| 117 | Ministério Fonte da Vida de Adoração | Santidade Ao Senhor | 13483 | `ministerio-fonte-da-vida-de-adoracao_santidade-ao-senhor` |
| 118 | Católicas | Ladainha Mãe De Deus | 13304 | `catolicas_ladainha-mae-de-deus` |
| 119 | Os Paralamas do Sucesso | Música Ligeira | 13202 | `os-paralamas-do-sucesso_musica-ligeira` |
| 120 | Hinos Avulsos CCB | Algemado No Mundo Eu Estava | 13052 | `hinos-avulsos-ccb_algemado-no-mundo-eu-estava` |
| 121 | Paulo César Baruk | Sou Livre | 12980 | `paulo-cesar-baruk_sou-livre` |
| 122 | Diego Fernandes | Um Amor de Verdade | 12954 | `diego-fernandes_um-amor-de-verdade` |
| 123 | Florence and The Machine | No Light No Light | 12529 | `florence-and-the-machine_no-light-no-light` |
| 124 | Justin Bieber | All I Wanna Is You | 12420 | `justin-bieber_all-i-wanna-is-you` |
| 125 | Avril Lavigne | Stop Standing There | 12329 | `avril-lavigne_stop-standing-there` |
| 126 | Marcos Witt | Levantaté y Salvame | 12269 | `marcos-witt_levantate-salvame` |
| 127 | Psirico | Saia e Bicicletinha | 12211 | `psirico_saia-biciletinha` |
| 128 | Israel Novaes | Você Merece Cachê | 12190 | `israel-novaes_voce-merece-cache` |
| 129 | Rebelde | A Voz Das Estrelas | 11842 | `rebelde-rbr_a-voz-das-estrelas` |
| 130 | One Direction | Everything About You | 11677 | `one-direction_everything-about-you` |
| 131 | Luan Santana | Foi Só Olhar Nos Seus Olhos | 11672 | `luan-santana_foi-so-olhar-nos-seus-olhos` |
| 132 | Banda Calypso | Primeiro Amor | 11607 | `banda-calypso_primeiro-amor` |
| 133 | Mumford & Sons | Babel | 11472 | `mumford-sons_babel` |
| 134 | Shakira | This Time For Africa | 11389 | `shakira_this-time-for-africa` |
| 135 | Clarice Falcão | I'm Nobody | 10893 | `clarice-falcao_im-nobody` |
| 136 | Hinos Avulsos CCB | Salmos 45 | 10756 | `hinos-avulsos-ccb_salmos-45` |
| 137 | João Lucas e Marcelo | As Mina Pira | 10411 | `joao-lucas-marcelo_as-mina-pira` |
| 138 | Fred & Gustavo | Pra Te Esquecer | 10260 | `fred-gustavo_pra-te-esquecer` |
| 139 | Victor e Leo | Tudo Que Você Ouvir | 10189 | `victor-leo_tudo-que-voce-ouvir` |
| 140 | Wesley Safadão | Subidinha | 9790 | `wesley-safadao_subidinha` |
| 141 | Aviões do Forró | Mistérios | 9646 | `avioes-do-forro_misterios` |
| 142 | Hinos Avulsos CCB | Anjo | 9462 | `hinos-avulsos-ccb_anjo` |
| 143 | System Of a Down | Dammit | 9341 | `system-of-a-down_dammit` |
| 144 | Pedro Paulo e Alex | Tá Que Tá | 9298 | `pedro-paulo-alex_ta-que-ta` |
| 145 | Lucas Lucco | Chulep | 9258 | `lucas-lucco_chulep` |
| 146 | Jake Bugg | Someone Told Me | 8902 | `jake-bugg_someone-told-me` |
| 147 | Victor e Leo | Estrada Vermelha | 8854 | `victor-leo_estrada-vermelha` |
| 148 | Chicabana | Bicicletinha | 8827 | `chicabana_bicicletinha` |
| 149 | Loubet | tsunami | 8727 | `loubet_tsunami` |
| 150 | Conrado e Aleksandro | Tem Quem Me Ama | 8370 | `conrado-aleksandro_tem-quem-me-ama` |
| 151 | Ludmila Ferber | Vem me saciar | 8277 | `ludmila-ferber_vem-me-saciar` |
| 152 | Hillsong United | Everything To Me | 8129 | `hillsong-united_everything-to-me` |
| 153 | Anjos Do Hanngar | Dia de sol | 8123 | `anjos-do-hanngar_dia-de-sol` |
| 154 | Fifth Harmony | Boss | 8076 | `fifth-harmony_boss` |
| 155 | Banda Calypso | Love you mon amor | 7863 | `banda-calypso_love-you-mon-amor` |
| 156 | Natiruts | Neguinha | 7601 | `natiruts_neguinha` |
| 157 | Michel Teló | Se Eu Não For | 7565 | `michel-telo_se-eu-nao-for` |
| 158 | Violetta | Ser Quién Soy | 7517 | `violetta_ser-quien-soy` |
| 159 | João Carreiro e Capataz | Um Pedido a Você | 7416 | `joao-carreiro-capataz_um-pedido-voce` |
| 160 | Hillsong United | Rise | 7412 | `hillsong-united_rise` |
| 161 | Diante do Trono | Pra Sempre Reinarás | 7297 | `diante-do-trono_pra-sempre-reinaras` |
| 162 | Taylor Swift | Clean | 7224 | `taylor-swift_clean` |
| 163 | Henrique e Diego | Indecisão | 6889 | `henrique-diego_indecisao` |
| 164 | Marcos e Belutti | Tô Fora | 6866 | `marcos-belutti_to-fora` |
| 165 | Péricles | Amar Amar Amar | 6724 | `pericles_amar-amar-amar` |
| 166 | Fernandinho | Poema de Salvação | 6718 | `fernandinho_poema-de-salvacao` |
| 167 | Diego Fernandes | Deus Te Vê | 6628 | `diego-fernandes_deus-te-ve` |
| 168 | Hillsong United | Perfect Love | 6463 | `hillsong-united_perfect-love` |
| 169 | Daniel Alencar | Eu Me Alegrarei | 6457 | `daniel-alencar_eu-me-alegrarei` |
| 170 | Pedro Paulo e Alex | Dança Kuduro | 6336 | `pedro-paulo-alex_danca-kuduro` |
| 171 | Lucas Lucco | Muié | 6322 | `lucas-lucco_muie` |
| 172 | Matheus e Kauan | Se Voltar É Seu | 6295 | `matheus-kauan_se-voltar-e-seu` |
| 173 | Hinos Avulsos CCB | Escuta Na Comunhã | 6286 | `hinos-avulsos-ccb_escuta-na-comunha` |
| 174 | Davi Sacer | Faz Chover | 6261 | `davi-sacer_faz-chover` |
| 175 | Hillsong United | Search My Heart | 6186 | `hillsong-united_search-my-heart` |
| 176 | Henrique e Juliano | Sem Nome | 6051 | `henrique-e-juliano_sem-nome` |
| 177 | Kleber Lucas | Ziguezageando | 5914 | `kleber-lucas_ziguezageando` |
| 178 | Fonte da Vida | Elevo Os Olhos Para Os Montes | 5721 | `fonte-da-vida_elevo-os-olhos-para-os-montes` |
| 179 | Chicabana | Flashback | 5554 | `chicabana_flashback` |
| 180 | João Lucas e Marcelo | Não Sei Me Controlar | 5468 | `joao-lucas-marcelo_nao-sei-me-controlar` |
| 181 | Hillsong United | Up In Arms | 5430 | `hillsong-united_up-in-arms` |
| 182 | Beyoncé | Radio | 5318 | `beyonce_radio` |
| 183 | Maskavo | Manga Verde | 5247 | `maskavo_manga-verde` |
| 184 | Comunidade Evangélica Internacional da Zona Sul | Majestoso Rei | 5112 | `comunidade-da-zona-sul_majestoso-rei-97837` |
| 185 | Kodaline | One Day | 4949 | `kodaline_one-day` |
| 186 | Munhoz & Mariano | Paixão Que Não Deu Certo | 4903 | `munhoz-mariano_paixao-que-nao-deu-certo` |
| 187 | Cristina Mel | Pra Jesus Louvar | 4534 | `cristina-mel_pra-jesus-louvar` |
| 188 | Fonte da Vida | Eu Quero Ser Um Prazer Para Ti | 4519 | `fonte-da-vida_eu-quero-ser-um-prazer-para-ti` |
| 189 | Taylor Swift | Wonderland | 4452 | `taylor-swift_wonderland` |
| 190 | Banda Calypso | Esperando Por Você | 4339 | `banda-calypso_esperando-por-voce` |
| 191 | Wesley Safadão | Rampeira | 4138 | `wesley-safadao_rampeira` |
| 192 | Zimbra | Pra Você Lembrar de Mim | 4085 | `zimbra_pra-voce-lembrar-de-mim` |
| 193 | Sorriso Maroto | Areia Em Minhas Mãos | 4007 | `sorriso-maroto_areia-em-minhas-maos` |
| 194 | Mumford & Sons | Whispers In The Dark | 3845 | `mumford-sons_whispers-in-the-dark` |
| 195 | Dorgival Dantas | Não Me Diga Bye Bye | 3804 | `dorgival-dantas_nao-me-diga-bye-bye` |
| 196 | Marcos e Belutti | Caixa D'água | 3799 | `marcos-belutti_caixa-dagua` |
| 197 | Lady Gaga | Big Girl Now | 3709 | `lady-gaga_big-girl-now` |
| 198 | Goo Goo Dolls | Become | 3657 | `goo-goo-dolls_become` |
| 199 | Robson Biollo | Te Vi Nos Meus Sonhos | 3625 | `robson-biollo_te-vi-nos-meus-sonhos` |
| 200 | Aviões do Forró | O Gato Bebe Leite | 3588 | `avioes-do-forro_o-gato-bebe-leite` |
| 201 | Casa de Davi | Santo É o Senhor | 3496 | `casa-de-davi_santo-e-o-senhor` |
| 202 | Wesley Safadão | Vagalumes | 3465 | `wesley-safadao_vagalumes` |
| 203 | Malta | Nada Se Compara | 3413 | `banda-malta_nada-se-compara` |
| 204 | Plain White T's | Shine | 3363 | `plain-white-ts_shine` |
| 205 | Hinos Avulsos CCB | Moça de Deus | 3304 | `hinos-avulsos-ccb_moca-de-deus` |
| 206 | He Is We | A Mess It Grows | 3228 | `he-is-we_a-mess-it-grows` |
| 207 | Bryan Adams | I Will Be Right Here | 3223 | `bryan-adams_i-will-be-right-here` |
| 208 | Maria Cecília e Rodolfo | Espalhe Amor | 3181 | `maria-cecilia-rodolfo_espalhe-amor` |
| 209 | Hinos Avulsos CCB | Eu Sei | 3179 | `hinos-avulsos-ccb_eu-sei` |
| 210 | Thaeme e Thiago | Partiu Balada | 3170 | `thaeme-thiago_partiu-balada` |
| 211 | 5 Seconds Of Summer | The Only Reason | 3137 | `5-seconds-of-summer_the-only-reason` |
| 212 | Hinos Avulsos CCB | Aos Céus Clamou | 3081 | `hinos-avulsos-ccb_aos-ceus-clamou` |
| 213 | Fernando e Sorocaba | Sem Reação | 2982 | `fernando-sorocaba_sem-reacao` |
| 214 | Imagine Dragons | America | 2935 | `imagine-dragons_america` |
| 215 | Banda Calypso | Love You Mon Amour | 2852 | `banda-calypso_love-you-mon-amour` |
| 216 | Alda Célia | Pai Nosso | 2845 | `alda-celia_pai-nosso` |
| 217 | Fonte da Vida | Maravilhoso | 2808 | `fonte-da-vida_maravilhoso` |
| 218 | Boyce Avenue | Tonight | 2804 | `boyce-avenue_tonight` |
| 219 | Judson Oliveira | Golias Você Vai Cair (espontânea) | 2800 | `judson-oliveira_golias-voce-vai-cair-espontanea` |
| 220 | Bastille | Overjoyed | 2642 | `bastille_overjoyed` |
| 221 | Fernando e Sorocaba | Cruel | 2583 | `fernando-sorocaba_cruel` |
| 222 | 5 Seconds Of Summer | Lost Boy | 2513 | `5-seconds-of-summer_lost-boy` |
| 223 | Bon Jovi | Amen | 2476 | `bon-jovi_amen` |
| 224 | Jason Derulo | Blind | 2322 | `jason-derulo_blind` |
| 225 | Aviões do Forró | Prefiro Ser Gordinho | 2275 | `avioes-do-forro_prefiro-ser-gordinho` |
| 226 | Eliana Ribeiro | Meu Sim | 2271 | `eliana-ribeiro_meu-sim` |
| 227 | Jesus Culture | You Are My God | 2254 | `jesus-culture_you-are-my-god` |
| 228 | Banda Passarela | Toma Juizo | 2242 | `banda-passarela_toma-juizo` |
| 229 | Chicabana | Ficar Sair | 2187 | `chicabana_ficar-sair` |
| 230 | The Lumineers | Flapper Girl | 2119 | `the-lumineers_flapper-girl` |
| 231 | Justin Bieber | Home This Christmas feat. The Band Perry | 2113 | `justin-bieber_home-this-christmas-feat-the-band-perry` |
| 232 | Miley Cyrus | Someone Else | 2035 | `miley-cyrus_someone-else` |
| 233 | Katy Perry | Double Rainbow | 2031 | `katy-perry_double-rainbow` |
| 234 | Mattos Nascimento | Grite Para Todo Mundo Ouvir | 2015 | `mattos-nascimento-musicas_grite-para-todo-mundo-ouvir` |
| 235 | Vineyard | Emmanuel | 1995 | `vineyard_emmanuel` |
| 236 | Wesley Safadão | Bolo Doido | 1961 | `wesley-safadao_bolo-doido` |
| 237 | Ministério Ipiranga | Verdadeiramente | 1955 | `ministerio-ipiranga_verdadeiramente` |
| 238 | Lady Gaga | No Way | 1925 | `lady-gaga_no-way` |
| 239 | Gilberto e Gilmar | Não Me Deixe No Escuro | 1917 | `gilberto-e-gilmar_nao-me-deixe-no-escuro` |
| 240 | Aviões do Forró | Quem Tem Sorte É Sortero | 1833 | `avioes-do-forro_quem-tem-sorte-e-sortero` |
| 241 | Mumford & Sons | Not With Haste | 1779 | `mumford-sons_not-with-haste` |
| 242 | Skillet | Shouldve When You Couldve | 1775 | `skillet_shouldve-when-you-couldve` |
| 243 | Justin Bieber | Recovery | 1685 | `justin-bieber_recovery` |
| 244 | Hillsong United | Con Mi Fé | 1675 | `hillsong-united_con-mi-fe` |
| 245 | Nx Zero | O destino 0.2 | 1562 | `nx-zero_o-destino-02` |
| 246 | Bastille | These Streets | 1503 | `bastille_these-streets` |
| 247 | Kleo Dibah & Rafael | É Dus Mais Bão | 1502 | `kleo-dibah-rafael_e-dus-mais-bao` |
| 248 | Hillsong Music Australia | Rise | 1499 | `hillsong-music-australia_rise` |
| 249 | Enrique Iglesias | Why Not Me | 1444 | `enrique-iglesias_why-not-me` |
| 250 | Alan Jackson | Little Man | 1413 | `alan-jackson_little-man` |
| 251 | Johnny Cash | For You | 1378 | `johnny-cash_for-you` |
| 252 | The White Buffalo | House Of Pain | 1356 | `the-white-buffalo_house-of-pain` |
| 253 | Israel Novaes | Mãe Deixa Eu Beber | 1312 | `israel-novaes_mae-deixa-eu-beber` |
| 254 | Salz Band | Teu Rio | 1301 | `salz-band_teu-rio` |
| 255 | Ouvir e Crer | Fui Atraído Pelo Teu Amor | 1272 | `ouvir-e-crer_fui-atraido-pelo-teu-amor` |
| 256 | Hinos Avulsos CCB | Quando Você Tenta Esconder de Mim a Sua Dor | 1148 | `hinos-avulsos-ccb_quando-voce-tenta-esconder-de-mim-a-sua-dor` |
| 257 | Israel e Rodolffo | No Escondidinho | 1147 | `israel-rodolfo_no-escondidinho` |
| 258 | Cristina Mel | É Só Vitória | 1118 | `cristina-mel_e-so-vitoria` |
| 259 | 5 Seconds Of Summer | Bad Dreams | 1105 | `5-seconds-of-summer_bad-dreams` |
| 260 | Hillsong United | Cristo Mi Amigo Fiel | 1057 | `hillsong-united_cristo-mi-amigo-fiel` |
| 261 | 5 Seconds Of Summer | Fly Away | 1048 | `5-seconds-of-summer_fly-away` |
| 262 | Desejo de Menina | Amo Você Demais | 1015 | `desejo-de-menina_amo-voce-demais` |
| 263 | Mumford & Sons | Holland Road | 953 | `mumford-sons_holland-road` |
| 264 | Colbie Caillat | Never Gonna Let You Down | 942 | `colbie-caillat_never-gonna-let-you-down` |
| 265 | Ed Sheeran | Billy Ruskin | 932 | `ed-sheeran_billy-ruskin` |
| 266 | Fernando e Sorocaba | Cruel | 922 | `fernando-sorocaba_cruel-` |
| 267 | Cristina Mel | É Só Vitória (Agora Adora) | 892 | `cristina-mel_e-so-vitoria-agora-adora` |
| 268 | Zé Neto e Cristiano | Festa do Cabide | 713 | `ze-neto-cristiano_festa-do-cabide` |
| 269 | Guilherme & Santiago | Solteiro Em Goiânia | 691 | `guilherme-e-santiago_solteiro-em-goiania` |
| 270 | Keane | The Happy Soldier | 666 | `keane_the-happy-soldier` |
| 271 | Guilherme & Santiago | Agora Cê Ta Solta | 652 | `guilherme-e-santiago_agora-ce-ta-solta` |
| 272 | Conrado e Aleksandro | Estrangeira | 650 | `conrado-aleksandro_estrangeira` |
| 273 | Pamela | Tô No Céu | 638 | `pamela_to-no-ceu` |
| 274 | Hinos Avulsos CCB | Mesmo Fraco Como Estou | 634 | `hinos-avulsos-ccb_mesmo-fraco-como-estou` |
| 275 | Hillsong United | Mi Mejor Amigo | 554 | `hillsong-united_mi-mejor-amigo` |
| 276 | Hinos Avulsos CCB | Certeza de Vencer | 551 | `hinos-avulsos-ccb_certeza-de-vencer` |
| 277 | Matheus e Kauan | Se Entrega | 526 | `matheus-kauan_se-entrega` |
| 278 | Tomate | Era Pra Ser | 506 | `tomate_era-pra-ser` |
| 279 | The Cranberries | Not Sorry | 484 | `the-cranberries_not-sorry` |
| 280 | Hillsong Music Australia | Seu Amor Nunca Falha (Relentless) | 428 | `hillsong-music-australia_seu-amor-nunca-falha-relentless` |
| 281 | Colbie Caillat | Hold On | 414 | `colbie-caillat_hold-on` |
| 282 | Bee Gees | Then You Left Me | 389 | `bee-gees_then-you-left-me` |
| 283 | Mumford & Sons | Kansas City | 384 | `mumford-sons_kansas-city` |
| 284 | Colbie Caillat | Live It Up | 330 | `colbie-caillat_live-it-up` |
| 285 | 5 Seconds Of Summer | Broken Pieces | 313 | `5-seconds-of-summer_broken-pieces` |
| 286 | Hillsong United | Tu Fama Gritaré | 307 | `hillsong-united_tu-fama-gritare` |
| 287 | Michael W. Smith | Come See | 278 | `michael-w-smith-musicas_come-see` |
| 288 | Selena Gomez | Parachute | 241 | `selena-gomez_parachute` |
| 289 | Gabriel Diniz | É Pra Tocar No Paredão | 173 | `gabriel-diniz_-pra-tocar-no-paredao` |
| 290 | Lorde | Still Sane | 144 | `lorde_still-sane` |
| 291 | U2 | North And South Of The River | 129 | `u2_north-and-south-of-the-river` |
| 292 | Miley Cyrus | Hands In The Air | 102 | `miley-cyrus_hands-in-the-air` |
| 293 | David Guetta | I'll Keep Loving You | 45 | `david-guetta_ill-keep-loving-you` |
| 294 | Bethel Church | You Are Faithful (amy Miller) | 26 | `bethel-church_you-are-faithful-amy-miller` |
| 295 | Birdy | Terrible Love | 0 | `birdy_terrible-love` |
| 296 | Supercombo | Vou Assombrar Seus Amigos e Parentes | 0 | `supercombo_vou-assombrar-seus-amigos-e-parentes` |

##### `EmG` (`id_seq=2`) — 4 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Ultraje a Rigor | Inútil | 291127 | `ultraje-a-rigor_inutil` |
| 2 | Planet Hemp | Mão Na Cabeça | 9934 | `planet-hemp_mao-na-cabeca` |
| 3 | Marcelo D2 | Mão Na Cabeça | 4327 | `marcelo-d2_mao-na-cabeca` |
| 4 | Eric Clapton | Fall Like Rain | 2021 | `eric-clapton_fall-like-rain` |

##### `CA7DmG7` (`id_seq=3`) — 5 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Martinho da Vila | Na Aba | 19877 | `martinho-da-vila_na-aba` |
| 2 | Benito Di Paula | Bendito Seja | 9206 | `benito-di-paula_bendito-seja` |
| 3 | Arlindo Cruz | Vai Pro Lado de Cá | 4815 | `arlindo-cruz_vai-pro-lado-de-ca` |
| 4 | Dorival Caymmi | Requebre que Eu Dou um Doce | 3822 | `dorival-caymmi_requebre-que-eu-dou-um-doce` |
| 5 | Bezerra da Silva | Na Aba | 2227 | `bezerra-da-silva_na-aba` |

##### `GmF` (`id_seq=4`) — 7 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Raça Negra | Cheia de Manias | 469306 | `raca-negra_cheia-de-manias` |
| 2 | Oriente | Fé | 23029 | `oriente_fe` |
| 3 | Shakira | Rabiosa | 19924 | `shakira_rabiosa` |
| 4 | Aviões do Forró | Piriri Pom Pom | 18935 | `avioes-do-forro_piriri-pom-pom` |
| 5 | Raça Negra | Cheias de Manias | 11487 | `raca-negra_cheias-de-manias` |
| 6 | Asa de Águia | Marajá | 6837 | `asa-de-aguia_maraja` |
| 7 | Sérgio Lopes | Carta À Sardes | 169 | `sergio-lopes_carta-a-sardes` |

##### `CC7FFm` (`id_seq=5`) — 3 músicas

| # | Artista | Música | Popularidade | `id_unico_musica` |
|---|---|---|---|---|
| 1 | Exaltasamba | Jogo de Sedução | 235078 | `exaltasamba-musicas_jogo-de-seducao` |
| 2 | Revelação | Jogo de Sedução | 83084 | `revelacao_jogo-de-seducao` |
| 3 | Claudia Leitte | Bem Vindo Amor | 41621 | `claudia-leitte_bem-vindo-amor` |

#### 2.3 Hipóteses candidatas aplicadas aos dados (Q2)

O script `/tmp/hypotheses_metrics.py` replica o carregamento de `main.py` e
compara cada hipótese de §1.5 com o conjunto de músicas que têm a tag. Comando
executado:

```bash
python3 /tmp/hypotheses_metrics.py
```

A saída completa ficou em `/tmp/hypotheses_metrics.out`. A tabela abaixo usa a
forma **total de matches (falsos positivos / falsos negativos)** em relação ao
conjunto de tags; falsos positivos são músicas que a regra casa e a tag não
marca, e falsos negativos são músicas marcadas pela tag que a regra não casa.

| Hipótese | `BmGDA` | `CGAmF` | `EmG` | `CA7DmG7` | `GmF` | `CC7FFm` |
|---|---:|---:|---:|---:|---:|---:|
| H1 tag-like | 199 (0/0) | 296 (0/0) | 4 (0/0) | 5 (0/0) | 7 (0/0) | 3 (0/0) |
| H2 contígua ordenada | 866 (667/0) | 1.216 (920/0) | 3.110 (3.106/0) | 96 (91/0) | 1.039 (1.032/0) | 132 (129/0) |
| H3 subsequência ordenada | 4.763 (4.564/0) | 5.887 (5.591/0) | 13.643 (13.639/0) | 427 (422/0) | 3.641 (3.634/0) | 280 (277/0) |
| H4 inclusão de conjunto | 5.768 (5.569/0) | 6.894 (6.598/0) | 14.160 (14.156/0) | 582 (577/0) | 3.847 (3.840/0) | 365 (362/0) |
| H5 inclusão de multiconjunto | 5.768 (5.569/0) | 6.894 (6.598/0) | 14.160 (14.156/0) | 582 (577/0) | 3.847 (3.840/0) | 365 (362/0) |
| H6 igualdade de conjunto | 395 (196/0) | 532 (236/0) | 4 (0/0) | 6 (1/0) | 7 (0/0) | 3 (0/0) |
| H7 igualdade de multiconjunto | 5 (3/197) | 5 (4/295) | 0 (0/4) | 0 (0/5) | 0 (0/7) | 0 (0/3) |
| H8 contígua com runs colapsados | 882 (683/0) | 1.235 (939/0) | 3.110 (3.106/0) | 96 (91/0) | 1.039 (1.032/0) | 132 (129/0) |

Resultado bruto que confirma a leitura do gerador de tags:

```text
tag_rule equals contiguous_subset for all sequences?
  BmGDA True tag=199 cs=199 only_tag=0 only_cs=0
  CGAmF True tag=296 cs=296 only_tag=0 only_cs=0
  EmG True tag=4 cs=4 only_tag=0 only_cs=0
  CA7DmG7 True tag=5 cs=5 only_tag=0 only_cs=0
  GmF True tag=7 cs=7 only_tag=0 only_cs=0
  CC7FFm True tag=3 cs=3 only_tag=0 only_cs=0
```

A diferença entre H1 e H2 não é de ordem nem de adjacência: é o vocabulário
fechado. A tabela seguinte parte das músicas que contêm a sequência como bloco
contíguo e separa as que têm algum acorde fora da sequência.

| Sequência | Contíguas (H2) | Sem acorde fora da sequência | Com acorde fora da sequência |
|---|---:|---:|---:|
| `BmGDA` | 866 | 199 | 667 |
| `CGAmF` | 1.216 | 296 | 920 |
| `EmG` | 3.110 | 4 | 3.106 |
| `CA7DmG7` | 96 | 5 | 91 |
| `GmF` | 1.039 | 7 | 1.032 |
| `CC7FFm` | 132 | 3 | 129 |

Exemplos de falsos positivos mais populares, para mostrar o tipo de música que
cada regra acrescenta:

- **H2 (contígua):** `BmGDA` casa Darvin — “Pensa Em Mim” (2.311.345); `CGAmF`
  casa Victor e Leo — “Fotos” (3.484.507); `EmG` casa Jorge e Mateus — “De
  Tanto Te Querer” (2.588.459); `CA7DmG7` casa Bruno e Marrone — “Apenas um
  Sorriso” (166.229); `GmF` casa The Beatles — “Hey Jude” (1.938.036); e
  `CC7FFm` casa Bruno e Marrone — “Acorrentado Em Você” (557.361).
- **H3 (subsequência):** `BmGDA` casa Skank — “Sutilmente” (3.104.944);
  `CGAmF` casa Red Hot Chili Peppers — “Californication” (4.401.236); `EmG`
  casa Legião Urbana — “Pais e Filhos” (4.973.242).
- **H4/H5 (conjunto/multiconjunto):** `BmGDA` e `CGAmF` também casam Red Hot
  Chili Peppers — “Californication” (4.401.236); `EmG` casa Legião Urbana —
  “Pais e Filhos” (4.973.242); `GmF` casa Cássia Eller — “Malandragem”
  (3.145.635); `CC7FFm` casa Bruno e Marrone — “Boate Azul” (2.736.687).
- **H6 (igualdade de conjunto):** `BmGDA` casa Mamonas Assassinas — “Sábado de
  Sol” (813.726); `CGAmF` casa Clarice Falcão — “De Todos Os Loucos do Mundo”
  (604.443); `CA7DmG7` casa Os Originais do Samba — “Samba da Vizinha”
  (1.812). Para `EmG`, `GmF` e `CC7FFm`, H6 não teve falso positivo.
- **H7 (igualdade de multiconjunto):** `BmGDA` casa Ministério Nova Geração —
  “Eu Anseio” (2.590); `CGAmF` casa Aviões do Forró — “Lapada Na Rachada”
  (60.044).

Observações sobre os resultados:

- H1 é a única hipótese que reproduz as tags exatamente para as 6 sequências.
  Isso é evidência de compatibilidade com o legado, não uma escolha de solução.
- H2, H3, H4 e H5 têm zero falsos negativos: todas as músicas com tag são
  incluídas, mas o conjunto cresce muito. H6 também tem zero falsos negativos
  nas 6, mas só porque a tag implica que a música contém todos os acordes da
  sequência; ela ainda adiciona falsos positivos em `BmGDA`, `CGAmF` e
  `CA7DmG7`.
- H7 tem recall baixo: só 2 das 199 tags de `BmGDA` e 1 das 296 tags de `CGAmF`
  têm exatamente o multiconjunto da sequência. A maioria das músicas com tag
  repete acordes ou usa acordes do vocabulário além da sequência.
- H4 e H5 têm os mesmos totais porque as 6 sequências não repetem acordes. Isso
  não vale para uma sequência customizada com repetição.
- A contagem case-sensitive de H2 é igual à case-insensitive para as 6
  sequências, porque os acordes dessas sequências aparecem na mesma grafia no
  CSV. O vocabulário geral tem 151 grupos de colisão de caixa (§1.3), então a
  normalização ainda é uma decisão em aberto para sequências novas.
- A regra sobre a string bruta e a regra sobre `musica.cifra` limpa produzem o
  mesmo conjunto de tags para as 6. Isso não garante equivalência para músicas
  com `|`, espaços ou tokens vazios; esses casos precisam de teste sintético.

### 3. Banco de dados: estado atual e restrições — Q3

#### 3.1 Dockerfile, dependências e persistência como estão hoje

- `Dockerfile:1` usa `FROM python:3.9-slim`.
- `Dockerfile:3` define `WORKDIR /app`.
- `Dockerfile:5-6` copiam `requirements.txt` e executam
  `pip install --no-cache-dir -r requirements.txt`.
- `Dockerfile:8` copia o repositório inteiro para a imagem (`COPY . .`),
  incluindo `data/top/dataset_final.csv`; o `.dockerignore` exclui apenas
  `.git`, `.venv`, `__pycache__` e `*.pyc` (`.dockerignore:1-4`).
- `Dockerfile:10` expõe a porta 8080.
- `Dockerfile:12` executa
  `gunicorn --bind 0.0.0.0:8080 main:app`. O comando não especifica
  `--workers` nem arquivo de configuração do gunicorn.
- `requirements.txt:4-5` lista somente `Flask==3.1.3` e `gunicorn==23.0.0`.
  Não há driver de banco, ORM, ferramenta de migração ou dependência de
  persistência.
- O `Dockerfile` não tem instrução `VOLUME`, não cria diretório de dados
  persistente e não define `USER` (portanto o processo roda como root na
  imagem). Não existe `docker-compose.yml` nem outro manifesto de serviços no
  repositório; os únicos arquivos de container encontrados são `Dockerfile` e
  `.dockerignore`.
- O comando documentado no README é `docker run -p 8080:8080 ciframe`
  (`README.md:15-18`), sem `-v`/bind mount.
- A ADR 0001 registra a escolha de um único `Dockerfile` local via gunicorn,
  mantendo a arquitetura de `main.py` único, busca em CSV na memória e Python
  3.9 (`docs/adr/0001-local-only-docker-deploy.md:9-12`), e deixa o alvo de
  nuvem indecidido (`docs/adr/0001-local-only-docker-deploy.md:14-16`).
- Em runtime, `main.py:49` abre `data/top/dataset_final.csv` por caminho
  relativo. Com `WORKDIR /app`, o caminho efetivo é
  `/app/data/top/dataset_final.csv`. O CSV é lido uma vez no import
  (`main.py:49-98`); não há recarga por requisição.
- Não há hoje nenhum arquivo de banco, esquema, migração ou inicialização de
  banco no repositório.

#### 3.2 Restrições que um banco embarcado precisa satisfazer

As restrições abaixo vêm dos requisitos fixos do enunciado e do código/deploy
atual; elas são registradas sem escolha de tecnologia.

1. **Container único e local, sem serviço externo adicional.** O enunciado fixa
   o `Dockerfile` único e local-only (`00-enunciado.md:63-65`); a ADR 0001
   descreve o mesmo modelo (`docs/adr/0001-local-only-docker-deploy.md:9-12,14-16`).
2. **Músicas e gêneros continuam no CSV em memória.** Não podem ser migrados
   para o banco (`00-enunciado.md:60-62`); o carregamento atual está em
   `main.py:49-98` e alimenta `musicas`, `genero_musicas`, `generos` e
   `acordes` (`main.py:37-47,74-96`).
3. **Somente o catálogo de sequências é persistido.** O enunciado separa
   explicitamente o catálogo de sequências do catálogo de músicas/gêneros
   (`00-enunciado.md:52-53,60-62`). Hoje o catálogo de sequências é o literal
   `sequencias` (`main.py:40-45`).
4. **Persistência entre reinícios.** O catálogo não pode voltar a ser perdido ao
   reiniciar o container (`00-enunciado.md:52-53`). O `Dockerfile` atual não
   declara `VOLUME` e o comando do README não usa volume (`README.md:15-18`):
   um arquivo gravado dentro do container fica na camada gravável e sobrevive a
   `docker restart`, mas não a `docker rm`/recriação do container sem volume ou
   bind mount.
5. **Compatibilidade com Python 3.9.** A imagem é `python:3.9-slim`
   (`Dockerfile:1`) e a ADR 0001 registra Python 3.9
   (`docs/adr/0001-local-only-docker-deploy.md:11`). Qualquer dependência
   precisa funcionar nessa versão.
6. **Instalação compatível com o Dockerfile atual.** O único passo de
   instalação é `pip install -r requirements.txt` (`Dockerfile:5-6`); não há
   `apt-get`, compilador ou `build-essential` no `Dockerfile`. A solução precisa
   ser biblioteca padrão do Python 3.9 ou instalável via `pip` no slim, sem
   serviço externo. (Fato da linguagem: o módulo `sqlite3` faz parte da
   biblioteca padrão do CPython 3.9; o projeto não o usa hoje e ele não aparece
   em `requirements.txt`.)
7. **Contrato de resposta preservado.** Os endpoints continuam retornando
   `json.dumps(...)` como string, não `jsonify` (`00-enunciado.md:68`;
   `main.py:197,201`).
8. **Associação com os ids atuais das 6 sequências.** O matching atual compara
   `str(id_seq)` com as tags (`main.py:209`) e os ids 0-5 vêm do dicionário
   `main.py:40-45`. Qualquer persistência do catálogo precisa manter essa
   associação para as 6 sequências originais continuarem produzindo os mesmos
   resultados (`00-enunciado.md:66-67`).
9. **Inicialização no mesmo processo de serving.** O CSV já é carregado no
   import de `main.py` (`main.py:49-98`) e o gunicorn importa `main:app`
   (`Dockerfile:12`); não há script de bootstrap separado nem serviço auxiliar.
10. **Ausência de infraestrutura de banco hoje.** Não há dependência, esquema,
    migração, volume, arquivo `.db` ou teste de banco no repositório; o
    `requirements.txt` tem apenas Flask e gunicorn (`requirements.txt:4-5`).

#### 3.3 Hipóteses candidatas de banco (Q3)

Nenhum candidato foi escolhido. Todos abaixo são embarcados, sem serviço
externo adicional, e teriam que lidar com o mesmo fato de deploy: o
`Dockerfile` atual não declara `VOLUME` (`Dockerfile:1-12`) e o comando do
README não usa `-v` (`README.md:15-18`). Um arquivo gravado na camada gravável
do container sobrevive a `docker restart`, mas não a `docker rm`/recriação sem
volume nomeado, bind mount ou `VOLUME` na imagem. Essa é uma decisão de deploy
separada da escolha do banco.

| Candidato | O que é | Implicação no `Dockerfile`/dependências | Persistência e bordas | Como validar |
|---|---|---|---|---|
| SQLite em arquivo | Banco SQL embutido, uma biblioteca e um arquivo local; `sqlite3` faz parte da biblioteca padrão do CPython 3.9. | Não exigiria `pip` novo; o `Dockerfile:5-6` continuaria igual. Precisaria de caminho gravável e, para sobreviver a `docker rm`, de volume/bind mount. | Arquivo sobrevive a restart; não sobrevive a recriação sem volume. Escritas concorrentes exigem cuidado (`WAL`, `busy_timeout`, transações); o gunicorn atual não fixa `--workers` (`Dockerfile:12`). | Criar o arquivo, inserir, reiniciar, recriar com e sem volume, consultar; testar escrita concorrente. |
| SQLite em memória | SQLite com `:memory:`, sem arquivo. | Nenhuma dependência nova; nenhum volume. | Não persiste entre reinícios; não atende sozinho ao requisito de persistência. | Útil apenas como fixture de teste; confirmar que o catálogo desaparece ao reiniciar. |
| JSON em arquivo | Lista/dicionário serializado com `json` da biblioteca padrão. | Nenhuma dependência nova; precisaria de caminho gravável e volume para `docker rm`. | Simples e legível; sem transações, índices ou consultas; escritas concorrentes exigem lock ou substituição atômica. | Inserir, reiniciar, recriar, validar leitura e escrita concorrente. |
| TinyDB | Banco de documentos embutido, instalado via `pip`, persistido em JSON. | Adicionaria dependência ao `requirements.txt`; a instalação continuaria via `pip` (`Dockerfile:5-6`). | Mesmo volume/bind mount; concorrência e atomicidade dependem do uso; não há SQL. | Testar criação, leitura, reinício, recriação e escrita concorrente. |
| `shelve`/`dbm` | Armazenamento chave-valor da biblioteca padrão. | Nenhuma dependência nova; caminho gravável e volume. | Binário, sem SQL; concorrência limitada; bom para poucos registros, não para consultas relacionais. | Testar persistência, recriação e acesso concorrente. |
| DuckDB | Banco analítico embutido, instalado via `pip`, com arquivo local. | Adicionaria dependência e wheel binária; o `Dockerfile` não tem `apt-get`/compilador (`Dockerfile:5-6`). | Arquivo sobrevive a restart; precisa de volume para recriação; normalmente um escritor por vez. | Verificar wheel para Python 3.9, criar/consultar, reiniciar e recriar. |
| LMDB/RocksDB | Armazenamento chave-valor embutido via `pip`. | Adicionaria dependência binária; mais complexo que o necessário para um catálogo pequeno. | Arquivo + volume; concorrência e transações variam por biblioteca. | Testar instalação no slim, persistência e concorrência. |
| PostgreSQL/MySQL externo | Serviço de banco separado do container da aplicação. | Exigiria outro serviço, rede e configuração; conflita com o container único/local-only (`00-enunciado.md:63-65`; ADR 0001). | Persistência robusta, mas fora do modelo de deploy atual. | Não é candidato sob as restrições atuais; registrar apenas como alternativa descartada por restrição. |

Pontos que valem para todos os candidatos:

- O catálogo é pequeno (6 sequências hoje), mas o formato precisa representar
  ordem e repetição de acordes se a regra de matching escolhida for H2/H3/H5/H8;
  um único campo texto/JSON e uma tabela filha de acordes têm implicações
  diferentes de consulta e migração.
- O processo roda como root na imagem atual, porque não há `USER` no
  `Dockerfile`; qualquer arquivo criado pelo processo teria esse dono.
- O gunicorn é iniciado sem `--workers` (`Dockerfile:12`); o default do gunicorn
  é um worker síncrono, mas isso não é uma garantia se a configuração mudar.
- Não há script de bootstrap separado: o CSV é carregado no import de
  `main.py` (`main.py:49-98`) e o gunicorn importa `main:app`
  (`Dockerfile:12`). Um banco precisaria inicializar schema/seed nesse mesmo
  fluxo ou em um passo próprio.
- O `requirements.txt` só tem Flask e gunicorn (`requirements.txt:4-5`); cada
  candidato via `pip` muda a imagem e precisa ser compatível com Python 3.9
  (`Dockerfile:1`).

### 4. Frontend existente: `#/porsequencia` — Q4

#### 4.1 Rota e carregamento

- A rota `/porsequencia` está em `static/assets/js/routes.js:17-21` e usa
  `templates/sequencia.html` com `SequenciaController` e
  `controllerAs: "Sequencia"`.
- O link para a página está em `static/templates/home.html:79`
  (`<a href="#/porsequencia">`).
- `static/index.html:123` contém `<div class="page" ng-view></div>`; os scripts
  são carregados em `static/index.html:138-147`, incluindo
  `assets/js/controllers/sequencia.js` na linha 145.
- O módulo Angular e a constante `GENEROS` estão em
  `static/assets/js/app.js:1-58`; a constante é uma lista fixa de gêneros
  (`static/assets/js/app.js:6-58`).

#### 4.2 Controller (`static/assets/js/controllers/sequencia.js`)

- As quatro sequências são objetos literais `sequencia1`..`sequencia4`
  (`sequencia.js:2-31`). Cada objeto tem `index: 1` e uma lista `acordes` de
  objetos `{acorde, cor}`.
- `vm.sequenciasFamosas` é inicializado vazio e recebe apenas essas quatro
  (`sequencia.js:33-37`). Não há chamada `$http` para carregar catálogo; o
  `$http` é usado somente na busca (`sequencia.js:77`).
- `vm.generos = GENEROS` (`sequencia.js:43`) usa a constante fixa do
  `app.js:6-58`; a página não chama `GET /generos`.
- `createChordsString` (`sequencia.js:55-61`) concatena `chords[i].acorde` com
  vírgula e remove a última vírgula.
- `pesquisarPorSequencia` (`sequencia.js:63-90`) define a sequência escolhida,
  monta `similares?sequencia=` + string de acordes e, se houver gênero
  selecionado, acrescenta `&generos=` (`sequencia.js:72-76`). `apiUrl` é `""`
  (`sequencia.js:72`), então a URL é relativa à origem Flask. Não há parâmetro
  `pagina` na requisição.
- No sucesso, `vm.musics = data` (`sequencia.js:83`); no erro,
  `vm.esfigeSpeech = "Ops! Algo errado."` (`sequencia.js:85-89`).
- `limparPesquisa` zera `minhaSequencia` e `musics` (`sequencia.js:92-95`);
  `goToLirics` abre `music.url` em nova janela (`sequencia.js:97-99`);
  `goToResults` rola até `#results` (`sequencia.js:101-104`).
- `temAcorde` (`sequencia.js:47-53`) verifica
  `vm.minhaSequencia.acordes.indexOf(acorde) > -1`; o template passa esse valor
  como `acorde-checked` para o directive `df-hex` (`sequencia.html:7`), cujo
  escopo declara `acordeChecked: '='` (`static/assets/js/directives/df-hex.js:7`).

#### 4.3 Template (`static/templates/sequencia.html`)

- A lista de sequências é renderizada em `sequencia.html:5-8` com
  `ng-repeat='sequencia in Sequencia.sequenciasFamosas'` e
  `ng-click="Sequencia.pesquisarPorSequencia(sequencia)"`; cada acorde é um
  `<df-hex>` (`sequencia.html:7`).
- O botão “Encontrei essas músicas” aparece condicionado a
  `Sequencia.showSearchResultsCount` e chama `goToResults()`
  (`sequencia.html:10-14`).
- O painel da sequência escolhida mostra o gênero em um `<select>` com
  `ng-options="genero for genero in Sequencia.generos | orderBy:'genero'"`
  (`sequencia.html:24-30`) e os acordes da sequência
  (`sequencia.html:34`).
- Os resultados são cards em `sequencia.html:40-59`, com
  `ng-repeat="music in Sequencia.musics | orderBy:'-popularidade'"`,
  `ng-hide="music.diferenca.length"` (`sequencia.html:42-43`), clique em
  `Sequencia.goToLirics(music)` (`sequencia.html:45`) e exibição de
  `music.nome_musica`, `music.nome_artista` e `music.genero`
  (`sequencia.html:51-53`).
- O endpoint de sequência não inclui a chave `diferenca` nos objetos retornados
  (`main.py:210-220`). No template, `music.diferenca` fica indefinido; a
  expressão Angular resulta em valor falsy e o `ng-hide` não esconde os cards.
- Não há formulário, campo de texto ou botão para cadastrar sequência; não há
  chamada para listar o catálogo do backend nem para `GET /generos`.

#### 4.4 O descompasso 4 vs. 6

| Posição na UI | Variável JS | Acordes no JS | Query gerada | Chave no backend | `id_seq` | Total de matches por tag | Está no JS? | Está no backend? |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | `sequencia1` | `Bm, G, D, A` | `similares?sequencia=Bm,G,D,A` | `BmGDA` | 0 | 199 | sim | sim |
| 2 | `sequencia2` | `C, G, Am, F` | `similares?sequencia=C,G,Am,F` | `CGAmF` | 1 | 296 | sim | sim |
| 3 | `sequencia3` | `Gm, F` | `similares?sequencia=Gm,F` | `GmF` | 4 | 7 | sim | sim |
| 4 | `sequencia4` | `C, C7, F, Fm` | `similares?sequencia=C,C7,F,Fm` | `CC7FFm` | 5 | 3 | sim | sim |
| — | — | `Em, G` | — | `EmG` | 2 | 4 | não | sim |
| — | — | `C, A7, Dm, G7` | — | `CA7DmG7` | 3 | 5 | não | sim |

- O backend tem seis chaves, na ordem de ids 0..5 (`main.py:40-45`); o JS tem
  quatro, correspondentes aos ids 0, 1, 4 e 5 (`sequencia.js:2-37`). Ficam de
  fora `EmG` (id 2) e `CA7DmG7` (id 3).
- O campo `index` dos quatro objetos JS é sempre `1` (`sequencia.js:3,11,19,25`)
  e não é lido pelo controller nem pelo template; a posição na UI vem da ordem
  dos `push` em `sequencia.js:34-37`.
- As consultas com vírgula geradas pelo JS funcionam porque o backend remove as
  vírgulas antes do lookup (`main.py:191`); foi verificado ao vivo que
  `Bm,G,D,A`, `C,G,Am,F`, `Gm,F` e `C,C7,F,Fm` retornam as mesmas chaves
  `BmGDA`, `CGAmF`, `GmF` e `CC7FFm`.
- Como o controller não envia `pagina`, o backend usa o default `'1'`
  (`main.py:176`) e a UI recebe no máximo 100 resultados
  (`main.py:35,226-228`), mesmo quando o total por tag é 199 ou 296. O
  `orderBy:'-popularidade'` do template reordena apenas o que veio na página 1.
- As sequências ausentes no JS (`EmG`, `CA7DmG7`) continuam acessíveis pela API
  se a chave for passada manualmente: os totais por tag são 4 e 5,
  respectivamente.

#### 4.5 Hipóteses candidatas de frontend (Q4)

Nenhuma opção foi escolhida. A página hoje tem quatro objetos fixos
(`sequencia.js:2-37`) e não consulta catálogo; qualquer opção abaixo teria que
decidir se o catálogo vem do backend, se existe formulário de cadastro e como a
lista é paginada.

| Candidato | O que mudaria | O que já existe | Bordas e como validar |
|---|---|---|---|
| Manter os 4 objetos e só alinhar para 6 | Acrescentar `EmG` e `CA7DmG7` como `sequencia5`/`sequencia6`; nenhuma chamada nova ao backend. | A lista fixa e o `ng-repeat` (`sequencia.js:2-37`; `sequencia.html:5-8`). | Continua sem refletir catálogo real e sem cadastro; validar que as 6 queries batem com as chaves de `main.py:40-45`. |
| Buscar o catálogo no backend ao carregar | `SequenciaController` faria uma chamada inicial e preencheria `vm.sequenciasFamosas` com a resposta. | `$http` já é injetado e usado na busca (`sequencia.js:1,77`); o `ng-repeat` já aceita uma lista. | Precisa de endpoint de listagem, estados de carregando/erro/vazio, formato estável e ordem; validar no browser e com `curl`. |
| Renderizar o catálogo no servidor | Flask injetaria a lista no HTML/template antes de o Angular iniciar. | Flask serve `static/index.html` (`main.py:101-103`); o template é estático (`sequencia.html:1-63`). | Evita um XHR inicial, mas acopla HTML/Flask e ainda precisa alimentar o controller; validar com o template servido pelo Flask, não por `file://`. |
| Híbrido: fallback fixo + atualização | Manter os 4/6 objetos como fallback e substituir quando a API responder. | A lista fixa atual e o `$http` existente. | Duplica a fonte de verdade e precisa definir o que fazer se a API falhar; validar com backend indisponível e com catálogo maior. |
| Formulário de cadastro + POST | Adicionar campos de nome/acordes, validação e envio; depois recarregar o catálogo. | Não há formulário, campo ou endpoint de criação (`sequencia.html:1-63`; `main.py:170-201`). | Precisa definir validação, duplicidade, erro, ordem e atualização da lista; validar com entradas vazias, inválidas, repetidas e válidas. |
| Manter os 4 atuais sem mudança | Nenhuma alteração no JS. | Comportamento atual de §4.2-4.4. | É o baseline, mas não atende ao requisito de a página refletir o catálogo real (`00-enunciado.md:54-55`); serve para comparar regressão. |
| Paginação na UI | Enviar `pagina` e adicionar controles, ou buscar todas as páginas, ou aumentar `TAM_PAGINA`. | O controller não envia `pagina` (`sequencia.js:72-77`); o backend usa default `'1'` (`main.py:176`) e corta em 100 (`main.py:35,226-228`). | O `orderBy:'-popularidade'` só reordena a página recebida (`sequencia.html:42`); validar totais 199/296 e páginas 2/3. |
| Cores e ordem das sequências | Backend devolve `cor`/posição, o frontend mapeia cores, ou a UI mantém uma paleta fixa. | Cada acorde JS tem `cor` fixa (`sequencia.js:5-8`); `index` é sempre `1` e não é lido (`sequencia.js:3,11,19,25`); a ordem vem dos `push` (`sequencia.js:34-37`). | Um catálogo só com acordes não traz cor; validar que a ordem exibida e as cores não dependem de detalhes internos do backend. |
| Gêneros | Continuar com `GENEROS` fixo ou buscar `GET /generos`. | `vm.generos = GENEROS` (`sequencia.js:43`; `app.js:6-58`); `/generos` existe (`main.py:158-160`) mas não é usado pela página. | Validar se a lista fixa cobre os gêneros do catálogo e se o filtro continua funcionando (`main.py:178-182,266-272`). |

### 5. Conexões entre componentes e fluxo de dados

- **Carga única do CSV:** `main.py:49-98` lê `data/top/dataset_final.csv`,
  cria `Musica` (`main.py:69-72`; `musica.py:1-22`) e monta
  `musicas_dict`/`musicas` (`main.py:74,87-89`), `genero_musicas`
  (`main.py:82-85,95-96`), `generos` (`main.py:66,92`) e `acordes`
  (`main.py:77-78`).
- **Endpoints de leitura:** `/` serve `static/index.html`
  (`main.py:101-103`); `/<path>` serve arquivos estáticos (`main.py:109-112`);
  `/search` (`main.py:114-142`), `/musicas` (`main.py:154-156`), `/generos`
  (`main.py:158-160`), `/acordes` (`main.py:162-164`) e
  `/musica/<m_id>/` (`main.py:166-168`) consultam as estruturas em memória.
  Todos retornam `json.dumps(...)`.
- **Fluxo da busca por sequência:** objetos JS fixos
  (`sequencia.js:2-37`) → `createChordsString` (`sequencia.js:55-61`) →
  `GET /similares?sequencia=...` (`sequencia.js:72-77`) → remoção de vírgulas e
  lookup em `sequencias` (`main.py:191-196`) → `id_seq` →
  `get_similares_por_sequencia` filtra `musicas` por gênero
  (`main.py:203-209`) → slice de página (`main.py:226-228`) →
  `json.dumps` (`main.py:197`) → `vm.musics` (`sequencia.js:83`) → cards
  (`sequencia.html:40-59`).
- **Fluxo de gênero:** a UI usa a constante `GENEROS`
  (`app.js:6-58`; `sequencia.js:43`) → `&generos=` (`sequencia.js:74-76`) →
  `generos_tag.split(',')` (`main.py:179-182`) → `apply_filtro`
  (`main.py:266-272`). O endpoint `GET /generos` existe (`main.py:158-160`),
  mas não é usado por `#/porsequencia`.
- **Fronteira de persistência hoje:** músicas e gêneros vêm do CSV em memória;
  o catálogo de sequências é o dicionário literal `main.py:40-45`; não há
  banco. O frontend de sequência não lê catálogo do backend: ele usa os quatro
  objetos fixos de `sequencia.js:2-37`.
- **Servidor:** `Dockerfile:12` serve `main:app` com gunicorn na porta 8080;
  no modo `python main.py`, `main.py:279-280` usa `app.run(debug=True)` e a
  porta default 5000.

## Trade-offs identificados

As alternativas abaixo são reais e nenhuma foi decidida. Elas se cruzam: a regra
de matching define se `musica.cifra` ou `musica.acordes` basta; o banco define
onde o catálogo vive; o frontend define como o catálogo chega à tela e como o
cadastro entra.

### Matching

| Opção | Prós | Contras | Evidência |
|---|---|---|---|
| H1 — tag-like (contígua + vocabulário fechado) | Reproduz exatamente as 6 tags atuais; zero falsos positivos/negativos; critério de regressão simples. | É um artefato do gerador: qualquer acorde extra na música desqualifica; baixa recall e resultado pouco intuitivo para “a sequência aparece”; exige verificar o vocabulário inteiro da música. | 199/296/4/5/7/3 matches, iguais às tags (§2.3). |
| H2 — contígua ordenada | Intuição direta de “a sequência aparece”; ordem e adjacência importam; inclui todas as tags. | Acordes de passagem quebram o match; gera 866/1.216/3.110/96/1.039/132, muito acima das tags; ainda precisa decidir repetição e normalização. | Todas as músicas com tag estão contidas; FP de 91 a 3.106 (§2.3). |
| H3 — subsequência ordenada | Tolera acordes de passagem; preserva a ordem; inclui todas as tags. | Pode casar acordes espalhados pela música; 4.763/5.887/13.643/427/3.641/280, com precisão baixa; custo de varredura maior. | FP de 277 a 13.639 (§2.3). |
| H4 — inclusão de conjunto | Simples; usa `musica.acordes` (`musica.py:17`); não precisa de ordem. | Ignora ordem e repetição; casa músicas com os mesmos acordes em qualquer ordem; 5.768/6.894/14.160/582/3.847/365. | FP de 362 a 14.156 (§2.3). |
| H5 — inclusão de multiconjunto | Acrescenta consciência de repetição ao H4. | Continua ignorando ordem; para as 6 dá o mesmo total de H4; implementação e validação mais complexas. | Mesmos totais de H4 porque as 6 não repetem acordes (§2.3). |
| H6/H7 — igualdade de conjunto/multiconjunto | Regra precisa; rejeita acordes extras; H7 também exige multiplicidade. | Recall baixo; H6 ainda aceita ordem trocada; H7 perde quase todas as tags; não serve como regra geral de descoberta. | H6: 395/532/4/6/7/3; H7: 5/5/0/0/0/0 (§2.3). |
| Repetição: ignorar, colapsar runs ou exigir multiplicidade | “Ignorar” é simples; “colapsar” lida com `A;A;B`; “exigir” preserva a intenção de repetição. | Ignorar perde informação; colapsar só trata repetição imediata; exigir multiplicidade pode rejeitar músicas que repetem de outra forma. | H8 muda 866→882 e 1.216→1.235; H7 mostra que exigir multiconjunto exato é restritivo (§2.3). |
| Normalização: caixa, enarmônicos, tokens não acordais | Aumenta a cobertura e evita falsos negativos por grafia; o gerador já lowercasa (`scripts/generate_data_set.py:12`). | Pode unir acordes distintos (`Am7`/`AM7`), exigir tabela enarmônica e mudar os totais; não há comportamento atual para copiar. | 151 grupos de colisão de caixa; 13 tokens sem letra; contagens enarmônicas diferentes (§1.3). |
| Matching ao vivo vs. pré-computado | Ao vivo é simples e sempre reflete o catálogo; pré-computado pode ser rápido por consulta. | Ao vivo varre 59.444 músicas com cifra por requisição (`main.py:203-209`); pré-computado precisa invalidar/atualizar quando o catálogo muda e armazenar tags por sequência. | `musicas` tem 67.585 linhas; 3.505.331 tokens; `get_similares_por_sequencia` filtra a coleção inteira. |

### Banco

| Opção | Prós | Contras | Implicação de deploy |
|---|---|---|---|
| SQLite em arquivo | Biblioteca padrão; SQL, transações e schema; um arquivo; sem serviço. | Precisa de volume para `docker rm`; concorrência de escrita; schema/migração; arquivo binário no container. | `Dockerfile` pode ficar igual; persistência real exige `VOLUME` ou `-v`. |
| SQLite em memória | Nenhum arquivo, nenhuma dependência, simples para teste. | Não persiste entre reinícios; não atende sozinho ao requisito. | Nenhum volume; catálogo perdido ao reiniciar. |
| JSON em arquivo | Biblioteca padrão; legível; fácil de inspecionar e versionar. | Sem transações/índices; concorrência exige lock ou escrita atômica; validação manual. | Precisa de caminho gravável e volume para `docker rm`. |
| TinyDB | API de documentos simples; persistência em JSON; instalação via `pip`. | Dependência nova; concorrência/atomicidade; sem SQL. | `requirements.txt` e imagem mudam; mesmo volume. |
| `shelve`/`dbm` | Biblioteca padrão; chave-valor simples. | Binário, sem SQL, concorrência limitada; formato menos inspecionável. | Caminho gravável + volume. |
| DuckDB | SQL analítico embutido; arquivo local; sem serviço. | Dependência/wheel binária; normalmente um escritor; imagem maior; compatibilidade com Python 3.9 precisa ser verificada. | `requirements.txt` muda; volume para recriação. |
| LMDB/RocksDB | Chave-valor embutido, transações e boa concorrência. | Dependência binária; complexidade desproporcional para 6 registros; API de baixo nível. | `requirements.txt` muda; volume. |
| PostgreSQL/MySQL externo | Concorrência e operação maduras. | Exige serviço/rede/configuração; conflita com o container único/local-only. | Não é candidato sob as restrições atuais (`00-enunciado.md:63-65`). |

### Frontend

| Opção | Prós | Contras | Validação |
|---|---|---|---|
| Alinhar a lista fixa para 6 | Menor mudança; preserva o comportamento Angular atual; não exige endpoint novo. | Continua hardcoded; não reflete catálogo real; duplica a fonte de verdade; não permite cadastro. | Comparar as 6 queries com `main.py:40-45` e conferir totais. |
| Buscar catálogo no backend | A página passa a refletir o catálogo; uma fonte de verdade; necessário para sequências novas. | Exige endpoint, estados de carregamento/erro/vazio, contrato de formato e ordem; `json.dumps`/`Content-Type` atual precisa ser considerado. | `curl` no endpoint + teste no browser via Flask, não `file://`. |
| Renderizar no servidor | Evita XHR inicial; catálogo já vem no HTML. | Acopla template/Flask; o controller Angular ainda precisa dos dados; menos flexível para atualizar sem reload. | Inspecionar HTML servido e testar criação/atualização. |
| Híbrido fallback + API | Tolera API indisponível; mantém algo visível. | Duas fontes de verdade; pode exibir lista desatualizada; precisa definir precedência. | Testar API offline, catálogo vazio e catálogo maior. |
| Formulário + POST | Permite cadastrar sequência nova, requisito da página. | Exige validação, duplicidade, erros, atualização da lista e talvez proteção contra submissão repetida; não há autenticação/CSRF hoje. | Testar entradas vazias, inválidas, repetidas, válidas e recarregamento. |
| Paginação na UI | Permite acessar os 199/296 resultados completos. | Exige controles/estado ou busca de todas as páginas; aumenta tráfego; `orderBy` atual só ordena a página. | Conferir páginas 1/2/3 e totais de `BmGDA`/`CGAmF`. |
| Cores/ordem/gêneros | Catálogo pode trazer metadados; UI pode continuar com paleta fixa. | Formato do catálogo cresce; `cor` e `index` atuais não têm semântica; `GENEROS` fixo pode divergir de `/generos`. | Comparar ordem/cores exibidas e filtrar por gênero. |

### Dependências entre as decisões

- Se a regra escolhida usar ordem/adjacência (H2/H3/H8), o armazenamento do
  catálogo precisa preservar a ordem dos acordes; se usar conjunto (H4/H6), um
  conjunto ou campo texto pode bastar.
- Se a regra exigir repetição (H5/H7), o armazenamento precisa preservar
  multiplicidade; um `set` de `musica.acordes` não serve.
- Se o critério de regressão for “mesmos resultados das 6”, H1 é a referência
  exata; se for “mesmas músicas com tag, mas matching mais intuitivo”, H2-H6
  mantêm as tags e mudam o conjunto retornado.
- Se o frontend puder cadastrar, a validação do backend precisa usar a mesma
  definição de sequência (tokens, caixa, repetição, vazio) usada no matching.
- Se o banco for arquivo, a decisão de volume/bind mount afeta se o catálogo
  sobrevive a `docker rm`; se for em memória, não sobrevive nem a restart.
- Se o frontend buscar o catálogo, o endpoint precisa de formato estável,
  ordenação e erro; se for hardcoded, o catálogo real e a UI podem divergir
  novamente.

## Questões abertas para a proposta

1. Qual é a definição aceita de “a sequência X aparece na música Y”: bloco
   contíguo, subsequência ordenada, conjunto, multiconjunto ou a regra
   tag-like? A ordem importa? Acordes de passagem invalidam? Repetição importa?
2. O critério de regressão das 6 é preservar exatamente as tags atuais (H1) ou
   preservar apenas as músicas com tag dentro de um conjunto maior (H2-H6)?
3. Qual representação usar no matching: `musica.cifra` (ordem/repetição) ou
   `musica.acordes` (conjunto)? A escolha precisa ser compatível com a regra e
   com o armazenamento do catálogo.
4. Quais normalizações entram: minúsculas, trim, enarmônicos, sufixos, tokens
   não acordais, `|`, espaços, tokens vazios? O que acontece com acorde
   desconhecido ou sequência vazia?
5. Qual o desempenho esperado e o tamanho máximo do catálogo? A busca será ao
   vivo sobre 59.444 músicas por requisição ou pré-computada/indexada? Como
   invalidar o índice quando uma sequência é criada?
6. Qual banco embarcado será usado? O arquivo precisa sobreviver a `docker rm`
   ou basta `docker restart`? Será adicionado `VOLUME`, bind mount ou comando
   documentado com `-v`?
7. Como o catálogo será modelado: uma linha com acordes serializados ou tabela
   de acordes com posição/repetição? Como fazer schema, seed das 6 e migrações?
8. Qual o contrato dos endpoints de catálogo: listar, criar, editar, remover?
   Quais status HTTP, formato de erro e ordenação? Como preservar
   `json.dumps(...)` e o `Content-Type: text/html` atual?
9. Como o frontend carrega o catálogo: hardcoded alinhado, XHR, render no
   servidor ou híbrido? Como tratar carregando/erro/vazio? A página precisa
   cadastrar ou só listar?
10. Como a UI trata paginação, ordem, cores, `index` e gêneros? A lista de
    gêneros continua fixa em `GENEROS` ou passa a vir de `/generos`?
11. Quais testes mínimos: regressão das 6 contra as tags, casos sintéticos de
    caixa/enarmônicos/repetição/vazio, persistência após restart/recriação,
    contrato dos endpoints e smoke test no browser?
12. Quais dados do CSV precisam de tratamento antes do matching: primeira linha
    ignorada (`main.py:50`), `replace('NA','')` global (`main.py:53`), cifras
    vazias (8.141 músicas), tokens não acordais e colisões de caixa?
