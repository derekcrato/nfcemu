#!/usr/bin/env node

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function fetch(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data);
    }).on('error', reject);
  });
}

function extractEmbedId(content, url) {
  const patterns = [
    /embed\/(\d+)-[^"']+\.html/i,
    /embed\/(\d+)-[^"']+/i,
    /id="gameFrame"/i,
    /data-game[=\s]*"(\d+)"/i,
    /game[=\s]*"(\d+)"/i
  ];

  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  const urlMatch = url.match(/\/(\d+)-/);
  if (urlMatch) return urlMatch[1];

  const pathMatch = url.match(/\/(\d+)$/);
  if (pathMatch) return pathMatch[1];

  return null;
}

function createEmbedPage(gameId, gameName) {
  const safeName = gameName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const fileName = `${safeName}.html`;
  const filePath = path.join(__dirname, '..', 'docs', fileName);

  const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>${gameName}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
        iframe { width: 100%; height: 100%; border: none; display: block; }
    </style>
</head>
<body>
    <iframe src="https://www.retrogames.cc/embed/${gameId}-${safeName}.html" allow="fullscreen; autoplay; gamepad; microphone" allowfullscreen></iframe>
</body>
</html>`;

  fs.writeFileSync(filePath, html, 'utf8');
  return { fileName, filePath };
}

function gitCommitAndPush(files) {
  try {
    execSync('git add ' + files.join(' '), { cwd: path.join(__dirname, '..') });
    execSync('git commit -m "feat: add retrogames embeds"', { cwd: path.join(__dirname, '..') });
    execSync('git push', { cwd: path.join(__dirname, '..') });
    console.log('✅ Committed and pushed to GitHub');
  } catch (error) {
    console.error('❌ Git error:', error.message);
    process.exit(1);
  }
}

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.error('Usage: node tools/create-game-link.js <retrogames-url>');
    console.error('Example: node tools/create-game-link.js https://www.retrogames.cc/snes-games/powerup-patch-v1-3-0.html');
    process.exit(1);
  }

  console.log('🔍 Fetching game page...');
  const content = await fetch(url);
  console.log('📄 Page fetched, looking for embed ID...');

  const gameId = extractEmbedId(content, url);
  if (!gameId) {
    console.error('❌ Could not find embed ID in the page');
    process.exit(1);
  }

  console.log('🎮 Found embed ID:', gameId);

  const urlPath = new URL(url).pathname;
  const gameName = urlPath.split('/').pop().replace(/\.html$/, '').replace(/-/g, ' ');
  console.log('📝 Game name:', gameName);

  console.log('🔨 Creating embed page...');
  const { fileName, filePath } = createEmbedPage(gameId, gameName);
  console.log('✅ Created:', fileName);

  console.log('🚀 Committing and pushing...');
  gitCommitAndPush([path.join('docs', fileName)]);

  const pagesUrl = `https://derekcrato.github.io/nfcemu/${fileName}`;
  console.log('\n🎉 Done!');
  console.log('📱 NFC Link:', pagesUrl);
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
