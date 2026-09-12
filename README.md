# AstraUpdate

**Deutsch** | [English](README.en.md)

**Bestehende Skills und Markdown-Agentenanweisungen mit Codex prüfen und gezielt verbessern.**

AstraUpdate enthält den Skill **`skill-prompt-optimizer`**. Er lässt Codex vorhandene Anweisungen lesen, inhaltlich beurteilen und direkt in den Originaldateien überarbeiten. Vor Änderungen werden Sicherungen angelegt; anschließend dokumentiert ein Bericht, was geändert wurde und was offen bleibt.

Grundlage ist der OpenAI-Beitrag [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) von Eric Provencher vom 11. September 2026. Die Umsetzung ist ein eigenständiges Projekt und kein offizielles OpenAI-Produkt.

## Was wird verbessert?

Der Skill prüft unter anderem, ob Auslöser zu breit formuliert sind, Referenzen unnötig immer geladen werden oder starre Abläufe die eigentliche Aufgabe behindern. Er kann überlange Anweisungen gezielter strukturieren und unnötige Freigabe- oder Stoppschleifen auflösen. Fachregeln und bewusst gesetzte Grenzen werden dabei erhalten.

Beispiel für einen Auslöser:

```text
Vorher: Diesen CSV-Import-Skill immer bei Daten, Dateien oder Dokumenten verwenden.
Nachher: Diesen Skill für die lokale Importvorschau von Aufträgen aus CSV verwenden.
```

Ob eine Änderung sinnvoll ist, entscheidet der Agent anhand des tatsächlichen Inhalts. Es gibt keine feste Kürzungsquote und keine automatische Ersetzung aller Wörter wie „immer“ oder „muss“.

## Voraussetzungen

- Codex mit Zugriff auf die zu prüfenden lokalen Dateien und auf den installierten Skill.
- Schreibrechte für Dateien, die tatsächlich überarbeitet werden sollen.
- Optional Python **3.9 oder neuer** für das mitgelieferte Hilfsskript. Es benötigt keine zusätzlichen Python-Pakete.
- Git für die Installation über die folgenden Befehle. Alternativ kann das Repository als ZIP heruntergeladen werden, sofern Zugriff auf das Repository besteht.

Der Skill stellt keinen eigenen Modellzugang bereit und wechselt das verwendete Modell nicht. Seine Empfehlungen sind auf Astra ausgerichtet; gemeinsam genutzte Anweisungen sollen weiterhin ihre fachlichen Anforderungen erfüllen.

## Installation

### Über Codex

Gib Codex diesen Auftrag:

```text
Installiere den Skill aus https://github.com/zinolang-cell/astraupdate,
Unterordner skill-prompt-optimizer, in meinem persönlichen Skillverzeichnis.
```

Bei einem privaten Repository benötigt die verwendete GitHub-Verbindung Zugriff darauf.

### Manuell unter Windows / PowerShell

Führe die Befehle in einem Arbeitsordner aus. Das Ziel wird bewusst nicht überschrieben, wenn der Skill schon installiert ist.

```powershell
git clone https://github.com/zinolang-cell/astraupdate.git
if ($LASTEXITCODE -ne 0) { throw 'Klonen fehlgeschlagen.' }

$skillHome = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $HOME '.codex\skills'
}
$skillTarget = Join-Path $skillHome 'skill-prompt-optimizer'
if (Test-Path -LiteralPath $skillTarget) { throw 'Skill bereits vorhanden: vor einem Update sichern und vergleichen.' }
New-Item -ItemType Directory -Path $skillHome -Force | Out-Null
Copy-Item -LiteralPath '.\astraupdate\skill-prompt-optimizer' -Destination $skillTarget -Recurse
```

### Manuell unter macOS / Linux

```sh
git clone https://github.com/zinolang-cell/astraupdate.git && (
  skill_home="${CODEX_HOME:-$HOME/.codex}/skills"
  skill_target="$skill_home/skill-prompt-optimizer"
  if [ -e "$skill_target" ]; then
    echo "Skill bereits vorhanden: vor einem Update sichern und vergleichen."
    exit 1
  fi
  mkdir -p "$skill_home" && cp -R ./astraupdate/skill-prompt-optimizer "$skill_target"
)
```

