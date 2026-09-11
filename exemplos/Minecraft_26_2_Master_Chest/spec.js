'use strict';

const { byte, int, float, double } = require('./nbt');

const DAMAGE_TYPES = Object.freeze([
  'minecraft:in_fire',
  'minecraft:on_fire',
  'minecraft:lava',
  'minecraft:explosion',
  'minecraft:player_explosion',
]);

const COMPONENT_IDS = Object.freeze([
  'minecraft:attribute_modifiers',
  'minecraft:block_state',
  'minecraft:blocks_attacks',
  'minecraft:container',
  'minecraft:custom_name',
  'minecraft:damage_resistant',
  'minecraft:enchantments',
  'minecraft:glider',
  'minecraft:potion_contents',
  'minecraft:repair_cost',
  'minecraft:tooltip_display',
  'minecraft:trim',
  'minecraft:unbreakable',
]);

const ENCHANTMENT_IDS = Object.freeze([
  'minecraft:aqua_affinity',
  'minecraft:bane_of_arthropods',
  'minecraft:blast_protection',
  'minecraft:breach',
  'minecraft:channeling',
  'minecraft:density',
  'minecraft:depth_strider',
  'minecraft:efficiency',
  'minecraft:feather_falling',
  'minecraft:fire_aspect',
  'minecraft:fire_protection',
  'minecraft:flame',
  'minecraft:fortune',
  'minecraft:impaling',
  'minecraft:infinity',
  'minecraft:knockback',
  'minecraft:looting',
  'minecraft:loyalty',
  'minecraft:luck_of_the_sea',
  'minecraft:lunge',
  'minecraft:lure',
  'minecraft:mending',
  'minecraft:multishot',
  'minecraft:piercing',
  'minecraft:power',
  'minecraft:projectile_protection',
  'minecraft:protection',
  'minecraft:punch',
  'minecraft:quick_charge',
  'minecraft:respiration',
  'minecraft:riptide',
  'minecraft:sharpness',
  'minecraft:silk_touch',
  'minecraft:smite',
  'minecraft:soul_speed',
  'minecraft:sweeping_edge',
  'minecraft:swift_sneak',
  'minecraft:thorns',
  'minecraft:unbreaking',
  'minecraft:wind_burst',
]);

const ITEM_IDS = Object.freeze([
  'minecraft:activator_rail',
  'minecraft:bow',
  'minecraft:brush',
  'minecraft:carrot_on_a_stick',
  'minecraft:chest',
  'minecraft:copper_grate',
  'minecraft:crossbow',
  'minecraft:elytra',
  'minecraft:fishing_rod',
  'minecraft:flint_and_steel',
  'minecraft:gray_shulker_box',
  'minecraft:mace',
  'minecraft:netherite_axe',
  'minecraft:netherite_boots',
  'minecraft:netherite_chestplate',
  'minecraft:netherite_helmet',
  'minecraft:netherite_hoe',
  'minecraft:netherite_leggings',
  'minecraft:netherite_pickaxe',
  'minecraft:netherite_shovel',
  'minecraft:netherite_spear',
  'minecraft:netherite_sword',
  'minecraft:orange_shulker_box',
  'minecraft:piston',
  'minecraft:potion',
  'minecraft:powered_rail',
  'minecraft:purple_shulker_box',
  'minecraft:red_shulker_box',
  'minecraft:redstone_lamp',
  'minecraft:shears',
  'minecraft:shield',
  'minecraft:sticky_piston',
  'minecraft:trident',
  'minecraft:warped_fungus_on_a_stick',
  'minecraft:white_shulker_box',
]);

function customName(text) {
  return { text, italic: byte(0) };
}

function enchantments(entries) {
  const result = {};
  for (const [id, level] of entries) result[`minecraft:${id}`] = int(level);
  return result;
}

function durableEnchantments(entries) {
  return enchantments([...entries, ['unbreaking', 3], ['mending', 1]]);
}

function trim() {
  return { material: 'minecraft:quartz', pattern: 'minecraft:silence' };
}

