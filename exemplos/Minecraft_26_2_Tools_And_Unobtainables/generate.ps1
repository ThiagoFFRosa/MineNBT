[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter()]
    [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = $PSScriptRoot
}

function New-TextComponent {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Color
    )

    return [ordered]@{
        text = $Text
        color = $Color
        italic = $false
    }
}

function New-PowerItem {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Lore,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Enchantments
    )

    $components = [ordered]@{
        'minecraft:enchantments' = $Enchantments
        'minecraft:unbreakable' = [ordered]@{}
        'minecraft:item_name' = New-TextComponent -Text $Name -Color 'gold'
        'minecraft:lore' = @(
            New-TextComponent -Text $Lore -Color 'yellow'
            New-TextComponent -Text 'Finite levels; unbreakable ItemStack' -Color 'dark_gray'
        )
    }

    return [ordered]@{
        components = $components
        count = 1
        id = $Id
    }
}

function New-UnobtainableItem {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Reason
    )

    return [ordered]@{
        components = [ordered]@{
            'minecraft:item_name' = New-TextComponent -Text $Name -Color 'light_purple'
            'minecraft:lore' = @(
                New-TextComponent -Text $Reason -Color 'gray'
                New-TextComponent -Text 'Registered item in Java 26.2' -Color 'dark_gray'
            )
        }
        count = 1
        id = $Id
    }
}

function Add-ContainerEntry {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Container,
        [Parameter(Mandatory = $true)][int]$Slot,
        [Parameter(Mandatory = $true)]$Item
    )

    $Container.Add([ordered]@{ item = $Item; slot = $Slot })
}

