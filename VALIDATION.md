# Validacao da preparacao de assets 26.2

## Execucao real no Windows

Foi usado Python do runtime local do Codex, pois `python`/`py` nao estavam no PATH:

```powershell
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/sync_minecraft_assets.py --version 26.2
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/audit_asset_examples.py --version 26.2
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Manifest oficial: https://piston-meta.mojang.com/mc/game/version_manifest_v2.json

- ID exato `26.2`, tipo `release`, releaseTime `2026-06-16T12:03:33+00:00`.
- Metadata validado com SHA-1 `bd23a7ec14eb492bc20d8d06508b6ebb0a63c31a`.
- Client: 39.193.383 bytes; SHA-1 esperado e calculado
  `2dc72797acbc1b63fc16a11c4ac393605f453754` (OK).
- A repeticao real reutilizou client.jar, asset index e pt-BR com hashes conferidos.
- 23 testes passaram. Foram testados offline force, cache corrompido, hash
  incorreto, recusa de snapshots/versoes inexistentes, ciclos de aliases/parents,
  ZIP traversal/ADS/symlinks e limpeza limitada a uma unica versao.
- A verificacao real comparou byte a byte TODOS os 10.968 arquivos extraidos de
  assets/ com o JAR e conferiu que nenhuma definicao de item foi descartada.
- A ultima execucao dos testes e da auditoria passou tambem no ambiente restrito,
  depois da correcao de heranca de permissoes de staging no Windows.

## Resultado

| Recurso | Quantidade |
| --- | ---: |
| Definicoes visuais catalogadas | 1.537 |
| Texturas PNG | 3.855 |
| Texturas item | 796 |
| Texturas block | 1.269 |
| Models | 3.928 |
| Sprites gerados por atlas indexados | 640 |
| direct | 520 |
| model_resolved | 117 |
| complex_model | 900 |
| missing | 0 |
| Referencias com problemas detectados | 0 |
| Nomes ausentes em en_us / pt_br | 0 / 0 |

O tamanho exato da pasta, incluindo JAR, assets e auditoria, esta no campo
`totalBytes` de `minecraft-assets/26.2/catalog/report.json`.

| Item exigido | Resultado |
| --- | --- |
| minecraft:diamond_sword | direct |
| minecraft:netherite_sword | direct |
| minecraft:bow | complex_model: condition / range_dispatch |
| minecraft:potion | complex_model: tint / multiplas camadas |
| minecraft:chest | complex_model: select sazonal / special |
| minecraft:furnace | complex_model: geometria / transformacao GUI |
| minecraft:spawner | complex_model: geometria / transformacao GUI |
| minecraft:purple_shulker_box | complex_model: special / transformacao GUI |

Os 900 casos que precisam de renderer estao individualizados com motivos e
referencias em `catalog/unresolved-items.json`; nenhum icone artificial foi gerado.

## Uso dos exemplos fornecidos

Todos os 36 arquivos SNBT foram lidos, sem falhas de parsing: 1.059 ocorrencias de
ItemStacks e 179 IDs unicos, todos cobertos pelo catalogo. A profundidade maxima
observada foi de quatro ItemStacks aninhados, incluindo baus e shulkers.
O override `minecraft:item_model=minecraft:end_portal_frame` foi encontrado em
dois exemplos e conferido como definicao complexa existente.

O auditor distingue ItemStacks de IDs de entidades, efeitos, atributos e textos.
Usa o SNBT fornecido como equivalente textual do NBT binario; nao valida a
equivalencia binaria nem comportamento dentro do jogo. Os exemplos nao foram
alterados e nenhum comando presente neles foi executado.

## Estrutura real e limites

- O JAR inclui en_us, mas pt-BR vem do asset index oficial. Foi baixado e validado
  com SHA-1 `6ebc2361114ce07d71af2cbf00b82d96220ac5f7`.
- Ha 163 valores de textura no formato objeto `{sprite, force_translucent}`,
  alem de 6.444 valores string. O parser foi adaptado; os JSON originais permanecem intactos.
- Paletted permutations dos atlas criam sprites sem PNG individual. O catalogo
  preserva a receita no indice atlas-sprites.json e reserva a renderizacao futura.
- A fonte e o conjunto de definicoes visuais `assets/minecraft/items`; nao foi
  executado um registry do jogo nem gerado um schema completo de components.
- So modelos generated estaticos de uma camada, sem tint/animacao/transformacao
  GUI, recebem directTexture. Texturas auxiliares nao sao apresentadas como icones.
- Containers, aparencia alterada por components, glint, perfis, modelos especiais
  e estados dinamicos continuam sendo responsabilidade de um futuro renderer.
- Todos os assets do JAR foram preservados. Downloads externos ao JAR se limitam
  ao manifest, metadata, asset index e idiomas necessarios; nao foram baixados sons.

Nenhum frontend, backend, banco, editor ou renderer foi criado.

## Etapa posterior: auditoria do registry

A auditoria offline foi adicionada em `tools/audit_minecraft_registry.py`, com
leitura de class files em `tools/minecraft_classfile.py` e inspecao simbolica
em `tools/minecraft_registry_source.py`. Os scripts anteriores e seus 23 testes
foram preservados. O novo conjunto em `tests/test_registry_audit.py` adiciona
26 testes: total de **49 testes passando**.

Comando executado:

```powershell
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/audit_minecraft_registry.py --version 26.2 --verbose
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Confirmados 1.537 registros de item, a partir das chamadas oficiais de registro,
com expansao de colecoes de cores e cobre. Sao 1.536 selecionaveis: 1.054 block
items e 482 itens normais. AIR e a unica exclusao, por ser o sentinela vazio.
Nao foram encontradas definicoes visuais sem registro nem IDs perdidos.

As 637 texturas simples cobrem 41,47% dos selecionaveis. Os 899 selecionaveis
complexos foram analisados recursivamente; o total bruto permanece 900 com AIR.
Nao foi introduzido nenhum missing e nao restaram diagnosticos de referencias.
Todos os 14 itens importantes foram confirmados como registrados e selecionaveis.

O relatorio completo, incluindo motivos sobrepostos, cadeias por item e projecao
incremental sem dupla contagem, esta em `minecraft-assets/26.2/catalog/AUDIT.md`.
As referencias tambem sao comparadas novamente contra o JAR, sem nova extracao.
O hash do client e verificado em toda execucao. Nao foi usada rede nesta etapa.

Precisao em relacao ao relatorio anterior: 1.537 era o total de definicoes
visuais, nao o tamanho correto do seletor. Os iconStatus originais foram mantidos,
mas a auditoria detalha tint aninhado, animacoes em texturas de blocos e distingue
tipos de tint de tipos de nos. Os 117 model_resolved continuam sendo texturas
simples, nao modelos multicamada. O valor totalBytes do report.json original
representa a etapa de sincronizacao/auditoria SNBT, anterior a estes derivados.