Prüfe anschließend, dass `skill-prompt-optimizer/SKILL.md` im persönlichen Skillverzeichnis liegt. Wird der Skill in der laufenden Sitzung noch nicht angezeigt, öffne eine neue Codex-Sitzung beziehungsweise starte Codex neu.

## Anwendung in Codex

### Direkt prüfen und überarbeiten

```text
Nutze $skill-prompt-optimizer, um alle meine persönlichen Skills und
Markdown-Agentenanweisungen im verfügbaren Umfang zu prüfen und passende
Verbesserungen direkt umzusetzen. Erstelle Sicherungen und einen Änderungsbericht.
```

**Ein bloßer Aufruf des Skills verwendet ebenfalls den Modus „direkt umsetzen“.** Er ist keine reine Berichtsfunktion.

### Nur prüfen, nichts umschreiben

```text
Nutze $skill-prompt-optimizer für ein Audit ohne Änderungen.
Prüfe meine persönlichen Skills und die AGENTS.md dieses Projekts.
```

„Nur prüfen“ und „Dry Run“ werden ebenfalls als Auftrag ohne Änderungen an den Quelldateien behandelt. Ein Inventar oder Bericht kann dabei trotzdem angelegt werden.

### Auf ein Projekt begrenzen

```text
Nutze $skill-prompt-optimizer ausschließlich für die Skills und
Markdown-Agentenanweisungen unter C:\Projekte\MeinProjekt.
Überarbeite passende Stellen direkt und dokumentiere die Änderungen.
```

Die Beispiele sind **Nachrichten an Codex**, keine Terminalbefehle. Zusätzliche Projekte sollten ausdrücklich mit ihren Pfaden genannt werden.

## Wie läuft eine Überarbeitung ab?

1. **Umfang erfassen:** Codex findet Skills über den Skillkatalog und das Dateisystem. Ein ausdrücklich eingeschränkter Auftrag hat Vorrang. Beim umfassenden Aufruf werden persönliche Skillverzeichnisse, vorhandene globale Agentenanweisungen und das aktuelle beziehungsweise genannte Projekt berücksichtigt.
2. **Inhalte verstehen:** Beschreibungen, Anweisungen und relevante Referenzen werden gelesen. Eine gefundene Datei zählt erst nach dem Lesen als inhaltlich geprüft.
3. **Änderungen beurteilen:** Codex unterscheidet hilfreiches Fachwissen von unnötiger Prozessvorgabe. In gemischten Markdown-Dokumenten werden Agentenanweisungen gezielt betrachtet.
4. **Originale sichern:** Vor dem Schreiben werden die aktuellen Inhalte bytegetreu gesichert. Bereits vorhandene lokale Änderungen gehören zum Ausgangsstand.
5. **Direkt bearbeiten:** Sinnvolle Änderungen erfolgen an den betreffenden Stellen. Bei Bedarf entstehen verlinkte Referenzen; es wird kein identischer Optimierungsblock an jede Datei angehängt.
6. **Prüfen und berichten:** Codex liest die Ergebnisse zurück, prüft Diffs, Verweise und relevante Verhaltensfälle und dokumentiert geänderte, unveränderte und offene Dateien.

Das Ergebnis hängt von Modell, Kontext und Qualität der Ausgangsanweisungen ab. Eine bestimmte Tokenersparnis oder messbare Qualitätssteigerung wird nicht zugesichert.

## Welche Dateien gehören dazu?

