# NFC Game Link Creator

Ferramenta para criar páginas de embed de jogos do retrogames.cc para uso com NFC.

## Uso

```bash
node tools/create-game-link.js <url-do-jogo>
```

### Exemplo

```bash
node tools/create-game-link.js https://www.retrogames.cc/snes-games/powerup-patch-v1-3-0.html
```

## Como funciona

1. Recebe a URL de um jogo do retrogames.cc
2. Extrai o ID de embed automaticamente
3. Cria uma página HTML com iframe limpo
4. Faz commit e push automático para o GitHub Pages

## Resultado

Após executar, você receberá um link NFC como:
```
https://derekcrato.github.io/nfcemu/powerup-patch.html
```

Basta gravar essa URL em uma tag NFC.

## Adicionando novos jogos

Para adicionar um novo jogo, basta executar o comando com a URL do jogo no retrogames.cc.
