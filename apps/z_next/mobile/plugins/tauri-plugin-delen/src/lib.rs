//! Delen: bestanden uit de Z-App openen en delen via Android.
//!
//! De Android-webview doet zelf niets met downloads en kent `navigator.share` niet. Deze plugin vult dat aan:
//! - een download (bijv. "Bestand openen / downloaden") haalt de Kotlin-kant op met de sessie van de webview en
//!   biedt hem aan in "Openen met";
//! - `navigator.share({ files, title, text, url })` uit de Z-App opent het deelmenu (WhatsApp, mail, Drive, ...);
//! - een link naar een `blob:`-adres met `download` gaat ook naar het deelmenu.
//!
//! Het JavaScript (`delen.js`) draait in elke pagina, maar doet alleen iets als de Kotlin-brug `ZNextDelen`
//! bestaat, dus alleen op Android. De brug accepteert alleen verzoeken van de Z-App en de startpagina.

use tauri::{
    plugin::{Builder, TauriPlugin},
    Runtime,
};

const DELEN_JS: &str = include_str!("delen.js");

pub fn init<R: Runtime>() -> TauriPlugin<R> {
    Builder::new("delen")
        .js_init_script(DELEN_JS.to_string())
        .setup(|_app, _api| {
            #[cfg(target_os = "android")]
            _api.register_android_plugin("eu.openaec.znext.delen", "DelenPlugin")?;
            Ok(())
        })
        .build()
}