| Datei oder Bereich | Behandlung |
| --- | --- |
| Eigene `SKILL.md` und zugehörige Anweisungsreferenzen | Inhaltlich prüfen und im Umsetzungsmodus passend bearbeiten |
| `AGENTS.md`, `AGENTS.override.md` und Markdown-Prompts | Anweisungen unter Beachtung ihres Geltungsbereichs prüfen |
| README, Architektur- und andere Fachdateien | Agentenanweisungen von fachlichem Inhalt unterscheiden |
| `agents/openai.yaml` | Bei geändertem Verhalten auf widersprüchliche Metadaten prüfen |
| Systemskills und aktive Plugin-Cacheversionen | Prüfen; standardmäßig Befunde und Änderungsvorschläge ausweisen, keine Cachedateien überschreiben |
| Andere Projekte | Einbeziehen, wenn sie im Auftrag ausdrücklich oder eindeutig eingeschlossen sind |

Verträge, Kundendaten, historische Protokolle und fachliche Beispiele werden nicht allein wegen ihrer Markdown-Endung umgeschrieben. Budgetgrenzen, Datenschutzanforderungen, Produktionsfreigaben und notwendige technische Abläufe bleiben erhalten. Ein Audit führt die beschriebenen Fachworkflows nicht aus und erteilt keine Freigabe für Deployments, Kampagnenänderungen oder externe Datenübertragungen.

## Das Python-Hilfsskript

[`audit_files.py`](skill-prompt-optimizer/scripts/audit_files.py) übernimmt deterministische Dateiarbeit. **Es schreibt die geprüften Originale nicht um und ruft kein Sprachmodell auf.** Die inhaltliche Optimierung übernimmt Codex anhand des Skills.

| Befehl | Funktion |
| --- | --- |
| `inventory` | Markdown-Dateien erfassen: Pfad, Kategorie, verwaltet/privat, Bytezahl, SHA-256 und Codierung |
| `snapshot` | Explizit ausgewählte Textdateien als bytegetreue `.bak`-Dateien mit Manifest sichern |
| `diff` | Gesicherte Originale mit dem aktuellen Stand vergleichen und einen Unified Diff erzeugen |

### Beispiel: manuelle Dateiverarbeitung

Die folgenden Terminalbefehle werden aus dem Repositoryordner ausgeführt. Ersetze die Beispielpfade durch tatsächlich vorhandene Pfade. Unter manchen Systemen heißt Python `python3` oder `py`.

```sh
mkdir .skill-optimizer-runs
python skill-prompt-optimizer/scripts/audit_files.py inventory --root /pfad/zum/projekt --out .skill-optimizer-runs/inventory.json
```

Mit `--root` können mehrere Wurzeln angegeben werden. `--file` ergänzt einzelne Markdown-Dateien; `--managed-root` fügt eine vollständig als verwaltet markierte Wurzel hinzu. Es gibt keine implizite Suche über die gesamte Festplatte.

Erstelle für eine Sicherung eine UTF-8-Datei `.skill-optimizer-runs/selection.json` mit den **absoluten** Pfaden der gewünschten bestehenden Dateien:

```json
[
  "/pfad/zum/projekt/AGENTS.md",
  "/pfad/zu/skills/mein-skill/SKILL.md"
]
```

Unter Windows sind beispielsweise `C:/Projekte/MeinProjekt/AGENTS.md` gültige absolute Pfade. Anschließend:

```sh
python skill-prompt-optimizer/scripts/audit_files.py snapshot --files .skill-optimizer-runs/selection.json --out .skill-optimizer-runs/snapshot
```

Nach der eigentlichen Bearbeitung durch Codex oder einen Menschen:

```sh
python skill-prompt-optimizer/scripts/audit_files.py diff --run .skill-optimizer-runs/snapshot --out .skill-optimizer-runs/changes.diff
```

Inventar und Diff benötigen vorhandene Elternordner und neue Ausgabedateinamen. Ein Snapshot benötigt ein noch nicht existierendes Zielverzeichnis. Für weitere Läufe neue Namen beziehungsweise Laufunterordner verwenden.

### Grenzen und Rückgabewerte

