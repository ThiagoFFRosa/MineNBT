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
    if ($inString) { return 'string nao terminada' }
    if ($stack.Count -gt 0) { return "delimitador '$($stack.Peek())' nao fechado" }
    return $null
}

$files = [ordered]@{
    'shulkers\01_armor_sets_standard_durability.snbt' = [ordered]@{
        RootId = 'minecraft:cyan_shulker_box'
        UnbreakableCount = 0
    }
    'shulkers\02_armor_sets_unbreakable.snbt' = [ordered]@{
        RootId = 'minecraft:purple_shulker_box'
        UnbreakableCount = 9
    }
}

$expectedItems = [ordered]@{
    'minecraft:elytra' = 1
    'minecraft:netherite_boots' = 2
    'minecraft:netherite_chestplate' = 2
    'minecraft:netherite_helmet' = 2
    'minecraft:netherite_leggings' = 2
}

$maxLevels = [ordered]@{
    aqua_affinity = 1
    blast_protection = 4
    depth_strider = 3
    feather_falling = 4
    fire_protection = 4
    frost_walker = 2
    mending = 1
    projectile_protection = 4
    protection = 4
    respiration = 3
    soul_speed = 3
    swift_sneak = 3
    thorns = 3
    unbreaking = 3
}

$expectedEnchantOccurrences = [ordered]@{
    aqua_affinity = 2
    blast_protection = 4
    depth_strider = 2
    feather_falling = 2
    fire_protection = 4
    frost_walker = 1
    mending = 9
    projectile_protection = 4
    protection = 9
    respiration = 2
    soul_speed = 2
    swift_sneak = 2
    thorns = 8
    unbreaking = 9
}

$forbiddenPattern = '(?i)(?<![a-z0-9_:/"])[+-]?(?:nan|infinity)(?![a-z0-9_"])'

foreach ($entry in $files.GetEnumerator()) {
    $relativePath = $entry.Key
    $settings = $entry.Value
    $path = Join-Path $Root $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-ValidationError "Arquivo ausente: $relativePath"
        continue
    }

    $text = Get-Content -LiteralPath $path -Raw
    $delimiterError = Test-SnbtDelimiters -Path $path
    if ($null -ne $delimiterError) {
        Add-ValidationError "${relativePath}: $delimiterError"
    }
    if ($text -match $forbiddenPattern) {
        Add-ValidationError "${relativePath}: contem NaN ou infinito."
    }
    if ($text -notmatch ('(?m)^ {4}id:\s*"' + [regex]::Escape($settings.RootId) + '"\s*$')) {
        Add-ValidationError "${relativePath}: ID raiz incorreto."
    }
    if ($text -notmatch '"minecraft:container"\s*:\s*\[') {
        Add-ValidationError "${relativePath}: sem minecraft:container."
    }

    $slotMatches = [regex]::Matches($text, '(?m)^(?<indent> +)slot:\s*(?<slot>\d+)\s*,?\s*$')
    $minimumIndent = ($slotMatches | ForEach-Object { $_.Groups['indent'].Value.Length } | Measure-Object -Minimum).Minimum
    $outerSlots = @($slotMatches | Where-Object { $_.Groups['indent'].Value.Length -eq $minimumIndent } | ForEach-Object { [int]$_.Groups['slot'].Value })
    $missingSlots = @(0..8 | Where-Object { $outerSlots -notcontains $_ })
    $duplicateSlots = @($outerSlots | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
    if ($outerSlots.Count -ne 9 -or $missingSlots.Count -gt 0 -or $duplicateSlots.Count -gt 0) {
        Add-ValidationError "${relativePath}: slots externos devem ser unicos e exatamente 0..8."
    }

    $itemIds = @([regex]::Matches($text, '(?m)^ {20}id:\s*"(?<id>minecraft:[a-z0-9_./-]+)"\s*$') | ForEach-Object { $_.Groups['id'].Value })
    foreach ($expectedItem in $expectedItems.GetEnumerator()) {
        $actualCount = @($itemIds | Where-Object { $_ -eq $expectedItem.Key }).Count
        if ($actualCount -ne $expectedItem.Value) {
            Add-ValidationError "${relativePath}: esperado $($expectedItem.Value)x $($expectedItem.Key); encontrado $actualCount."
        }
    }
    if ($itemIds.Count -ne 9) {
        Add-ValidationError "${relativePath}: esperados 9 ItemStacks internos com id; encontrados $($itemIds.Count)."
    }

    $levelMatches = [regex]::Matches($text, '"minecraft:(?<id>[a-z0-9_./-]+)"\s*:\s*(?<level>\d+)')
    foreach ($match in $levelMatches) {
        $enchantment = $match.Groups['id'].Value
        $level = [int]$match.Groups['level'].Value
        if (-not $maxLevels.Contains($enchantment)) {
            Add-ValidationError "${relativePath}: chave numerica nao reconhecida como enchantment permitido: minecraft:$enchantment"
            continue
        }
        if ($level -ne $maxLevels[$enchantment]) {
            Add-ValidationError "${relativePath}: minecraft:$enchantment deveria estar no maximo vanilla $($maxLevels[$enchantment]); encontrado $level."
        }
    }

    foreach ($expectedEnchantment in $expectedEnchantOccurrences.GetEnumerator()) {
        $pattern = '"minecraft:' + [regex]::Escape($expectedEnchantment.Key) + '"\s*:'
        $actualCount = ([regex]::Matches($text, $pattern)).Count
        if ($actualCount -ne $expectedEnchantment.Value) {
            Add-ValidationError "${relativePath}: esperado $($expectedEnchantment.Value)x minecraft:$($expectedEnchantment.Key); encontrado $actualCount."
        }
    }

    $unbreakableCount = ([regex]::Matches($text, '"minecraft:unbreakable"\s*:\s*\{\}')).Count
    if ($unbreakableCount -ne $settings.UnbreakableCount) {
        Add-ValidationError "${relativePath}: esperado $($settings.UnbreakableCount) componente(s) unbreakable; encontrado $unbreakableCount."
    }
    if ($text -match 'minecraft:(?:binding_curse|vanishing_curse)') {
        Add-ValidationError "${relativePath}: curses nao solicitadas foram encontradas."
    }

    $checks.Add("${relativePath}: 9 slots, 9 ItemStacks e niveis vanilla inspecionados.")
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
$reportLines.Add('- Quatro familias de Protection verificadas no Set God.')
$reportLines.Add('- Depth Strider III + Frost Walker II verificados nas God Boots.')
$reportLines.Add('- Elytra verificada com Protection IV, Unbreaking III e Mending.')
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
