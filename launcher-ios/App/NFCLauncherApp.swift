import SwiftUI
import CoreNFC

@main
struct NFCLauncherApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var nfcManager = NFCManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(nfcManager)
                .onContinueUserActivity(NSUserActivityTypeBrowsingWeb, perform: { userActivity in
                    nfcManager.handleUserActivity(userActivity)
                })
        }
    }
}

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     continue userActivity: NSUserActivity,
                     restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
        NFCManager.shared.handleUserActivity(userActivity)
        return true
    }
}

class NFCManager: ObservableObject {
    static let shared = NFCManager()

    @Published var message: String = "Aproxime uma tag NFC"
    @Published var status: String = "idle"

    private var nfcSession: NFCNDEFReaderSession?
    private let githubRepo: String = {
        Bundle.main.object(forInfoDictionaryKey: "GITHUB_REPO") as? String ?? "derekcrato/nfcemu"
    }()

    func startScanning() {
        guard NFCNDEFReaderSession.readingAvailable else {
            message = "NFC nao disponivel"
            return
        }
        message = "Aproxime a tag NFC"
        status = "scanning"
        nfcSession = NFCNDEFReaderSession(delegate: self, queue: nil, invalidateAfterFirstRead: true)
        nfcSession?.alertMessage = "Aproxime a tag NFC"
        nfcSession?.begin()
    }

    func handleUserActivity(_ userActivity: NSUserActivity) {
        guard userActivity.activityType == NSUserActivityTypeBrowsingWeb else { return }
        let ndefMessage = userActivity.ndefMessagePayload
        guard !ndefMessage.records.isEmpty,
              ndefMessage.records.first?.typeNameFormat != .empty else { return }
        processMessage(ndefMessage)
    }

    private func processMessage(_ message: NFCNDEFMessage) {
        var url: String?
        for record in message.records {
            if record.typeNameFormat == .nfcWellKnown,
               let found = String(data: record.payload, encoding: .utf8),
               found.hasPrefix("https://") {
                url = found
                break
            }
        }

        guard let url = url, url.contains(githubRepo) else {
            self.message = "Tag NFC nao autorizada"
            return
        }

        guard let gameId = extractGameId(from: url) else {
            self.message = "Jogo nao identificado"
            return
        }

        launchGame(gameId: gameId)
    }

    private func extractGameId(from url: String) -> String? {
        let parts = url.split(separator: "/", maxSplits: 6)
        guard parts.count >= 6 else { return nil }
        let system = String(parts[4])
        let name = String(parts[5])
        let base = name.split(separator: ".").first.map(String.init) ?? name
        return system + "-" + base.replacingOccurrences(of: " ", with: "_")
    }

    private func launchGame(gameId: String) {
        let standaloneIdentifier = "com.nfc.game." + gameId.lowercased()
        if let url = URL(string: "\(standaloneIdentifier)://play"), UIApplication.shared.canOpenURL(url) {
            UIApplication.shared.open(url)
            message = "Abrindo \(gameId)..."
            return
        }

        if let baseURL = URL(string: "com.retroarch://play"), UIApplication.shared.canOpenURL(baseURL) {
            let encoded = gameId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? gameId
            if let playURL = URL(string: "com.retroarch://play?game=\(encoded)") {
                UIApplication.shared.open(playURL)
                message = "Abrindo no RetroArch..."
                return
            }
        }

        message = "RetroArch nao instalado"
        status = "error"

        if let webURL = URL(string: "https://github.com/\(githubRepo)/releases") {
            UIApplication.shared.open(webURL)
        }
    }
}

extension NFCManager: NFCNDEFReaderSessionDelegate {
    func readerSession(_ session: NFCNDEFReaderSession, didDetectNDEFs messages: [NFCNDEFMessage]) {
        guard let message = messages.first else { return }
        DispatchQueue.main.async {
            self.processMessage(message)
            self.status = "done"
        }
    }

    func readerSession(_ session: NFCNDEFReaderSession, didInvalidateWithError error: Error) {
        DispatchQueue.main.async {
            self.status = "idle"
            if self.message == "Aproxime a tag NFC" {
                self.message = "Session encerrada"
            }
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var nfcManager: NFCManager

    var body: some View {
        VStack(spacing: 20) {
            Text(nfcManager.message)
                .font(.title2)
                .multilineTextAlignment(.center)
                .padding()

            Button(action: {
                nfcManager.startScanning()
            }) {
                Text("Escanear NFC")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .padding()
                    .background(.blue)
                    .cornerRadius(12)
            }
        }
        .padding()
    }
}
