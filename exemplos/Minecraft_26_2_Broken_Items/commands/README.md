# Comandos de blocos

Os IDs foram confirmados no registry de blocos 26.2. Nenhum comando foi executado.

- `paste_one_at_a_time.txt`: linhas com `/` para colar individualmente no chat.
- `place_block_artifacts.mcfunction`: sintaxe de função, sem `/`, usando posições separadas.

Alguns estados são transitórios ou dependem do ambiente: fogo pode apagar, fluidos fluem, portais podem atualizar, `moving_piston`/`piston_head` são estados técnicos e `bubble_column` precisa de água. Isso não torna o comando sintaticamente inválido, mas o bloco pode mudar logo após ser colocado.
