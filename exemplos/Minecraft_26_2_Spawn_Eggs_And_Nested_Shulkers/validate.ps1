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

$validTextColors = @(
    'black', 'dark_blue', 'dark_green', 'dark_aqua', 'dark_red', 'dark_purple',
    'gold', 'gray', 'dark_gray', 'blue', 'green', 'aqua', 'red',
    'light_purple', 'yellow', 'white'
)

function Test-TextColors {
    param(
        [Parameter(Mandatory = $true)][AllowNull()]$Value,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter()][string]$Path = '$'
    )

    if ($null -eq $Value) { return }

    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $propertyNames = @($Value.PSObject.Properties.Name)
        if ($propertyNames -contains 'text' -and $propertyNames -contains 'color') {
            $color = [string]$Value.color
            $isNamedColor = $script:validTextColors -contains $color
            $isHexColor = $color -match '^#[0-9A-Fa-f]{6}$'
            if (-not $isNamedColor -and -not $isHexColor) {
                Add-ValidationError "${Label}: cor de texto invalida '$color' em $Path."
            }
        }
        foreach ($property in $Value.PSObject.Properties) {
            Test-TextColors -Value $property.Value -Label $Label -Path "$Path.$($property.Name)"
        }
        return
    }

    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $index = 0
        foreach ($item in $Value) {
            Test-TextColors -Value $item -Label $Label -Path "$Path[$index]"
            $index++
        }
    }
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

