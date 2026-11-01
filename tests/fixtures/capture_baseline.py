#!/usr/bin/env python3
"""Captura o baseline das 6 sequências legadas para o fixture golden.

Script one-off, fora da suíte `unittest`. Roda a partir da raiz do repositório,
com o app já servindo o código atual (antes de qualquer refactor):

    .venv/bin/python main.py
    .venv/bin/python tests/fixtures/capture_baseline.py --base-url http://localhost:5000

O fixture é o único registro do "antes": depois que `main.py` mudar, o
comportamento de hoje não é mais reproduzível com segurança. Não regenere este
arquivo após o refactor.

Usa apenas a biblioteca padrão (`urllib.request`, `json`); `requests` não é
dependência do projeto.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

KEYS = ["BmGDA", "CGAmF", "EmG", "CA7DmG7", "GmF", "CC7FFm"]

# Contagens por página medidas na pesquisa (01-research.md:865-874).
EXPECTED_PAGES = {
    "BmGDA": [100, 99],
    "CGAmF": [100, 100, 96],
    "EmG": [4],
    "CA7DmG7": [5],
    "GmF": [7],
    "CC7FFm": [3],
}

PAGE_SIZE = 100
MAX_PAGES = 1000

FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sequencias_golden.json"
)


def fetch_page(base_url, key, page):
    query = urllib.parse.urlencode({"sequencia": key, "pagina": page})
    url = "%s/similares?%s" % (base_url, query)
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise SystemExit("falha ao acessar %s: %s" % (url, exc))

    try:
        data = json.loads(body)
    except ValueError:
        raise SystemExit("resposta nao e JSON em %s: %r" % (url, body[:200]))

    if not isinstance(data, list):
        raise SystemExit("resposta inesperada em %s: %r" % (url, data))
    return data


def capture(base_url, key):
    """Percorre as páginas até uma vazia e devolve (ids, contagens)."""
    ids = set()
    paginas = []
    page = 1

    while True:
        data = fetch_page(base_url, key, page)
        if not data:
            break

        for item in data:
            ids.add(item["id_unico_musica"])

        paginas.append(len(data))
        page += 1
        if page > MAX_PAGES:
            raise SystemExit("paginacao nao terminou para %s" % key)

    return ids, paginas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:5000",
        help="origem do Flask (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--output",
        default=FIXTURE,
        help="caminho do fixture (default: tests/fixtures/sequencias_golden.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="sobrescreve um fixture existente (nao usar apos o refactor)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if os.path.exists(args.output) and not args.force:
        raise SystemExit(
            "fixture ja existe em %s; nao regenere depois do refactor "
            "(use --force apenas se for intencional)" % args.output
        )

    fixture = {}
    problems = []

    for key in KEYS:
        ids, paginas = capture(base_url, key)
        fixture[key] = {"ids": sorted(ids), "paginas": paginas}

        total = sum(paginas)
        if len(ids) != total:
            problems.append(
                "%s: %d ids unicos != %d somados nas paginas"
                % (key, len(ids), total)
            )
        if paginas != EXPECTED_PAGES[key]:
            problems.append(
                "%s: paginas %s != esperado %s"
                % (key, paginas, EXPECTED_PAGES[key])
            )

        print("%-8s ids=%3d paginas=%s" % (key, len(ids), paginas))

    if problems:
        print("\nDIVERGENCIA — fixture NAO foi gravado:", file=sys.stderr)
        for problem in problems:
            print("  - " + problem, file=sys.stderr)
        return 1

    directory = os.path.dirname(os.path.abspath(args.output))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(fixture, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("\nfixture gravado em %s" % args.output)
    print(json.dumps(fixture, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
