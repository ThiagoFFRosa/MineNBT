# Minecraft Java 26.2 — Master Chest

Este kit contém um `minecraft:chest` standalone com cinco shulkers e 66 ItemStacks internos. Nenhum save, chunk, entidade ou `player.dat` é alterado.

## Arquivo para importar

- `minecraft_26_2_master_chest.nbt`: NBT binário comprimido com GZip, com raiz `TAG_Compound` anônima representando diretamente o ItemStack moderno.
- `minecraft_26_2_master_chest.snbt`: representação textual equivalente, indicada para editores que recebem SNBT ou para auditoria humana.
- `minecraft_26_2_master_chest_manifest.txt`: inventário completo de itens, slots, componentes, encantamentos e atributos.

Se o editor aceitar `.nbt`, tente primeiro o arquivo binário. Se ele esperar texto no campo de ItemStack, use o conteúdo do `.snbt`. O ItemStack raiz usa `id`, `count` e `components`; não usa `Count`, `tag`, `BlockEntityTag` nem a sintaxe antiga `Enchantments`.

## Estrutura

- Slot 0: `ARMOR`, White Shulker Box, 5 itens.
- Slot 1: `TOOLS`, Gray Shulker Box, 14 itens.
- Slot 2: `WEAPONS`, Red Shulker Box, 18 itens.
- Slot 3: `TESTS`, Purple Shulker Box, 13 itens.
- Slot 4: `GLITCH BLOCKS`, Orange Shulker Box, 16 itens.

Todas as shulkers internas têm `count:1` e não alteram `minecraft:max_stack_size`. Isso evita a falha anterior em que ItemStacks inválidos eram descartados e apareciam como `Air x0`.

## Observações importantes

- Os encantamentos incompatíveis e níveis experimentais são deliberados e permanecem visíveis.
- `Unbreakable` é ocultado por `minecraft:tooltip_display`, sem esconder `minecraft:enchantments`.
- Os itens duráveis possuem `minecraft:unbreakable`, `minecraft:repair_cost=0`, Unbreaking III, Mending I e resistência a fogo, lava e explosões.
- O bônus `minecraft:oxygen_bonus` do helmet usa um modifier individual com `display:{type:"hidden"}`. Os três atributos defensivos vanilla do helmet permanecem no componente e continuam visíveis.
- A Armored Elytra contém `minecraft:glider` e copia exatamente os valores defensivos da Netherite Chestplate 26.2: 8 armor, 3 toughness e `0.10000000149011612` knockback resistance.
- As duas armas de bloqueio usam a configuração padrão do componente `minecraft:blocks_attacks` do Shield da 26.2.
- A AFK Potion tem somente Regeneration II, `duration=-1`, sem partículas nem ícone. Leite continua removendo o efeito normalmente.
- Nos Rails, propriedades não especificadas, como shape e waterlogged, continuam usando os defaults vanilla de colocação; somente `powered="true"` foi sobrescrito.

Os resultados de gameplay de Multishot em Bow, Power/Flame/Infinity em Crossbow, Sharpness em Mace, blocking em Spear/Sword, Glider Chestplate e estados impossíveis de blocos só podem ser confirmados dentro do jogo.

## Segurança

Faça o primeiro teste em uma cópia de segurança do mundo. Este kit não deve ser importado diretamente em um save importante sem backup.

## Regeneração e validação

Com Node.js disponível:

```powershell
node .\generate.js --check
node .\generate.js
node .\validate.js
node .\validate_reference.js --source-dir <pasta-com-relatorios-26.2>
```

O primeiro comando não grava arquivos. O validador relê o NBT binário, descomprime, parseia todos os ItemStacks, reserializa para SNBT e compara byte a byte com o `.snbt`.
O validador de referência é opcional e serve para repetir a conferência contra relatórios externos da versão; o resultado desta entrega está preservado em `SOURCE_VALIDATION_REPORT.md`.
