# Datenschutzerklärung

## 1. Einleitung
Willkommen bei „Waffensachkunde²“. Der Schutz Ihrer persönlichen Daten ist uns wichtig. Nachfolgend informieren wir Sie, welche Daten wir erheben, wofür wir sie verwenden und welche Rechte Sie haben.

---

## 2. Verantwortliche Stelle
Verantwortlich für die Datenverarbeitung ist
[Ihr Name oder Firmenname]
[Adresse]
[E-Mail-Adresse]

---

## 3. Erhebung und Verwendung personenbezogener Daten

### 3.1 Registrierung und Authentifizierung
Bei der Erstellung eines Benutzerkontos erheben wir:

- Ihren gewählten Benutzernamen inklusive vierstelliger ID („YOYO-ID“)
- Ihr Passwort (wird sicher gehasht gespeichert)
- Ihre E-Mail-Adresse (optional)

Diese Daten verwenden wir, um Ihre Anmeldung zu ermöglichen und Ihre Identität zu schützen. Nach erfolgreichem Login erhalten Sie sogenannte JSON-Web-Tokens, die wir für Ihren Sitzungsstatus und autorisierte API-Aufrufe einsetzen.

### 3.2 Lern- und Prüfungsdaten
Während Sie in der App lernen oder Prüfungen absolvieren, erfassen wir:

- Ihre Antworten auf jede Frage
- Ob Ihre Auswahl korrekt war
- Statistiken wie Anzahl beantworteter Fragen, Fortschritt und Trefferquote

Diese Informationen speichern wir lokal auf Ihrem Gerät (in SharedPreferences und SQLite) und – sofern Sie eingeloggt sind – auch auf unserem Backend-Server in einer MongoDB-Datenbank. So können Sie Ihre Fortschritte geräteübergreifend fortsetzen und Ihre Leistungsentwicklung nachvollziehen.

### 3.3 Online-Spiele und Freundesfunktionen
Für den Mehrspielermodus erheben und verwenden wir:

- Ihre Freundeslisten und Freundschaftsanfragen
- Spiel-Einladungen und offene Spiele
- Spielstände, Antworten und Ergebnisse
- Echtzeit-Benachrichtigungen per WebSocket

Zweck ist die Organisation und Durchführung von Duellen mit anderen Nutzern. Die beteiligten Daten werden ausschließlich für diese Spielfunktionen gespeichert.

### 3.4 Chat-Benachrichtigungen
Sofern Sie Chat-Funktionen nutzen (Zählen ungelesener Nachrichten), erfassen wir lediglich die Anzahl ungelesener Mitteilungen, um Ihnen eine Benachrichtigung einzublenden. Der Inhalt der Nachrichten wird dabei nicht weiterverarbeitet, sofern Sie in der App keine Chatnachrichten versenden.

### 3.5 Log-Daten und Server-Protokolle
Auf unserem Server protokollieren wir alle Zugriffe, Fehlermeldungen und Systemereignisse in rotierenden Log-Dateien. Dies dient der Stabilität, Sicherheit und Fehleranalyse unseres Systems.

---

## 4. Weitergabe und Übermittlung von Daten

- Eine Weitergabe an externe Dienstleister (z. B. Werbe- oder Analyseanbieter) findet nicht statt.
- Innerhalb unseres Systems erhalten lediglich unsere eigenen Backend-Dienste und Datenbanken Zugriff.
- Ausgenommen davon ist die Übermittlung von Echtzeit-Benachrichtigungen über unser Socket-System, das ebenfalls auf unseren Servern gehostet ist.

---

## 5. Speicherdauer

- Ihre Kontoinformationen bleiben bestehen, bis Sie Ihr Konto löschen.
- Lern- und Spiel-Daten werden dauerhaft in der Datenbank vorgehalten, um Ihre Historie und Statistiken abzubilden.
- Log-Dateien behalten wir für begrenzte Zeit zur Fehleranalyse; ältere Protokolle werden automatisch gelöscht.

---

## 6. Technische und organisatorische Maßnahmen

