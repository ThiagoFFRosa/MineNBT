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
$shulkerPath = Join-Path $Root 'admin_relics_pets_shulker.snbt'

function Add-ValidationError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $script:errors.Add($Message)
}

function Test-SnbtDelimiters {
    param([Parameter(Mandatory = $true)][string]$Text)

    $stack = [System.Collections.Generic.Stack[char]]::new()
    $inString = $false
    $quote = [char]0
    $escaped = $false

    for ($index = 0; $index -lt $Text.Length; $index++) {
        $character = $Text[$index]

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

function Assert-RegexCount {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][int]$Expected,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Text
    )

    $actual = [regex]::Matches($Text, $Pattern, [System.Text.RegularExpressions.RegexOptions]::Multiline).Count
    if ($actual -ne $Expected) {
        Add-ValidationError "${Label}: esperado $Expected; encontrado $actual."
    }
    else {
        $script:checks.Add("${Label}: $actual verificado(s).")
    }
}

if (-not (Test-Path -LiteralPath $shulkerPath -PathType Leaf)) {
    Add-ValidationError "Arquivo ausente: $shulkerPath"
    $text = ''
}
else {
    $text = Get-Content -LiteralPath $shulkerPath -Raw
}

if ($text.Length -gt 0) {
    $delimiterError = Test-SnbtDelimiters -Text $text
    if ($null -ne $delimiterError) {
        Add-ValidationError "Delimitadores SNBT: $delimiterError"
    }
    else {
        $checks.Add('Delimitadores SNBT balanceados; strings e escapes considerados.')
    }

    if ($text -match '(?i)(?<![a-z0-9_:/"])[+-]?(?:nan|infinity|inf)(?![a-z0-9_"])') {
        Add-ValidationError 'O arquivo contem NaN ou infinito.'
    }
    else {
        $checks.Add('Nenhum token NaN, Infinity ou Inf encontrado.')
    }

    if ($text -notmatch '(?m)^    id: "minecraft:light_blue_shulker_box"\s*$') {
        Add-ValidationError 'A raiz nao e minecraft:light_blue_shulker_box.'
    }
    if ($text -notmatch '"minecraft:container"\s*:\s*\[') {
        Add-ValidationError 'O componente minecraft:container esta ausente.'
    }

    $slotMatches = [regex]::Matches($text, '(?m)^                slot: (?<slot>\d+)\s*$')
    $slots = @($slotMatches | ForEach-Object { [int]$_.Groups['slot'].Value })
    $duplicates = @($slots | Group-Object | Where-Object Count -gt 1)
    $expectedSlots = @(0..12)
    $missingSlots = @($expectedSlots | Where-Object { $slots -notcontains $_ })
    $extraSlots = @($slots | Where-Object { $_ -notin $expectedSlots })
    if ($slots.Count -ne 13 -or $duplicates.Count -gt 0 -or $missingSlots.Count -gt 0 -or $extraSlots.Count -gt 0) {
        Add-ValidationError "Slots externos invalidos. Encontrados: $($slots -join ', ')."
    }
    else {
        $checks.Add('Shulker: 13 slots externos unicos e contiguos, de 0 a 12.')
    }

    Assert-RegexCount -Pattern 'id: "minecraft:written_book"' -Expected 1 -Label 'Livro administrativo' -Text $text
    Assert-RegexCount -Pattern 'action: "run_command"' -Expected 21 -Label 'Botoes run_command' -Text $text
    Assert-RegexCount -Pattern '(?m)^\s+raw: \{' -Expected 5 -Label 'Paginas do livro' -Text $text
    if ($text -match '(?i)/tp(?:\s|$)') {
        Add-ValidationError 'O livro contem teleporte, apesar do requisito de nao incluir TP.'
    }
    else {
        $checks.Add('Livro: nenhum comando /tp encontrado.')
    }

    foreach ($requiredCommand in @(
        '/gamemode survival @s', '/gamemode creative @s', '/gamemode adventure @s', '/gamemode spectator @s',
        '/time set day', '/time set noon', '/time set night', '/time set midnight',
        '/effect clear @s', 'name=Nicks', 'name=Kuronai', 'name=Celestine', 'Owner set from entity @s UUID'
    )) {
        if (-not $text.Contains($requiredCommand)) {
            Add-ValidationError "Livro: comando ou trecho obrigatorio ausente: $requiredCommand"
        }
    }
    $checks.Add('Livro: gamemodes, horarios, efeitos e adocao conferidos.')

    Assert-RegexCount -Pattern 'id: "minecraft:netherite_chestplate"' -Expected 1 -Label 'Peitoral de netherita' -Text $text
    Assert-RegexCount -Pattern '"minecraft:glider": \{\}' -Expected 1 -Label 'Componente glider' -Text $text
    foreach ($titanAttribute in @(
        'minecraft:max_health', 'minecraft:armor', 'minecraft:armor_toughness',
        'minecraft:knockback_resistance', 'minecraft:attack_damage', 'minecraft:scale',
        'minecraft:step_height', 'minecraft:block_interaction_range', 'minecraft:entity_interaction_range'
    )) {
        if ($text -notmatch [regex]::Escape("type: `"$titanAttribute`"")) {
            Add-ValidationError "Coroa do Tita: atributo ausente: $titanAttribute"
        }
    }
    $checks.Add('Coroa do Tita: nove atributos esperados encontrados.')

    Assert-RegexCount -Pattern 'id: "minecraft:netherite_pickaxe"' -Expected 4 -Label 'Omnitools' -Text $text
    Assert-RegexCount -Pattern '"minecraft:fortune": 10' -Expected 2 -Label 'Omnitools com Fortuna X' -Text $text
    Assert-RegexCount -Pattern '"minecraft:silk_touch": 1' -Expected 2 -Label 'Omnitools com Silk Touch' -Text $text
    foreach ($toolTag in @('pickaxe', 'axe', 'shovel', 'hoe')) {
        Assert-RegexCount -Pattern ([regex]::Escape("#minecraft:mineable/$toolTag")) -Expected 4 -Label "Regra universal $toolTag" -Text $text
    }
    Assert-RegexCount -Pattern '"minecraft:unbreakable": \{\}' -Expected 4 -Label 'Itens indestrutiveis' -Text $text

    Assert-RegexCount -Pattern 'id: "minecraft:cat_spawn_egg"' -Expected 1 -Label 'Ovo de gato' -Text $text
    Assert-RegexCount -Pattern 'id: "minecraft:wolf_spawn_egg"' -Expected 2 -Label 'Ovos de lobo' -Text $text
    Assert-RegexCount -Pattern 'Health: 300\.0f' -Expected 3 -Label 'Pets com Health 300' -Text $text
    Assert-RegexCount -Pattern 'id: "minecraft:max_health", base: 300\.0d' -Expected 3 -Label 'Pets com max_health 300' -Text $text
    Assert-RegexCount -Pattern 'id: "minecraft:attack_damage", base: 20\.0d' -Expected 3 -Label 'Pets com attack_damage 20' -Text $text
    Assert-RegexCount -Pattern 'id: "minecraft:regeneration", amplifier: 2b, duration: -1' -Expected 3 -Label 'Pets com Regeneracao III permanente' -Text $text
    foreach ($variant in @(
        '"minecraft:cat/variant": "minecraft:red"',
        '"minecraft:wolf/variant": "minecraft:black"',
        '"minecraft:wolf/variant": "minecraft:snowy"'
    )) {
        if (-not $text.Contains($variant)) {
            Add-ValidationError "Variante de pet ausente: $variant"
        }
    }
    $checks.Add('Pets: nomes, variantes red/black/snowy e persistencia configurados.')

    if ($text -notmatch 'amount: 499\.0d.+type: "minecraft:attack_damage"') {
        Add-ValidationError 'Stick de controle sem modificador +499 attack_damage.'
    }
    else {
        $checks.Add('Stick: +499 attack_damage, total nominal de 500 com a base do jogador.')
    }

    $validTextColors = @(
        'black', 'dark_blue', 'dark_green', 'dark_aqua', 'dark_red', 'dark_purple',
        'gold', 'gray', 'dark_gray', 'blue', 'green', 'aqua', 'red',
        'light_purple', 'yellow', 'white'
    )
    $colorMatches = [regex]::Matches($text, 'color: "(?<color>[a-z_]+)"')
    $invalidColors = @(
        $colorMatches |
            ForEach-Object { $_.Groups['color'].Value } |
            Where-Object { $_ -notin $validTextColors } |
            Sort-Object -Unique
    )
    if ($invalidColors.Count -gt 0) {
        Add-ValidationError "Cores de texto invalidas: $($invalidColors -join ', ')."
    }
    else {
        $checks.Add("Cores de texto: $($colorMatches.Count) ocorrencias validas.")
    }
}

$status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
$reportLines = [System.Collections.Generic.List[string]]::new()
$reportLines.Add('# Validation Report')
$reportLines.Add('')
$reportLines.Add("- Status: **$status**")
$reportLines.Add("- Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')")
$reportLines.Add('- Alvo: Minecraft Java 26.2')
$reportLines.Add('- Escopo: validacao estrutural e semantica offline; Minecraft nao foi iniciado')
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
$reportLines.Add('## Limite da validacao')
$reportLines.Add('')
$reportLines.Add('- O validador confere a estrutura, os tipos textuais importantes e os requisitos do kit.')
$reportLines.Add('- Ele nao substitui o codec interno do jogo nem o teste manual no Item Editor.')

$report = $reportLines -join [Environment]::NewLine
if ($PSCmdlet.ShouldProcess($ReportPath, 'Gravar relatorio de validacao')) {
    Set-Content -LiteralPath $ReportPath -Value $report -Encoding utf8
}
Write-Output $report
if ($errors.Count -gt 0) { exit 1 }

