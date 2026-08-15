package com.nfc.launcher;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.nfc.tech.NdefFormatable;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "NFCLauncher";
    private NfcAdapter nfcAdapter;
    private TextView statusText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        statusText = findViewById(R.id.status_text);
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);

        if (nfcAdapter == null) {
            statusText.setText("NFC não disponível neste dispositivo");
            return;
        }

        if (!nfcAdapter.isEnabled()) {
            statusText.setText("Ative o NFC nas configurações");
            return;
        }

        statusText.setText("Aproxime uma tag NFC");
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (nfcAdapter != null) {
            Intent intent = new Intent(this, MainActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            nfcAdapter.enableForegroundDispatch(this, 
                new android.app.PendingIntent.getActivity(this, 0, intent, 
                    android.app.PendingIntent.FLAG_MUTABLE),
                null, null);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (nfcAdapter != null) {
            nfcAdapter.disableForegroundDispatch(this);
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        
        if (NfcAdapter.ACTION_NDEF_DISCOVERED.equals(intent.getAction())) {
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag != null) {
                processTag(tag);
            }
        } else if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(intent.getAction())) {
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag != null) {
                statusText.setText("Tag detectada! Use ACTION_NDEF_DISCOVERED");
            }
        }
    }

    private void processTag(Tag tag) {
        statusText.setText("Processando tag...");
        
        Ndef ndef = Ndef.get(tag);
        if (ndef != null) {
            try {
                ndef.connect();
                NdefMessage ndefMessage = ndef.getNdefMessage();
                if (ndefMessage != null) {
                    String content = new String(ndefMessage.getRecords()[0].getPayload());
                    handleTagContent(content);
                } else {
                    statusText.setText("Tag vazia");
                }
                ndef.close();
            } catch (Exception e) {
                Log.e(TAG, "Erro ao ler tag", e);
                statusText.setText("Erro ao ler tag: " + e.getMessage());
            }
        } else {
            statusText.setText("Tag não formatada como NDEF");
        }
    }

    private void handleTagContent(String content) {
        runOnUiThread(() -> statusText.setText("Conteúdo: " + content));
        
        new Thread(() -> {
            try {
                JSONObject response = fetchGameInfo(content);
                if (response != null && response.has("download_url")) {
                    String downloadUrl = response.getString("download_url");
                    launchGame(downloadUrl);
                } else {
                    runOnUiThread(() -> statusText.setText("Jogo não encontrado"));
                }
            } catch (Exception e) {
                Log.e(TAG, "Erro ao buscar jogo", e);
                runOnUiThread(() -> statusText.setText("Erro: " + e.getMessage()));
            }
        }).start();
    }

    private JSONObject fetchGameInfo(String tagId) throws Exception {
        String urlStr = "https://raw.githubusercontent.com/derekcrato/nfcemu/main/dist/games.json";
        URL url = new URL(urlStr);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();
        
        JSONArray games = new JSONArray(sb.toString());
        for (int i = 0; i < games.length(); i++) {
            JSONObject game = games.getJSONObject(i);
            if (game.getString("tag_id").equals(tagId)) {
                return game;
            }
        }
        return null;
    }

    private void launchGame(String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            startActivity(intent);
            runOnUiThread(() -> statusText.setText("Abrindo jogo..."));
        } catch (Exception e) {
            Log.e(TAG, "Erro ao abrir jogo", e);
            runOnUiThread(() -> statusText.setText("Erro ao abrir jogo"));
        }
    }
}
