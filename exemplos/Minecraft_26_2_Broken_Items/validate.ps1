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
$warnings = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[string]]::new()

function Add-ValidationError {
    param([string]$Message)
    $script:errors.Add($Message)
}

function Test-SnbtDelimiters {
    param([string]$Path)

    $text = Get-Content -LiteralPath $Path -Raw
    $stack = [System.Collections.Generic.Stack[char]]::new()
    $inString = $false
    $quote = [char]0
    $escaped = $false

    for ($index = 0; $index -lt $text.Length; $index++) {
        $character = $text[$index]

        if ($inString) {
            if ($escaped) {
                $escaped = $false
                continue
            }
            if ($character -eq '\') {
                $escaped = $true
                continue
            }
            if ($character -eq $quote) {
                $inString = $false
            }
            continue
        }

        if ($character -eq '"' -or $character -eq "'") {
            $inString = $true
            $quote = $character
            continue
        }

        if ($character -eq '{' -or $character -eq '[' -or $character -eq '(') {
            $stack.Push($character)
            continue
        }

        if ($character -eq '}' -or $character -eq ']' -or $character -eq ')') {
            if ($stack.Count -eq 0) {
                return "fechamento '$character' sem abertura no indice $index"
            }
            $opening = $stack.Pop()
            $expected = switch ($opening) {
                '{' { '}' }
                '[' { ']' }
                '(' { ')' }
            }
            if ($character -ne $expected) {
                return "delimitador '$opening' fechado por '$character' no indice $index"
            }
        }
    }

    if ($inString) {
        return 'string nao terminada'
    }
    if ($stack.Count -gt 0) {
        return "delimitador '$($stack.Peek())' nao fechado"
    }
    return $null
}

$requiredDirectories = @('items', 'shulker', 'blocks', 'commands', 'rejected_or_impossible')
foreach ($directory in $requiredDirectories) {
    $path = Join-Path $Root $directory
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        Add-ValidationError "Diretorio ausente: $directory"
    }
}

$requiredFiles = @(
    'README.md',
    'blocks\README.md',
    'commands\place_block_artifacts.mcfunction',
    'commands\paste_one_at_a_time.txt',
    'rejected_or_impossible\README.md',
    'shulker\broken_items_shulker.snbt'
)
foreach ($relativePath in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $relativePath) -PathType Leaf)) {
        Add-ValidationError "Arquivo ausente: $relativePath"
    }
}

$itemFiles = @(Get-ChildItem -LiteralPath (Join-Path $Root 'items') -Filter '*.snbt' -File | Sort-Object Name)
if ($itemFiles.Count -ne 27) {
    Add-ValidationError "Esperados 27 itens individuais; encontrados $($itemFiles.Count)."
}

$expectedNumbers = 1..27 | ForEach-Object { '{0:D2}' -f $_ }
$actualNumbers = $itemFiles | ForEach-Object { if ($_.BaseName -match '^(\d{2})_') { $Matches[1] } }
foreach ($number in $expectedNumbers) {
    if ($actualNumbers -notcontains $number) {
        Add-ValidationError "Item numerado ausente: $number"
    }
}

$allowedItems = @(
    'minecraft:acacia_slab', 'minecraft:amethyst_shard', 'minecraft:bamboo', 'minecraft:bedrock',
    'minecraft:blaze_rod', 'minecraft:bow', 'minecraft:carrot', 'minecraft:chest',
    'minecraft:diamond_sword', 'minecraft:elytra', 'minecraft:enchanted_book', 'minecraft:feather',
    'minecraft:firework_rocket', 'minecraft:netherite_axe', 'minecraft:netherite_chestplate',
    'minecraft:netherite_pickaxe', 'minecraft:netherite_sword', 'minecraft:paper', 'minecraft:player_head',
    'minecraft:potion', 'minecraft:rabbit_foot', 'minecraft:shulker_box', 'minecraft:slime_ball', 'minecraft:stick'
)

$forbiddenPattern = '(?i)(?<![a-z0-9_:/"])[+-]?(?:nan|infinity)(?![a-z0-9_"])'
foreach ($file in $itemFiles) {
    $relative = 'items/' + $file.Name
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $delimiterError = Test-SnbtDelimiters -Path $file.FullName
    if ($null -ne $delimiterError) {
        Add-ValidationError "${relative}: $delimiterError"
    }
    if ($text -match $forbiddenPattern) {
        Add-ValidationError "${relative}: contem NaN ou infinito."
    }

    $rootIdMatch = [regex]::Match($text, '(?m)^ {4}id:\s*"(?<id>minecraft:[a-z0-9_./-]+)"\s*$')
    if (-not $rootIdMatch.Success) {
        Add-ValidationError "${relative}: ItemStack raiz sem id reconhecivel."
    }
    elseif ($allowedItems -notcontains $rootIdMatch.Groups['id'].Value) {
        Add-ValidationError "${relative}: id raiz nao consta no snapshot permitido: $($rootIdMatch.Groups['id'].Value)"
    }

    $rootCountMatch = [regex]::Match($text, '(?m)^ {4}count:\s*(?<count>-?\d+)\s*,?\s*$')
    if (-not $rootCountMatch.Success) {
        Add-ValidationError "${relative}: ItemStack raiz sem count inteiro."
    }
    else {
        $count = [int]$rootCountMatch.Groups['count'].Value
        if ($count -lt 1 -or $count -gt 99) {
            Add-ValidationError "${relative}: count fora do intervalo 1..99: $count"
        }
    }
}
$checks.Add("27 arquivos individuais inspecionados para id, count, strings e delimitadores.")

