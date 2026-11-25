# Comércio exterior do agro no Microsoft Fabric com dbt

Projeto de estudo e portfólio, **em construção**.

**Pergunta de negócio:** para onde, de quais estados e por quais vias e portos sai o agro brasileiro, e como isso muda
no tempo?

Desenho planejado: o Data Factory ingere os dados da API do Comex Stat em um Lakehouse, e um dbt job transforma em um
Warehouse. Por "agro" entendem-se aqui os capítulos 01 a 24 do Sistema Harmonizado, um recorte que não cobre todo o
agronegócio (madeira, celulose e algodão, por exemplo, ficam de fora).

A automação de verificação deste repositório foi adaptada de um projeto anterior do autor.

Fonte: Secex/MDIC - Comex Stat.