- Unterstützt werden UTF-8, UTF-8 mit BOM und UTF-16 mit BOM. Andere beziehungsweise uneindeutige Codierungen werden gemeldet.
- Symlinks und Windows-Junctions werden nicht verfolgt. Benötigte Ziele können nach Prüfung über ihren tatsächlichen Pfad angegeben werden.
- Unter anderem `.git`, `node_modules`, virtuelle Python-Umgebungen, Buildordner und `.skill-optimizer-runs` werden beim Inventar ausgelassen.
- Exitcode `0` bedeutet erfolgreich; `1` meldet Verarbeitungsfehler, bei `diff` auch fehlende aktuelle Dateien. Ungültige CLI-Argumente können Exitcode `2` erzeugen.
- Ein Inventar kann trotz Teilfehlern vorliegen. Deshalb immer `errors` und `skipped` lesen.
- Der Snapshot erfasst vorhandene ausgewählte Dateien. Neu angelegte Referenzen müssen zusätzlich im Bericht und Änderungsnachweis aufgeführt werden.

## Sicherungen, Bericht und Wiederherstellung

Laufartefakte werden außerhalb der Skillverzeichnisse in einem beschreibbaren Ordner unter `.skill-optimizer-runs/<lauf-id>` abgelegt. Das Manifest ordnet jeder Sicherung ihre Originaldatei und Prüfsumme zu.

Ein Bericht nennt Suchumfang, Quellenstand, tatsächliche Inhaltsprüfung, Änderungen, unveränderte Dateien, Prüfungen und verbleibende Einschränkungen. „Alle geprüft“ bedeutet alle Dateien des dokumentierten Umfangs, nicht automatisch jede Datei auf dem Rechner.

Für eine Wiederherstellung kann Codex anhand des Manifests gezielt die gewünschten Originale zurückkopieren. Zuvor müssen Änderungen seit dem Audit berücksichtigt werden. Der Helfer bietet keinen automatischen Restore und führt keinen Git-Reset aus. Sicherungen und Berichte können interne Inhalte enthalten; die mitgelieferte `.gitignore` schließt Laufartefakte vom normalen Git-Staging aus.

## Aufbau des Repositorys

```text
astraupdate/
├── README.md
├── README.en.md
├── LICENSE
├── tests/
│   └── test_audit_files.py
└── skill-prompt-optimizer/
    ├── SKILL.md
    ├── LICENSE
    ├── agents/openai.yaml
    ├── references/
    │   ├── pruefgrundlage.md
    │   └── dateiverarbeitung.md
    └── scripts/audit_files.py
```

`SKILL.md` enthält den Ablauf für Codex. Die Prüfgrundlage dokumentiert den Artikelstand, die Dateiverarbeitung erklärt die Helferaufrufe. `agents/openai.yaml` liefert Anzeigename und Beispielaufruf. Die Lizenz liegt zusätzlich im Skillordner, damit sie bei einer isolierten Installation erhalten bleibt.

## Tests

Aus dem Repositoryordner:

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

Die Tests prüfen unter anderem, dass das Inventar Originale unverändert lässt, Sicherungen bytegetreu sind, Ausschlüsse wirken und Diffs Änderungen sowie Fehler sichtbar machen. Betriebssystemspezifische Tests können übersprungen werden, wenn notwendige Rechte fehlen. Sie bestätigen die Dateiverarbeitung, nicht automatisch die Qualität jeder durch ein Modell vorgenommenen Überarbeitung.

Für eine Funktionsprüfung des Skills eignet sich zusätzlich ein isoliertes Beispielprojekt: einen passenden Auftrag und einen sachfremden Auftrag prüfen und dabei den Erhalt der Fachregeln kontrollieren.

## Updates und Lizenz

Für Updates `git pull --ff-only` im geklonten Repository ausführen, die installierte Fassung sichern und mit der neuen Fassung vergleichen. Kopiere anschließend die gewünschten aktualisierten Skilldateien in dein Skillverzeichnis. Es gibt keinen automatischen Updateprozess.

Der Code und die eigenen Anweisungen dieses Repositorys stehen unter der [MIT-Lizenz](LICENSE). Der verlinkte OpenAI-Beitrag ist eine externe Quelle und wird durch diese Lizenz nicht neu lizenziert.
