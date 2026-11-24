// Z-Next Mobile: navigator.share en blob-downloads naar het deelmenu van Android (via de Kotlin-brug ZNextDelen).
(function () {
  if (window.__znextDelen) return;
  window.__znextDelen = true;

  var brug = window.ZNextDelen;
  if (!brug) return; // Niet op Android: niets doen.

  function naarBase64(blob) {
    return new Promise(function (ok, fout) {
      var lezer = new FileReader();
      lezer.onload = function () {
        var s = String(lezer.result);
        ok(s.slice(s.indexOf(",") + 1));
      };
      lezer.onerror = function () {
        fout(lezer.error);
      };
      lezer.readAsDataURL(blob);
    });
  }

  function deelBlobs(lijst, titel, tekst) {
    return Promise.all(
      lijst.map(function (b) {
        return naarBase64(b.blob).then(function (data) {
          return { naam: b.naam || "bestand", type: b.blob.type || "application/octet-stream", data: data };
        });
      })
    ).then(function (bestanden) {
      brug.deelBestanden(JSON.stringify(bestanden), titel || "", tekst || "");
    });
  }

  if (!navigator.share) {
    navigator.canShare = function (d) {
      return !!d && (!!(d.files && d.files.length) || !!d.url || !!d.text || !!d.title);
    };
    navigator.share = function (d) {
      d = d || {};
      var tekst = [d.text, d.url].filter(Boolean).join("\n");
      if (d.files && d.files.length) {
        var lijst = [];
        for (var i = 0; i < d.files.length; i++) lijst.push({ naam: d.files[i].name, blob: d.files[i] });
        return deelBlobs(lijst, d.title, tekst);
      }
      brug.deelTekst(d.title || "", tekst);
      return Promise.resolve();
    };
  }

  // <a href="blob:..." download="..."> opent in de webview niets; bied het bestand aan in het deelmenu.
  document.addEventListener(
    "click",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href^="blob:"]') : null;
      if (!a) return;
      e.preventDefault();
      fetch(a.href)
        .then(function (r) {
          return r.blob();
        })
        .then(function (blob) {
          return deelBlobs([{ naam: a.getAttribute("download") || "bestand", blob: blob }], "", "");
        });
    },
    true
  );
})();