function attribute(type, amount, id, slot, hidden = false) {
  const modifier = {
    type: `minecraft:${type}`,
    amount: double(amount),
    id,
    operation: 'add_value',
    slot,
  };
  if (hidden) modifier.display = { type: 'hidden' };
  return modifier;
}

function durableItem(number, name, id, enchantmentEntries, extraComponents = {}, notes = []) {
  const components = {
    'minecraft:custom_name': customName(name),
    'minecraft:enchantments': durableEnchantments(enchantmentEntries),
    ...extraComponents,
    'minecraft:unbreakable': {},
    'minecraft:repair_cost': int(0),
    'minecraft:damage_resistant': { types: [...DAMAGE_TYPES] },
    'minecraft:tooltip_display': {
      hidden_components: ['minecraft:unbreakable', 'minecraft:damage_resistant'],
    },
  };
  return { number, name, id: `minecraft:${id}`, count: 1, durable: true, components, notes };
}

function plainItem(number, name, id, count, extraComponents = {}, notes = []) {
  return {
    number,
    name,
    id: `minecraft:${id}`,
    count,
    durable: false,
    components: {
      'minecraft:custom_name': customName(name),
      ...extraComponents,
    },
    notes,
  };
}

const helmetAttributes = [
  attribute('armor', 3.0, 'minecraft:armor.helmet', 'head'),
  attribute('armor_toughness', 3.0, 'minecraft:armor.helmet', 'head'),
  attribute('knockback_resistance', 0.10000000149011612, 'minecraft:armor.helmet', 'head'),
  attribute('oxygen_bonus', 9.0, 'master_chest:oxygen_bonus', 'head', true),
];

const elytraAttributes = [
  attribute('armor', 8.0, 'minecraft:armor.chestplate', 'chest', true),
  attribute('armor_toughness', 3.0, 'minecraft:armor.chestplate', 'chest', true),
  attribute('knockback_resistance', 0.10000000149011612, 'minecraft:armor.chestplate', 'chest', true),
];

const shieldBlocksAttacks = {
  block_delay_seconds: float(0.25),
  block_sound: 'minecraft:item.shield.block',
  bypassed_by: '#minecraft:bypasses_shield',
  disabled_sound: 'minecraft:item.shield.break',
  item_damage: {
    base: float(1.0),
    factor: float(1.0),
    threshold: float(3.0),
  },
};

const armor = [
  durableItem(1, 'Legacy Netherite Helmet', 'netherite_helmet', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5],
    ['thorns', 3], ['respiration', 3], ['aqua_affinity', 1],
  ], {
    'minecraft:trim': trim(),
    'minecraft:attribute_modifiers': helmetAttributes,
  }, ['oxygen_bonus +9 in head slot; only the oxygen modifier is hidden']),
  durableItem(2, 'Legacy Netherite Chestplate', 'netherite_chestplate', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5], ['thorns', 3],
  ], { 'minecraft:trim': trim() }),
  durableItem(3, 'Legacy Netherite Leggings', 'netherite_leggings', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5],
    ['thorns', 3], ['swift_sneak', 3],
  ], { 'minecraft:trim': trim() }),
  durableItem(4, 'Legacy Netherite Boots', 'netherite_boots', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5],
    ['thorns', 3], ['feather_falling', 4], ['depth_strider', 3], ['soul_speed', 3],
  ], { 'minecraft:trim': trim() }, ['No Frost Walker']),
  durableItem(5, 'Armored Elytra', 'elytra', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5], ['thorns', 3],
  ], {
    'minecraft:glider': {},
    'minecraft:attribute_modifiers': elytraAttributes,
  }, ['Exact Netherite Chestplate defense: armor 8, toughness 3, knockback resistance 0.10000000149011612']),
];

