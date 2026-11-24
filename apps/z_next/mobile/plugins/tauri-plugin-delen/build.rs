// Geen commando's: de plugin werkt via de webview (downloads en een JavaScript-brug), niet via de IPC van Tauri.
const COMMANDS: &[&str] = &[];

fn main() {
    tauri_plugin::Builder::new(COMMANDS).android_path("android").build();
}
