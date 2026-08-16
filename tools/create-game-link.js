const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function fetch(url) {
  return new Promise(function(resolve, reject) {
    var client = url.startsWith('https') ? https : http;
    client.get(url, function(res) {
      var data = '';
      res.on('data', function(chunk) { data += chunk; });
      res.on('end', function() { resolve(data); });
    }).on('error', reject);
  });
}

function extractEmbedId(content, url) {
  var patterns = [
    /embed\/(\d+)-[^"']+\.html/i,
    /embed\/(\d+)-[^"']+/i
  ];

  for (var i = 0; i < patterns.length; i++) {
    var match = content.match(patterns[i]);
    if (match && match[1]) {
      return match[1];
    }
  }

  var urlMatch = url.match(/\/(\d+)-/);
  if (urlMatch) return urlMatch[1];

  return null;
}

function createEmbedPage(gameId, gameName) {
  var safeName = gameName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  var fileName = safeName + '.html';
  var filePath = path.join(__dirname, '..', 'docs', fileName);

  var html = '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">\n    <title>' + gameName + '</title>\n    <style>\n        * { margin: 0; padding: 0; box-sizing: border-box; }\n        html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }\n        iframe { width: 100%; height: 100%; border: none; display: block; }\n    </style>\n</head>\n<body>\n    <iframe src="https://www.retrogames.cc/embed/' + gameId + '-' + safeName + '.html" allow="fullscreen; autoplay; gamepad; microphone" allowfullscreen></iframe>\n</body>\n</html>';

  fs.writeFileSync(filePath, html, 'utf8');
  return { fileName: fileName, filePath: filePath };
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

function main() {
  var url = process.argv[2];
  if (!url) {
    console.error('Usage: nfc-game-link-creator <retrogames-url>');
    process.exit(1);
  }

  console.log('🔍 Fetching game page...');
  fetch(url).then(function(content) {
    console.log('📄 Page fetched, looking for embed ID...');

    var gameId = extractEmbedId(content, url);
    if (!gameId) {
      console.error('❌ Could not find embed ID in the page');
      process.exit(1);
    }

    console.log('🎮 Found embed ID:', gameId);

    var urlParts = url.split('/');
    var gameName = urlParts[urlParts.length - 1].replace(/\.html$/, '').replace(/-/g, ' ');
    console.log('📝 Game name:', gameName);

    console.log('🔨 Creating embed page...');
    var result = createEmbedPage(gameId, gameName);
    console.log('✅ Created:', result.fileName);

    console.log('🚀 Committing and pushing...');
    gitCommitAndPush([path.join('docs', result.fileName)]);

    var pagesUrl = 'https://derekcrato.github.io/nfcemu/' + result.fileName;
    console.log('\n🎉 Done!');
    console.log('📱 NFC Link:', pagesUrl);
  }).catch(function(err) {
    console.error('❌ Error:', err.message);
    process.exit(1);
  });
}

main();
