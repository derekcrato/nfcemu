import SwiftUI
import CoreNFC

extension URL {
    var queryParameters: [String: String]? {
        guard let components = URLComponents(url: self, resolvingAgainstBaseURL: false),
              let queryItems = components.queryItems else { return nil }
        return Dictionary(uniqueKeysWithValues: queryItems.compactMap { item in
            guard let value = item.value else { return nil }
            return (item.name, value)
        })
    }
}

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

    func application(_ app: UIApplication, open url: URL,
                     options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
        guard url.scheme == "com.nfc.launcher" else { return false }
        if let game = url.queryParameters?["game"] {
            NFCManager.shared.launchGame(gameId: game)
            return true
        }
        return false
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
        guard let path = URL(string: url)?.path else { return nil }
        let trimmed = path.replacingOccurrences(of: "^/roms/", with: "", options: .regularExpression)
        let components = trimmed.split(separator: "/", maxSplits: 1)
        guard components.count == 2 else { return nil }
        let system = String(components[0])
        let filename = String(components[1])
        let base = filename.split(separator: ".").first.map(String.init) ?? filename
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
