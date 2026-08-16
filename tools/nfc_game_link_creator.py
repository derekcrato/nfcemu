import urllib.request
import re
import os
import sys
import subprocess

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

def create_embed_page(game_id, game_name):
    safe_name = re.sub(r'[^a-z0-9]+', '-', game_name.lower()).strip('-')
    safe_name = re.sub(r'-+', '-', safe_name)
    file_name = f"{safe_name}.html"
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(exe_dir, '..', '..'))
    file_path = os.path.join(repo_root, 'docs', file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return file_name, file_path, repo_root

def git_commit_push(files, repo_root):
    try:
        subprocess.run(['git', 'add'] + files, cwd=repo_root, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'feat: add retrogames embeds'], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(['git', 'push'], cwd=repo_root, check=True, capture_output=True)
        print('✅ Committed and pushed to GitHub')
    except subprocess.CalledProcessError as e:
        print('❌ Git error:', e.stderr.decode('utf-8', errors='ignore'))
        input('Press Enter to exit...')
        sys.exit(1)

def main():
    print('=' * 50)
    print('       NFC Game Link Creator')
    print('=' * 50)
    print()

    url = input('Cole a URL do jogo do retrogames.cc: ').strip()
    if not url:
        print('❌ URL nao pode estar vazia!')
        input('Press Enter to exit...')
        sys.exit(1)

    print()
    print('🔍 Fetching game page...')
    try:
        content = fetch(url)
    except Exception as e:
        print('❌ Erro ao baixar a pagina:', e)
        input('Press Enter to exit...')
        sys.exit(1)

    print('📄 Page fetched, looking for embed ID...')

    game_id = extract_embed_id(content, url)
    if not game_id:
        print('❌ Could not find embed ID in the page')
        input('Press Enter to exit...')
        sys.exit(1)
    print('🎮 Found embed ID:', game_id)

    path_parts = url.split('/')
    game_name = path_parts[-1].replace('.html', '').replace('-', ' ')
    print('📝 Game name:', game_name)

    print('🔨 Creating embed page...')
    file_name, file_path, repo_root = create_embed_page(game_id, game_name)
    print('✅ Created:', file_name)
    print('📁 Repo root:', repo_root)

    print('🚀 Committing and pushing...')
    git_commit_push([os.path.join('docs', file_name)], repo_root)

    pages_url = f'https://derekcrato.github.io/nfcemu/{file_name}'
    print()
    print('=' * 50)
    print('🎉 Done!')
    print('📱 NFC Link:', pages_url)
    print('=' * 50)
    print()
    input('Press Enter to exit...')

if __name__ == '__main__':
    main()
