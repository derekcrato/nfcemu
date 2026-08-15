# NFC RetroArch Launcher

Sistema de emulador NFC para Android e iOS usando RetroArch standalone por jogo.

## Estrutura

```
nfc/
├── roms/                    # ROMs organizadas por sistema
│   ├── gba/
│   ├── gbx/
│   ├── md/
│   ├── ms/
│   ├── nes/
│   ├── snes/
│   └── ps1/
├── launcher-android/        # App NFC para Android
├── launcher-ios/            # App NFC para iOS
├── packager/                # Empacota RetroArch standalone por jogo
├── scripts/                 # Utilitarios
└── .github/workflows/       # CI/CD
```

## Como funciona

1. **Tag NFC** contem URL HTTPS apontando para este repositorio, ex:
   `https://raw.githubusercontent.com/USER/REPO/main/roms/nes/SuperMarioBros.nes`

2. **App Launcher** (Android/iOS) le a tag NFC:
   - Valida se a URL pertence ao repositorio autorizado
   - Identifica o jogo pelo caminho `/roms/<system>/<nome>`
   - Verifica se o RetroArch standalone do jogo esta instalado
   - Se nao, pergunta se o usuario quer instalar (baixa APK/IPA do GitHub)
   - Se sim, abre o jogo via intent/URL scheme

3. **Standalone RetroArch** e um APK/IPA por jogo contendo:
   - RetroArch otimizado com apenas o core necessario
   - ROM embutida
   - Icone e nome exclusivos

## Uso

### Escrevendo tags NFC

Use qualquer app de gravacao NFC para escrever URLs no formato:
```
https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/roms/SISTEMA/JOGO.EXT
```

### Build local

```bash
# Gerar configuracao dos jogos
python3 scripts/generate_nfc_links.py

# Build standalone Android
python3 packager/build_standalone.py android

# Build standalone iOS
python3 packager/build_standalone.py ios
```

### GitHub Actions

O CI automatico faz:
- Scan de novas ROMs em `roms/`
- Geracao de `dist/games.json`
- Build de APKs standalone por jogo
- Build dos launchers Android e iOS
- Publicacao em GitHub Releases

## Configuracao

Edite `scripts/generate_nfc_links.py` para ajustar:
- `SYSTEM_CORES` - mapeamento sistema -> core RetroArch
- `SYSTEM_EXT` - extensoes aceitas por sistema

## Permissoes

### Android
- `android.permission.NFC` - leitura de tags
- `android.permission.INTERNET` - download de APKs
- `android.permission.REQUEST_INSTALL_PACKAGES` - instalacao side-load

### iOS
- `NFC Tag Reading` - leitura de tags (CoreNFC)
- `Associated Domains` - para universal links (background NFC)

## Notas

- RetroArch e obrigatorio como base (sem excecao)
- Standalone APKs sao gerados com core + ROM embutidos
- Apos primeira instalacao, o jogo abre sem NFC
- NFC subsequente apenas abre o jogo instalado
- Todos os binaries sao hospedados no proprio repositorio GitHub

## Links NFC de teste

Use esses links para gravar nas tags NFC:

- `nes/Super Mario Bros. 3.nes`
- `snes/Super Mario World.sfc`
- `snes/Super Bomberman 5.sfc`
- `gba/Pokemon Crystal Advanced Redux.gba`
- `gba/Pokemon GS Chronicles.gba`
- `gbx/Crystal Version.GBC`
- `gbx/Pokemon vermelho.gb`
- `gbx/Pokemon Yellow.gbc`
- `md/Michael Jackson Moonwalker.bin`
- `ms/Alex Kidd in Miracle World.sms`
- `ms/Psycho Fox.sms`
- `ms/Sapo Xule vs. Os Invasores do Brejo.bin`
- `ps1/Digimon World.cue`

Exemplo de link completo:
```
https://raw.githubusercontent.com/derekcrato/nfcemu/main/roms/nes/Super%20Mario%20Bros.%203.nes
```

## Estado do projeto

- `roms/` deve ser preenchido localmente e nao e versionado
- `dist/games.json` e gerado automaticamente a partir de `roms/`
- Launchers e packager estao prontos para build/teste
- CI/CD precisa de ajustes para nao mexer em `roms/`
