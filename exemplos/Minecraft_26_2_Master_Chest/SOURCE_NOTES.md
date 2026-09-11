# Fontes e decisões de compatibilidade

- Versão instalada confirmada em `C:\Users\Fuzz.s\AppData\Roaming\.minecraft\versions\26.2\26.2.json`.
- `server.jar` oficial baixado temporariamente da URL declarada nesse manifesto e validado com SHA-1 `823e2250d24b3ddac457a60c92a6a941943fcd6a`.
- O `version.json` interno informa `world_version=4903`, data pack `107.1`, Java 25 e build estável 26.2.
- Os dados oficiais do jar confirmam todos os IDs de encantamentos usados, incluindo `minecraft:lunge`, e os damage types `in_fire`, `on_fire`, `lava`, `explosion` e `player_explosion`.
- A documentação técnica oficial da 26.1 confirma que `minecraft:damage_resistant.types` aceita um ID ou uma lista de IDs.
- A documentação técnica oficial da 1.21.5 confirma os formatos simplificados de `minecraft:enchantments`, `minecraft:attribute_modifiers` e `minecraft:tooltip_display`.
- A documentação técnica oficial da 1.21.6 confirma o campo de display individual em attribute modifiers. Para ocultar somente o bônus de oxigênio foi usado `display:{type:"hidden"}`.
- Os defaults de itens da 26.2 foram comparados com os relatórios de dados gerados da versão: Netherite Chestplate `8/3/0.10000000149011612`, Elytra com `glider` e a configuração de `blocks_attacks` do Shield.
- Os block states foram limitados a propriedades existentes: `waterlogged` no Copper Grate; `extended` e `facing` em Pistons; `lit` em Redstone Lamp; `powered` nos dois Rails.

Links oficiais consultados:

- https://feedback.minecraft.net/hc/en-us/articles/46690753273997-Minecraft-Java-Edition-26-2
- https://feedback.minecraft.net/hc/en-us/articles/44551668333837-Minecraft-Java-Edition-26-1
- https://feedback.minecraft.net/hc/en-us/articles/35298208390797-Minecraft-Java-Edition-1-21-5-Spring-to-Life
- https://feedback.minecraft.net/hc/en-us/articles/37432144057997-Minecraft-Java-Edition-1-21-6-Chase-the-Skies
- https://feedback.minecraft.net/hc/en-us/articles/41809981427213-Minecraft-Java-Edition-1-21-11-Mounts-of-Mayhem
