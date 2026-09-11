# Minecraft 26.2 Registry Audit

## Registry

- Raw visual definitions: 1537
- Official registered items: 1537
- Selectable items: 1536
- Block items selectable: 1054
- Normal items selectable: 482
- Non-selectable definitions: 1

Fonte: client.jar oficial local, conferido com SHA-1 do metadata da release. Inspecao estatica de Items.<clinit>, helpers de registro, ItemIds/BlockItemIds, colecoes de cores/cobre, factories/lambdas e superclasses de Item. Nenhuma lista manual de IDs.

`selectable` significa Item registrado que pode representar um stack nao vazio; inclui itens acessiveis por comandos, como spawner. Nao significa disponibilidade em survival nem presenca em abas creative. AIR e excluido porque ItemStack.isEmpty o trata como vazio. isBlockItem vem da hierarquia real da classe construida, nao do nome/textura.

Definicoes com registro confirmado: 1537; sem registro: 0. IDs excluidos: minecraft:air. Colecoes geram IDs reais; aliases de blocos em Item.BY_BLOCK nao criam novos IDs de item.

## Icon coverage

- direct: 520
- model_resolved: 117
- complex_model: 899
- missing: 0
- Current usable icons: 637 / 1536 (41.47%)

## Complex model breakdown

Total bruto: 900; selecionaveis: 899. Categorias se sobrepoem; NAO somar suas contagens. A tabela primaryReasons e exclusiva.

| Categoria | Todas as definicoes | Selecionaveis |
|---|---:|---:|
| animated_texture | 19 | 19 |
| block_model | 752 | 752 |
| bundle_selected_item | 17 | 17 |
| composite | 33 | 33 |
| condition | 26 | 26 |
| empty_model | 1 | 0 |
| generated_sprite | 29 | 29 |
| geometry | 753 | 753 |
| gui_transform | 836 | 836 |
| material_options | 17 | 17 |
| multiple_layers | 38 | 38 |
| range_dispatch | 6 | 6 |
| select | 71 | 71 |
| special_model | 63 | 63 |
| tinted | 27 | 27 |
| tinted_faces | 11 | 11 |

### Motivo principal (exclusivo)

- animated_texture: 1
- block_model: 752
- bundle_selected_item: 17
- condition: 6
- empty_model: 1
- geometry: 1
- gui_transform: 3
- multiple_layers: 1
- range_dispatch: 2
- select: 39
- special_model: 63
- tinted: 14

## Renderer opportunities

Ganhos independentes em relacao aos icones atuais:

- model_geometry: +708 itens; afeta 773 ao incluir dependencias.
- special_models: +51 itens; afeta 63 ao incluir dependencias.
- state_dispatch: +17 itens; afeta 80 ao incluir dependencias.
- tints: +7 itens; afeta 30 ao incluir dependencias.
- texture_layers: +1 itens; afeta 38 ao incluir dependencias.
- texture_animation: +1 itens; afeta 19 ao incluir dependencias.
- composite_models: +0 itens; afeta 33 ao incluir dependencias.
- atlas_sprites: +0 itens; afeta 29 ao incluir dependencias.
- bundle_contents: +0 itens; afeta 17 ao incluir dependencias.

Plano incremental, sem contar itens duas vezes:

1. model_geometry: +708; total 1345 (87.57%).
2. special_models: +51; total 1396 (90.89%).
3. state_dispatch: +33; total 1429 (93.03%).
4. texture_animation: +18; total 1447 (94.21%).
5. tints: +18; total 1465 (95.38%).
6. composite_models: +16; total 1481 (96.42%).
7. bundle_contents: +17; total 1498 (97.53%).
8. texture_layers: +9; total 1507 (98.11%).
9. atlas_sprites: +29; total 1536 (100.0%).

Every branch must be supported. Greedy highest single-feature marginal gain; when all single gains are zero, highest-gain required dependency bundle (ties: fewer capabilities, then lexical order). Independent gains are separate; no double counting.

