# Minecraft 26.2 Broken Items

Kit isolado de ItemStacks experimentais para **Minecraft Java 26.2**. Nenhum save, `level.dat`, `playerdata`, chunk, arquivo de região ou conteúdo de `.minecraft` foi alterado.

> **Faça backup do mundo antes de importar.** Teste primeiro em um mundo singleplayer descartável e nunca leve estes itens a um servidor sem autorização.

## Qual formato foi usado

O exemplo real fornecido é **SNBT textual**, não JSON: ele usa chaves não obrigatoriamente entre aspas, compostos `{}`, listas `[]` e sufixos NBT como `1b`, `2.0f` e `50.0d`. A forma persistida de um ItemStack 26.2 é um composto com `id`, `count` e `components`.

Por isso os arquivos usam a extensão `.snbt`. O nome exato do mod/editor não foi informado, então a extensão e o fluxo de importação específicos dele não puderam ser confirmados. Se o seletor não mostrar `.snbt`, escolha “todos os arquivos” ou cole o conteúdo como texto, desde que o editor aceite um ItemStack persistido como o exemplo.

Esta estrutura não é a mesma coisa que um argumento de `/give`. Em comandos, os componentes aparecem entre colchetes depois do ID do item. Aqui os arquivos representam o ItemStack persistido completo para importação pelo editor.

## Fontes e versão verificadas

- Release oficial 26.2, publicada em 16 de junho de 2026: <https://feedback.minecraft.net/hc/en-us/articles/46690753273997-Minecraft-Java-Edition-26-2>
- Relatórios de registry 26.2 derivados do gerador oficial do jogo: <https://github.com/misode/mcmeta/tree/26.2-summary>
- Lista de itens 26.2: <https://github.com/misode/mcmeta/blob/26.2-registries/item/data.json>
- Esquema aberto de codecs/NBT usado na conferência dos campos: <https://github.com/SpyglassMC/vanilla-mcdoc>

Foram confirmados localmente: **data version 4903**, **protocol version 776**, **data pack format 107.1** e **resource pack format 88.0**.

## Componentes confirmados para 26.2

`minecraft:attack_range`, `minecraft:attribute_modifiers`, `minecraft:consumable`, `minecraft:container`, `minecraft:damage`, `minecraft:death_protection`, `minecraft:enchantment_glint_override`, `minecraft:enchantments`, `minecraft:equippable`, `minecraft:fireworks`, `minecraft:food`, `minecraft:glider`, `minecraft:item_model`, `minecraft:item_name`, `minecraft:lore`, `minecraft:max_damage`, `minecraft:max_stack_size`, `minecraft:ominous_bottle_amplifier`, `minecraft:piercing_weapon`, `minecraft:potion_contents`, `minecraft:profile`, `minecraft:rarity`, `minecraft:stored_enchantments`, `minecraft:swing_animation`, `minecraft:tool`, `minecraft:tooltip_display`, `minecraft:unbreakable` e `minecraft:weapon`.

Detalhes importantes confirmados:

- `count` e `minecraft:max_stack_size`: intervalo `1..99`.
- Encantamentos: níveis `1..255`; o kit usa no máximo 10.
- `minecraft:ominous_bottle_amplifier`: `0..4` (o valor 4 corresponde a Ominous V).
- `minecraft:attack_range`: alcance máximo permitido de 64; o kit usa 32.
- `minecraft:container`: lista de `{slot, item}`, com slots `0..255`; a shulker usa exatamente `0..26`.
- Remoções de componentes padrão são patches com chave prefixada por `!`, por exemplo `"!minecraft:max_damage": {}`.
- `minecraft:swing_animation` existe na 26.2 e aceita `none`, `whack` ou `stab`.
- `minecraft:item_model` referencia uma definição de item; `minecraft:end_portal_frame` existe no registry 26.2.

## Arquivos de itens

`VALIDATED` significa que estrutura, IDs e limites passaram no validador local; não significa que o item foi importado no jogo. `EXPERIMENTAL` significa que a sintaxe foi conferida, mas o comportamento ou a interoperabilidade com o editor ainda precisa de teste manual.

