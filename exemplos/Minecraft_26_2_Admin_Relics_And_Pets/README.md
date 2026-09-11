# Minecraft 26.2 - Relíquias Administrativas e Pets

Kit de importação para um Item Editor compatível com ItemStacks em SNBT/Data Components da Java 26.2.

Arquivo principal:

- `admin_relics_pets_shulker.snbt` - uma Light Blue Shulker Box com todos os itens.

O kit não modifica saves, não abre mundos e não instala datapack, mod, plugin ou resource pack.

## Conteúdo da shulker

| Slot | Item | Função |
|---:|---|---|
| 0 | Console Administrativa | Livro com botões para gamemode, horário, efeitos e adoção dos pets |
| 1 | Aegis Flightplate | Peitoral de netherita indestrutível com `minecraft:glider` e proteções combinadas |
| 2 | Coroa do Titã | +80 de vida, armadura, dano, alcance, tamanho, step height e resistência a knockback |
| 3 | Omnitool da Fortuna | Ferramenta universal com Fortuna X e durabilidade normal |
| 4 | Omnitool Toque Suave | Ferramenta universal com Silk Touch e durabilidade normal |
| 5 | Omnitool Eterna da Fortuna | Variante indestrutível com Fortuna X |
| 6 | Omnitool Eterna Toque Suave | Variante indestrutível com Silk Touch |
| 7 | Ovo de Nicks | Gato laranja `red`, 300 HP, ataque base 20 e Regeneração III permanente |
| 8 | Ovo de Kuronai | Black Wolf, 300 HP, ataque base 20 e Regeneração III permanente |
| 9 | Ovo de Celestine | Snowy Wolf, 300 HP, ataque base 20 e Regeneração III permanente |
| 10 | Stick para Matar Pets Gods | +499 de attack damage; com o dano base do jogador, totaliza 500 |
| 11 | Ossos | 64 unidades para domesticação vanilla alternativa |
| 12 | Bacalhau | 64 unidades para domesticar Nicks pela mecânica vanilla |

## Livro administrativo

O livro não possui teleporte. Ele contém:

- Survival, Creative, Adventure e Spectator;
- dia, meio-dia, noite e meia-noite;
- Visão Noturna, Velocidade III, Pressa IV, Força III, Resistência II, Resistência ao Fogo, Respiração Aquática, Regeneração II e Queda Lenta;
- botão para limpar todos os efeitos;
- botões para adotar Nicks, Kuronai e Celestine.

Os botões usam `click_event` com `run_command`. Cheats ou permissão de comandos são obrigatórios. Versões modernas podem mostrar uma tela de confirmação antes de executar comandos elevados vindos de livros.

## Adoção dos pets

1. Gere o pet com o ovo.
2. Fique a até 16 blocos dele.
3. Abra a página **ADOTAR PETS** do livro.
4. Clique no nome correspondente.

O botão copia o UUID do jogador que clicou para o campo `Owner` do pet mais próximo com aquele nome. Isso evita colocar um UUID fixo e faz o mesmo ItemStack funcionar para qualquer jogador com permissão.

Os ossos e o bacalhau são uma alternativa vanilla. O botão do livro é recomendado porque atribui o dono diretamente. O gato possui ataque base 20, mas continua usando a IA normal de gato e não se transforma em um combatente equivalente a um lobo.

## Ferramentas universais

As quatro Omnitools substituem o componente `minecraft:tool` por regras para:

- `#minecraft:mineable/pickaxe`;
- `#minecraft:mineable/axe`;
- `#minecraft:mineable/shovel`;
- `#minecraft:mineable/hoe`.

Isso unifica velocidade e drops de mineração. As interações de botão direito continuam sendo as da picareta de netherita; o componente não adiciona simultaneamente os gestos de tirar casca, criar caminho ou arar terra.

## Segurança e limites

- Faça backup do mundo antes de importar itens experimentais.
- O stick causa aproximadamente 500 de dano e pode matar praticamente qualquer criatura comum.
- Os pets não são invulneráveis: possuem 300 HP e Regeneração III, portanto o stick continua sendo um método de remoção.
- Nenhum valor usa `NaN`, infinito, overflow, recursão de containers ou payload gigante.
- A validação incluída é offline e não substitui o codec do jogo ou um teste manual no Item Editor.

## Uso

Importe diretamente o conteúdo de `admin_relics_pets_shulker.snbt` no Item Editor. Não copie o arquivo para `level.dat`, `playerdata` ou pastas de região.