Vanilla definition-level capability estimate, not rendered-image verification, effort estimate or arbitrary component/resource-pack coverage. Special renderers include base GUI/material handling. Bundle contents require support for the contained item.

## Important item checks

| ID | Registrado | Selectable | Kind | Status | Motivos |
|---|---|---|---|---|---|
| minecraft:diamond_sword | True | True | item | direct | simples |
| minecraft:netherite_sword | True | True | item | direct | simples |
| minecraft:bow | True | True | item | complex_model | condition, range_dispatch |
| minecraft:crossbow | True | True | item | complex_model | condition, range_dispatch, select |
| minecraft:potion | True | True | item | complex_model | multiple_layers, tinted |
| minecraft:splash_potion | True | True | item | complex_model | multiple_layers, tinted |
| minecraft:chest | True | True | block_item | complex_model | gui_transform, select, special_model |
| minecraft:furnace | True | True | block_item | complex_model | block_model, geometry, gui_transform |
| minecraft:spawner | True | True | block_item | complex_model | block_model, geometry, gui_transform |
| minecraft:purple_shulker_box | True | True | block_item | complex_model | gui_transform, special_model |
| minecraft:bundle | True | True | item | complex_model | bundle_selected_item, composite, condition, gui_transform, select |
| minecraft:player_head | True | True | block_item | complex_model | gui_transform, special_model |
| minecraft:written_book | True | True | item | direct | simples |
| minecraft:firework_rocket | True | True | item | direct | simples |

### minecraft:diamond_sword

`assets/minecraft/items/diamond_sword.json` → `assets/minecraft/items/diamond_sword.json#/model [minecraft:model]` → `assets/minecraft/models/item/diamond_sword.json` → `assets/minecraft/models/item/handheld.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/diamond_sword.png`

### minecraft:netherite_sword

`assets/minecraft/items/netherite_sword.json` → `assets/minecraft/items/netherite_sword.json#/model [minecraft:model]` → `assets/minecraft/models/item/netherite_sword.json` → `assets/minecraft/models/item/handheld.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/netherite_sword.png`

### minecraft:bow

`assets/minecraft/items/bow.json` → `assets/minecraft/items/bow.json#/model [minecraft:condition]` → `assets/minecraft/items/bow.json#/model/on_false [minecraft:model]` → `assets/minecraft/models/item/bow.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/bow.png`

### minecraft:crossbow

`assets/minecraft/items/crossbow.json` → `assets/minecraft/items/crossbow.json#/model [minecraft:select]` → `assets/minecraft/items/crossbow.json#/model/fallback [minecraft:condition]` → `assets/minecraft/items/crossbow.json#/model/fallback/on_false [minecraft:model]` → `assets/minecraft/models/item/crossbow.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/crossbow_standby.png`

### minecraft:potion

`assets/minecraft/items/potion.json` → `assets/minecraft/items/potion.json#/model [minecraft:model]` → `assets/minecraft/models/item/potion.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/potion_overlay.png` → `assets/minecraft/textures/item/potion.png`

### minecraft:splash_potion

`assets/minecraft/items/splash_potion.json` → `assets/minecraft/items/splash_potion.json#/model [minecraft:model]` → `assets/minecraft/models/item/splash_potion.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/potion_overlay.png` → `assets/minecraft/textures/item/splash_potion.png`

### minecraft:chest

`assets/minecraft/items/chest.json` → `assets/minecraft/items/chest.json#/model [minecraft:select]` → `assets/minecraft/items/chest.json#/model/fallback [minecraft:special]` → `assets/minecraft/models/item/chest.json` → `assets/minecraft/models/item/template_chest.json`

### minecraft:furnace

