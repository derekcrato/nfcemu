import urllib.request
import re
import os
import sys
import subprocess
import json

CONFIG_FILE = 'nfc_tool_config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8', errors='ignore')

def extract_embed_id(content, url):
    match = re.search(r'embed/(\d+)-', content)
    if match:
        return match.group(1)
    match = re.search(r'\/(\d+)-', url)
    if match:
        return match.group(1)
    return None

def create_embed_page(game_id, game_name, overwrite=False):
    safe_name = re.sub(r'[^a-z0-9]+', '-', game_name.lower()).strip('-')
    safe_name = re.sub(r'-+', '-', safe_name)
    file_name = f"{safe_name}.html"
    
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(exe_dir, '..', '..'))
    file_path = os.path.join(repo_root, 'docs', file_name)

    if os.path.exists(file_path) and not overwrite:
        return None, file_path, repo_root

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{game_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
        iframe {{ width: 100%; height: 100%; border: none; display: block; }}
    </style>
</head>
<body>
    <iframe src="https://www.retrogames.cc/embed/{game_id}-{safe_name}.html" allow="fullscreen; autoplay; gamepad; microphone" allowfullscreen></iframe>
</body>
</html>'''

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return file_name, file_path, repo_root

def git_commit_push(files, repo_root, message):
    try:
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        
        result_add = subprocess.run(['git', 'add'] + files, cwd=repo_root, capture_output=True, text=True, env=env)
        if result_add.returncode != 0:
            print('❌ Git add error:', result_add.stderr)
            return False
            
        result_commit = subprocess.run(['git', 'commit', '-m', message], cwd=repo_root, capture_output=True, text=True, env=env)
        if result_commit.returncode != 0:
            print('❌ Git commit error:', result_commit.stderr)
            return False
            
        result_push = subprocess.run(['git', 'push'], cwd=repo_root, capture_output=True, text=True, env=env)
        if result_push.returncode != 0:
            print('❌ Git push error:', result_push.stderr)
            return False
            
        print('✅ Committed and pushed to GitHub')
        return True
    except Exception as e:
        print('❌ Git error:', str(e))
        return False

def find_repo_root():
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.abspath(os.path.join(exe_dir, '..', '..')),
        os.path.abspath(os.path.join(exe_dir, '..')),
        exe_dir,
        os.path.expanduser('~/Desktop/nfc'),
        'C:\\Users\\Derek\\Desktop\\nfc',
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, '.git')):
            return path
    return None

def list_games():
    repo_root = find_repo_root()
    if not repo_root:
        return []
    docs_dir = os.path.join(repo_root, 'docs')
    games = []
    if os.path.exists(docs_dir):
        for f in os.listdir(docs_dir):
            if f.endswith('.html') and f not in ['index.html', 'game.html', 'embed.html', 'powerup-patch.html']:
                games.append(f)
    return sorted(games)

def delete_game(file_name):
    repo_root = find_repo_root()
    if not repo_root:
        return False
    file_path = os.path.join(repo_root, 'docs', file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def main():
    repo_root = find_repo_root()
    if not repo_root:
        print('❌ Repositório Git não encontrado!')
        print('Certifique-se de que o repositório nfc está clonado em: C:\\Users\\Derek\\Desktop\\nfc')
        input('Press Enter to exit...')
        sys.exit(1)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('=' * 50)
        print('       NFC Game Link Manager')
        print('=' * 50)
        print()
        print(f'Repo: {repo_root}')
        print()
        print('1. Gerar novo link')
        print('2. Listar todos os jogos')
        print('3. Excluir jogo')
        print('4. Sair')
        print()
        
        choice = input('Escolha uma opcao: ').strip()
        
        if choice == '1':
            url = input('Cole a URL do jogo do retrogames.cc: ').strip()
            if not url:
                print('❌ URL nao pode estar vazia!')
                input('Press Enter to continue...')
                continue
            
            print()
            print('🔍 Fetching game page...')
            try:
                content = fetch(url)
            except Exception as e:
                print('❌ Erro ao baixar a pagina:', e)
                input('Press Enter to continue...')
                continue

            game_id = extract_embed_id(content, url)
            if not game_id:
                print('❌ Could not find embed ID in the page')
                input('Press Enter to continue...')
                continue
            print('🎮 Found embed ID:', game_id)

            path_parts = url.split('/')
            game_name = path_parts[-1].replace('.html', '').replace('-', ' ')
            print('📝 Game name:', game_name)

            file_name, file_path, repo_root = create_embed_page(game_id, game_name)
            if file_name is None:
                overwrite = input(f'⚠️  {file_name} already exists. Overwrite? (y/n): ').strip().lower()
                if overwrite != 'y':
                    print('Cancelled.')
                    input('Press Enter to continue...')
                    continue
                file_name, file_path, repo_root = create_embed_page(game_id, game_name, overwrite=True)

            print('✅ Created:', file_name)
            print('🚀 Committing and pushing...')
            success = git_commit_push([os.path.join('docs', file_name)], repo_root, f'feat: add {file_name}')
            if success:
                pages_url = f'https://derekcrato.github.io/nfcemu/{file_name}'
                print()
                print('=' * 50)
                print('🎉 Done!')
                print('📱 NFC Link:', pages_url)
                print('=' * 50)
            input('Press Enter to continue...')

        elif choice == '2':
            games = list_games()
            if not games:
                print('Nenhum jogo encontrado.')
            else:
                print()
                print('Jogos cadastrados:')
                print('-' * 50)
                for i, game in enumerate(games, 1):
                    print(f'{i}. {game}')
                    print(f'   https://derekcrato.github.io/nfcemu/{game}')
                    print()
            input('Press Enter to continue...')

        elif choice == '3':
            games = list_games()
            if not games:
                print('Nenhum jogo para excluir.')
                input('Press Enter to continue...')
                continue
            print()
            print('Jogos disponiveis para exclusao:')
            for i, game in enumerate(games, 1):
                print(f'{i}. {game}')
            print()
            idx = input('Numero do jogo para excluir (ou 0 para cancelar): ').strip()
            try:
                idx = int(idx)
                if idx == 0:
                    continue
                if idx < 1 or idx > len(games):
                    print('❌ Numero invalido!')
                    input('Press Enter to continue...')
                    continue
                game_to_delete = games[idx - 1]
                confirm = input(f'Tem certeza que deseja excluir {game_to_delete}? (y/n): ').strip().lower()
                if confirm == 'y':
                    if delete_game(game_to_delete):
                        git_commit_push([f'docs/{game_to_delete}'], repo_root, f'remove: delete {game_to_delete}')
                        print(f'✅ {game_to_delete} excluido!')
                    else:
                        print('❌ Erro ao excluir arquivo.')
                else:
                    print('Cancelled.')
            except ValueError:
                print('❌ Entrada invalida!')
            input('Press Enter to continue...')

        elif choice == '4':
            print('Saindo...')
            sys.exit(0)

        else:
            print('❌ Opcao invalida!')
            input('Press Enter to continue...')

if __name__ == '__main__':
    main()