$powerDefinitions = @(
    [ordered]@{ Id = 'minecraft:netherite_sword'; Name = 'Omega Netherite Sword'; Lore = 'All melee damage families together'; Enchantments = [ordered]@{ 'minecraft:sharpness' = 10; 'minecraft:smite' = 10; 'minecraft:bane_of_arthropods' = 10; 'minecraft:fire_aspect' = 5; 'minecraft:knockback' = 5; 'minecraft:looting' = 10; 'minecraft:sweeping_edge' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:netherite_pickaxe'; Name = 'Omega Netherite Pickaxe'; Lore = 'Fortune and Silk Touch together'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:silk_touch' = 1; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:netherite_axe'; Name = 'Omega Netherite Axe'; Lore = 'Tool and melee enchantments combined'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:silk_touch' = 1; 'minecraft:sharpness' = 10; 'minecraft:smite' = 10; 'minecraft:bane_of_arthropods' = 10; 'minecraft:fire_aspect' = 5; 'minecraft:looting' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:netherite_shovel'; Name = 'Omega Netherite Shovel'; Lore = 'Fortune and Silk Touch together'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:silk_touch' = 1; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:netherite_hoe'; Name = 'Omega Netherite Hoe'; Lore = 'Fortune and Silk Touch together'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:silk_touch' = 1; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:netherite_spear'; Name = 'Omega Netherite Spear'; Lore = 'Lunge and all melee damage families'; Enchantments = [ordered]@{ 'minecraft:lunge' = 10; 'minecraft:sharpness' = 10; 'minecraft:smite' = 10; 'minecraft:bane_of_arthropods' = 10; 'minecraft:fire_aspect' = 5; 'minecraft:knockback' = 5; 'minecraft:looting' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:mace'; Name = 'Omega Mace'; Lore = 'Density and Breach together'; Enchantments = [ordered]@{ 'minecraft:density' = 10; 'minecraft:breach' = 10; 'minecraft:wind_burst' = 10; 'minecraft:sharpness' = 10; 'minecraft:smite' = 10; 'minecraft:bane_of_arthropods' = 10; 'minecraft:fire_aspect' = 5; 'minecraft:knockback' = 5; 'minecraft:looting' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:bow'; Name = 'Omega Bow'; Lore = 'Infinity and Mending together'; Enchantments = [ordered]@{ 'minecraft:power' = 10; 'minecraft:punch' = 5; 'minecraft:flame' = 1; 'minecraft:infinity' = 1; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:crossbow'; Name = 'Omega Crossbow'; Lore = 'Multishot and Piercing together'; Enchantments = [ordered]@{ 'minecraft:quick_charge' = 5; 'minecraft:multishot' = 3; 'minecraft:piercing' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:trident'; Name = 'Omega Trident'; Lore = 'Loyalty and Riptide together'; Enchantments = [ordered]@{ 'minecraft:impaling' = 10; 'minecraft:loyalty' = 10; 'minecraft:riptide' = 10; 'minecraft:channeling' = 1; 'minecraft:sharpness' = 10; 'minecraft:fire_aspect' = 5; 'minecraft:knockback' = 5; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:fishing_rod'; Name = 'Omega Fishing Rod'; Lore = 'Maximum strong fishing enchantments'; Enchantments = [ordered]@{ 'minecraft:luck_of_the_sea' = 10; 'minecraft:lure' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:shears'; Name = 'Omega Shears'; Lore = 'Fortune and Silk Touch utility'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:silk_touch' = 1; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:brush'; Name = 'Omega Brush'; Lore = 'Strong utility enchantments'; Enchantments = [ordered]@{ 'minecraft:efficiency' = 10; 'minecraft:fortune' = 10; 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:flint_and_steel'; Name = 'Eternal Flint and Steel'; Lore = 'Indestructible utility item'; Enchantments = [ordered]@{ 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } },
    [ordered]@{ Id = 'minecraft:shield'; Name = 'Eternal Shield'; Lore = 'Indestructible defensive item'; Enchantments = [ordered]@{ 'minecraft:mending' = 1; 'minecraft:unbreaking' = 10 } }
)

$unobtainableDefinitions = @(
    [ordered]@{ Id = 'minecraft:bedrock'; Name = 'Bedrock'; Reason = 'Creative/technical block; not collectible in Survival' },
    [ordered]@{ Id = 'minecraft:end_portal_frame'; Name = 'End Portal Frame'; Reason = 'Stronghold structure block; not collectible' },
    [ordered]@{ Id = 'minecraft:reinforced_deepslate'; Name = 'Reinforced Deepslate'; Reason = 'Ancient City block; not collectible' },
    [ordered]@{ Id = 'minecraft:barrier'; Name = 'Barrier'; Reason = 'Operator-only invisible block' },
    [ordered]@{ Id = 'minecraft:light'; Name = 'Light Block'; Reason = 'Operator-only invisible light source' },
    [ordered]@{ Id = 'minecraft:structure_void'; Name = 'Structure Void'; Reason = 'Operator-only structure helper' },
    [ordered]@{ Id = 'minecraft:structure_block'; Name = 'Structure Block'; Reason = 'Operator-only structure tool' },
    [ordered]@{ Id = 'minecraft:jigsaw'; Name = 'Jigsaw Block'; Reason = 'Operator-only worldgen tool' },
    [ordered]@{ Id = 'minecraft:command_block'; Name = 'Command Block'; Reason = 'Operator-only command block' },
    [ordered]@{ Id = 'minecraft:repeating_command_block'; Name = 'Repeating Command Block'; Reason = 'Operator-only command block' },
    [ordered]@{ Id = 'minecraft:chain_command_block'; Name = 'Chain Command Block'; Reason = 'Operator-only command block' },
    [ordered]@{ Id = 'minecraft:command_block_minecart'; Name = 'Command Block Minecart'; Reason = 'Operator-only vehicle item' },
    [ordered]@{ Id = 'minecraft:debug_stick'; Name = 'Debug Stick'; Reason = 'Operator-only block state tool' },
    [ordered]@{ Id = 'minecraft:knowledge_book'; Name = 'Knowledge Book'; Reason = 'Technical command item' },
    [ordered]@{ Id = 'minecraft:spawner'; Name = 'Monster Spawner'; Reason = 'Does not drop as an item in Survival' },
    [ordered]@{ Id = 'minecraft:trial_spawner'; Name = 'Trial Spawner'; Reason = 'Does not drop as an item in Survival' },
    [ordered]@{ Id = 'minecraft:vault'; Name = 'Vault'; Reason = 'Does not drop as an item in Survival' },
    [ordered]@{ Id = 'minecraft:test_block'; Name = 'Test Block'; Reason = 'Game-test/operator block' },
    [ordered]@{ Id = 'minecraft:test_instance_block'; Name = 'Test Instance Block'; Reason = 'Game-test/operator block' },
    [ordered]@{ Id = 'minecraft:petrified_oak_slab'; Name = 'Petrified Oak Slab'; Reason = 'Legacy stone-behavior slab; no Survival source' },
    [ordered]@{ Id = 'minecraft:farmland'; Name = 'Farmland Item'; Reason = 'Registered ItemStack but not normally collectible' },
    [ordered]@{ Id = 'minecraft:dirt_path'; Name = 'Dirt Path Item'; Reason = 'Registered ItemStack but not normally collectible' },
    [ordered]@{ Id = 'minecraft:budding_amethyst'; Name = 'Budding Amethyst'; Reason = 'Never drops, including with Silk Touch' },
    [ordered]@{ Id = 'minecraft:suspicious_sand'; Name = 'Suspicious Sand Item'; Reason = 'World block that does not drop as itself' },
    [ordered]@{ Id = 'minecraft:suspicious_gravel'; Name = 'Suspicious Gravel Item'; Reason = 'World block that does not drop as itself' },
    [ordered]@{ Id = 'minecraft:ender_dragon_spawn_egg'; Name = 'Ender Dragon Spawn Egg'; Reason = 'Creative/command-only spawn egg' },
    [ordered]@{ Id = 'minecraft:wither_spawn_egg'; Name = 'Wither Spawn Egg'; Reason = 'Creative/command-only spawn egg' }
)

$powerContainer = [System.Collections.Generic.List[object]]::new()
for ($slot = 0; $slot -lt $powerDefinitions.Count; $slot++) {
    $definition = $powerDefinitions[$slot]
    $item = New-PowerItem -Id $definition.Id -Name $definition.Name -Lore $definition.Lore -Enchantments $definition.Enchantments
    Add-ContainerEntry -Container $powerContainer -Slot $slot -Item $item
}

$powerShulker = [ordered]@{
    components = [ordered]@{
        'minecraft:container' = $powerContainer.ToArray()
        'minecraft:item_name' = New-TextComponent -Text 'Omega Tools - Java 26.2' -Color 'red'
        'minecraft:lore' = @(
            New-TextComponent -Text '15 strong and unbreakable tools' -Color 'gold'
            New-TextComponent -Text 'Includes normally incompatible enchantments' -Color 'yellow'
        )
    }
    count = 1
    id = 'minecraft:red_shulker_box'
}

$unobtainableContainer = [System.Collections.Generic.List[object]]::new()
for ($slot = 0; $slot -lt $unobtainableDefinitions.Count; $slot++) {
    $definition = $unobtainableDefinitions[$slot]
    $item = New-UnobtainableItem -Id $definition.Id -Name $definition.Name -Reason $definition.Reason
    Add-ContainerEntry -Container $unobtainableContainer -Slot $slot -Item $item
}

$unobtainableShulker = [ordered]@{
    components = [ordered]@{
        'minecraft:container' = $unobtainableContainer.ToArray()
        'minecraft:item_name' = New-TextComponent -Text 'Unobtainable Items - Java 26.2' -Color 'light_purple'
        'minecraft:lore' = @(
            New-TextComponent -Text '27 registered items unavailable in Survival' -Color 'gray'
            New-TextComponent -Text 'Portal-only blocks are documented separately' -Color 'dark_gray'
        )
    }
    count = 1
    id = 'minecraft:black_shulker_box'
}

$outputDirectory = Join-Path $Root 'shulkers'
$outputs = [ordered]@{
    (Join-Path $outputDirectory '01_power_tools.snbt') = ($powerShulker | ConvertTo-Json -Depth 100)
    (Join-Path $outputDirectory '02_unobtainable_items.snbt') = ($unobtainableShulker | ConvertTo-Json -Depth 100)
}

if ($PSCmdlet.ShouldProcess($outputDirectory, 'Criar pasta de saida')) {
    $null = New-Item -ItemType Directory -Path $outputDirectory -Force
}

foreach ($entry in $outputs.GetEnumerator()) {
    if ($PSCmdlet.ShouldProcess($entry.Key, 'Gravar ItemStack SNBT/JSON')) {
        Set-Content -LiteralPath $entry.Key -Value $entry.Value -Encoding utf8
    }
}

Write-Output "Power tools: $($powerDefinitions.Count)"
Write-Output "Unobtainable items: $($unobtainableDefinitions.Count)"
Write-Output "Output: $outputDirectory"