$masterPath = Join-Path $Root 'shulker\broken_items_shulker.snbt'
if (Test-Path -LiteralPath $masterPath -PathType Leaf) {
    $masterText = Get-Content -LiteralPath $masterPath -Raw
    $delimiterError = Test-SnbtDelimiters -Path $masterPath
    if ($null -ne $delimiterError) {
        Add-ValidationError "shulker/broken_items_shulker.snbt: $delimiterError"
    }
    if ($masterText -match $forbiddenPattern) {
        Add-ValidationError 'Shulker mestre contem NaN ou infinito.'
    }
    if ($masterText -notmatch '(?m)^ {4}id:\s*"minecraft:shulker_box"\s*$') {
        Add-ValidationError 'Shulker mestre sem id raiz minecraft:shulker_box.'
    }
    if ($masterText -notmatch '"minecraft:container"\s*:\s*\[') {
        Add-ValidationError 'Shulker mestre sem minecraft:container.'
    }

    $slotMatches = [regex]::Matches($masterText, '(?m)^(?<indent> +)slot:\s*(?<slot>\d+)\s*,?\s*$')
    if ($slotMatches.Count -eq 0) {
        Add-ValidationError 'Nenhum slot encontrado na shulker mestre.'
    }
    else {
        $minimumIndent = ($slotMatches | ForEach-Object { $_.Groups['indent'].Value.Length } | Measure-Object -Minimum).Minimum
        $outerSlots = @($slotMatches | Where-Object { $_.Groups['indent'].Value.Length -eq $minimumIndent } | ForEach-Object { [int]$_.Groups['slot'].Value })
        $duplicates = @($outerSlots | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
        if ($duplicates.Count -gt 0) {
            Add-ValidationError "Slots externos duplicados: $($duplicates -join ', ')"
        }
        $missing = @(0..26 | Where-Object { $outerSlots -notcontains $_ })
        $extra = @($outerSlots | Where-Object { $_ -lt 0 -or $_ -gt 26 })
        if ($missing.Count -gt 0) {
            Add-ValidationError "Slots externos ausentes: $($missing -join ', ')"
        }
        if ($extra.Count -gt 0) {
            Add-ValidationError "Slots externos fora de 0..26: $($extra -join ', ')"
        }
        if ($outerSlots.Count -ne 27) {
            Add-ValidationError "Esperados 27 slots externos; encontrados $($outerSlots.Count)."
        }
        $checks.Add("Shulker mestre: $($outerSlots.Count) slots externos unicos analisados.")
    }
}

$status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'
$reportLines = [System.Collections.Generic.List[string]]::new()
$reportLines.Add('# Validation Report')
$reportLines.Add('')
$reportLines.Add("- Status: **$status**")
$reportLines.Add("- Gerado em: $timestamp")
$reportLines.Add('- Alvo: Minecraft Java 26.2 (data version 4903, protocol 776)')
$reportLines.Add('- Escopo: validacao estrutural offline; Minecraft nao foi iniciado')
$reportLines.Add('')
$reportLines.Add('## Checks')
$reportLines.Add('')
foreach ($check in $checks) {
    $reportLines.Add("- $check")
}
$reportLines.Add('- Delimitadores `{}`, `[]` e `()` balanceados, com strings e escapes considerados.')
$reportLines.Add('- ItemStacks raiz verificados para `id` e `count` no intervalo 1..99.')
$reportLines.Add('- Tokens `NaN`, `Infinity` e `-Infinity` proibidos.')
$reportLines.Add('- Estrutura de pastas e arquivos obrigatorios verificada.')
$reportLines.Add('')
$reportLines.Add('## Errors')
$reportLines.Add('')
if ($errors.Count -eq 0) {
    $reportLines.Add('- Nenhum erro estrutural encontrado.')
}
else {
    foreach ($message in $errors) {
        $reportLines.Add("- $message")
    }
}
$reportLines.Add('')
$reportLines.Add('## Warnings')
$reportLines.Add('')
$reportLines.Add('- Este validador nao substitui o codec do jogo nem um teste manual no editor.')
foreach ($message in $warnings) {
    $reportLines.Add("- $message")
}

$report = $reportLines -join [Environment]::NewLine
if ($PSCmdlet.ShouldProcess($ReportPath, 'Gravar relatorio de validacao')) {
    Set-Content -LiteralPath $ReportPath -Value $report -Encoding utf8
}

Write-Output $report
if ($errors.Count -gt 0) {
    exit 1
}