const tools = [
  durableItem(6, 'Fortune Pickaxe', 'netherite_pickaxe', [['efficiency', 5], ['fortune', 3]]),
  durableItem(7, 'Silk Pickaxe', 'netherite_pickaxe', [['efficiency', 5], ['silk_touch', 1]]),
  durableItem(8, 'Fortune Axe', 'netherite_axe', [
    ['efficiency', 5], ['fortune', 3], ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5],
    ['fire_aspect', 2], ['looting', 3],
  ]),
  durableItem(9, 'Silk Axe', 'netherite_axe', [
    ['efficiency', 5], ['silk_touch', 1], ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5],
    ['fire_aspect', 2], ['looting', 3],
  ]),
  durableItem(10, 'Fortune Shovel', 'netherite_shovel', [['efficiency', 5], ['fortune', 3]]),
  durableItem(11, 'Silk Shovel', 'netherite_shovel', [['efficiency', 5], ['silk_touch', 1]]),
  durableItem(12, 'Fortune Hoe', 'netherite_hoe', [['efficiency', 5], ['fortune', 3]]),
  durableItem(13, 'Silk Hoe', 'netherite_hoe', [['efficiency', 5], ['silk_touch', 1]]),
  durableItem(14, 'Eternal Shears', 'shears', [['efficiency', 5], ['silk_touch', 1]]),
  durableItem(15, 'Eternal Flint and Steel', 'flint_and_steel', []),
  durableItem(16, 'Fishing Rod', 'fishing_rod', [['luck_of_the_sea', 3], ['lure', 3]]),
  durableItem(17, 'Eternal Brush', 'brush', []),
  durableItem(18, 'Carrot on a Stick', 'carrot_on_a_stick', []),
  durableItem(19, 'Warped Fungus on a Stick', 'warped_fungus_on_a_stick', []),
];

const swordEnchantments = [
  ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5], ['fire_aspect', 2], ['looting', 3], ['sweeping_edge', 3],
];
const spearEnchantments = [
  ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5], ['fire_aspect', 2], ['looting', 3], ['lunge', 3],
];
const bowBase = [['power', 5], ['flame', 1], ['infinity', 1], ['piercing', 4]];
const crossbowBase = [['power', 5], ['flame', 1], ['infinity', 1], ['piercing', 4]];

const weapons = [
  durableItem(20, 'God Sword', 'netherite_sword', swordEnchantments, {}, ['No Knockback']),
  durableItem(21, 'God Sword [Knockback]', 'netherite_sword', [...swordEnchantments, ['knockback', 2]]),
  durableItem(22, 'God Mace', 'mace', [
    ['density', 5], ['breach', 4], ['smite', 5], ['bane_of_arthropods', 5], ['wind_burst', 3],
    ['fire_aspect', 2], ['looting', 3],
  ], {}, ['Deliberately has no Sharpness']),
  durableItem(23, 'God Spear', 'netherite_spear', spearEnchantments, {}, ['No Knockback']),
  durableItem(24, 'God Spear [Knockback]', 'netherite_spear', [...spearEnchantments, ['knockback', 2]]),
  durableItem(25, 'Bow [Clean]', 'bow', bowBase, {}, ['No Multishot; no Punch']),
  durableItem(26, 'Bow [Multishot]', 'bow', [...bowBase, ['multishot', 1]], {}, ['No Punch']),
  durableItem(27, 'Bow [Punch]', 'bow', [...bowBase, ['punch', 2]], {}, ['No Multishot']),
  durableItem(28, 'Bow [Multishot + Punch]', 'bow', [...bowBase, ['multishot', 1], ['punch', 2]]),
  durableItem(29, 'Crossbow [Multishot]', 'crossbow', [['quick_charge', 3], ['multishot', 1], ...crossbowBase], {}, ['No Punch']),
  durableItem(30, 'Crossbow [Multishot + Punch]', 'crossbow', [['quick_charge', 3], ['multishot', 1], ...crossbowBase, ['punch', 2]]),
  durableItem(31, 'Crossbow [Single]', 'crossbow', [['quick_charge', 3], ...crossbowBase], {}, ['No Multishot; no Punch']),
  durableItem(32, 'Crossbow [Single + Punch]', 'crossbow', [['quick_charge', 3], ...crossbowBase, ['punch', 2]], {}, ['No Multishot']),
  durableItem(33, 'Crossbow [Machine Gun]', 'crossbow', [['quick_charge', 5], ['multishot', 1], ...crossbowBase, ['punch', 2]]),
  durableItem(34, 'Crossbow [Machine Gun Single]', 'crossbow', [['quick_charge', 5], ...crossbowBase, ['punch', 2]], {}, ['No Multishot']),
  durableItem(35, 'Trident [Loyalty]', 'trident', [['impaling', 5], ['loyalty', 3], ['channeling', 1]]),
  durableItem(36, 'Trident [Riptide]', 'trident', [['impaling', 5], ['riptide', 3]], {}, ['No Loyalty; no Channeling']),
  durableItem(37, 'Eternal Shield', 'shield', []),
];

