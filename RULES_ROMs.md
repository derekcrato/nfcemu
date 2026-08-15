# Regra Fixa - NÃO ALTERAR ROMS

A pasta `roms/` é propriedade do usuário e NUNCA deve ser modificada, sobrescrita, deletada ou movida por este sistema.

## Proibido
- Sobrescrever arquivos em `roms/`
- Deletar arquivos em `roms/`
- Mover arquivos de/para `roms/`
- Executar `git checkout` ou `git reset` em `roms/`
- Qualquer comando que altere o conteúdo de `roms/`

## Permitido
- Ler arquivos de `roms/` para gerar `dist/games.json`
- Commitar ROMs existentes para o GitHub
- Adicionar novas ROMs (apenas se o usuário solicitar explicitamente)

## Proteção Git
O arquivo `.gitattributes` na raiz impede que hooks e CI alterem `roms/` acidentalmente.

## Em caso de dúvida
NÃO execute nenhuma operação em `roms/` sem autorização explícita do usuário.
