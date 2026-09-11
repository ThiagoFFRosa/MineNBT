# Infraestrutura de assets Minecraft

Ferramenta local em Python 3.10+ (somente biblioteca padrao) para baixar, validar,
preservar e catalogar assets de releases oficiais Minecraft Java. Esta etapa nao
cria site, backend, editor NBT ou renderer.

Na raiz do projeto:

```powershell
python tools/sync_minecraft_assets.py --version 26.2
python tools/audit_asset_examples.py --version 26.2
python -m unittest discover -s tests -v
```

O destino e sempre `minecraft-assets/<versao>/` dentro deste projeto, mesmo ao
executar o script de outro diretorio. Internet e necessaria para consultar o manifest.
Use `--force` para baixar novamente; `--clean` para remover apenas a versao escolhida
e reconstruir. O client em cache so e reutilizado apos conferir SHA-1 e tamanho.
Nao ha fallback para snapshots nem para uma versao diferente da solicitada.

O Python nao estava no PATH deste PC durante a preparacao. Foi utilizado o runtime
Python ja fornecido pelo Codex; a ferramenta tambem funciona com uma instalacao
normal de Python 3.10+ e nao depende do Codex.

Comando efetivamente usado neste PC (PowerShell):

```powershell
& 'C:\Users\Fuzz.s\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/sync_minecraft_assets.py --version 26.2
```

Leia o README gerado em `minecraft-assets/<versao>/README.md` para estrutura,
classificacao de icones e limitacoes. Todos os assets do JAR sao preservados; pt-BR
e obtido pelo asset index oficial quando ausente no JAR. Arquivos existentes em
`exemplos/` permanecem intactos.

## Exemplos

O auditor le todos os `.snbt` em `exemplos/`, percorre os ItemStacks aninhados e
confere seus IDs e overrides `minecraft:item_model` no catalogo vanilla.
O `.nbt` binario tem uma representacao `.snbt` fornecida na mesma pasta, utilizada
na auditoria. Nao executa comandos, nao altera os exemplos e nao valida gameplay.
O resultado e `catalog/example-coverage.json`. Repita a auditoria apos cada sync,
pois `catalog/` e reconstruido pela sincronizacao.

## Versionamento

Somente o JAR oficial, staging temporario e cache Python sao ignorados.
Catalogos e assets extraidos continuam disponiveis para versionamento; o projeto
nao tinha `.gitignore` nem repositorio Git inicializado nesta etapa.
Os assets pertencem ao Minecraft/Mojang/Microsoft e sao usados para integracao
com Minecraft. A ferramenta nao concede direitos de redistribuicao dos assets.

## Auditoria do registry e do futuro renderer

Depois da sincronizacao, execute a auditoria separada, totalmente offline:

```powershell
python tools/audit_minecraft_registry.py --version 26.2 --verbose
```

O client local e validado por SHA-1. A ferramenta inspeciona as classes oficiais
de registro com nomes legiveis, expande as colecoes de cores/cobre e verifica a
hierarquia real de cada classe Item/BlockItem. Nao executa Java nem o jogo.
Formatos de bytecode nao suportados abortam; nenhum ID e inferido de texturas.

Arquivos derivados em `minecraft-assets/<versao>/catalog/`:

- `registry.json`: entrada por ID, com `selectable`, `kind`, nomes e icone.
- `registry-provenance.json`: evidencia oficial por ID e hashes de classes/metodos.
- `non-selectable-definitions.json`: exclusoes justificadas.
- `complex-model-breakdown.json`: motivos, referencias, ramos e diagnosticos.
- `renderer-requirements.json`: capacidades necessarias e itens afetados.
- `renderer-coverage.json`: ganhos independentes e incrementais, sem dupla contagem.
- `important-item-checks.json`: verificacao dos 14 itens solicitados.
- `AUDIT.md`: relatorio humano completo.

Na 26.2, as 1.537 definicoes correspondem a registros reais. O seletor deve filtrar
`selectable == true`: sao 1.536 entradas (1.054 BlockItems e 482 itens normais).
`minecraft:air` e registrado, mas ItemStack.isEmpty o trata como vazio.
Itens acessiveis por comandos permanecem selecionaveis; nao e uma lista de abas creative.