const tests = [
  durableItem(38, 'TEST - Mace Sharpness', 'mace', [
    ['density', 5], ['breach', 4], ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5],
    ['wind_burst', 3], ['fire_aspect', 2], ['looting', 3],
  ]),
  durableItem(39, 'TEST - Spear No Lunge', 'netherite_spear', [
    ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5], ['fire_aspect', 2], ['looting', 3], ['knockback', 2],
  ], {}, ['No Lunge']),
  durableItem(40, 'TEST - Bow Multishot II', 'bow', [...bowBase, ['punch', 2], ['multishot', 2]]),
  durableItem(41, 'TEST - Bow Multishot III', 'bow', [...bowBase, ['punch', 2], ['multishot', 3]]),
  durableItem(42, 'TEST - Crossbow Multishot II', 'crossbow', [['quick_charge', 5], ...crossbowBase, ['punch', 2], ['multishot', 2]]),
  durableItem(43, 'TEST - Crossbow Multishot III', 'crossbow', [['quick_charge', 5], ...crossbowBase, ['punch', 2], ['multishot', 3]]),
  durableItem(44, 'TEST - Crossbow Quick Charge IV', 'crossbow', [['quick_charge', 4], ['multishot', 1], ...crossbowBase, ['punch', 2]]),
  durableItem(45, 'TEST - Mace Wind Burst IV', 'mace', [
    ['density', 5], ['breach', 4], ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5],
    ['wind_burst', 4], ['fire_aspect', 2], ['looting', 3],
  ]),
  durableItem(46, 'TEST - Mace Wind Burst V', 'mace', [
    ['density', 5], ['breach', 4], ['sharpness', 5], ['smite', 5], ['bane_of_arthropods', 5],
    ['wind_burst', 5], ['fire_aspect', 2], ['looting', 3],
  ]),
  durableItem(47, 'TEST - Glider Netherite Chestplate', 'netherite_chestplate', [
    ['protection', 5], ['fire_protection', 5], ['blast_protection', 5], ['projectile_protection', 5], ['thorns', 3],
  ], { 'minecraft:trim': trim(), 'minecraft:glider': {} }, ['Uses the chestplate base attributes; no manual attribute override']),
  durableItem(48, 'TEST - Blocking God Sword', 'netherite_sword', swordEnchantments, {
    'minecraft:blocks_attacks': shieldBlocksAttacks,
  }, ['Vanilla Shield blocks_attacks configuration']),
  durableItem(49, 'TEST - Blocking Spear', 'netherite_spear', spearEnchantments, {
    'minecraft:blocks_attacks': shieldBlocksAttacks,
  }, ['Vanilla Shield blocks_attacks configuration']),
  plainItem(50, 'AFK Potion', 'potion', 1, {
    'minecraft:potion_contents': {
      custom_effects: [{
        id: 'minecraft:regeneration',
        amplifier: byte(1),
        duration: int(-1),
        ambient: byte(1),
        show_particles: byte(0),
        show_icon: byte(0),
      }],
    },
  }, ['Regeneration II only; infinite duration; removable with milk']),
];

function blockStateItem(number, name, id, count, state, notes) {
  return plainItem(number, name, id, count, { 'minecraft:block_state': state }, notes);
}

