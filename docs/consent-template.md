# Einwilligungserklärung — Vorlage

> **Diese Datei ist eine unverbindliche Muster-Vorlage.** Sie enthält nur
> Platzhalter in eckigen Klammern (z. B. `[Name des Betreuers]`) und **keine**
> echten Daten. Vor dem Einsatz an die eigene Situation anpassen.

## Hinweis: Vorlage, keine Rechtsberatung

Dies ist eine **unverbindliche Muster-Vorlage** und **keine Rechtsberatung**. Sie
erhebt keinen Anspruch auf Vollständigkeit oder Rechtsgültigkeit und ersetzt keine
anwaltliche oder datenschutzfachliche Prüfung. Lassen Sie die Erklärung im Zweifel
**anwaltlich bzw. datenschutzfachlich prüfen** und passen Sie sie an Ihre konkrete
Situation an, bevor Sie sie verwenden. Erst die geprüfte, ausgefüllte Fassung
entfaltet Wirkung — dieses Muster für sich genommen nicht.

Es werden hier **besondere Kategorien personenbezogener Daten** verarbeitet
(Gesundheitsdaten, ggf. eines Kindes — Art. 9 DSGVO). Eine dokumentierte
Einwilligung sollte vorliegen, bevor eine Fallakte angelegt wird. Bei Daten eines
Kindes erteilen die **Sorgeberechtigten** die Einwilligung.

---

## Zweck der Verarbeitung

Die Daten werden ausschließlich zur **privaten medizinischen
Recherche-Unterstützung** zu einem seltenen bzw. komplexen Krankheitsfall
verarbeitet. Konkret: das Strukturieren der Krankengeschichte und das Nachschlagen
in öffentlichen medizinischen Wissensquellen, um Hypothesen für das Gespräch mit
den behandelnden Ärztinnen und Ärzten vorzubereiten.

Dies ist **keine Diagnose** und **kein Medizinprodukt**. Die Ergebnisse ersetzen
keine ärztliche Beurteilung und treffen keine Behandlungsentscheidung.

## Welche Daten

Verarbeitet werden ausschließlich **pseudonymisierte** Daten:

- die **Krankengeschichte in pseudonymisierter Form** — symptombezogen und
  HPO-codiert, mit **Initialen statt Klarname** und **Alter statt exaktem
  Geburtsdatum**;
- gegebenenfalls **zusammengefasste Ergebnisse** einer genetischen Auswertung
  (Befund-Zusammenfassung), **nicht** das genetische Rohgenom.

Folgendes wird **nicht** verarbeitet: Klarname, vollständiges Geburtsdatum,
Anschrift, Versichertennummer oder andere unmittelbar identifizierende Angaben.

Betroffene Person (pseudonymisiert): `[Initialen der betroffenen Person]`,
Alter: `[Alter in Jahren]`.

## Wo gespeichert

Die Fallakte liegt in einem **lokalen bzw. geteilten, verschlüsselten Ordner**
(z. B. einer **verschlüsselten** Dropbox) auf dem Gerät der betreuenden Person.
Es gibt **keinen zentralen Rechner** und **keine Cloud-Datenbank**, in der die Akte
zentral gespeichert würde.

Genetische **Rohdaten (VCF)** verlassen das lokale Gerät **nicht** und werden
ausschließlich lokal ausgewertet.

## Verarbeitung über die Claude-API

Zur Beantwortung von Fragen werden die Inhalte des Chats **transient** an die
Claude-API von Anthropic übertragen und dort zur Erzeugung der Antwort verarbeitet.
Dazu ist wichtig:

- **Anthropic trainiert seine Modelle nicht auf den über die API übertragenen
  Inhalten.**
- Durch die **Pseudonymisierung** enthalten die übertragenen Inhalte **keinen
  Klarnamen** und kein exaktes Geburtsdatum.
- Genetische Rohdaten (VCF) werden **nicht** an die Claude-API übertragen.

## Pseudonymisierung

Vor dem Anlegen der Akte werden die Daten pseudonymisiert:

- **Initialen statt Klarname** (z. B. `[Initialen]` statt des vollständigen Namens);
- **Alter statt Geburtsdatum** (z. B. „7 Jahre" statt eines exakten Datums);
- Symptome werden, soweit möglich, als **HPO-Codes** erfasst statt als Freitext mit
  identifizierenden Details.

Ziel ist **Datensparsamkeit**: Es werden nur die Angaben verarbeitet, die für die
Recherche tatsächlich nötig sind, und so wenig identifizierende Information wie
möglich.

## Rechte (Widerruf, Löschung)

Die einwilligende Person hat insbesondere das Recht:

- die Einwilligung **jederzeit zu widerrufen** (der **Widerruf** wirkt für die
  Zukunft und ist ohne Angabe von Gründen möglich);
- auf **Löschung** der Akte (der gesamte Ordner bzw. die Fallakte wird gelöscht);
- auf **Auskunft** über die verarbeiteten Daten;
- auf **Berichtigung** unrichtiger Daten.

Ein **Widerruf** oder eine verlangte **Löschung** wird umgesetzt, indem die
betreffende Fallakte und die zugehörigen lokalen Verarbeitungsspuren entfernt werden.

## Aufbewahrung

Die Akte wird nur so lange aufbewahrt, wie es für den oben genannten Zweck
erforderlich ist, längstens bis `[Aufbewahrungsfrist, z. B. Abschluss der Recherche]`.
Bei **Widerruf** der Einwilligung oder Wegfall des Zwecks wird die Akte
**gelöscht**.

---

## Einwilligung

Ich/Wir willige(n) in die oben beschriebene Verarbeitung der pseudonymisierten
Daten zu den genannten Zwecken ein. Ich/Wir habe(n) den Hinweis gelesen, dass es
sich um eine private Recherche-Unterstützung handelt und **nicht** um eine Diagnose.

| Feld | Eintrag |
|---|---|
| Ort | `[Ort]` |
| Datum | `[Datum]` |
| Name der/des Sorgeberechtigten | `[Name der/des Sorgeberechtigten]` |
| Betreuende Person (Kurator) | `[Name des Betreuers]` |
| Unterschrift | `[Unterschrift]` |
