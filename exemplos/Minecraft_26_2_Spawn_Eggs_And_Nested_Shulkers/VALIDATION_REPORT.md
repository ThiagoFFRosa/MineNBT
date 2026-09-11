# Validation Report

- Status: **PASS**
- Gerado em: 2026-09-01 18:05:14 -03:00
- Alvo: Minecraft Java 26.2
- Escopo: validacao estrutural e de conteudo offline; Minecraft nao foi iniciado

## Checks

- Spawn Egg Chest: 4 shulkers e lotes 27 + 27 + 27 + 7 verificados.
- Spawn Eggs: 88 IDs unicos, completos e com count 64 verificados.
- Spawn Egg Chest: cores dos componentes de texto verificadas.
- Nested shulkers: 1 raiz + 27 intermediarias + 729 folhas verificados.
- Nested shulkers: 757 ItemStacks, 16 cores e count 64 em todos verificados.
- Nested shulkers: 757 componentes minecraft:max_stack_size 64 verificados.
- Profundidade limitada: nenhuma das 729 shulkers-folha contem outro container.
- Nested shulkers: cores dos componentes de texto verificadas.

## Errors

- Nenhum erro encontrado.

## Safety limit

- O nesting termina nas 729 shulkers-folha; recursao adicional nao foi gerada.
- O validador nao substitui um teste manual no editor ou o codec do jogo.
