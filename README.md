# RentSmart — Sistema de Orçamento de Locação (R.M Imóveis)

Aplicação em Python (POO) com interface web local. Usa apenas a biblioteca padrão — **não precisa instalar nada**.

## Como executar
1. Instale o Python 3.9+.
2. No terminal, dentro desta pasta: `python app.py`
3. Abra http://localhost:8000 no navegador.
4. Preencha os dados e clique em **Calcular orçamento**.

O CSV da projeção de 12 meses é salvo em `projecao_12_meses.csv` (na pasta do projeto) e também pode ser baixado pela página.

## Estrutura
- `models.py` — classes: `Imovel` (abstrata), `ImovelResidencial`, `Apartamento`, `Casa`, `Estudio`, `TaxaContratual`, `Orcamento`, `Projecao`.
- `app.py` — servidor HTTP local (rota `/` e `/api/orcamento`).
- `static/index.html` — front end (HTML, CSS e JS).

## Regras implementadas
Aluguel-base: apto R$ 700, casa R$ 900, estúdio R$ 1.200. Adicional 2 quartos: apto +200, casa +250. Garagem (casa/apto): +300. Estúdio: pacote de 2 vagas R$ 250 + R$ 60 por vaga extra. Apto sem crianças: 5% de desconto após os adicionais. Taxa contratual: R$ 2.000 em até 5 parcelas, tratada separadamente do aluguel.
