# Z-Next Mobile

Z-Next als app voor Android en iOS, gebouwd met **Tauri 2 mobile** (dezelfde basis als `supercloud-mobile`).

## Hoe de app werkt (versie 0.1)

De app is een schil om de Z-App. De startpagina (`www/index.html`) opent `https://erp.voorbeeld.nl/zapp` in de
webview van de app. Inloggen gaat met de gewone ERPNext-login; alle schermen komen van de site. Een wijziging aan de
Z-App staat dus meteen ook in de app, zonder nieuwe app-versie. Zonder internet toont de startpagina een melding met
"Opnieuw proberen".

De Z-App krijgt geen toegang tot Tauri-functies (`capabilities/default.json` staat alleen `core:default` toe).

## Bouwen

De Android- en iOS-projecten (`src-tauri/gen/`) staan niet in de repo; de workflow
[`.github/workflows/mobile.yml`](../.github/workflows/mobile.yml) maakt ze bij elke build opnieuw aan.

| Platform | Waar | Resultaat |
|---|---|---|
| Android | GitHub Actions (ubuntu) | debug-APK (arm64) als artifact `z-next-android-debug-apk` |
| iOS | GitHub Actions (macOS) | simulator-build (zonder ondertekening) als artifact `z-next-ios-simulator-app` |

Lokaal (met Android SDK, NDK en Java 17, of op een Mac met Xcode):

```bash
cd mobile
npm ci
npm run android:init && npm run icon
npm run android:apk
```

## Installeren op een Android-telefoon

Download het artifact bij de laatste run van "Mobiele app" in GitHub Actions, pak het uit en zet de `.apk` op de
telefoon. Sta "installeren uit onbekende bron" toe voor de app waarmee je hem opent.

## Nog te doen

- **iPhone-testversie op een echt toestel:** een Apple Developer-account (team-ID) en ondertekening; daarna via
  TestFlight.
- **Google Play en App Store:** ondertekende release-builds, winkelvermelding en privacyverklaring.
- **Meer dan een schil:** pushmeldingen, camera direct naar een project, en de mobiele schermen uit de README van
  Z-Next (projecttegels, uren per week, tabbalk).
