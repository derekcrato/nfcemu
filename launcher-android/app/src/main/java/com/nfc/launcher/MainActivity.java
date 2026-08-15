package com.nfc.launcher;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Environment;

import java.io.IOException;
import java.util.Arrays;

public class MainActivity extends AppCompatActivity {
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

        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(@NonNull Intent intent) {
        super.onNewIntent(intent);
        handleIntent(intent);
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
                readRawTag(tag);
                return;
            }

            try {
                ndef.connect();
                NdefMessage message = ndef.getNdefMessage();
                ndef.close();
                if (message != null && message.getRecords().length > 0) {
                    processNdefMessage(message);
                }
            } catch (IOException | FormatException e) {
                e.printStackTrace();
                Toast.makeText(this, "Erro ao ler NFC", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void readRawTag(Tag tag) {
        NdefMessage message = createFallbackMessage(tag);
        if (message != null) {
            processNdefMessage(message);
        }
    }

    private NdefMessage createFallbackMessage(Tag tag) {
        byte[] id = tag.getId();
        String tagId = bytesToHex(id);
        String url = "https://raw.githubusercontent.com/" + getGitHubRepo() + "/main/roms/unknown/" + tagId;
        NdefRecord record = NdefRecord.createUri(url);
        return new NdefMessage(new NdefRecord[]{record});
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02X", b));
        return sb.toString();
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
            Toast.makeText(this, "Repositorio GitHub nao autorizado", Toast.LENGTH_SHORT).show();
            return;
        }

        String gameId = extractGameId(url);
        if (gameId == null) {
            Toast.makeText(this, "Nao foi possivel identificar o jogo", Toast.LENGTH_SHORT).show();
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
        boolean isAndroid = true;
        boolean isIOS = false;

        String standalonePkg = getStandalonePackage(gameId);
        if (isPackageInstalled(standalonePkg)) {
            openStandalone(gameId, standalonePkg);
            return;
        }

        String basePkg = "com.retroarch.aarch64";
        if (isPackageInstalled(basePkg)) {
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

    private void openRetroArchBase(String gameId, String pkg) {
        Intent launch = new Intent(Intent.ACTION_MAIN);
        launch.setClassName(pkg, "com.retroarch.browser.retroactivity.RetroActivityFuture");
        launch.putExtra("ROM", getCachedRomPath(gameId));
        launch.putExtra("LIBRETRO", getCorePath(gameId));
        launch.putExtra("CONFIGFILE", "/storage/emulated/0/Android/data/" + pkg + "/files/retroarch.cfg");
        launch.putExtra("QUITFOCUS", "");
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(launch);
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

    private String getCachedRomPath(String gameId) {
        return "/storage/emulated/0/Android/data/com.nfc.launcher/files/roms/" + gameId + ".rom";
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
