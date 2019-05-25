# Beabsichtigte Bugs:
- "schön":
	- pwned-passwords-api wird nach jedem zeichen gefragt, nicht einmal am ende der eingabe -> passwort aus hashprefixen rekonstruierbar
	- xss durch known plaintext. fixbar durch csp-header

- "ḧässlich", gerade nicht (absichtlich) eingebaut
	- StorageClient.encrypt verwendet immer den selben iv (globale variable)
	- xss durch fehlermeldung
