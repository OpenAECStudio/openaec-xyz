package eu.openaec.znext.delen

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.Intent
import android.net.Uri
import android.util.Base64
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.MimeTypeMap
import android.webkit.URLUtil
import android.webkit.WebView
import android.widget.Toast
import androidx.core.content.FileProvider
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Plugin
import org.json.JSONArray
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/** Eigen FileProvider-klasse, zodat hij niet botst met de FileProvider van de app (camera). */
class DelenFileProvider : FileProvider()

/**
 * Downloads uit de webview openen ("Openen met") en navigator.share naar het deelmenu van Android.
 * Bestanden komen tijdelijk in de cache (map `gedeeld/`) en worden met een content://-adres gedeeld.
 */
@TauriPlugin
class DelenPlugin(private val activity: Activity) : Plugin(activity) {
  companion object {
    /** Alleen de Z-App en de eigen startpagina mogen de brug gebruiken. */
    private val TOEGESTANE_HOSTS = setOf("erp.voorbeeld.nl", "tauri.localhost")
  }

  private lateinit var webView: WebView

  override fun load(webView: WebView) {
    this.webView = webView
    webView.addJavascriptInterface(Brug(), "ZNextDelen")
    webView.setDownloadListener { url, userAgent, contentDisposition, mimetype, _ ->
      if (url.startsWith("https://") || url.startsWith("http://")) {
        downloadEnOpen(url, userAgent, contentDisposition, mimetype)
      }
    }
  }

  private fun map(): File = File(activity.cacheDir, "gedeeld").apply { mkdirs() }

  private fun uriVoor(bestand: File): Uri =
    FileProvider.getUriForFile(activity, activity.packageName + ".delen", bestand)

  private fun veiligeNaam(naam: String): String =
    naam.replace(Regex("[\\\\/:*?\"<>|]"), "_").trim().ifEmpty { "bestand" }

  private fun mimeVoor(naam: String, gegeven: String?): String {
    if (!gegeven.isNullOrBlank() && gegeven != "application/octet-stream") return gegeven
    val ext = MimeTypeMap.getFileExtensionFromUrl(naam.replace(" ", "_")).lowercase()
    return MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
  }

  private fun melding(tekst: String) {
    activity.runOnUiThread { Toast.makeText(activity, tekst, Toast.LENGTH_SHORT).show() }
  }

  /** Voert [actie] uit als de pagina in de webview van een toegestane host komt. */
  private fun alsToegestaan(actie: () -> Unit) {
    activity.runOnUiThread {
      val host = Uri.parse(webView.url ?: "").host
      if (host in TOEGESTANE_HOSTS) actie()
    }
  }

  // --- Downloads ------------------------------------------------------------------------------------------------

  private fun downloadEnOpen(url: String, userAgent: String?, contentDisposition: String?, mimetype: String?) {
    val naam = veiligeNaam(URLUtil.guessFileName(url, contentDisposition, mimetype))
    melding("$naam wordt opgehaald…")
    thread {
      try {
        val verbinding = URL(url).openConnection() as HttpURLConnection
        CookieManager.getInstance().getCookie(url)?.let { verbinding.setRequestProperty("Cookie", it) }
        userAgent?.let { verbinding.setRequestProperty("User-Agent", it) }
        verbinding.connectTimeout = 20_000
        verbinding.readTimeout = 60_000
        if (verbinding.responseCode !in 200..299) {
          melding("Ophalen mislukt (${verbinding.responseCode})")
          return@thread
        }
        val bestand = File(map(), naam)
        verbinding.inputStream.use { invoer -> bestand.outputStream().use { invoer.copyTo(it) } }
        val type = mimeVoor(naam, verbinding.contentType?.substringBefore(';') ?: mimetype)
        activity.runOnUiThread { openMet(uriVoor(bestand), type, naam) }
      } catch (e: Exception) {
        melding("Ophalen mislukt: ${e.message}")
      }
    }
  }

  /** "Openen met" (bijv. een PDF-app); zonder app voor dit type: het deelmenu. */
  private fun openMet(uri: Uri, type: String, naam: String) {
    val bekijk = Intent(Intent.ACTION_VIEW).apply {
      setDataAndType(uri, type)
      addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    try {
      activity.startActivity(Intent.createChooser(bekijk, "Openen met"))
    } catch (e: ActivityNotFoundException) {
      deel(listOf(uri), type, naam, "")
    }
  }

  // --- Deelmenu -------------------------------------------------------------------------------------------------

  private fun deel(uris: List<Uri>, type: String, titel: String, tekst: String) {
    val stuur = if (uris.size == 1) {
      Intent(Intent.ACTION_SEND).apply { putExtra(Intent.EXTRA_STREAM, uris[0]) }
    } else {
      Intent(Intent.ACTION_SEND_MULTIPLE).apply { putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(uris)) }
    }
    stuur.type = type
    if (titel.isNotBlank()) {
      stuur.putExtra(Intent.EXTRA_SUBJECT, titel)
      stuur.putExtra(Intent.EXTRA_TITLE, titel)
    }
    if (tekst.isNotBlank()) stuur.putExtra(Intent.EXTRA_TEXT, tekst)
    if (uris.isNotEmpty()) {
      val clip = ClipData.newRawUri(titel, uris[0])
      uris.drop(1).forEach { clip.addItem(ClipData.Item(it)) }
      stuur.clipData = clip
      stuur.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    activity.startActivity(Intent.createChooser(stuur, "Delen"))
  }

  inner class Brug {
    /** [json]: lijst van { naam, type, data (base64) }. */
    @JavascriptInterface
    fun deelBestanden(json: String, titel: String, tekst: String) {
      alsToegestaan {
        thread {
          try {
            val lijst = JSONArray(json)
            val uris = ArrayList<Uri>()
            var type = ""
            for (i in 0 until lijst.length()) {
              val item = lijst.getJSONObject(i)
              val naam = veiligeNaam(item.optString("naam", "bestand"))
              val bestand = File(map(), naam)
              bestand.writeBytes(Base64.decode(item.getString("data"), Base64.DEFAULT))
              val t = mimeVoor(naam, item.optString("type"))
              type = if (type.isEmpty() || type == t) t else "*/*"
              uris.add(uriVoor(bestand))
            }
            activity.runOnUiThread { deel(uris, type.ifEmpty { "*/*" }, titel, tekst) }
          } catch (e: Exception) {
            melding("Delen mislukt: ${e.message}")
          }
        }
      }
    }

    @JavascriptInterface
    fun deelTekst(titel: String, tekst: String) {
      alsToegestaan { deel(emptyList(), "text/plain", titel, tekst) }
    }
  }
}