| Item | Arquivo | Base Item | Components utilizados | Risco | Status |
|---|---|---|---|---|---|
| Overstacked Diamond Sword | `items/01_max_stack.snbt` | `diamond_sword` | remoção de `damage`/`max_damage`, `max_stack_size` | MEDIUM | EXPERIMENTAL |
| Paradox Blade | `items/02_cursed_sword.snbt` | `netherite_sword` | `enchantments`, `attribute_modifiers` | HIGH | EXPERIMENTAL |
| Contradiction Bow | `items/03_cursed_bow.snbt` | `bow` | `enchantments`, `unbreakable` | HIGH | EXPERIMENTAL |
| Fourfold Aegis | `items/04_god_armor.snbt` | `netherite_chestplate` | `enchantments`, `attribute_modifiers`, `unbreakable` | HIGH | EXPERIMENTAL |
| Aegis Wings | `items/05_super_elytra.snbt` | `elytra` | `enchantments`, `attribute_modifiers`, `unbreakable` | HIGH | EXPERIMENTAL |
| Bedrock Biscuit | `items/06_edible_bedrock.snbt` | `bedrock` | `food`, `consumable`, `max_stack_size` | MEDIUM | VALIDATED |
| Impossible Glider Feather | `items/07_glider_feather.snbt` | `feather` | `glider`, `equippable`, `max_stack_size` | HIGH | EXPERIMENTAL |
| Sword Hat | `items/08_sword_hat.snbt` | `diamond_sword` | `equippable` | MEDIUM | EXPERIMENTAL |
| 9999 Armor Slab | `items/09_9999_armor.snbt` | `acacia_slab` | `attribute_modifiers`, `max_stack_size` | HIGH | EXPERIMENTAL |
| Velocity Foot | `items/10_ultra_speed.snbt` | `rabbit_foot` | `attribute_modifiers`, `equippable` | HIGH | EXPERIMENTAL |
| Moonstep Slime | `items/11_ultra_jump_safe_fall.snbt` | `slime_ball` | `attribute_modifiers`, `equippable` | HIGH | EXPERIMENTAL |
| Long Arm of the Stick | `items/12_extreme_attack_range.snbt` | `stick` | `attack_range`, `weapon` | HIGH | EXPERIMENTAL |
| Builder's Horizon | `items/13_extreme_block_reach.snbt` | `blaze_rod` | `attribute_modifiers` | HIGH | EXPERIMENTAL |
| Eternal Contradiction Pick | `items/14_indestructible_tool.snbt` | `netherite_pickaxe` | `enchantments`, `unbreakable` | MEDIUM | VALIDATED |
| Eightfold Elixir | `items/15_impossible_potion.snbt` | `potion` | `potion_contents` | HIGH | VALIDATED |
| Paper of Second Chances | `items/16_death_protection.snbt` | `paper` | `death_protection` | HIGH | EXPERIMENTAL |
| Ominous Amethyst | `items/17_ominous_item.snbt` | `amethyst_shard` | `ominous_bottle_amplifier` | MEDIUM | VALIDATED |
| Notch Profile Head | `items/18_notch_head.snbt` | `player_head` | `profile` | LOW | EXPERIMENTAL |
| Cursed Book | `items/19_cursed_book.snbt` | `enchanted_book` | `stored_enchantments` | MEDIUM | VALIDATED |
| Pickaxe Stick | `items/20_impossible_tool.snbt` | `stick` | `tool` | MEDIUM | EXPERIMENTAL |
| Shieldbreaker Carrot | `items/21_weapon_carrot.snbt` | `carrot` | `weapon`, `attribute_modifiers` | MEDIUM | EXPERIMENTAL |
| Bamboo Impaler | `items/22_piercing_weapon.snbt` | `bamboo` | `piercing_weapon`, `weapon` | HIGH | EXPERIMENTAL |
| Stabbing Blaze Rod | `items/23_custom_swing.snbt` | `blaze_rod` | `swing_animation`, `weapon` | MEDIUM | EXPERIMENTAL |
| Portal Frame Stick | `items/24_model_swap.snbt` | `stick` | `item_model` | LOW | VALIDATED |
| Quietly Impossible Axe | `items/25_hidden_tooltip.snbt` | `netherite_axe` | `tooltip_display`, `enchantments`, `attribute_modifiers` | HIGH | EXPERIMENTAL |
| Prismatic Fivefold Rocket | `items/26_ridiculous_firework.snbt` | `firework_rocket` | `fireworks` | HIGH | EXPERIMENTAL |
| Finite Container Paradox | `items/27_nested_container.snbt` | `chest` | `container` | HIGH | EXPERIMENTAL |
| Forever Artifacts master shulker | `shulker/broken_items_shulker.snbt` | `shulker_box` | `container`, `item_name`, `lore` | HIGH | EXPERIMENTAL |

## O que permanece incerto

- A extensão/função de importação exata do mod “Item Editor”, pois o nome e a versão do mod não foram fornecidos.
- O resultado visual e funcional de `glider`, `piercing_weapon`, `swing_animation`, `weapon` e atributos de alcance aplicados a bases incomuns.
- Clamping e interação de atributos altos quando outros mods alteram as mesmas estatísticas.
- Resolução online da textura do perfil `Notch`.
- Importação de uma shulker grande de uma vez pelo editor; por isso todos os itens também estão separados.

Nenhuma dessas incertezas foi “preenchida” com sintaxe inventada; os campos usados existem no esquema/registry 26.2. A incerteza é de comportamento e integração com o editor.

## Artefatos de bloco rejeitados

`water`, `lava`, `fire`, `soul_fire`, `nether_portal`, `end_portal`, `end_gateway`, `moving_piston`, `piston_head` e `bubble_column` existem no registry de blocos, mas não no registry de itens 26.2. Eles não foram falsificados como ItemStacks. Veja `rejected_or_impossible/README.md` e os comandos seguros para copiar manualmente em `commands/`.

## Ordem recomendada de teste

1. Execute `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\validate.ps1` nesta pasta.
2. Importe primeiro **`items/24_model_swap.snbt`**. É um stick de baixo risco que troca apenas nome/modelo visual.
3. Teste depois um item individual por vez.
4. Importe `shulker/broken_items_shulker.snbt` somente depois que o editor aceitar os arquivos individuais.
5. Se algo for rejeitado, feche a tela de importação e registre a mensagem exata; não tente injetar o item pelo save.

## Limites de segurança adotados

O kit não contém `NaN`, infinitos, overflow intencional, listas gigantes, livros, entidades, chunks, payload recursivo, NBT bomb ou container infinito. O único nesting é finito: chest > shulker > diamonds. Nenhum comando foi executado e nada foi copiado para `.minecraft`.
