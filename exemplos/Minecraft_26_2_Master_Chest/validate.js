'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { decodeNbt, toSnbt, numericValue } = require('./nbt');
const {
  DAMAGE_TYPES,
  COMPONENT_IDS,
  ENCHANTMENT_IDS,
  ITEM_IDS,
  SHULKERS,
  shieldBlocksAttacks,
  buildMasterChest,
  allPayloadItems,
} = require('./spec');

const ROOT = __dirname;
const NBT_PATH = path.join(ROOT, 'minecraft_26_2_master_chest.nbt');
const SNBT_PATH = path.join(ROOT, 'minecraft_26_2_master_chest.snbt');
const MANIFEST_PATH = path.join(ROOT, 'minecraft_26_2_master_chest_manifest.txt');
const REFERENCE_PATH = path.join(ROOT, 'minecraft_26_2_reference.json');
const REPORT_PATH = path.join(ROOT, 'VALIDATION_REPORT.md');

function hash(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function equalSnbt(left, right) {
  return toSnbt(left) === toSnbt(right);
}

function getContainer(stack) {
  return stack.components && stack.components['minecraft:container'];
}

function getName(stack) {
  const value = stack.components && stack.components['minecraft:custom_name'];
  return value && value.text;
}

function validate({ writeReport = true } = {}) {
  const errors = [];
  const checks = [];
  const fail = (message) => errors.push(message);
  const pass = (message) => checks.push(message);
  const assert = (condition, message) => (condition ? pass(message) : fail(message));

  for (const required of [NBT_PATH, SNBT_PATH, MANIFEST_PATH, REFERENCE_PATH]) {
    if (!fs.existsSync(required)) fail(`Arquivo ausente: ${path.basename(required)}`);
  }
  if (errors.length) return finish();

  const binary = fs.readFileSync(NBT_PATH);
  assert(binary[0] === 0x1f && binary[1] === 0x8b, '.nbt possui cabeçalho GZip');

  let decoded;
  try {
    decoded = decodeNbt(binary);
    pass('NBT binário descompactado e parseado até EOF sem bytes residuais');
  } catch (error) {
    fail(`Falha ao parsear NBT binário: ${error.message}`);
    return finish();
  }

  const root = decoded.root;
  assert(decoded.rootName === '', 'Raiz TAG_Compound anônima');
  assert(decoded.compressed, 'NBT detectado como comprimido');

  const snbt = fs.readFileSync(SNBT_PATH, 'utf8');
  const reconstructedSnbt = `${toSnbt(root)}\n`;
  assert(reconstructedSnbt === snbt, '.nbt relido e reserializado é byte a byte equivalente ao .snbt');
  assert(toSnbt(root) === toSnbt(buildMasterChest()), 'Conteúdo relido corresponde integralmente à especificação declarada');

  assert(root.id === 'minecraft:chest', 'ItemStack raiz usa minecraft:chest');
  assert(numericValue(root.count) === 1, 'Master Chest possui count=1');
  assert(getName(root) === 'Master Chest', 'Nome da raiz é Master Chest');
  assert(!Object.hasOwn(root.components, 'minecraft:max_stack_size'), 'Master Chest não sobrescreve max_stack_size');

  const masterContainer = getContainer(root);
  assert(Array.isArray(masterContainer) && masterContainer.length === 5, 'Master Chest contém exatamente cinco shulkers');
  if (!Array.isArray(masterContainer)) return finish();

  const expectedPayload = allPayloadItems();
  const actualPayload = [];
  const seenNumbers = new Set();
  const validItemIds = new Set(ITEM_IDS);
  const validComponents = new Set(COMPONENT_IDS);
  const validEnchantments = new Set(ENCHANTMENT_IDS);

  masterContainer.forEach((outerEntry, outerSlot) => {
    const expectedShulker = SHULKERS[outerSlot];
    const stack = outerEntry.item;
    assert(numericValue(outerEntry.slot) === outerSlot, `Master slot ${outerSlot} está contíguo`);
    assert(Boolean(stack && expectedShulker && stack.id === expectedShulker.id), `Master slot ${outerSlot} contém ${expectedShulker ? expectedShulker.name : 'shulker esperada'}`);
    if (!stack || !expectedShulker) return;
    assert(numericValue(stack.count) === 1, `${expectedShulker.name}: shulker count=1`);
    assert(!Object.hasOwn(stack.components, 'minecraft:max_stack_size'), `${expectedShulker.name}: sem override de max_stack_size`);
    assert(getName(stack) === expectedShulker.name, `${expectedShulker.name}: nome correto`);

    const inner = getContainer(stack);
    assert(Array.isArray(inner), `${expectedShulker.name}: container presente`);
    if (!Array.isArray(inner)) return;
    assert(inner.length === expectedShulker.items.length, `${expectedShulker.name}: ${inner.length} ItemStacks conforme esperado`);
    assert(inner.length <= 27, `${expectedShulker.name}: não excede 27 slots`);

    inner.forEach((entry, slot) => {
      const definition = expectedShulker.items[slot];
      const item = entry.item;
      assert(numericValue(entry.slot) === slot, `${expectedShulker.name} slot ${slot}: índice contíguo`);
      if (!item || !definition) {
        fail(`${expectedShulker.name} slot ${slot}: ItemStack ou definição ausente`);
        return;
      }
      actualPayload.push({ item, definition, shulker: expectedShulker.name, slot });
      seenNumbers.add(definition.number);
    });
  });

  assert(actualPayload.length === 66, 'Foram reparseados 66 ItemStacks de payload');
  assert(seenNumbers.size === 66 && Math.min(...seenNumbers) === 1 && Math.max(...seenNumbers) === 66, 'Numeração lógica 01–66 completa');
  assert(masterContainer.every((entry) => entry.item.id.endsWith('_shulker_box')), 'Nenhum payload está solto diretamente no Master Chest');

  let durableCount = 0;
  let unbreakableCount = 0;
  let repairZeroCount = 0;
  let noAirCount = 0;

  for (const { item, definition, shulker, slot } of actualPayload) {
    const label = `${shulker} slot ${slot} (${definition.name})`;
    assert(item.id === definition.id, `${label}: ID correto`);
    assert(validItemIds.has(item.id), `${label}: ID consta na referência 26.2`);
    assert(numericValue(item.count) === definition.count && definition.count > 0, `${label}: count=${definition.count}`);
    if (item.id !== 'minecraft:air' && numericValue(item.count) > 0) noAirCount += 1;
    assert(getName(item) === definition.name, `${label}: custom_name correto`);
    assert(equalSnbt(item.components, definition.components), `${label}: componentes e valores exatos`);

    const componentKeys = Object.keys(item.components);
    for (const componentId of componentKeys) {
      if (!validComponents.has(componentId)) fail(`${label}: componente não reconhecido na referência: ${componentId}`);
    }
    assert(!componentKeys.includes('minecraft:lore'), `${label}: sem Lore`);
    assert(!componentKeys.includes('minecraft:custom_data'), `${label}: sem custom_data fictício`);
    assert(!componentKeys.includes('minecraft:max_stack_size'), `${label}: sem override de max_stack_size`);

    const enchants = item.components['minecraft:enchantments'];
    if (enchants) {
      for (const [enchantmentId, level] of Object.entries(enchants)) {
        if (!validEnchantments.has(enchantmentId)) fail(`${label}: enchantment ID não reconhecido: ${enchantmentId}`);
        if (numericValue(level) <= 0) fail(`${label}: nível inválido em ${enchantmentId}`);
      }
    }

    if (definition.durable) {
      durableCount += 1;
      const unbreakable = item.components['minecraft:unbreakable'];
      const repairCost = item.components['minecraft:repair_cost'];
      const tooltip = item.components['minecraft:tooltip_display'];
      const resistant = item.components['minecraft:damage_resistant'];
      if (unbreakable && Object.keys(unbreakable).length === 0) unbreakableCount += 1;
      if (repairCost && numericValue(repairCost) === 0) repairZeroCount += 1;
      if (!enchants || numericValue(enchants['minecraft:unbreaking']) !== 3 || numericValue(enchants['minecraft:mending']) !== 1) {
        fail(`${label}: Unbreaking III/Mending I ausente ou incorreto`);
      }
      if (!tooltip || !tooltip.hidden_components.includes('minecraft:unbreakable')) fail(`${label}: Unbreakable não está oculto`);
      if (tooltip && tooltip.hidden_components.includes('minecraft:enchantments')) fail(`${label}: enchantments foram ocultados indevidamente`);
      if (!resistant || JSON.stringify(resistant.types) !== JSON.stringify(DAMAGE_TYPES)) fail(`${label}: lista damage_resistant incorreta`);
    }
  }

  assert(noAirCount === 66, 'Zero IDs minecraft:air e zero stacks com count=0');
  assert(durableCount === 49, '49 itens duráveis identificados');
  assert(unbreakableCount === 49, '49 itens duráveis possuem unbreakable={}');
  assert(repairZeroCount === 49, '49 itens duráveis possuem repair_cost=0');

  const byNumber = new Map(actualPayload.map(({ item, definition }) => [definition.number, item]));
  for (const number of [1, 2, 3, 4]) {
    const value = byNumber.get(number).components['minecraft:trim'];
    assert(value && value.pattern === 'minecraft:silence' && value.material === 'minecraft:quartz', `Item ${number}: Silence + Quartz trim`);
  }
  assert(!Object.hasOwn(byNumber.get(4).components['minecraft:enchantments'], 'minecraft:frost_walker'), 'Boots não possuem Frost Walker');

  const helmetModifiers = byNumber.get(1).components['minecraft:attribute_modifiers'];
  const oxygen = helmetModifiers.find((entry) => entry.type === 'minecraft:oxygen_bonus');
  assert(helmetModifiers.length === 4, 'Helmet preserva três modifiers vanilla e adiciona somente oxygen_bonus');
  assert(oxygen && numericValue(oxygen.amount) === 9 && oxygen.slot === 'head', 'Helmet: oxygen_bonus=9 somente no slot head');
  assert(oxygen && oxygen.display && oxygen.display.type === 'hidden', 'Helmet: somente oxygen_bonus usa display hidden');
  assert(helmetModifiers.filter((entry) => entry.type !== 'minecraft:oxygen_bonus').every((entry) => !entry.display), 'Helmet: modifiers vanilla não foram ocultados');

  const armoredElytra = byNumber.get(5);
  const elytraModifiers = armoredElytra.components['minecraft:attribute_modifiers'];
  assert(Boolean(armoredElytra.components['minecraft:glider']), 'Armored Elytra contém glider');
  assert(elytraModifiers.length === 3, 'Armored Elytra possui somente três modifiers defensivos');
  const expectedDefense = new Map([
    ['minecraft:armor', 8],
    ['minecraft:armor_toughness', 3],
    ['minecraft:knockback_resistance', 0.10000000149011612],
  ]);
  assert(elytraModifiers.every((entry) => expectedDefense.get(entry.type) === numericValue(entry.amount) && entry.slot === 'chest' && entry.display.type === 'hidden'), 'Armored Elytra copia exatamente defesa 8/3/0.10000000149011612 no slot chest e oculta os modifiers');

  const gliderChestplate = byNumber.get(47);
  assert(Boolean(gliderChestplate.components['minecraft:glider']), 'TEST Glider Netherite Chestplate contém glider');
  assert(!Object.hasOwn(gliderChestplate.components, 'minecraft:attribute_modifiers'), 'TEST Glider Chestplate não sobrescreve atributos vanilla');

  for (const number of [48, 49]) {
    assert(equalSnbt(byNumber.get(number).components['minecraft:blocks_attacks'], shieldBlocksAttacks), `Item ${number}: blocks_attacks igual ao Shield vanilla 26.2`);
  }

  const afk = byNumber.get(50).components['minecraft:potion_contents'];
  const effects = afk && afk.custom_effects;
  assert(Array.isArray(effects) && effects.length === 1, 'AFK Potion possui exatamente um custom effect');
  if (Array.isArray(effects) && effects.length === 1) {
    const effect = effects[0];
    assert(effect.id === 'minecraft:regeneration', 'AFK Potion usa Regeneration');
    assert(numericValue(effect.amplifier) === 1, 'AFK Potion usa amplifier=1 (Regeneration II)');
    assert(numericValue(effect.duration) === -1, 'AFK Potion usa duration=-1 (infinita)');
    assert(numericValue(effect.show_particles) === 0 && numericValue(effect.show_icon) === 0, 'AFK Potion não mostra partículas nem ícone');
  }

  for (let number = 51; number <= 66; number += 1) {
    const state = byNumber.get(number).components['minecraft:block_state'];
    assert(state && Object.values(state).every((value) => typeof value === 'string'), `Item ${number}: block_state usa valores string`);
  }
  assert(equalSnbt(byNumber.get(51).components['minecraft:block_state'], { waterlogged: 'true' }), 'Copper Grate: somente waterlogged=true');
  for (let number = 52; number <= 63; number += 1) {
    const state = byNumber.get(number).components['minecraft:block_state'];
    assert(state.extended === 'true' && ['up', 'down', 'north', 'south', 'east', 'west'].includes(state.facing), `Item ${number}: piston extended=true e facing válido`);
  }
  assert(equalSnbt(byNumber.get(64).components['minecraft:block_state'], { lit: 'true' }), 'Redstone Lamp: lit=true');
  assert(equalSnbt(byNumber.get(65).components['minecraft:block_state'], { powered: 'true' }), 'Powered Rail: somente powered=true');
  assert(equalSnbt(byNumber.get(66).components['minecraft:block_state'], { powered: 'true' }), 'Activator Rail: somente powered=true');

  for (let number = 38; number <= 49; number += 1) {
    assert(getName(byNumber.get(number)).startsWith('TEST -'), `Item ${number}: nome começa com TEST -`);
  }
  assert(getName(byNumber.get(50)) === 'AFK Potion', 'Item 50 preserva o nome explicitamente pedido AFK Potion');

  const manifest = fs.readFileSync(MANIFEST_PATH, 'utf8');
  assert(expectedPayload.every((definition) => manifest.includes(`${String(definition.number).padStart(2, '0')} | slot`) && manifest.includes(definition.name)), 'Manifest contém os 66 nomes e números');
  const reference = JSON.parse(fs.readFileSync(REFERENCE_PATH, 'utf8'));
  assert(reference.minecraftVersion === '26.2' && reference.worldVersion === 4903, 'Referência congelada aponta para Minecraft 26.2 / world_version 4903');
  assert(reference.serverJarSha1 === '823e2250d24b3ddac457a60c92a6a941943fcd6a', 'SHA-1 do server.jar oficial registrado corretamente');

  function finish() {
    const status = errors.length === 0 ? 'PASS' : 'FAIL';
    const report = [
      '# Validation Report',
      '',
      `- Status: **${status}**`,
      `- Gerado em: ${new Date().toISOString()}`,
      '- Alvo: Minecraft Java 26.2',
      '- Escopo: NBT binário + equivalência SNBT + validação semântica offline',
      '',
      '## Checks',
      '',
      ...checks.map((message) => `- ${message}`),
      '',
      '## Errors',
      '',
      ...(errors.length ? errors.map((message) => `- ${message}`) : ['- Nenhum erro encontrado.']),
      '',
      '## Hashes',
      '',
      ...(fs.existsSync(NBT_PATH) ? [`- NBT SHA-256: \`${hash(fs.readFileSync(NBT_PATH))}\``] : []),
      ...(fs.existsSync(SNBT_PATH) ? [`- SNBT SHA-256: \`${hash(fs.readFileSync(SNBT_PATH))}\``] : []),
      '',
      '## Limite da validação',
      '',
      '- O validador relê o arquivo binário, confere tipos NBT, estrutura, IDs congelados da 26.2 e todos os requisitos do prompt.',
      '- O comportamento dos itens deliberadamente incompatíveis continua dependendo de teste manual dentro do jogo.',
      '- Nenhum save ou arquivo em `.minecraft` foi modificado.',
      '',
    ].join('\n');
    if (writeReport) fs.writeFileSync(REPORT_PATH, report, 'utf8');
    return { status, checks: checks.length, errors, report, reportPath: REPORT_PATH };
  }

  return finish();
}

if (require.main === module) {
  const result = validate({ writeReport: !process.argv.includes('--check') });
  process.stdout.write(result.report);
  if (result.status !== 'PASS') process.exitCode = 1;
}

module.exports = { validate };
