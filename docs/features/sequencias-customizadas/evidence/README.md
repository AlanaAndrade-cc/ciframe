# Evidências da fase 1

Scripts Python 3 usados para caracterizar o código e os dados da pesquisa. Todos
leem `data/top/dataset_final.csv` e não alteram `main.py`, `musica.py`, `data/`
nem `scripts/`.

Rodar a partir da raiz do repositório:

```bash
python3 docs/features/sequencias-customizadas/evidence/tag_summary.py > docs/features/sequencias-customizadas/evidence/tag_summary.out
python3 docs/features/sequencias-customizadas/evidence/q2_report.py > docs/features/sequencias-customizadas/evidence/q2_report.out
python3 docs/features/sequencias-customizadas/evidence/hypotheses_metrics.py > docs/features/sequencias-customizadas/evidence/hypotheses_metrics.out
python3 docs/features/sequencias-customizadas/evidence/extra_metrics.py > docs/features/sequencias-customizadas/evidence/extra_metrics.out
```

As saídas correspondentes estão nos arquivos `.out` deste diretório. O
`q2_report.py` importa `musica.py` do projeto e precisa ser executado da raiz do
repositório.
