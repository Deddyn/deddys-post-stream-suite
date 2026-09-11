# LoL VOD Timestamps — Windows

## Avvio

Apri start.cmd. Serve Python 3.11+ con Tkinter e tzdata; il launcher supporta anche il runtime incluso in Codex.

Metti soltanto la chiave Riot nel file `Riot API.txt` accanto a start.cmd, salvato in UTF-8. L’app legge il file all’avvio e prima di ogni generazione o test Riot. Il campo è mascherato e non modificabile: per cambiare chiave modifica il file. Il file è escluso da Git, ma resta un file locale in chiaro: non includerlo quando condividi la cartella.

1. Inserisci il link YouTube del VOD pubblico di una live conclusa.
2. Premi Test YouTube per compilare Start ed End, oppure direttamente Genera timestamp.
3. Controlla le righe e modifica i titoli con doppio clic. Spazio include/esclude le righe.
4. Premi Copia.

Start ed End sono automatici e non modificabili, in formato GG-MM-AAAA HH:MM:SS, nella timezone indicata (Europe/Rome predefinita). Offset (in seconds) sposta i timestamp: positivo avanti, negativo indietro. La chiave YouTube e la durata manuale non sono richieste.

Nessuna preferenza viene caricata o salvata. URL, Start, End e risultati ripartono vuoti; offset, timezone e i tre account EUW ripartono dai valori predefiniti. Gli eventuali vecchi settings.json non vengono più utilizzati.

## Diagnostica e limiti

Test Riot verifica Account-v1, cronologia e dettaglio Match-v5 per gli account preconfigurati Deddy#616, Toni Bonji#PALLE e Bubbals#EUW. I rapporti non contengono chiavi. I test non salvano risultati o preferenze.

YouTube viene letto tramite i metadati pubblici liveBroadcastDetails della pagina, senza scaricare video né eseguire script. Servono startTimestamp ed endTimestamp validi. Consenso, login, blocchi o modifiche della pagina possono impedire la lettura: l’app segnala il problema senza inventare orari. Non viene usata la data di pubblicazione.

Tutte le queue sono incluse. Gli ID vengono paginati, deduplicati e ordinati. Sono incluse le partite iniziate nell’intervallo [Start, End), usando gameStartTimestamp. Match precedenti alla live sono esclusi. Riot potrebbe non restituire cronologie molto vecchie.

Su Summoner’s Rift CLASSIC il matchup usa teamPosition: è una stima Riot e può non riflettere lane swap. In caso incerto compare Champion vs ?. Altre modalità usano Champion - modalità. Più account nello stesso match producono una sola riga, con priorità al primo account configurato presente e una nota di verifica.

VOD ritagliati possono richiedere un offset; tagli multipli non si correggono con un unico offset. Il formato copiato è una lista timestamp, senza capitolo iniziale artificiale.

## Test

Dalla cartella: `py -3 -m unittest discover -s tests -v`. Test offline con credenziali fittizie. I test GUI richiedono Tkinter. Le API reali si verificano con i pulsanti dell’app.

Moduli: core.py (match e date), api.py (API), youtube_public.py (pagina pubblica), credentials.py (file chiave), diagnostics.py (test API), gui.py (interfaccia). settings.py rimane solo per compatibilità con i test precedenti, non è usato dall’app.

Fonti: https://developer.riotgames.com/apis/ e https://github.com/yt-dlp/yt-dlp/issues/489

Progetto personale non affiliato a Riot Games o YouTube.