Repita esta auditoria apos cada sync: o sincronizador reconstrói `catalog/`.
Os catálogos originais e os exemplos nao sao modificados pela auditoria.
A projecao mede suporte potencial aos ramos vanilla, nao imagens renderizadas
nem suporte irrestrito a components/resource packs. O sincronizador original
continua sem renderer; direct/model_resolved significam lookup de textura simples.

## Frontend NBT GEN (catálogo e renderer base)

A primeira interface funcional usa **React 19, TypeScript, Vite e Three.js**. Foi
desenvolvida e validada com Node.js 20.20.2. Os assets continuam em
`minecraft-assets/<versao>/`: um plugin Vite mínimo serve diretamente esse
diretório, sem links simbólicos ou uma segunda cópia no código-fonte (no build,
ele é incluído normalmente em `dist`). Isso funciona também no Windows.

```powershell
npm install
npm run dev
npm test
npm run build
npm run validate:frontend
```

Abra o endereço exibido pelo Vite. O picker usa as 1.536 entradas `selectable`
do registry oficial, busca ID/nome inglês/pt-BR sem diferenciar acentos e filtra
itens e Block Items. O grid usa imagens para sprites e `IntersectionObserver`
para só resolver geometria próxima da viewport.

### Arquitetura do frontend

- `src/minecraft`: versão, registry, pesquisa e caminhos de assets seguros;
- `src/renderer/models`: herança de modelos, variáveis `#texture` e caches;
- `src/renderer/block`: geometria vanilla e transformação `display.gui`;
- `src/renderer/textures`: cache de textura com nearest-neighbor;
- `src/components` e `src/app`: estado e apresentação React, sem lógica de assets.

O renderer 3D é isolado e mantém **um único contexto WebGL compartilhado**. Cada
preview é convertido em imagem e guardado em memória; geometrias temporárias são
descartadas. Faces, UV, rotação de face/elemento, materiais transparentes,
iluminação previsível, câmera ortográfica e transformações GUI são suportadas.
`cullface` é deliberadamente ignorado no preview de inventário; ambient occlusion
e iluminação vanilla são aproximados.

Renderers especiais, tint dinâmico, layers, state dispatch, animações, atlas,
conteúdo de bundles e editores NBT/components permanecem explicitamente fora do
escopo. Esses itens não desaparecem: recebem fallback e diagnóstico. Execute
`npm run validate:frontend` para recalcular `frontend-validation.json` a partir de
todos os itens e modelos reais da versão atual.

# NBT GEN — editor de ItemStacks

A aplicação agora usa `/` como landing, `/editor` como workspace e mantém `/renderer-test` como ferramenta exclusiva de desenvolvimento. O fluxo principal abre o seletor pesquisável dos 1.536 itens, cria um `EditableItem` moderno (`id`, `count`, `components`) e oferece preview, validação e exportação.

## Arquitetura do editor

- `src/minecraft/item/`: modelo interno normalizado, operações imutáveis, capabilities e validação.
- `src/minecraft/nbt/`: parser/serializer SNBT, command moderno e Project JSON.
- `src/components/editor/`: shell, editor genérico e editor recursivo de containers.
- `src/renderer/`: permanece independente da UI; caches e contexto WebGL compartilhado são reutilizados.
- `exemplos/`: corpus de fixtures e referência, nunca importado como código experimental no bundle.

Chests, barrels e shulker boxes têm 27 slots. Cada slot contém o mesmo `EditableItem`, permitindo nesting sem um schema reduzido. Somente o caminho aberto é montado, e a inspeção informa profundidade, total de itens e tamanho estimado. Undo/redo mantém uma janela de 50 estados imutáveis.

Há UI visual para text components, lore, enchantments sem limite artificial, `unbreakable` e valores numéricos comuns. Components conhecidos sem formulário dedicado e components desconhecidos continuam preservados no editor JSON estruturado.

## Formatos

- Import real: Project JSON e SNBT moderno.
- Export real: SNBT, `/give` com component syntax e Project JSON.
- NBT binário aparece apenas como “Em desenvolvimento”; nenhum arquivo falso é produzido.

O parser aceita compounds, lists, strings escapadas, bare values e sufixos numéricos. Nesta versão os números são normalizados para `number`; preservar a largura exata da tag numérica e importar NBT binário permanecem limitações documentadas.

## Frontend

```bash
npm install
npm run dev
npm test
npm run build
npm run validate:frontend
```

Desktop é prioritário; em telas menores a navegação compacta e o preview passa para baixo do editor.
