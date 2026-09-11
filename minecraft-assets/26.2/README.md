# Minecraft Java 26.2: assets vanilla

Release oficial confirmada pelo [manifest da Mojang](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json).
O client JAR, metadata e asset index sao validados pelos SHA-1 oficiais.
Os idiomas en_us/pt_br ausentes no JAR sao obtidos do armazenamento oficial
resources.download.minecraft.net, com hash e tamanho do asset index.

## Executar / atualizar (na raiz do projeto, Python 3.10+)

```powershell
python tools/sync_minecraft_assets.py --version 26.2
python tools/sync_minecraft_assets.py --version 26.2 --force
python tools/sync_minecraft_assets.py --version 26.2 --clean
```

Troque `--version` por outra release oficial. Snapshots/pre-releases/RC sao recusados.
`--force` baixa novamente os arquivos oficiais; normalmente o cache e validado.
`--clean` remove SOMENTE minecraft-assets/26.2/ e refaz a sincronizacao.
O manifest e consultado e a release validada antes de qualquer limpeza.
Os assets e catalogos sao reconstruidos em staging; uma falha preserva a ultima
geracao concluida (exceto quando --clean foi solicitado explicitamente).

## Estrutura

- metadata/: manifest, entrada, version.json, client-version.json, asset-index.json, build-info.json.
- raw/client.jar: client oficial com SHA-1 validado, sem copias duplicadas.
- assets/: estrutura integral original do JAR, incluindo models, textures,
  items, blockstates, atlases, equipment, shaders, fontes e arquivos .mcmeta.
- catalog/items.json: uma entrada por definicao, nomes oficiais, fontes e analise do icone.
- catalog/textures.json: PNGs fisicos, dimensoes e metadados de animacao.
- catalog/models.json: caminho e JSON completo de cada modelo no campo data.
- catalog/atlas-sprites.json: sprites gerados por atlas, separados dos PNGs fisicos.
- catalog/unresolved-items.json: itens complexos/ausentes, motivos e referencias.
- catalog/report.json: contagens, proveniencia, hashes, traducao e limitacoes.

Todos os caminhos de assets nos catalogos sao relativos a esta pasta.

## Status dos icones

- direct: layer0 aponta para textures/item/<nome>.png, apos validar a cadeia;
  uma textura de mesmo nome, sozinha, nunca sobrepoe uma definicao complexa.
- model_resolved: modelo generated de camada unica resolvido para outra textura.
- complex_model: requer geometria, tint, camadas, animacao, transformacao de GUI,
  conditions/select/range_dispatch/composite, atlas ou renderizador especial.
  Nao geramos PNG nem escolhemos arbitrariamente uma variante.
- missing: definicao/modelo/textura necessarios nao resolvidos para um icone simples.

`directTexture` so e preenchido nos dois primeiros estados. `resolvedTextures`
pode incluir texturas auxiliares/particle e NAO representa um icone pronto.
`references` preserva cadeias e identificadores especiais; `resourceIssues`
registra referencias nao encontradas. Air e outros modelos vazios sao complexos,
nao itens perdidos. Modelos especiais podem resolver texturas em codigo do jogo.

O catalogo e baseado em definicoes VISUAIS, nao em um registry executado do jogo.
Podem existir variantes visuais e entradas sem item registravel ou nome proprio.
As traducoes usam apenas chaves item.<namespace>.<id> ou block.<namespace>.<id>;
ausencias ficam null, sem inventar traducao. Leia report.json para os casos reais.
Os exemplos NBT/SNBT do projeto sao referencias de cobertura; componentes que
trocam aparencia ou nome nao alteram este catalogo vanilla. O auditor separado
tools/audit_asset_examples.py confere ItemStacks e minecraft:item_model dos SNBT.

## Propriedade

Os assets pertencem ao Minecraft/Mojang/Microsoft. Este projeto apenas os utiliza
para integracao com Minecraft e nao concede direitos de redistribuicao dos assets.
Nenhum site, editor NBT ou renderizador foi criado nesta etapa.

## Estruturas observadas

O parser suporta texturas como string, aliases #layer e objetos com `sprite`.
Opcoes de material como `force_translucent` sao preservadas e exigem renderer.
As contagens reais dos tipos de valor ficam em report.json/modelTextureValueTypes.
Os atlas podem criar sprites por `paletted_permutations`; o indice separado
preserva a receita original, sem fabricar arquivos PNG.