- **Verschlüsselung**: Ihre Daten werden über HTTPS (TLS) und WSS übertragen.
- **Passwortschutz**: Passwörter werden mit Argon2-Hashing sicher gespeichert, nicht im Klartext.
- **Zugriffsschutz**: JSON-Web-Tokens regeln den Zugriff auf geschützte Endpunkte.
- **Server-Härtung**: Unsere Datenbank ist durch Anwendungskonfiguration und Firewall geschützt.

---

## 7. Ihre Rechte
Sie haben jederzeit das Recht auf:

- Auskunft über die bei uns gespeicherten Daten
- Berichtigung unrichtiger Daten
- Löschung Ihrer Daten (sofern keine gesetzlichen Aufbewahrungsfristen entgegenstehen)
- Einschränkung der Verarbeitung
- Datenübertragbarkeit
- Widerruf erteilter Einwilligungen

Zur Ausübung Ihrer Rechte oder bei Fragen zum Datenschutz wenden Sie sich bitte an:
[Datenschutz-Kontakt: E-Mail-Adresse]

---

## 8. Änderungen dieser Erklärung
Wir behalten uns vor, diese Datenschutzerklärung bei Bedarf anzupassen. Bitte prüfen Sie sie regelmäßig. Die jeweils aktuelle Version finden Sie in der App unter **Einstellungen → Datenschutz**.

---

# Privacy Policy

## 1. Introduction
Welcome to “Waffensachkunde²”. Protecting your personal data is important to us. Below, we explain what information we collect, how we use it, and what rights you have.

## 2. Data Controller
The entity responsible for data processing is:
[Your Name or Company Name]
[Address]
[E-mail Address]

## 3. Collection and Use of Personal Data

### 3.1 Registration and Authentication
When you create an account, we collect:

- Your chosen username (including a four-digit suffix)
- Your password (securely hashed)
- Your e-mail address (optional)

We use these details to enable your login and protect your identity. After successful authentication, you receive JSON Web Tokens that authorize your requests to our backend.

### 3.2 Learning and Exam Data
As you learn or take practice exams in the app, we record:

- Your answers to each question
- Whether your selections were correct
- Statistics such as answered question count, progress, and accuracy

This information is stored locally on your device (SharedPreferences and SQLite) and—if you are logged in—also on our server’s MongoDB database. This allows you to resume progress across devices and review your performance over time.

### 3.3 Online Games and Friends Features
For the multiplayer mode, we collect and use:

- Your friends list and pending friend requests
- Invitations and open games
- Game states, answers, and results
- Real-time notifications via WebSocket

These data are used solely to host and manage duels with other users.

### 3.4 Chat Notifications
If you use any chat-related features, we only count how many unread messages you have to display a notification badge. We do not process the content of chat messages beyond this count.

### 3.5 Log Data and Server Logs
Our server logs record all requests, errors, and system events in rotating log files. This helps us maintain system stability, diagnose issues, and ensure security.

## 4. Data Sharing and Transfer
- We do not share your personal data with external advertising or analytics providers.
- Only our own backend services and databases have access.
- Real-time notifications are transmitted via our own WebSocket infrastructure.

## 5. Data Retention
- Account information is retained until you delete your account.
- Learning and game data remain stored to preserve your history and statistics.
- Log files are kept for a limited period for troubleshooting and then automatically purged.

## 6. Security Measures
- **Encryption**: All data is transmitted over HTTPS and WSS (TLS).
- **Password Protection**: Passwords are hashed using Argon2, never stored in plain text.
- **Access Control**: JSON Web Tokens secure all protected API endpoints.
- **Server Hardening**: Our database and application servers are protected by firewalls and security best practices.

## 7. Your Rights
You have the right to:

- Request access to your stored data
- Correct any inaccuracies
- Request deletion of your data (subject to legal retention requirements)
- Restrict processing of your data
- Obtain your data in a portable format
- Withdraw any consent you have given

To exercise these rights or for any privacy-related inquiries, please contact:
[Data Protection Contact E-mail]

## 8. Changes to This Privacy Policy
We may update this policy as needed. Please review it periodically. The latest version is always available in the app under **Settings → Privacy Policy**.
