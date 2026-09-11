# Minecraft 26.2 Armor Sets

Duas shulker boxes em SNBT textual para importação manual em um editor de ItemStack compatível com Minecraft Java 26.2.

> **Faça backup do mundo antes de importar e teste em um mundo singleplayer descartável.**

Nenhum save, arquivo em `.minecraft` ou processo do Minecraft foi aberto ou alterado durante a criação.

## Arquivos

| Arquivo | Conteúdo | Durabilidade |
|---|---|---|
| `shulkers/01_armor_sets_standard_durability.snbt` | Set Vanilla Max, Set God e Elytra | Normal; todos possuem Unbreaking III + Mending |
| `shulkers/02_armor_sets_unbreakable.snbt` | Os mesmos 9 itens | `minecraft:unbreakable` em todos os itens; mantém Unbreaking III + Mending |

## Slots das duas shulkers

| Slot | Item | Enchantments especiais |
|---:|---|---|
| 0 | Vanilla Max Helmet | Protection IV, Respiration III, Aqua Affinity I, Thorns III, Unbreaking III, Mending |
| 1 | Vanilla Max Chestplate | Protection IV, Thorns III, Unbreaking III, Mending |
| 2 | Vanilla Max Leggings | Protection IV, Swift Sneak III, Thorns III, Unbreaking III, Mending |
| 3 | Vanilla Max Boots | Protection IV, Feather Falling IV, Depth Strider III, Soul Speed III, Thorns III, Unbreaking III, Mending |
| 4 | God Helmet | Protection IV + Blast/Fire/Projectile Protection IV, além dos encantamentos do capacete |
| 5 | God Chestplate | Protection IV + Blast/Fire/Projectile Protection IV, Thorns III, Unbreaking III, Mending |
| 6 | God Leggings | As quatro proteções, Swift Sneak III, Thorns III, Unbreaking III, Mending |
| 7 | God Boots | As quatro proteções, Depth Strider III + Frost Walker II, Feather Falling IV, Soul Speed III, Thorns III, Unbreaking III, Mending |
| 8 | Protected Elytra | Protection IV, Unbreaking III e Mending |

O Set Vanilla Max evita combinações incompatíveis. O Set God reúne as quatro famílias que usam o mesmo `exclusive_set` de armadura. As God Boots também unem Depth Strider e Frost Walker, que usam o mesmo conjunto exclusivo de botas.

Todos os níveis permanecem nos máximos vanilla da 26.2; não foram usados níveis 10, 255 ou outros valores exagerados.

## Validação e fontes

- Registry de encantamentos 26.2: <https://github.com/misode/mcmeta/blob/26.2-registries/enchantment/data.json>
- Dados vanilla dos encantamentos e seus `max_level`: <https://github.com/misode/mcmeta/tree/26.2-data/data/minecraft/enchantment>
- Esquema de ItemStack/Data Components: <https://github.com/SpyglassMC/vanilla-mcdoc>

O script `validate.ps1` verifica offline:

- delimitadores e strings;
- os dois arquivos esperados;
- nove slots externos únicos, exatamente `0..8`;
- duas peças de cada tipo de armadura e uma Elytra;
- níveis máximos de todos os encantamentos;
- quantidades esperadas de encantamentos incompatíveis;
- ausência de `minecraft:unbreakable` na primeira shulker;
- exatamente nove componentes `minecraft:unbreakable` na segunda.

Execute com:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\validate.ps1
```

Importe primeiro `shulkers/01_armor_sets_standard_durability.snbt`. Use a versão indestrutível apenas depois de confirmar que o editor aceitou a primeira.
