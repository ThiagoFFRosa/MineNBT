# Minecraft Java 26.2 — Spawn Eggs e shulkers aninhadas

Kit textual de ItemStacks para importar manualmente em um editor de NBT/Item Editor que aceite SNBT/JSON da Java Edition 26.2.

## Arquivos principais

- `items/01_all_spawn_eggs_chest.snbt`: Chest com quatro shulkers coloridas contendo os 88 Spawn Eggs registrados na 26.2. Cada ovo possui `count: 64`.
- `items/02_nested_rainbow_shulkers_64x.snbt`: pilha de 64 shulkers roxas, preenchida com shulkers coloridas aninhadas e também empilhadas em 64.
- `data/spawn_egg_ids_26.2.txt`: lista exata dos 88 IDs usada pelo gerador e pelo validador.
- `generate.ps1`: gerador deterministico dos dois ItemStacks.
- `validate.ps1`: validador offline de contagens, IDs, slots e profundidade.
- `VALIDATION_REPORT.md`: resultado da ultima validacao.

## Chest de Spawn Eggs

O registry da Java 26.2 possui 88 IDs terminados em `_spawn_egg`. Como cada shulker tem 27 slots, eles foram distribuidos assim:

| Slot da Chest | Shulker | Ovos | Slots usados |
|---:|---|---:|---|
| 0 | Red | 27 | 0–26 |
| 1 | Orange | 27 | 0–26 |
| 2 | Yellow | 27 | 0–26 |
| 3 | Lime | 7 | 0–6 |

Cada Spawn Egg aparece exatamente uma vez e com `count: 64`. As quatro shulkers dentro da Chest possuem `count: 1`, pois a solicitacao de pilha completa se aplica aos ovos; o experimento de shulkers empilhadas fica no segundo arquivo.

## Shulkers coloridas aninhadas em 64

A shulker experimental possui uma estrutura finita e auditavel:

- camada 1: uma `purple_shulker_box` raiz com `count: 64`;
- camada 2: 27 pilhas de shulkers coloridas, todas com `count: 64`;
- camada 3: cada shulker da camada 2 contem 27 pilhas de shulkers-folha coloridas, todas com `count: 64`;
- total: 757 ItemStacks de shulker (`1 + 27 + 729`), usando as 16 cores;
- as 729 shulkers-folha nao possuem outro container, encerrando a estrutura.

Cada um dos 757 ItemStacks tambem possui `minecraft:max_stack_size: 64`. Esse override e obrigatorio porque a shulker vanilla tem limite padrao 1; usar `count: 64` sem aumentar o limite faz o jogo rejeitar os ItemStacks internos e exibi-los como `Air x0`.

As caixas continuam usando as 16 cores de shulker. Para os nomes personalizados, o gerador converte cada cor de tinta para uma cor de texto aceita pelo Minecraft (por exemplo, Orange vira `gold` e Lime vira `green`).

Uma shulker tem apenas 27 slots; portanto, “64 stacks” foi implementado como uma **pilha de 64 shulkers em cada slot**, e nao como 64 slots inexistentes.

## Limite de seguranca

Nesting infinito nao pode ser serializado. Repetir 27 filhos em muitas camadas cresce exponencialmente e pode formar um NBT bomb, travando o editor, o jogo ou o carregamento do chunk. Este kit para deliberadamente na terceira camada fisica e o validador exige exatamente esse limite.

Mesmo assim, o segundo arquivo e experimental: teste somente em mundo descartavel e mantenha backup. Alguns editores ou servidores podem normalizar shulkers para `count: 1`, recusar containers aninhados ou rejeitar o ItemStack inteiro.

## Como usar

1. Faca backup e abra um mundo descartavel.
2. Importe o arquivo `.snbt` desejado como um ItemStack completo.
3. Nao importe o arquivo aninhado em servidor publico ou mundo importante.
4. Se o editor mostrar uma pre-visualizacao muito lenta, cancele sem salvar.

O kit nao altera `.minecraft`, saves, `level.dat`, `playerdata`, chunks ou o jogo automaticamente.

## Fontes

- Registry de itens 26.2: <https://raw.githubusercontent.com/misode/mcmeta/26.2-registries/item/data.json>
- Notas oficiais do Minecraft Java 26.2: <https://feedback.minecraft.net/hc/en-us/articles/46690753273997-Minecraft-Java-Edition-26-2>
