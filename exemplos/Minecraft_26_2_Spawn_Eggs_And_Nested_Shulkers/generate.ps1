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

function Get-TextColorForDye {
    param([Parameter(Mandatory = $true)][string]$Color)

    switch ($Color) {
        'white' { 'white' }
        'orange' { 'gold' }
        'magenta' { 'light_purple' }
        'light_blue' { 'aqua' }
        'yellow' { 'yellow' }
        'lime' { 'green' }
        'pink' { 'light_purple' }
        'gray' { 'gray' }
        'light_gray' { 'gray' }
        'cyan' { 'dark_aqua' }
        'purple' { 'dark_purple' }
        'blue' { 'blue' }
        'brown' { 'gold' }
        'green' { 'dark_green' }
        'red' { 'red' }
        'black' { 'black' }
        default { throw "Cor de shulker sem equivalente de texto: $Color" }
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

function New-ShulkerId {
    param([Parameter(Mandatory = $true)][string]$Color)
    return "minecraft:${Color}_shulker_box"
}

$eggListPath = Join-Path $Root 'data\spawn_egg_ids_26.2.txt'
if (-not (Test-Path -LiteralPath $eggListPath -PathType Leaf)) {
    throw "Lista de Spawn Eggs ausente: $eggListPath"
}

[string[]]$spawnEggIds = @(
    Get-Content -LiteralPath $eggListPath |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)

if ($spawnEggIds.Length -ne 88) {
    throw "Esperados 88 Spawn Eggs da Java 26.2; encontrados $($spawnEggIds.Length)."
}
if (@($spawnEggIds | Where-Object { $_ -notmatch '^[a-z0-9_]+_spawn_egg$' }).Count -gt 0) {
    throw 'A lista contem um ID que nao termina em _spawn_egg ou possui caracteres invalidos.'
}
if (@($spawnEggIds | Group-Object | Where-Object Count -gt 1).Count -gt 0) {
    throw 'A lista de Spawn Eggs contem IDs duplicados.'
}

$eggShulkerColors = @('red', 'orange', 'yellow', 'lime')
$chestContainer = [System.Collections.Generic.List[object]]::new()
$eggCursor = 0

for ($batch = 0; $batch -lt $eggShulkerColors.Count; $batch++) {
    $eggContainer = [System.Collections.Generic.List[object]]::new()
    $batchStart = $eggCursor
    for ($slot = 0; $slot -lt 27 -and $eggCursor -lt $spawnEggIds.Length; $slot++) {
        $eggItem = [ordered]@{
            count = 64
            id = "minecraft:$($spawnEggIds[$eggCursor])"
        }
        Add-ContainerEntry -Container $eggContainer -Slot $slot -Item $eggItem
        $eggCursor++
    }

    $batchCount = $eggCursor - $batchStart
    $shulkerColor = $eggShulkerColors[$batch]
    $eggShulker = [ordered]@{
        components = [ordered]@{
            'minecraft:container' = $eggContainer.ToArray()
            'minecraft:item_name' = New-TextComponent -Text "Spawn Eggs $($batch + 1)/4" -Color (Get-TextColorForDye -Color $shulkerColor)
            'minecraft:lore' = @(
                New-TextComponent -Text "$batchCount egg stacks; each count 64" -Color 'gray'
            )
        }
        count = 1
        id = New-ShulkerId -Color $shulkerColor
    }
    Add-ContainerEntry -Container $chestContainer -Slot $batch -Item $eggShulker
}

if ($eggCursor -ne $spawnEggIds.Length) {
    throw "Nem todos os Spawn Eggs foram empacotados: $eggCursor de $($spawnEggIds.Length)."
}

$spawnEggChest = [ordered]@{
    components = [ordered]@{
        'minecraft:container' = $chestContainer.ToArray()
        'minecraft:item_name' = New-TextComponent -Text 'All Spawn Eggs - Java 26.2' -Color 'aqua'
        'minecraft:lore' = @(
            New-TextComponent -Text '88 registered Spawn Eggs' -Color 'yellow'
            New-TextComponent -Text 'Every egg stack has count 64' -Color 'gold'
        )
    }
    count = 1
    id = 'minecraft:chest'
}

$rainbowColors = @(
    'white', 'orange', 'magenta', 'light_blue', 'yellow', 'lime', 'pink', 'gray',
    'light_gray', 'cyan', 'purple', 'blue', 'brown', 'green', 'red', 'black'
)

$rootNestedContainer = [System.Collections.Generic.List[object]]::new()
$leafStackCount = 0

for ($outerSlot = 0; $outerSlot -lt 27; $outerSlot++) {
    $leafContainer = [System.Collections.Generic.List[object]]::new()
    for ($leafSlot = 0; $leafSlot -lt 27; $leafSlot++) {
        $colorIndex = (($outerSlot * 27) + $leafSlot) % $rainbowColors.Count
        $leafItem = [ordered]@{
            components = [ordered]@{
                'minecraft:max_stack_size' = 64
            }
            count = 64
            id = New-ShulkerId -Color $rainbowColors[$colorIndex]
        }
        Add-ContainerEntry -Container $leafContainer -Slot $leafSlot -Item $leafItem
        $leafStackCount++
    }

    $middleColor = $rainbowColors[$outerSlot % $rainbowColors.Count]
    $middleShulker = [ordered]@{
        components = [ordered]@{
            'minecraft:max_stack_size' = 64
            'minecraft:container' = $leafContainer.ToArray()
            'minecraft:item_name' = New-TextComponent -Text "Nested Rainbow $($outerSlot + 1)/27" -Color (Get-TextColorForDye -Color $middleColor)
            'minecraft:lore' = @(
                New-TextComponent -Text 'Contains 27 shulker stacks at count 64' -Color 'gray'
                New-TextComponent -Text 'Leaf layer; nesting stops inside those stacks' -Color 'dark_gray'
            )
        }
        count = 64
        id = New-ShulkerId -Color $middleColor
    }
    Add-ContainerEntry -Container $rootNestedContainer -Slot $outerSlot -Item $middleShulker
}

$nestedRainbowShulkers = [ordered]@{
    components = [ordered]@{
        'minecraft:max_stack_size' = 64
        'minecraft:container' = $rootNestedContainer.ToArray()
        'minecraft:item_name' = New-TextComponent -Text '64x Rainbow Nested Shulkers' -Color 'light_purple'
        'minecraft:lore' = @(
            New-TextComponent -Text 'Root count 64; every internal stack count 64' -Color 'gold'
            New-TextComponent -Text 'Bounded to 3 physical layers and 757 shulker ItemStacks' -Color 'yellow'
        )
    }
    count = 64
    id = 'minecraft:purple_shulker_box'
}

if ($leafStackCount -ne 729) {
    throw "Esperadas 729 pilhas-folha; encontradas $leafStackCount."
}

$outputDirectory = Join-Path $Root 'items'
$outputs = [ordered]@{
    (Join-Path $outputDirectory '01_all_spawn_eggs_chest.snbt') = ($spawnEggChest | ConvertTo-Json -Depth 100)
    (Join-Path $outputDirectory '02_nested_rainbow_shulkers_64x.snbt') = ($nestedRainbowShulkers | ConvertTo-Json -Depth 100)
}

if ($PSCmdlet.ShouldProcess($outputDirectory, 'Criar pasta de saida')) {
    $null = New-Item -ItemType Directory -Path $outputDirectory -Force
}
foreach ($entry in $outputs.GetEnumerator()) {
    if ($PSCmdlet.ShouldProcess($entry.Key, 'Gravar ItemStack SNBT/JSON')) {
        Set-Content -LiteralPath $entry.Key -Value $entry.Value -Encoding utf8
    }
}

Write-Output "Spawn Eggs: $($spawnEggIds.Length)"
Write-Output "Egg shulkers in Chest: $($eggShulkerColors.Count)"
Write-Output 'Nested shulker ItemStacks: 757 (1 root + 27 middle + 729 leaves)'
Write-Output "Output: $outputDirectory"