function Get-Container {
    param(
        [Parameter(Mandatory = $true)]$Item,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ($Item.components.PSObject.Properties.Name -notcontains 'minecraft:container') {
        Add-ValidationError "${Label}: minecraft:container ausente."
        return @()
    }
    return @($Item.components.'minecraft:container')
}

function Test-ContiguousSlots {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Container,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $slots = @($Container | ForEach-Object { [int]$_.slot })
    $duplicates = @($slots | Group-Object | Where-Object Count -gt 1)
    if ($duplicates.Count -gt 0) {
        Add-ValidationError "${Label}: slots duplicados."
    }
    for ($slot = 0; $slot -lt $Container.Count; $slot++) {
        if ($slots -notcontains $slot) {
            Add-ValidationError "${Label}: slot $slot ausente."
        }
    }
}

function Test-MaxStackSize64 {
    param([Parameter(Mandatory = $true)]$Item)

    if ($Item.PSObject.Properties.Name -notcontains 'components') {
        return $false
    }
    if ($Item.components.PSObject.Properties.Name -notcontains 'minecraft:max_stack_size') {
        return $false
    }
    return [int]$Item.components.'minecraft:max_stack_size' -eq 64
}

$eggListPath = Join-Path $Root 'data\spawn_egg_ids_26.2.txt'
if (-not (Test-Path -LiteralPath $eggListPath -PathType Leaf)) {
    Add-ValidationError "Lista de IDs ausente: $eggListPath"
    [string[]]$expectedEggIds = @()
}
else {
    [string[]]$expectedEggIds = @(
        Get-Content -LiteralPath $eggListPath |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            ForEach-Object { "minecraft:$_" }
    )
}

if ($expectedEggIds.Length -ne 88) {
    Add-ValidationError "Lista de IDs: esperados 88 Spawn Eggs; encontrados $($expectedEggIds.Length)."
}
$duplicateExpectedEggs = @($expectedEggIds | Group-Object | Where-Object Count -gt 1)
if ($duplicateExpectedEggs.Count -gt 0) {
    Add-ValidationError 'Lista de IDs: existem Spawn Eggs duplicados.'
}
if (@($expectedEggIds | Where-Object { $_ -notmatch '^minecraft:[a-z0-9_]+_spawn_egg$' }).Count -gt 0) {
    Add-ValidationError 'Lista de IDs: existe ID fora do formato de Spawn Egg.'
}

$eggChestPath = Join-Path $Root 'items\01_all_spawn_eggs_chest.snbt'
$nestedPath = Join-Path $Root 'items\02_nested_rainbow_shulkers_64x.snbt'
$eggChest = Read-JsonItemStack -Path $eggChestPath
$nestedRoot = Read-JsonItemStack -Path $nestedPath

if ($null -ne $eggChest) {
    Test-TextColors -Value $eggChest -Label 'Spawn Egg Chest'
    if ($eggChest.id -ne 'minecraft:chest' -or [int]$eggChest.count -ne 1) {
        Add-ValidationError 'Spawn Egg Chest: raiz deve ser minecraft:chest com count 1.'
    }
    $chestContainer = @(Get-Container -Item $eggChest -Label 'Spawn Egg Chest')
    if ($chestContainer.Count -ne 4) {
        Add-ValidationError "Spawn Egg Chest: esperadas 4 shulkers; encontradas $($chestContainer.Count)."
    }
    Test-ContiguousSlots -Container $chestContainer -Label 'Spawn Egg Chest'

    $expectedBatchSizes = @(27, 27, 27, 7)
    $expectedShulkerIds = @(
        'minecraft:red_shulker_box', 'minecraft:orange_shulker_box',
        'minecraft:yellow_shulker_box', 'minecraft:lime_shulker_box'
    )
    $actualEggIds = [System.Collections.Generic.List[string]]::new()

    for ($batch = 0; $batch -lt $chestContainer.Count; $batch++) {
        $entry = @($chestContainer | Where-Object { [int]$_.slot -eq $batch })
        if ($entry.Count -ne 1) {
            Add-ValidationError "Spawn Egg Chest: shulker do slot $batch ausente ou duplicada."
            continue
        }
        $shulker = $entry[0].item
        if ($shulker.id -ne $expectedShulkerIds[$batch] -or [int]$shulker.count -ne 1) {
            Add-ValidationError "Spawn Egg Chest: shulker $batch possui ID ou count incorreto."
        }
        $eggContainer = @(Get-Container -Item $shulker -Label "Egg shulker $batch")
        if ($eggContainer.Count -ne $expectedBatchSizes[$batch]) {
            Add-ValidationError "Egg shulker ${batch}: esperados $($expectedBatchSizes[$batch]) ovos; encontrados $($eggContainer.Count)."
        }
        Test-ContiguousSlots -Container $eggContainer -Label "Egg shulker $batch"
        foreach ($eggEntry in $eggContainer) {
            $egg = $eggEntry.item
            $actualEggIds.Add([string]$egg.id)
            if ([int]$egg.count -ne 64) {
                Add-ValidationError "Egg shulker ${batch}: $($egg.id) nao possui count 64."
            }
            if ($egg.id -notmatch '^minecraft:[a-z0-9_]+_spawn_egg$') {
                Add-ValidationError "Egg shulker ${batch}: ID nao e Spawn Egg: $($egg.id)."
            }
            if ($egg.PSObject.Properties.Name -contains 'components') {
                if ($egg.components.PSObject.Properties.Name -contains 'minecraft:container') {
                    Add-ValidationError "Egg shulker ${batch}: Spawn Egg contem container inesperado."
                }
            }
        }
    }

    if ($actualEggIds.Count -ne 88) {
        Add-ValidationError "Spawn Egg Chest: esperados 88 ovos; encontrados $($actualEggIds.Count)."
    }
    $duplicateActualEggs = @($actualEggIds | Group-Object | Where-Object Count -gt 1)
    if ($duplicateActualEggs.Count -gt 0) {
        Add-ValidationError 'Spawn Egg Chest: existem IDs duplicados.'
    }
    $missingEggs = @($expectedEggIds | Where-Object { $actualEggIds -notcontains $_ })
    $unexpectedEggs = @($actualEggIds | Where-Object { $expectedEggIds -notcontains $_ })
    if ($missingEggs.Count -gt 0) {
        Add-ValidationError "Spawn Egg Chest: IDs ausentes: $($missingEggs -join ', ')."
    }
    if ($unexpectedEggs.Count -gt 0) {
        Add-ValidationError "Spawn Egg Chest: IDs inesperados: $($unexpectedEggs -join ', ')."
    }
    $checks.Add('Spawn Egg Chest: 4 shulkers e lotes 27 + 27 + 27 + 7 verificados.')
    $checks.Add('Spawn Eggs: 88 IDs unicos, completos e com count 64 verificados.')
    $checks.Add('Spawn Egg Chest: cores dos componentes de texto verificadas.')
}

$validShulkerIds = @(
    'minecraft:white_shulker_box', 'minecraft:orange_shulker_box',
    'minecraft:magenta_shulker_box', 'minecraft:light_blue_shulker_box',
    'minecraft:yellow_shulker_box', 'minecraft:lime_shulker_box',
    'minecraft:pink_shulker_box', 'minecraft:gray_shulker_box',
    'minecraft:light_gray_shulker_box', 'minecraft:cyan_shulker_box',
    'minecraft:purple_shulker_box', 'minecraft:blue_shulker_box',
    'minecraft:brown_shulker_box', 'minecraft:green_shulker_box',
    'minecraft:red_shulker_box', 'minecraft:black_shulker_box'
)

if ($null -ne $nestedRoot) {
    Test-TextColors -Value $nestedRoot -Label 'Nested shulkers'
    if ($nestedRoot.id -ne 'minecraft:purple_shulker_box' -or [int]$nestedRoot.count -ne 64) {
        Add-ValidationError 'Nested shulkers: raiz deve ser purple_shulker_box com count 64.'
    }
    $rootHasMaxStackSize64 = Test-MaxStackSize64 -Item $nestedRoot
    if (-not $rootHasMaxStackSize64) {
        Add-ValidationError 'Nested shulkers: raiz sem minecraft:max_stack_size 64.'
    }
    $rootContainer = @(Get-Container -Item $nestedRoot -Label 'Nested root')
    if ($rootContainer.Count -ne 27) {
        Add-ValidationError "Nested root: esperadas 27 shulkers; encontradas $($rootContainer.Count)."
    }
    Test-ContiguousSlots -Container $rootContainer -Label 'Nested root'

    $allNestedIds = [System.Collections.Generic.List[string]]::new()
    $allNestedIds.Add([string]$nestedRoot.id)
    $middleCount = 0
    $leafCount = 0
    $middleMaxStackSize64Count = 0
    $leafMaxStackSize64Count = 0

    foreach ($middleEntry in $rootContainer) {
        $middle = $middleEntry.item
        $middleCount++
        $allNestedIds.Add([string]$middle.id)
        if ($validShulkerIds -notcontains $middle.id) {
            Add-ValidationError "Nested root: ID intermediario invalido: $($middle.id)."
        }
        if ([int]$middle.count -ne 64) {
            Add-ValidationError "Nested root: shulker intermediaria no slot $($middleEntry.slot) nao possui count 64."
        }
        if (Test-MaxStackSize64 -Item $middle) {
            $middleMaxStackSize64Count++
        }
        $leafContainer = @(Get-Container -Item $middle -Label "Nested middle $($middleEntry.slot)")
        if ($leafContainer.Count -ne 27) {
            Add-ValidationError "Nested middle $($middleEntry.slot): esperadas 27 folhas; encontradas $($leafContainer.Count)."
        }
        Test-ContiguousSlots -Container $leafContainer -Label "Nested middle $($middleEntry.slot)"

        foreach ($leafEntry in $leafContainer) {
            $leaf = $leafEntry.item
            $leafCount++
            $allNestedIds.Add([string]$leaf.id)
            if ($validShulkerIds -notcontains $leaf.id) {
                Add-ValidationError "Nested leaf: ID invalido: $($leaf.id)."
            }
            if ([int]$leaf.count -ne 64) {
                Add-ValidationError "Nested leaf: $($leaf.id) nao possui count 64."
            }
            if (Test-MaxStackSize64 -Item $leaf) {
                $leafMaxStackSize64Count++
            }
            if ($leaf.PSObject.Properties.Name -contains 'components') {
                if ($leaf.components.PSObject.Properties.Name -contains 'minecraft:container') {
                    Add-ValidationError 'Nested leaf: terceira camada contem outro container; limite violado.'
                }
            }
        }
    }

    if ($middleCount -ne 27 -or $leafCount -ne 729) {
        Add-ValidationError "Nested shulkers: esperadas 27 intermediarias e 729 folhas; encontradas $middleCount e $leafCount."
    }
    if ($middleMaxStackSize64Count -ne 27) {
        Add-ValidationError "Nested shulkers: esperados 27 overrides minecraft:max_stack_size 64 nas intermediarias; encontrados $middleMaxStackSize64Count."
    }
    if ($leafMaxStackSize64Count -ne 729) {
        Add-ValidationError "Nested shulkers: esperados 729 overrides minecraft:max_stack_size 64 nas folhas; encontrados $leafMaxStackSize64Count."
    }
    $maxStackSize64Count = [int]$rootHasMaxStackSize64 + $middleMaxStackSize64Count + $leafMaxStackSize64Count
    if ($maxStackSize64Count -ne 757) {
        Add-ValidationError "Nested shulkers: esperados 757 overrides minecraft:max_stack_size 64; encontrados $maxStackSize64Count."
    }
    if ($allNestedIds.Count -ne 757) {
        Add-ValidationError "Nested shulkers: esperados 757 ItemStacks; encontrados $($allNestedIds.Count)."
    }
    $distinctColors = @($allNestedIds | Sort-Object -Unique)
    if ($distinctColors.Count -ne 16) {
        Add-ValidationError "Nested shulkers: esperadas 16 cores; encontradas $($distinctColors.Count)."
    }
    $checks.Add('Nested shulkers: 1 raiz + 27 intermediarias + 729 folhas verificados.')
    $checks.Add('Nested shulkers: 757 ItemStacks, 16 cores e count 64 em todos verificados.')
    $checks.Add('Nested shulkers: 757 componentes minecraft:max_stack_size 64 verificados.')
    $checks.Add('Profundidade limitada: nenhuma das 729 shulkers-folha contem outro container.')
    $checks.Add('Nested shulkers: cores dos componentes de texto verificadas.')
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
$reportLines.Add('## Safety limit')
$reportLines.Add('')
$reportLines.Add('- O nesting termina nas 729 shulkers-folha; recursao adicional nao foi gerada.')
$reportLines.Add('- O validador nao substitui um teste manual no editor ou o codec do jogo.')

$report = $reportLines -join [Environment]::NewLine
if ($PSCmdlet.ShouldProcess($ReportPath, 'Gravar relatorio de validacao')) {
    Set-Content -LiteralPath $ReportPath -Value $report -Encoding utf8
}
Write-Output $report
if ($errors.Count -gt 0) { exit 1 }
