# Dateiverarbeitung bei mehreren Dateien

**Zuerst Freigabe:** Vor Zustimmung zum konkreten Vorschlag nur lesen und Ergebnisse im Gespräch anzeigen oder im Arbeitsspeicher halten. Die folgenden Helferaufrufe erzeugen Dateien; führe sie erst aus, wenn auch die jeweiligen Inventar-, Sicherungs- oder Diffdateien freigegeben sind. Das Skript selbst stellt keine Rückfragen; der Agent setzt die Freigabegrenze aus `SKILL.md` durch.

Der Helfer benötigt Python 3.9 oder neuer und nur dessen Standardbibliothek. Fehlt `python` auf Windows, nutze einen vorhandenen Python-Pfad; im Codex-Desktop kann `load_workspace_dependencies` den gebündelten Pfad liefern. Ohne Python lassen sich Inventar, bytegetreue Sicherung und Diff mit vorhandenen Dateitools erstellen. Dieser Helfer schreibt niemals in die geprüften Quelldateien und führt keine semantische Optimierung aus; diese erledigt der Agent nach dem Lesen.

## Inventar

Alle Wurzeln werden explizit übergeben. Lege den Elternordner der Inventar- oder Diffausgabe vorher an und wähle jeweils einen neuen Dateinamen; bestehende Ausgaben werden nicht überschrieben. Für PowerShell, mit zuvor ermittelten echten Pfaden:

```powershell
& $pythonExe $helperPath inventory --root $personalSkills --root $projectPath --out $inventoryPath
```

Ergänze für vorhandene globale Einzeldateien `--file $globalAgentsPath`, für weitere Wurzeln weitere `--root`-Argumente. Nutze `--managed-root $activePluginSkillRoot` für die im Katalog eingebundenen Pluginversionen. Inventarisiere nicht sämtliche historischen Versionen eines Caches. Argumente mit Leerzeichen als einzelne PowerShell-Variablen oder korrekt zitierte Literale übergeben, nicht als zusammengesetzte Shellbefehle.

Das JSON enthält `files`, `roots`, `errors` und `skipped`. Pro Markdown-Datei werden Pfad, Art, Kennzeichnung als verwaltet, Byteumfang, SHA-256 und Codierung erfasst. Die Dateikategorie ist ein Suchhinweis, keine abschließende Entscheidung über Inhalt oder Eigentum. Bei Teilfehlern bleibt das Inventar verfügbar, der Exitcode ist 1; lies dann `errors`. Dateien mit unbekannter Codierung oder Lesefehlern nicht blind neu speichern. Junctions und Symlinks werden ausgelassen; ist ein darüber erreichbares Ziel Teil des Auftrags, erfasse dessen verifizierten tatsächlichen Pfad gezielt.

## Sicherung vor der Bearbeitung

Lege die Laufartefakte in einem beschreibbaren Projektordner unter `.skill-optimizer-runs/<eindeutige-lauf-id>` ab, außerhalb der Skillverzeichnisse. Nutze einen separaten noch nicht vorhandenen Unterordner für die Sicherung. Speichere die explizit ausgewählten bestehenden Quelldateien als JSON-Array absoluter Pfade in einer UTF-8-Datei:

```json
["C:/Beispiel/skills/mein-skill/SKILL.md", "C:/Beispiel/projekt/AGENTS.md"]
```

```powershell
& $pythonExe $helperPath snapshot --files $selectionPath --out $newSnapshotDirectory
```

Der Helfer erzeugt nummerierte `.bak`-Dateien und `manifest.json` mit Zuordnung und Prüfsummen. Bestehende Sicherungsordner werden nicht überschrieben. Prüfe das erfolgreiche Ergebnis, bevor du Originale bearbeitest. Vergleiche den aktuellen Hash mit dem gesicherten Stand unmittelbar vor deiner Änderung; bei zwischenzeitlichen Fremdänderungen erneut lesen und mit neuer Sicherung darauf aufbauen. Erhalte die bestehende Codierung, BOM und Zeilenenden.

Lege vor dem Schreiben auch die Ausgangsversion von `agents/openai.yaml` oder anderen notwendigen Begleitdateien in derselben Auswahl ab. Der Inventarscan findet Markdown; die Sicherung akzeptiert gezielt ausgewählte Textdateien. Für neue Referenzen existiert kein Original: erfasse Pfad und Grund separat im Bericht und halte ihren Inhalt im Diff als neue Datei fest. Lösche keine bestehenden Ressourcen ohne Prüfung ihrer Nutzer und Referenzen.

## Diff und Nachweis

```powershell
& $pythonExe $helperPath diff --run $snapshotDirectory --out $diffPath
```

Lies den Diff zusätzlich zu den Rückleseprüfungen. Ein erfolgreiches Skript bestätigt Dateiverarbeitung, nicht fachliche Richtigkeit. Ergänze neue Dateien und unveränderte beziehungsweise offene Kandidaten im Bericht. Prüfe geänderte relative Verweise vom jeweiligen Dokument aus. Bei geänderter Anweisung gilt als Verhaltensprüfung, ob ein realistischer Auftrag noch vollständig erfüllt wird und ein sachfremder Auftrag den Skill nicht unnötig auslöst.

Sicherungen enthalten gegebenenfalls interne Informationen; belasse sie lokal und verlinke sie im Bericht. Für eine vom Nutzer gewünschte Wiederherstellung verwende die Zuordnung im Manifest, prüfe mögliche Änderungen seit dem Audit und stelle nur die gewünschten Originale wieder her. Es gibt keinen automatischen Restore oder pauschalen Git-Reset.
