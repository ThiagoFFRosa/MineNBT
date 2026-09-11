'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { writeGzipNbt, toSnbt, numericValue } = require('./nbt');
const {
  DAMAGE_TYPES,
  COMPONENT_IDS,
  ENCHANTMENT_IDS,
  ITEM_IDS,
  SHULKERS,
  buildMasterChest,
  allPayloadItems,
} = require('./spec');

const ROOT = __dirname;
const OUTPUTS = Object.freeze({
  nbt: path.join(ROOT, 'minecraft_26_2_master_chest.nbt'),
  snbt: path.join(ROOT, 'minecraft_26_2_master_chest.snbt'),
  manifest: path.join(ROOT, 'minecraft_26_2_master_chest_manifest.txt'),
  reference: path.join(ROOT, 'minecraft_26_2_reference.json'),
});

function levelText(enchantments) {
  if (!enchantments) return 'none';
  return Object.entries(enchantments)
    .map(([id, level]) => `${id}=${numericValue(level)}`)
    .join(', ');
}

function attributeText(attributes) {
  if (!attributes) return 'none';
  return attributes.map((entry) => {
    const hidden = entry.display && entry.display.type === 'hidden' ? ', display=hidden' : '';
    return `${entry.type} ${numericValue(entry.amount)} (${entry.operation}, ${entry.slot}, id=${entry.id}${hidden})`;
  }).join('; ');
}

function componentDetails(item) {
  const components = item.components;
  const details = [];
  if (components['minecraft:block_state']) {
    details.push(`block_state=${JSON.stringify(components['minecraft:block_state'])}`);
  }
  if (components['minecraft:damage_resistant']) {
    details.push(`damage_resistant=${components['minecraft:damage_resistant'].types.join(',')}`);
  }
  if (components['minecraft:trim']) {
    const value = components['minecraft:trim'];
    details.push(`trim=${value.pattern}+${value.material}`);
  }
  if (components['minecraft:glider']) details.push('glider=present');
  if (components['minecraft:blocks_attacks']) details.push('blocks_attacks=vanilla shield configuration');
  if (components['minecraft:potion_contents']) {
    const effect = components['minecraft:potion_contents'].custom_effects[0];
    details.push(`potion=${effect.id}, amplifier=${numericValue(effect.amplifier)}, duration=${numericValue(effect.duration)}, particles=${numericValue(effect.show_particles)}, icon=${numericValue(effect.show_icon)}`);
  }
  return details.length ? details.join('; ') : 'none';
}

function renderManifest() {
  const items = allPayloadItems();
  const durableCount = items.filter((item) => item.durable).length;
  const lines = [
    'MINECRAFT JAVA 26.2 - MASTER CHEST MANIFEST',
    '=============================================',
    '',
    'Root ItemStack: minecraft:chest, count=1, name=Master Chest',
    `Nested shulkers: ${SHULKERS.length}`,
    `Payload ItemStacks: ${items.length}`,
    `Durable ItemStacks with unbreakable/repair_cost=0: ${durableCount}`,
    'No payload item is stored directly in the Master Chest.',
    'No item has minecraft:lore or minecraft:custom_data.',
    '',
  ];

  for (const shulker of SHULKERS) {
    lines.push(`[${shulker.name}] ${shulker.id} - Master Chest slot ${SHULKERS.indexOf(shulker)}`);
    lines.push('-'.repeat(72));
    for (const item of items.filter((entry) => entry.shulker === shulker.name)) {
      lines.push(`${String(item.number).padStart(2, '0')} | slot ${item.slot} | ${item.name}`);
      lines.push(`   ID: ${item.id}`);
      lines.push(`   Count: ${item.count}`);
      lines.push(`   Components: ${Object.keys(item.components).join(', ')}`);
      lines.push(`   Enchantments: ${levelText(item.components['minecraft:enchantments'])}`);
      lines.push(`   Attribute modifiers: ${attributeText(item.components['minecraft:attribute_modifiers'])}`);
      lines.push(`   Special values: ${componentDetails(item)}`);
      if (item.notes.length) lines.push(`   Notes: ${item.notes.join('; ')}`);
      lines.push('');
    }
  }

  lines.push('Gameplay experiments are intentionally not marked as successful or failed.');
  lines.push('Their behavior must be confirmed inside Minecraft Java 26.2 on a backed-up test world.');
  return `${lines.join('\r\n')}\r\n`;
}

function renderReference() {
  return `${JSON.stringify({
    minecraftVersion: '26.2',
    worldVersion: 4903,
    dataPackVersion: '107.1',
    serverJarSha1: '823e2250d24b3ddac457a60c92a6a941943fcd6a',
    clientJarSha1: '2dc72797acbc1b63fc16a11c4ac393605f453754',
    reportSha256: {
      registries: 'fcce28462563e28477eb72074807e1ff7f106e2244fefbfd74afe84334d34ed9',
      blocks: '0b1470910281d2f7ac36544672fc04befcd600c9dab1574d0636727ae6531726',
      itemComponents: 'b0e9cf2633892ea39f59ba2039fcdcb9e9253a961b439dcd3f98e7687d5019d7',
    },
    itemIds: ITEM_IDS,
    componentIds: COMPONENT_IDS,
    enchantmentIds: ENCHANTMENT_IDS,
    attributeIdsUsed: ['minecraft:armor', 'minecraft:armor_toughness', 'minecraft:knockback_resistance', 'minecraft:oxygen_bonus'],
    damageTypesUsed: DAMAGE_TYPES,
    blockStatesUsed: {
      minecraft_copper_grate: { waterlogged: ['true', 'false'] },
      minecraft_piston: { extended: ['true', 'false'], facing: ['up', 'down', 'north', 'south', 'east', 'west'] },
      minecraft_sticky_piston: { extended: ['true', 'false'], facing: ['up', 'down', 'north', 'south', 'east', 'west'] },
      minecraft_redstone_lamp: { lit: ['true', 'false'] },
      minecraft_powered_rail: { powered: ['true', 'false'] },
      minecraft_activator_rail: { powered: ['true', 'false'] },
    },
    netheriteChestplateDefense: {
      armor: 8.0,
      armorToughness: 3.0,
      knockbackResistance: 0.10000000149011612,
    },
  }, null, 2)}\n`;
}

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function generate({ checkOnly = false } = {}) {
  const root = buildMasterChest();
  const snbt = `${toSnbt(root)}\n`;
  const manifest = renderManifest();
  const reference = renderReference();

  if (checkOnly) {
    return {
      mode: 'check-only',
      payloadItems: allPayloadItems().length,
      shulkers: SHULKERS.length,
      snbtBytes: Buffer.byteLength(snbt, 'utf8'),
    };
  }

  fs.writeFileSync(OUTPUTS.snbt, snbt, 'utf8');
  writeGzipNbt(OUTPUTS.nbt, root, '');
  fs.writeFileSync(OUTPUTS.manifest, manifest, 'utf8');
  fs.writeFileSync(OUTPUTS.reference, reference, 'utf8');

  return {
    mode: 'generated',
    payloadItems: allPayloadItems().length,
    shulkers: SHULKERS.length,
    files: Object.fromEntries(Object.entries(OUTPUTS).map(([name, filePath]) => [name, {
      path: filePath,
      bytes: fs.statSync(filePath).size,
      sha256: sha256(filePath),
    }])),
  };
}

if (require.main === module) {
  const result = generate({ checkOnly: process.argv.includes('--check') });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

module.exports = { OUTPUTS, generate, renderManifest, renderReference };
