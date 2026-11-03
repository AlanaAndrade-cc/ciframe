# deciframe

Descubra as músicas que você já sabe tocar (e ainda não faz ideia). Busque por
título/artista, gênero, pelos acordes que você já manja, ou por sequências de
acordes famosas — o deciframe cruza isso com uma base de cifras e sugere
músicas parecidas.

Stack: backend Flask (Python) servindo uma API JSON + um frontend AngularJS
estático. Músicas e gêneros vêm de um CSV em memória; o catálogo de sequências
de acordes fica num arquivo SQLite (`/app/var/sequences.db`).

## Rodando localmente

### Com Docker

```
docker build -t ciframe .
docker run -p 8080:8080 -v deciframe-data:/app/var ciframe
```

Acesse [http://localhost:8080](http://localhost:8080).

O volume nomeado `deciframe-data` preserva o catálogo de sequências entre
`docker restart` e `docker rm`. Sem `-v`, um `docker rm` descarta o catálogo e
o próximo `run` volta às 6 sequências originais.

### Com virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Acesse [http://localhost:5000](http://localhost:5000).

---

Para convenções de contribuição, veja [CONTRIB.md](CONTRIB.md). Licença: [LICENSE](LICENSE).
