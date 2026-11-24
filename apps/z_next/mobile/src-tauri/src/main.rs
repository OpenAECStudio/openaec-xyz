// Op Windows geen extra consolevenster in een release-build.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    z_next_mobile_lib::run()
}
