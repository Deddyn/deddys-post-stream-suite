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

### Download YouTube

La colonna Download contiene due pulsanti: Youtube e Twitch, abilitati separatamente in base al link e all’offset della piattaforma. Entrambi propongono la durata Riot con 10 secondi prima e 20 dopo, modificabili prima del salvataggio. Un solo download alla volta.

Youtube usa il file `yt-dlp` fornito accanto a start.cmd, avviato con lo stesso Python dell’app, e FFmpeg già disponibile. Non richiede pip. Se presente, usa Deno in `%USERPROFILE%/.deno/bin/deno.exe`. Il ritaglio usa download-sections e force-keyframes-at-cuts: la ricodifica può richiedere tempo. Output MP4, nessuna sovrascrittura, configurazioni esterne yt-dlp ignorate. Il nome proposto include la piattaforma.

L’offset YouTube viene applicato all’inizio grezzo della partita, indipendentemente dall’offset Twitch. La lettura dei metadati e il download sono operazioni distinte: un VOD leggibile può comunque non essere scaricabile. Blocchi YouTube, login o dipendenze richieste da nuove versioni vengono riportati nel messaggio di errore. Non vengono letti automaticamente cookie del browser. Documentazione: https://github.com/yt-dlp/yt-dlp#usage-and-options

### Download Twitch

Inserisci Twitch VOD URL e Twitch offset (in seconds). La colonna Download sostituisce Verifica, con un pulsante per partita attivo solo con URL Twitch valido e offset intero. Non è necessario includere la partita nei timestamp per scaricarla.

Il pulsante apre un ritaglio modificabile: inizio partita meno 10 secondi, fine partita più 20 secondi. La durata proviene dai dati Riot, non dalla partita successiva. Se manca la durata, il download non viene proposto. Scegli un nuovo file MP4; i file esistenti non vengono sovrascritti. Un download alla volta, con stato nella finestra. Non chiudere l’app durante il download: il processo esterno potrebbe continuare e non verrebbe più monitorato. Un fallimento può lasciare file parziali.

Twitch offset si somma all’istante della partita rispetto all’inizio YouTube, prima dei margini. Esempio: se Twitch è partito 30 secondi prima di YouTube, usa +30; se è partito 30 secondi dopo, usa -30. Non eredita Offset (in seconds), che riguarda solo i timestamp YouTube. I due link devono riferirsi alla stessa trasmissione; l’app non verifica automaticamente l’allineamento o eventuali tagli. Controlla il primo ritaglio. Gli intervalli negativi sono limitati a zero; gli intervalli interamente precedenti al VOD vengono rifiutati.

CLI ufficiale 1.56.5 in tools/TwitchDownloaderCLI, archivio verificato con SHA-256 8b1b0695f2b1b6bf0d2535fab4b84032951cded8cf4078dfdf4d58e391c813a0. Sorgente: https://github.com/lay295/TwitchDownloader/releases/tag/1.56.5 . Usa FFmpeg già presente nella cartella Downloads/TwitchDownloaderGUI-1.56.5-Windows-x64. Il programma grafico non viene modificato. Binari esclusi da Git: su un’altra macchina occorre ripristinare questi percorsi.

La CLI seleziona la qualità migliore disponibile e usa trim Exact. Il flusso attuale supporta VOD accessibili senza OAuth; VOD privati, riservati o eliminati possono fallire. I test automatici verificano calcoli, pulsanti e argomenti del processo; un download reale richiede un VOD Twitch accessibile.

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
