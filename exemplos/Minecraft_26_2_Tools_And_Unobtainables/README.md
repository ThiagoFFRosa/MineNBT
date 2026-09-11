# Minecraft Java 26.2 — ferramentas fortes e itens inobtiveis

Kit textual de ItemStacks para importar manualmente em um editor de NBT/Item Editor que aceite SNBT/JSON de ItemStack da Java Edition 26.2.

## Arquivos principais

- `shulkers/01_power_tools.snbt`: shulker vermelha com 15 armas, ferramentas e utilitarios fortes, todos indestrutiveis.
- `shulkers/02_unobtainable_items.snbt`: shulker preta completa, com 27 itens registrados que nao podem ser obtidos como ItemStack no Survival normal.
- `commands/portal_blocks.txt`: alternativa para colocar os blocos de portal que nao possuem uma forma de item registrada.
- `generate.ps1`: gerador deterministico das duas shulkers.
- `validate.ps1`: validador offline do kit.
- `VALIDATION_REPORT.md`: resultado da ultima validacao.

## Shulker 1 — ferramentas fortes

Todos os itens possuem `minecraft:unbreakable`, Mending quando aplicavel e Unbreaking X. Os encantamentos ofensivos/de ferramenta usam niveis fortes, mas finitos e dentro do intervalo aceito pelo componente (`1..255`).

| Slot | Item | Destaques |
|---:|---|---|
| 0 | Netherite Sword | Sharpness/Smite/Bane X juntos, Looting X, Sweeping Edge X |
| 1 | Netherite Pickaxe | Efficiency X, Fortune X e Silk Touch juntos |
| 2 | Netherite Axe | encantamentos de ferramenta e de combate combinados |
| 3 | Netherite Shovel | Efficiency X, Fortune X e Silk Touch juntos |
| 4 | Netherite Hoe | Efficiency X, Fortune X e Silk Touch juntos |
| 5 | Netherite Spear | Lunge X mais encantamentos de combate combinados |
| 6 | Mace | Density X e Breach X juntos, Wind Burst X |
| 7 | Bow | Power X, Punch V, Infinity e Mending juntos |
| 8 | Crossbow | Multishot III e Piercing X juntos, Quick Charge V |
| 9 | Trident | Loyalty X e Riptide X juntos, Channeling |
| 10 | Fishing Rod | Luck of the Sea X e Lure X |
| 11 | Shears | Efficiency X, Fortune X e Silk Touch |
| 12 | Brush | Efficiency X e Fortune X |
| 13 | Flint and Steel | indestrutivel, Mending e Unbreaking X |
| 14 | Shield | indestrutivel, Mending e Unbreaking X |

## Shulker 2 — 27 itens inobtiveis

| Slot | ID | Motivo resumido |
|---:|---|---|
| 0 | `minecraft:bedrock` | bloco tecnico/Creative, nao coletavel no Survival normal |
| 1 | `minecraft:end_portal_frame` | estrutura do Stronghold, nao coletavel |
| 2 | `minecraft:reinforced_deepslate` | estrutura da Ancient City, nao coletavel |
| 3 | `minecraft:barrier` | bloco de operador |
| 4 | `minecraft:light` | bloco de operador invisivel |
| 5 | `minecraft:structure_void` | bloco de operador |
| 6 | `minecraft:structure_block` | bloco de operador |
| 7 | `minecraft:jigsaw` | bloco de operador |
| 8 | `minecraft:command_block` | bloco de operador |
| 9 | `minecraft:repeating_command_block` | bloco de operador |
| 10 | `minecraft:chain_command_block` | bloco de operador |
| 11 | `minecraft:command_block_minecart` | veiculo de operador |
| 12 | `minecraft:debug_stick` | ferramenta de operador |
| 13 | `minecraft:knowledge_book` | item tecnico/comando |
| 14 | `minecraft:spawner` | nao coletavel como item no Survival |
| 15 | `minecraft:trial_spawner` | nao coletavel como item no Survival |
| 16 | `minecraft:vault` | nao coletavel como item no Survival |
| 17 | `minecraft:test_block` | bloco de teste/operador |
| 18 | `minecraft:test_instance_block` | bloco de teste/operador |
| 19 | `minecraft:petrified_oak_slab` | variante legacy sem receita/geracao Survival |
| 20 | `minecraft:farmland` | forma de ItemStack nao coletavel normalmente |
| 21 | `minecraft:dirt_path` | forma de ItemStack nao coletavel normalmente |
| 22 | `minecraft:budding_amethyst` | nao cai nem com Silk Touch |
| 23 | `minecraft:suspicious_sand` | bloco existe no mundo, mas nao cai como item |
| 24 | `minecraft:suspicious_gravel` | bloco existe no mundo, mas nao cai como item |
| 25 | `minecraft:ender_dragon_spawn_egg` | ovo de spawn exclusivo de Creative/comandos |
| 26 | `minecraft:wither_spawn_egg` | ovo de spawn exclusivo de Creative/comandos |

## Sobre os portais

`minecraft:end_portal`, `minecraft:end_gateway` e `minecraft:nether_portal` existem no registro de **blocos**, mas nao no registro de **itens** da 26.2. Por isso nao foram falsificados dentro da shulker. Um ItemStack com esses IDs seria invalido e pode virar ar ao ser carregado.

O arquivo `commands/portal_blocks.txt` contem comandos `/setblock` para testes. No Nether, o "frame" normal do portal e Obsidian — o bloco tecnico e apenas a superficie roxa `nether_portal`.

## Como usar com seguranca

1. Faca backup do mundo e teste primeiro em um mundo descartavel.
2. No editor, importe o arquivo da shulker inteira como um ItemStack.
3. Se o editor aceitar apenas o composto interno, copie todo o objeto raiz do `.snbt`.
4. Nao coloque os blocos tecnicos perto de construcoes importantes; alguns podem atualizar, desaparecer ou alterar chunks quando colocados.

O kit nao altera `.minecraft`, saves, `level.dat`, `playerdata`, chunks ou o jogo automaticamente.

## Fontes de compatibilidade

- Registry de itens 26.2: <https://raw.githubusercontent.com/misode/mcmeta/26.2-registries/item/data.json>
- Registry de blocos 26.2: <https://raw.githubusercontent.com/misode/mcmeta/26.2-registries/block/data.json>
- Registry de encantamentos 26.2: <https://raw.githubusercontent.com/misode/mcmeta/26.2-registries/enchantment/data.json>
- Notas oficiais do Minecraft Java 26.2: <https://feedback.minecraft.net/hc/en-us/articles/46690753273997-Minecraft-Java-Edition-26-2>

