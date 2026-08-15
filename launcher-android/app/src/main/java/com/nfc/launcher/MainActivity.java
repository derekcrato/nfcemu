package com.nfc.launcher;

import android.Manifest;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.os.Bundle;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Arrays;

public class MainActivity extends AppCompatActivity {
    private static final int NFC_PERMISSION_REQUEST = 1001;
    private NfcAdapter nfcAdapter;
    private PendingIntent pendingIntent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        if (nfcAdapter == null) {
            Toast.makeText(this, "NFC nao suportado", Toast.LENGTH_LONG).show();
            finish();
            return;
        }

        pendingIntent = PendingIntent.getActivity(
                this, 0,
                new Intent(this, getClass()).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
                PendingIntent.FLAG_MUTABLE
        );

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.NFC)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.NFC},
                    NFC_PERMISSION_REQUEST);
        }

        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(@NonNull Intent intent) {
        super.onNewIntent(intent);
        handleIntent(intent);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == NFC_PERMISSION_REQUEST &&
                grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Permissao NFC concedida", Toast.LENGTH_SHORT).show();
        } else {
            Toast.makeText(this, "Permissao NFC negada", Toast.LENGTH_LONG).show();
        }
    }

    private void handleIntent(Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (NfcAdapter.ACTION_NDEF_DISCOVERED.equals(action) ||
            NfcAdapter.ACTION_TAG_DISCOVERED.equals(action) ||
            NfcAdapter.ACTION_TECH_DISCOVERED.equals(action)) {
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag == null) return;

            Ndef ndef = Ndef.get(tag);
            if (ndef == null) {
                Toast.makeText(this, "Tag NFC sem NDEF", Toast.LENGTH_SHORT).show();
                return;
            }

            try {
                ndef.connect();
                NdefMessage message = ndef.getNdefMessage();
                ndef.close();
                if (message != null && message.getRecords().length > 0) {
                    processNdefMessage(message);
                }
            } catch (IOException | android.nfc.FormatException e) {
                e.printStackTrace();
                Toast.makeText(this, "Erro ao ler NFC", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void processNdefMessage(NdefMessage message) {
        String url = null;
        for (NdefRecord record : message.getRecords()) {
            if (record.getTnf() == NdefRecord.TNF_WELL_KNOWN &&
                Arrays.equals(record.getType(), NdefRecord.RTD_URI)) {
                url = parseUriRecord(record);
                break;
            }
        }

        if (url == null) {
            Toast.makeText(this, "Tag NFC sem URL valida", Toast.LENGTH_SHORT).show();
            return;
        }

        if (!url.contains(getGitHubRepo())) {
            Toast.makeText(this, "Repositorio nao autorizado", Toast.LENGTH_SHORT).show();
            return;
        }

        String gameId = extractGameId(url);
        if (gameId == null) {
            Toast.makeText(this, "Jogo nao identificado", Toast.LENGTH_SHORT).show();
            return;
        }

        launchGame(gameId);
    }

    private String parseUriRecord(NdefRecord record) {
        String prefix = "";
        int index = 0;
        byte[] payload = record.getPayload();
        if (payload.length > 0) {
            index = payload[0] & 0xFF;
            String[] prefixes = {
                "", "https://", "https://www.", "http://", "http://www.",
                "tel:", "mailto:", "ftp://", "ftps://", "sftp://",
                "smb://", "nfs://", "ftp://", "dav://", "news:",
                "telnet://", "imap:", "rtsp://", "urn:", "pop:",
                "sip:", "sips:", "tftp:", "btspp://", "btl2cap://",
                "btgoep://", "tcp-btspp://", "tcp-btl2cap://",
                "tcp-btgoep://", "urn:nfc:", "urn:nfc:", "urn:nfc:"
            };
            if (index < prefixes.length) {
                prefix = prefixes[index];
            }
        }
        return prefix + new String(payload, index, payload.length - index);
    }

    private String extractGameId(String url) {
        String[] parts = url.split("/roms/");
        if (parts.length < 2) return null;
        String path = parts[1];
        String[] tokens = path.split("/");
        if (tokens.length < 2) return null;
        String system = tokens[0];
        String name = tokens[1];
        int dot = name.lastIndexOf('.');
        if (dot > 0) name = name.substring(0, dot);
        return system + "-" + name.replace(" ", "_").replace("(", "").replace(")", "").replace("'", "");
    }

    private String getGitHubRepo() {
        return BuildConfig.GITHUB_REPO;
    }

    private void launchGame(String gameId) {
        String standalonePkg = getStandalonePackage(gameId);
        if (isPackageInstalled(standalonePkg)) {
            openStandalone(gameId, standalonePkg);
            return;
        }

        String basePkg = "com.retroarch.aarch64";
        if (isPackageInstalled(basePkg)) {
            cacheRomForBase(gameId);
            openRetroArchBase(gameId, basePkg);
            return;
        }

        new AlertDialog.Builder(this)
                .setTitle("Instalar RetroArch")
                .setMessage("Voce precisa instalar o RetroArch para jogar. Deseja baixar agora?")
                .setPositiveButton("Instalar", (d, w) -> downloadAndInstallRetroArch(gameId))
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private String getStandalonePackage(String gameId) {
        return "com.nfc.game." + gameId.toLowerCase();
    }

    private boolean isPackageInstalled(String pkg) {
        try {
            getPackageManager().getPackageInfo(pkg, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    private void openStandalone(String gameId, String pkg) {
        Intent launch = new Intent(Intent.ACTION_MAIN);
        launch.setClassName(pkg, "com.retroarch.browser.retroactivity.RetroActivityFuture");
        launch.putExtra("ROM", "/storage/emulated/0/Android/data/" + pkg + "/files/roms/" + gameId + ".rom");
        launch.putExtra("LIBRETRO", "/data/data/" + pkg + "/files/cores/" + getCoreForGame(gameId) + "_libretro_android.so");
        launch.putExtra("CONFIGFILE", "/storage/emulated/0/Android/data/" + pkg + "/files/retroarch.cfg");
        launch.putExtra("QUITFOCUS", "");
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(launch);
    }

    private void cacheRomForBase(String gameId) {
        File cacheDir = new File(getExternalFilesDir(null), "roms");
        if (!cacheDir.exists()) cacheDir.mkdirs();
        File cached = new File(cacheDir, gameId + ".rom");
        if (cached.exists()) return;

        String romPath = getGameRomPath(gameId);
        if (romPath == null) return;
        File src = new File(romPath);
        if (!src.exists()) return;

        try (FileInputStream fis = new FileInputStream(src);
             FileOutputStream fos = new FileOutputStream(cached)) {
            byte[] buf = new byte[65536];
            int len;
            while ((len = fis.read(buf)) > 0) {
                fos.write(buf, 0, len);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void openRetroArchBase(String gameId, String pkg) {
        Intent launch = new Intent(Intent.ACTION_MAIN);
        launch.setClassName(pkg, "com.retroarch.browser.retroactivity.RetroActivityFuture");
        launch.putExtra("ROM", "/storage/emulated/0/Android/data/com.nfc.launcher/files/roms/" + gameId + ".rom");
        launch.putExtra("LIBRETRO", "/data/data/" + pkg + "/files/cores/" + getCoreForGame(gameId) + "_libretro_android.so");
        launch.putExtra("CONFIGFILE", "/storage/emulated/0/Android/data/" + pkg + "/files/retroarch.cfg");
        launch.putExtra("QUITFOCUS", "");
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(launch);
    }

    private String getGameRomPath(String gameId) {
        String system = gameId.split("-")[0];
        String base = gameId.substring(system.length() + 1).replace("_", " ");
        File dir = new File(getExternalFilesDir(null), "../roms/" + system);
        if (!dir.exists()) return null;
        File[] files = dir.listFiles();
        if (files == null) return null;
        for (File f : files) {
            String name = f.getName();
            int dot = name.lastIndexOf('.');
            if (dot > 0 && name.substring(0, dot).equalsIgnoreCase(base)) {
                return f.getAbsolutePath();
            }
        }
        return null;
    }

    private String getCoreForGame(String gameId) {
        String system = gameId.split("-")[0];
        switch (system) {
            case "gba": return "mgba";
            case "gbx": return "gambatte";
            case "md": return "genesis_plus_gx";
            case "ms": return "genesis_plus_gx";
            case "nes": return "fceumm";
            case "snes": return "snes9x";
            case "ps1": return "mednafen_psx";
            default: return "fceumm";
        }
    }

    private String getCorePath(String gameId) {
        return "/data/data/com.retroarch.aarch64/cores/" + getCoreForGame(gameId) + "_libretro_android.so";
    }

    private void downloadAndInstallRetroArch(String gameId) {
        String repo = getGitHubRepo();
        String apkUrl = "https://raw.githubusercontent.com/" + repo + "/main/dist/standalone/" + gameId + ".apk";
        Intent i = new Intent(Intent.ACTION_VIEW);
        i.setData(Uri.parse(apkUrl));
        startActivity(i);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (nfcAdapter != null) {
            nfcAdapter.enableForegroundDispatch(this, pendingIntent, null, null);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (nfcAdapter != null) {
            nfcAdapter.disableForegroundDispatch(this);
        }
    }
}
