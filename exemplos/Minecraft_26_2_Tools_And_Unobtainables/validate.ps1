[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter()]
    [string]$Root,

    [Parameter()]
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = $PSScriptRoot
}
if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $ReportPath = Join-Path $Root 'VALIDATION_REPORT.md'
}

$errors = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[string]]::new()

function Add-ValidationError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $script:errors.Add($Message)
}

function Read-JsonItemStack {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-ValidationError "Arquivo ausente: $Path"
        return $null
    }

    $text = Get-Content -LiteralPath $Path -Raw
    if ($text -match '(?i)(?<![a-z0-9_:/\"])[+-]?(?:nan|infinity)(?![a-z0-9_\"])') {
        Add-ValidationError "${Path}: contem NaN ou infinito."
    }

    try {
        return $text | ConvertFrom-Json
    }
    catch {
        Add-ValidationError "${Path}: JSON/SNBT invalido: $($_.Exception.Message)"
        return $null
    }
}

function Test-ExactContainer {
    param(
        [Parameter(Mandatory = $true)]$Stack,
        [Parameter(Mandatory = $true)][string]$ExpectedRootId,
        [Parameter(Mandatory = $true)][string[]]$ExpectedItemIds,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ($Stack.id -ne $ExpectedRootId) {
        Add-ValidationError "${Label}: ID raiz esperado $ExpectedRootId; encontrado $($Stack.id)."
    }
    if ([int]$Stack.count -ne 1) {
        Add-ValidationError "${Label}: count raiz deve ser 1."
    }
    if ($Stack.components.PSObject.Properties.Name -notcontains 'minecraft:container') {
        Add-ValidationError "${Label}: componente minecraft:container ausente."
        return @()
    }

    $container = @($Stack.components.'minecraft:container')
    if ($container.Count -ne $ExpectedItemIds.Count) {
        Add-ValidationError "${Label}: esperados $($ExpectedItemIds.Count) slots; encontrados $($container.Count)."
    }

    $slots = @($container | ForEach-Object { [int]$_.slot })
    $duplicateSlots = @($slots | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
    if ($duplicateSlots.Count -gt 0) {
        Add-ValidationError "${Label}: slots duplicados: $($duplicateSlots -join ', ')."
    }

    for ($index = 0; $index -lt $ExpectedItemIds.Count; $index++) {
        $entry = @($container | Where-Object { [int]$_.slot -eq $index })
        if ($entry.Count -ne 1) {
            Add-ValidationError "${Label}: slot $index ausente ou duplicado."
            continue
        }
        if ($entry[0].item.id -ne $ExpectedItemIds[$index]) {
            Add-ValidationError "${Label}: slot $index deveria conter $($ExpectedItemIds[$index]); encontrado $($entry[0].item.id)."
        }
        if ([int]$entry[0].item.count -ne 1) {
            Add-ValidationError "${Label}: slot $index deve ter count 1."
        }
    }

    return $container
}

function Test-EnchantmentPair {
    param(
        [Parameter(Mandatory = $true)]$Container,
        [Parameter(Mandatory = $true)][int]$Slot,
        [Parameter(Mandatory = $true)][string[]]$Enchantments,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $item = @($Container | Where-Object { [int]$_.slot -eq $Slot })[0].item
    $actual = @($item.components.'minecraft:enchantments'.PSObject.Properties.Name)
    foreach ($enchantment in $Enchantments) {
        if ($actual -notcontains $enchantment) {
            Add-ValidationError "${Label}: slot $Slot sem $enchantment."
        }
    }
}

$registeredItems = @(
    'minecraft:red_shulker_box', 'minecraft:black_shulker_box',
    'minecraft:netherite_sword', 'minecraft:netherite_pickaxe', 'minecraft:netherite_axe',
    'minecraft:netherite_shovel', 'minecraft:netherite_hoe', 'minecraft:netherite_spear',
    'minecraft:mace', 'minecraft:bow', 'minecraft:crossbow', 'minecraft:trident',
    'minecraft:fishing_rod', 'minecraft:shears', 'minecraft:brush', 'minecraft:flint_and_steel',
    'minecraft:shield', 'minecraft:bedrock', 'minecraft:end_portal_frame',
    'minecraft:reinforced_deepslate', 'minecraft:barrier', 'minecraft:light',
    'minecraft:structure_void', 'minecraft:structure_block', 'minecraft:jigsaw',
    'minecraft:command_block', 'minecraft:repeating_command_block', 'minecraft:chain_command_block',
    'minecraft:command_block_minecart', 'minecraft:debug_stick', 'minecraft:knowledge_book',
    'minecraft:spawner', 'minecraft:trial_spawner', 'minecraft:vault', 'minecraft:test_block',
    'minecraft:test_instance_block', 'minecraft:petrified_oak_slab', 'minecraft:farmland',
    'minecraft:dirt_path', 'minecraft:budding_amethyst', 'minecraft:suspicious_sand',
    'minecraft:suspicious_gravel', 'minecraft:ender_dragon_spawn_egg', 'minecraft:wither_spawn_egg'
)

$registeredEnchantments = @(
    'minecraft:bane_of_arthropods', 'minecraft:breach', 'minecraft:channeling',
    'minecraft:density', 'minecraft:efficiency', 'minecraft:fire_aspect', 'minecraft:flame',
    'minecraft:fortune', 'minecraft:impaling', 'minecraft:infinity', 'minecraft:knockback',
    'minecraft:looting', 'minecraft:loyalty', 'minecraft:luck_of_the_sea', 'minecraft:lunge',
    'minecraft:lure', 'minecraft:mending', 'minecraft:multishot', 'minecraft:piercing',
    'minecraft:power', 'minecraft:punch', 'minecraft:quick_charge', 'minecraft:riptide',
    'minecraft:sharpness', 'minecraft:silk_touch', 'minecraft:smite', 'minecraft:sweeping_edge',
    'minecraft:unbreaking', 'minecraft:wind_burst'
)

$powerIds = @(
    'minecraft:netherite_sword', 'minecraft:netherite_pickaxe', 'minecraft:netherite_axe',
    'minecraft:netherite_shovel', 'minecraft:netherite_hoe', 'minecraft:netherite_spear',
    'minecraft:mace', 'minecraft:bow', 'minecraft:crossbow', 'minecraft:trident',
    'minecraft:fishing_rod', 'minecraft:shears', 'minecraft:brush', 'minecraft:flint_and_steel',
    'minecraft:shield'
)

$unobtainableIds = @(
    'minecraft:bedrock', 'minecraft:end_portal_frame', 'minecraft:reinforced_deepslate',
    'minecraft:barrier', 'minecraft:light', 'minecraft:structure_void',
    'minecraft:structure_block', 'minecraft:jigsaw', 'minecraft:command_block',
    'minecraft:repeating_command_block', 'minecraft:chain_command_block',
    'minecraft:command_block_minecart', 'minecraft:debug_stick', 'minecraft:knowledge_book',
    'minecraft:spawner', 'minecraft:trial_spawner', 'minecraft:vault', 'minecraft:test_block',
    'minecraft:test_instance_block', 'minecraft:petrified_oak_slab', 'minecraft:farmland',
    'minecraft:dirt_path', 'minecraft:budding_amethyst', 'minecraft:suspicious_sand',
    'minecraft:suspicious_gravel', 'minecraft:ender_dragon_spawn_egg', 'minecraft:wither_spawn_egg'
)

$powerPath = Join-Path $Root 'shulkers\01_power_tools.snbt'
$unobtainablePath = Join-Path $Root 'shulkers\02_unobtainable_items.snbt'
$powerStack = Read-JsonItemStack -Path $powerPath
$unobtainableStack = Read-JsonItemStack -Path $unobtainablePath

$powerContainer = @()
if ($null -ne $powerStack) {
    $powerContainer = @(Test-ExactContainer -Stack $powerStack -ExpectedRootId 'minecraft:red_shulker_box' -ExpectedItemIds $powerIds -Label 'Power tools')
    foreach ($entry in $powerContainer) {
        $item = $entry.item
        if ($registeredItems -notcontains $item.id) {
            Add-ValidationError "Power tools: ID nao registrado na lista auditada: $($item.id)."
        }
        if ($item.components.PSObject.Properties.Name -notcontains 'minecraft:unbreakable') {
            Add-ValidationError "Power tools: slot $($entry.slot) sem minecraft:unbreakable."
        }
        if ($item.components.PSObject.Properties.Name -notcontains 'minecraft:enchantments') {
            Add-ValidationError "Power tools: slot $($entry.slot) sem minecraft:enchantments."
            continue
        }
        foreach ($property in $item.components.'minecraft:enchantments'.PSObject.Properties) {
            if ($registeredEnchantments -notcontains $property.Name) {
                Add-ValidationError "Power tools: enchantment nao registrado: $($property.Name)."
            }
            $level = [int]$property.Value
            if ($level -lt 1 -or $level -gt 255) {
                Add-ValidationError "Power tools: nivel fora do intervalo 1..255 em $($property.Name): $level."
            }
        }
    }

    Test-EnchantmentPair -Container $powerContainer -Slot 0 -Enchantments @('minecraft:sharpness', 'minecraft:smite', 'minecraft:bane_of_arthropods') -Label 'Sword conflict set'
    Test-EnchantmentPair -Container $powerContainer -Slot 1 -Enchantments @('minecraft:fortune', 'minecraft:silk_touch') -Label 'Pickaxe conflict set'
    Test-EnchantmentPair -Container $powerContainer -Slot 6 -Enchantments @('minecraft:density', 'minecraft:breach') -Label 'Mace conflict set'
    Test-EnchantmentPair -Container $powerContainer -Slot 7 -Enchantments @('minecraft:infinity', 'minecraft:mending') -Label 'Bow conflict set'
    Test-EnchantmentPair -Container $powerContainer -Slot 8 -Enchantments @('minecraft:multishot', 'minecraft:piercing') -Label 'Crossbow conflict set'
    Test-EnchantmentPair -Container $powerContainer -Slot 9 -Enchantments @('minecraft:loyalty', 'minecraft:riptide') -Label 'Trident conflict set'
    $checks.Add('Power tools: 15 slots, IDs, niveis e componentes unbreakable verificados.')
    $checks.Add('Seis combinacoes normalmente incompatíveis verificadas.')
}

if ($null -ne $unobtainableStack) {
    $unobtainableContainer = @(Test-ExactContainer -Stack $unobtainableStack -ExpectedRootId 'minecraft:black_shulker_box' -ExpectedItemIds $unobtainableIds -Label 'Unobtainable items')
    foreach ($entry in $unobtainableContainer) {
        if ($registeredItems -notcontains $entry.item.id) {
            Add-ValidationError "Unobtainable items: ID nao registrado na lista auditada: $($entry.item.id)."
        }
    }
    $forbiddenItemIds = @('minecraft:end_portal', 'minecraft:end_gateway', 'minecraft:nether_portal')
    $actualIds = @($unobtainableContainer | ForEach-Object { $_.item.id })
    foreach ($forbiddenId in $forbiddenItemIds) {
        if ($actualIds -contains $forbiddenId) {
            Add-ValidationError "Unobtainable items: bloco sem forma de item inserido indevidamente: $forbiddenId."
        }
    }
    $checks.Add('Unobtainable items: 27 slots e 27 IDs registrados verificados.')
    $checks.Add('End Portal, End Gateway e Nether Portal confirmados ausentes como ItemStacks.')
}

$status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
$reportLines = [System.Collections.Generic.List[string]]::new()
$reportLines.Add('# Validation Report')
$reportLines.Add('')
$reportLines.Add("- Status: **$status**")
$reportLines.Add("- Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')")
$reportLines.Add('- Alvo: Minecraft Java 26.2')
$reportLines.Add('- Escopo: validacao estrutural e de conteudo offline; Minecraft nao foi iniciado')
$reportLines.Add('')
$reportLines.Add('## Checks')
$reportLines.Add('')
foreach ($check in $checks) { $reportLines.Add("- $check") }
$reportLines.Add('')
$reportLines.Add('## Errors')
$reportLines.Add('')
if ($errors.Count -eq 0) {
    $reportLines.Add('- Nenhum erro encontrado.')
}
else {
    foreach ($message in $errors) { $reportLines.Add("- $message") }
}
$reportLines.Add('')
$reportLines.Add('## Warning')
$reportLines.Add('')
$reportLines.Add('- O validador nao substitui um teste manual no editor ou o codec do jogo.')

$report = $reportLines -join [Environment]::NewLine
if ($PSCmdlet.ShouldProcess($ReportPath, 'Gravar relatorio de validacao')) {
    Set-Content -LiteralPath $ReportPath -Value $report -Encoding utf8
}
Write-Output $report
if ($errors.Count -gt 0) { exit 1 }