const glitchBlocks = [
  blockStateItem(51, 'Nether Water Copper Grate', 'copper_grate', 64, { waterlogged: 'true' }, ['Waterlogged placement experiment in the Nether']),
  blockStateItem(52, 'TEST - Headless Piston UP', 'piston', 16, { extended: 'true', facing: 'up' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(53, 'TEST - Headless Piston DOWN', 'piston', 16, { extended: 'true', facing: 'down' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(54, 'TEST - Headless Piston NORTH', 'piston', 16, { extended: 'true', facing: 'north' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(55, 'TEST - Headless Piston SOUTH', 'piston', 16, { extended: 'true', facing: 'south' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(56, 'TEST - Headless Piston EAST', 'piston', 16, { extended: 'true', facing: 'east' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(57, 'TEST - Headless Piston WEST', 'piston', 16, { extended: 'true', facing: 'west' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(58, 'TEST - Headless Sticky Piston UP', 'sticky_piston', 16, { extended: 'true', facing: 'up' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(59, 'TEST - Headless Sticky Piston DOWN', 'sticky_piston', 16, { extended: 'true', facing: 'down' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(60, 'TEST - Headless Sticky Piston NORTH', 'sticky_piston', 16, { extended: 'true', facing: 'north' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(61, 'TEST - Headless Sticky Piston SOUTH', 'sticky_piston', 16, { extended: 'true', facing: 'south' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(62, 'TEST - Headless Sticky Piston EAST', 'sticky_piston', 16, { extended: 'true', facing: 'east' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(63, 'TEST - Headless Sticky Piston WEST', 'sticky_piston', 16, { extended: 'true', facing: 'west' }, ['Headless piston / bedrock-removal experiment']),
  blockStateItem(64, 'TEST - Lit Redstone Lamp', 'redstone_lamp', 16, { lit: 'true' }, ['Persistent lit state experiment']),
  blockStateItem(65, 'TEST - Powered Rail', 'powered_rail', 16, { powered: 'true' }, ['Unspecified shape and waterlogged properties use vanilla placement defaults']),
  blockStateItem(66, 'TEST - Powered Activator Rail', 'activator_rail', 16, { powered: 'true' }, ['Unspecified shape and waterlogged properties use vanilla placement defaults']),
];

const SHULKERS = Object.freeze([
  { name: 'ARMOR', id: 'minecraft:white_shulker_box', items: armor },
  { name: 'TOOLS', id: 'minecraft:gray_shulker_box', items: tools },
  { name: 'WEAPONS', id: 'minecraft:red_shulker_box', items: weapons },
  { name: 'TESTS', id: 'minecraft:purple_shulker_box', items: tests },
  { name: 'GLITCH BLOCKS', id: 'minecraft:orange_shulker_box', items: glitchBlocks },
]);

function toItemStack(definition) {
  return {
    components: definition.components,
    count: int(definition.count),
    id: definition.id,
  };
}

function toContainer(items) {
  return items.map((definition, slot) => ({ item: toItemStack(definition), slot: int(slot) }));
}

function buildMasterChest() {
  const shulkerStacks = SHULKERS.map((shulker) => ({
    components: {
      'minecraft:custom_name': customName(shulker.name),
      'minecraft:container': toContainer(shulker.items),
    },
    count: int(1),
    id: shulker.id,
  }));

  return {
    components: {
      'minecraft:custom_name': customName('Master Chest'),
      'minecraft:container': shulkerStacks.map((stack, slot) => ({ item: stack, slot: int(slot) })),
    },
    count: int(1),
    id: 'minecraft:chest',
  };
}

function allPayloadItems() {
  return SHULKERS.flatMap((shulker) => shulker.items.map((item, slot) => ({ ...item, shulker: shulker.name, slot })));
}

module.exports = {
  DAMAGE_TYPES,
  COMPONENT_IDS,
  ENCHANTMENT_IDS,
  ITEM_IDS,
  SHULKERS,
  shieldBlocksAttacks,
  helmetAttributes,
  elytraAttributes,
  buildMasterChest,
  allPayloadItems,
};
