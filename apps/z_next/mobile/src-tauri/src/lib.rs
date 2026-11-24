//! Z-Next Mobile: de schil om de Z-App. De startpagina (www/index.html) opent de Z-App op de ERP-omgeving;
//! inloggen en alle schermen komen van de site zelf.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_delen::init())
        .run(tauri::generate_context!())
        .expect("Z-Next kon niet starten");
}