`assets/minecraft/items/furnace.json` → `assets/minecraft/items/furnace.json#/model [minecraft:model]` → `assets/minecraft/models/block/furnace.json` → `assets/minecraft/models/block/orientable.json` → `assets/minecraft/models/block/orientable_with_bottom.json` → `assets/minecraft/models/block/cube.json` → `assets/minecraft/models/block/block.json` → `assets/minecraft/textures/block/furnace_top.png` → `assets/minecraft/textures/block/furnace_top.png` → `assets/minecraft/textures/block/furnace_front.png` → `assets/minecraft/textures/block/furnace_side.png` → `assets/minecraft/textures/block/furnace_side.png` → `assets/minecraft/textures/block/furnace_side.png` → `assets/minecraft/textures/block/furnace_top.png` → `assets/minecraft/textures/block/furnace_front.png` → `assets/minecraft/textures/block/furnace_side.png` → `assets/minecraft/textures/block/furnace_top.png`

### minecraft:spawner

`assets/minecraft/items/spawner.json` → `assets/minecraft/items/spawner.json#/model [minecraft:model]` → `assets/minecraft/models/block/spawner.json` → `assets/minecraft/models/block/cube_all_inner_faces.json` → `assets/minecraft/models/block/cube_all.json` → `assets/minecraft/models/block/cube.json` → `assets/minecraft/models/block/block.json` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png` → `assets/minecraft/textures/block/spawner.png`

### minecraft:purple_shulker_box

`assets/minecraft/items/purple_shulker_box.json` → `assets/minecraft/items/purple_shulker_box.json#/model [minecraft:special]` → `assets/minecraft/models/item/purple_shulker_box.json` → `assets/minecraft/models/item/template_shulker_box.json`

### minecraft:bundle

`assets/minecraft/items/bundle.json` → `assets/minecraft/items/bundle.json#/model [minecraft:select]` → `assets/minecraft/items/bundle.json#/model/fallback [minecraft:model]` → `assets/minecraft/models/item/bundle.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/bundle.png`

### minecraft:player_head

`assets/minecraft/items/player_head.json` → `assets/minecraft/items/player_head.json#/model [minecraft:special]` → `assets/minecraft/models/item/template_skull.json`

### minecraft:written_book

`assets/minecraft/items/written_book.json` → `assets/minecraft/items/written_book.json#/model [minecraft:model]` → `assets/minecraft/models/item/written_book.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/written_book.png`

### minecraft:firework_rocket

`assets/minecraft/items/firework_rocket.json` → `assets/minecraft/items/firework_rocket.json#/model [minecraft:model]` → `assets/minecraft/models/item/firework_rocket.json` → `assets/minecraft/models/item/generated.json` → `minecraft:builtin/generated` → `assets/minecraft/textures/item/firework_rocket.png`

## Findings

- O catalogo anterior era visual e permaneceu intacto. AIR era corretamente complexo como modelo vazio, mas nao deve ser selecionavel.
- Os motivos anteriores misturavam tipos de nos, tipos de tint e tipos de renderizadores. Esta auditoria os separa por contexto e detecta tint dentro de todos os ramos.
- Animacao tambem e verificada em texturas de faces/blocos, nao apenas nas camadas generated verificadas anteriormente. Isso detalha dependencias sem mudar os iconStatus existentes.
- heavy_core usa texture_size como metadata e faces com slots sem #; TextureSlots.getMaterial aceita nomes de slot com ou sem #. Nao e referencia quebrada.
- 117 model_resolved sao texturas simples resolvidas por modelo, NAO 117 modelos multicamada suportados.
- Modelos especiais usam base para contexto/GUI; sua geometria e tratada pelo renderer especial, evitando exigir dois renderizadores desnecessariamente na projecao.
- Select/condition/range_dispatch sao analisados em todos os ramos. Nenhuma variante e escolhida arbitrariamente.
- Nao houve rede, novo download/extracao, alteracao de exemplos, frontend ou renderer.
- registry-provenance.json registra hashes das classes/metodos e a evidencia por ID; registry.json apenas referencia essa origem.
- O adaptador de bytecode e deliberadamente limitado: estruturas futuras nao reconhecidas abortam. Nao e uma JVM, nem executa o jogo ou valida disponibilidade por feature flags.
