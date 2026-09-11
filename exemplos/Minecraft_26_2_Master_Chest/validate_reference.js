'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {
  DAMAGE_TYPES,
  COMPONENT_IDS,
  ENCHANTMENT_IDS,
  ITEM_IDS,
} = require('./spec');

const ROOT = __dirname;
const REPORT_PATH = path.join(ROOT, 'SOURCE_VALIDATION_REPORT.md');

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function stripNamespace(id) {
  return id.startsWith('minecraft:') ? id.slice('minecraft:'.length) : id;
}

function validateReference(sourceDirectory, { writeReport = true } = {}) {
  const paths = {
    registries: path.join(sourceDirectory, 'registries.json'),
    blocks: path.join(sourceDirectory, 'blocks.json'),
    itemComponents: path.join(sourceDirectory, 'item_components.json'),
  };
  const errors = [];
  const checks = [];
  const assert = (condition, message) => (condition ? checks.push(message) : errors.push(message));

  for (const [name, filePath] of Object.entries(paths)) {
    assert(fs.existsSync(filePath), `${name}: arquivo de relatório presente`);
  }

  if (!errors.length) {
    const registries = JSON.parse(fs.readFileSync(paths.registries, 'utf8'));
    const blocks = JSON.parse(fs.readFileSync(paths.blocks, 'utf8'));
    const itemComponents = JSON.parse(fs.readFileSync(paths.itemComponents, 'utf8'));

    const registrySet = (key) => new Set(registries[key]);
    const missing = (values, set) => values.map(stripNamespace).filter((id) => !set.has(id));

    const missingItems = missing(ITEM_IDS, registrySet('item'));
    assert(missingItems.length === 0, `Todos os ${ITEM_IDS.length} IDs de item constam no registro 26.2${missingItems.length ? `; ausentes: ${missingItems.join(', ')}` : ''}`);
    const absentDefaults = ITEM_IDS.map(stripNamespace).filter((id) => !Object.hasOwn(itemComponents, id));
    assert(absentDefaults.length === 0, `Todos os IDs de item possuem entrada no relatório de componentes padrão${absentDefaults.length ? `; ausentes: ${absentDefaults.join(', ')}` : ''}`);

    const missingEnchantments = missing(ENCHANTMENT_IDS, registrySet('enchantment'));
    assert(missingEnchantments.length === 0, `Todos os ${ENCHANTMENT_IDS.length} enchantment IDs constam no registro 26.2${missingEnchantments.length ? `; ausentes: ${missingEnchantments.join(', ')}` : ''}`);

    const missingComponents = missing(COMPONENT_IDS, registrySet('data_component_type'));
    assert(missingComponents.length === 0, `Todos os ${COMPONENT_IDS.length} component IDs constam no registro 26.2${missingComponents.length ? `; ausentes: ${missingComponents.join(', ')}` : ''}`);

    const missingDamage = missing(DAMAGE_TYPES, registrySet('damage_type'));
    assert(missingDamage.length === 0, `Todos os ${DAMAGE_TYPES.length} damage type IDs constam no registro 26.2${missingDamage.length ? `; ausentes: ${missingDamage.join(', ')}` : ''}`);

    const attributeIds = ['minecraft:armor', 'minecraft:armor_toughness', 'minecraft:knockback_resistance', 'minecraft:oxygen_bonus'];
    const missingAttributes = missing(attributeIds, registrySet('attribute'));
    assert(missingAttributes.length === 0, `Todos os atributos usados constam no registro 26.2${missingAttributes.length ? `; ausentes: ${missingAttributes.join(', ')}` : ''}`);
    assert(registrySet('trim_pattern').has('silence'), 'Trim pattern minecraft:silence existe');
    assert(registrySet('trim_material').has('quartz'), 'Trim material minecraft:quartz existe');

    const requiredStates = {
      copper_grate: { waterlogged: ['true'] },
      piston: { extended: ['true'], facing: ['up', 'down', 'north', 'south', 'east', 'west'] },
      sticky_piston: { extended: ['true'], facing: ['up', 'down', 'north', 'south', 'east', 'west'] },
      redstone_lamp: { lit: ['true'] },
      powered_rail: { powered: ['true'] },
      activator_rail: { powered: ['true'] },
    };
    for (const [blockId, requiredProperties] of Object.entries(requiredStates)) {
      const report = blocks[blockId];
      assert(Array.isArray(report) && report.length >= 1, `${blockId}: relatório de block states presente`);
      if (!Array.isArray(report) || !report.length) continue;
      const properties = report[0];
      for (const [property, requiredValues] of Object.entries(requiredProperties)) {
        const available = properties[property];
        assert(Array.isArray(available) && requiredValues.every((value) => available.includes(value)), `${blockId}.${property}: valores solicitados existem (${requiredValues.join(', ')})`);
      }
    }

    const chestplateModifiers = itemComponents.netherite_chestplate['minecraft:attribute_modifiers'];
    const chestplateValues = Object.fromEntries(chestplateModifiers.map((entry) => [entry.type, entry.amount]));
    assert(chestplateValues['minecraft:armor'] === 8.0, 'Netherite Chestplate vanilla: armor=8.0');
    assert(chestplateValues['minecraft:armor_toughness'] === 3.0, 'Netherite Chestplate vanilla: armor_toughness=3.0');
    assert(chestplateValues['minecraft:knockback_resistance'] === 0.10000000149011612, 'Netherite Chestplate vanilla: knockback_resistance=0.10000000149011612');
    assert(Object.hasOwn(itemComponents.elytra, 'minecraft:glider'), 'Elytra vanilla possui minecraft:glider');

    const shield = itemComponents.shield['minecraft:blocks_attacks'];
    assert(shield.block_delay_seconds === 0.25, 'Shield vanilla: block_delay_seconds=0.25');
    assert(shield.block_sound === 'minecraft:item.shield.block', 'Shield vanilla: block_sound correto');
    assert(shield.bypassed_by === '#minecraft:bypasses_shield', 'Shield vanilla: bypassed_by correto');
    assert(shield.disabled_sound === 'minecraft:item.shield.break', 'Shield vanilla: disabled_sound correto');
    assert(shield.item_damage.base === 1.0 && shield.item_damage.factor === 1.0 && shield.item_damage.threshold === 3.0, 'Shield vanilla: item_damage 1/1/3');
  }

  const status = errors.length ? 'FAIL' : 'PASS';
  const hashes = Object.fromEntries(Object.entries(paths).filter(([, filePath]) => fs.existsSync(filePath)).map(([name, filePath]) => [name, sha256(filePath)]));
  const report = [
    '# Source Validation Report',
    '',
    `- Status: **${status}**`,
    '- Alvo: relatórios de dados Minecraft Java 26.2',
    '',
    '## Checks',
    '',
    ...checks.map((message) => `- ${message}`),
    '',
    '## Errors',
    '',
    ...(errors.length ? errors.map((message) => `- ${message}`) : ['- Nenhum erro encontrado.']),
    '',
    '## SHA-256 dos relatórios consultados',
    '',
    ...Object.entries(hashes).map(([name, value]) => `- ${name}: \`${value}\``),
    '',
  ].join('\n');

  if (writeReport) fs.writeFileSync(REPORT_PATH, report, 'utf8');
  return { status, checks: checks.length, errors, report };
}

if (require.main === module) {
  const sourceIndex = process.argv.indexOf('--source-dir');
  if (sourceIndex === -1 || !process.argv[sourceIndex + 1]) {
    process.stderr.write('Usage: node validate_reference.js --source-dir <directory> [--check]\n');
    process.exit(2);
  }
  const result = validateReference(path.resolve(process.argv[sourceIndex + 1]), { writeReport: !process.argv.includes('--check') });
  process.stdout.write(result.report);
  if (result.status !== 'PASS') process.exitCode = 1;
}

module.exports = { validateReference };
