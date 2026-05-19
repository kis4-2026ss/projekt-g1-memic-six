# WebLegacy AI: PHP-to-C# Modernization Engine

**Ein Projekt von Aldin Memic & Amadin Six für KIS4 (AI-Assisted Software Engineering)**

Dieses Tool nutzt modernste KI-Methoden, um veraltete PHP-Backends automatisiert in moderne ASP.NET Core Architekturen zu transformieren. Dabei steht nicht die bloße Syntax-Übersetzung im Vordergrund, sondern die Wiederherstellung und Modernisierung der Software-Architektur.

---
👉 **[Zum detaillierten Projekt-Proposal](./Proposal.md)**

---

## 🛠️ Troubleshooting & Bekannte API-Herausforderungen

### Fehler: `503 Service Unavailable` (Modell-Überlastung)
Beim Ausführen des Tests kann es temporär zu folgendem Fehler beim API-Aufruf kommen:
```text
Error calling Gemini API: 503 UNAVAILABLE. 
This model is currently experiencing high demand. Spikes in demand are usually temporary. 
Please try again later.
```

#### Bedeutung des Fehlers
Der HTTP-Statuscode **`503 Service Unavailable`** besagt, dass die Google-Server für das angeforderte Modell (standardmäßig `gemini-flash-latest`) derzeit überlastet sind. Dieser Fehler liegt **nicht** an eurem Code oder eurer API-Konfiguration, sondern rein an der aktuellen Netzauslastung auf Google-Seite.

#### Lösungsansätze
Sollte dieser Fehler auftreten, gibt es zwei schnelle Wege, um den Test dennoch erfolgreich auszuführen:
1. **Erneutes Ausführen nach kurzer Wartezeit:** Spikes in der Nachfrage sind meist sehr kurzlebig. Ein erneuter Versuch nach 1–2 Minuten löst das Problem in den meisten Fällen bereits.
2. **Wechsel auf ein hochverfügbares Modell:** Ihr könnt in `src/utils/gemini_client.py` temporär das genutzte Modell (Zeile 18) von `gemini-flash-latest` auf eines der moderneren und weniger ausgelasteten Modelle umschreiben, wie zum Beispiel:
   * `'gemini-2.5-flash'`
   * `'gemini-2.0-flash'`
