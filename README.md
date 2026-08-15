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

### 1. Instale o launcher primeiro

O launcher e quem intercepta a tag NFC e abre o jogo.

- **Android**: instale o APK do launcher pela release `launchers-*` no GitHub.
- **iOS**: instale o IPA do launcher pela release `launchers-*` no GitHub.

Se o launcher nao estiver instalado, a URL da tag NFC abrira no navegador e dara erro 404, pois `raw.githubusercontent.com` nao e uma pagina HTML.

### 2. Escreva as tags NFC

Use qualquer app de gravacao NFC para escrever URLs no formato:
```
https://derekcrato.github.io/nfcemu/?game=ID_DO_JOGO
```

A pagina de redirecionamento vai:
- Tentar abrir o NFC Launcher automaticamente
- Se o launcher nao estiver instalado, mostrar botao para baixar
- Se estiver instalado, abrir o jogo direto

### 3. Aproxime a tag do celular

Com o launcher instalado:
- O app abre automaticamente
- Identifica o jogo pela URL
- Se o standalone ja existir, abre o jogo direto
- Se nao existir, baixa e instala o standalone do RetroArch

### Build local

```bash
# Gerar configuracao dos jogos
python3 scripts/generate_nfc_links.py

# Build standalone Android
python3 packager/build_standalone.py android

# Build standalone iOS
python3 packager/build_standalone.py ios
```

Nota: o build standalone requer cores do RetroArch baixados em `/tmp/ra-cores` ou no diretorio definido por `RETROARCH_CORES_DIR`.

Para baixar os cores manualmente:
```bash
mkdir -p /tmp/ra-cores
cd /tmp/ra-cores
curl -L -o mgba_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/mgba_libretro_android.so.zip
curl -L -o gambatte_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/gambatte_libretro_android.so.zip
curl -L -o genesis_plus_gx_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/genesis_plus_gx_libretro_android.so.zip
curl -L -o fceumm_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/fceumm_libretro_android.so.zip
curl -L -o snes9x_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/snes9x_libretro_android.so.zip
curl -L -o mednafen_psx_libretro_android.so.zip https://buildbot.libretro.com/nightly/android/latest/mednafen_psx_libretro_android.so.zip
unzip \*.zip -d /tmp/ra-cores
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

- `https://derekcrato.github.io/nfcemu/?game=gba-Pokemon_Crystal_advanced_Redux`
- `https://derekcrato.github.io/nfcemu/?game=gba-Pokemon_GS_Chronicles`
- `https://derekcrato.github.io/nfcemu/?game=gbx-Crystal_Version`
- `https://derekcrato.github.io/nfcemu/?game=gbx-Pokemon_vermelho`
- `https://derekcrato.github.io/nfcemu/?game=gbx-Pokemon_Yellow`
- `https://derekcrato.github.io/nfcemu/?game=md-Michael_Jackson_Moonwalker`
- `https://derekcrato.github.io/nfcemu/?game=ms-Alex_Kidd_in_Miracle_World`
- `https://derekcrato.github.io/nfcemu/?game=ms-Psycho_Fox`
- `https://derekcrato.github.io/nfcemu/?game=ms-Sapo_Xule_vs._Os_Invasores_do_Brejo`
- `https://derekcrato.github.io/nfcemu/?game=nes-Super_Mario_Bros._3`
- `https://derekcrato.github.io/nfcemu/?game=ps1-Digimon_World`
- `https://derekcrato.github.io/nfcemu/?game=snes-Super_Bomberman_5`
- `https://derekcrato.github.io/nfcemu/?game=snes-Super_Mario_World`

Exemplo de link completo:
```
https://raw.githubusercontent.com/derekcrato/nfcemu/main/roms/nes/Super%20Mario%20Bros.%203.nes
```

## Estado do projeto

- `roms/` deve ser preenchido localmente e nao e versionado
- `dist/games.json` e gerado automaticamente a partir de `roms/`
- Launchers Android/iOS prontos para build/teste
- Packager standalone funcional para APK/IPA
- CI/CD ajustado para nao depender de `roms/**`
