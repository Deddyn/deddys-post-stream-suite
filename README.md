# LoL VOD Timestamps — Windows

App desktop Python/Tkinter per generare timestamp delle partite League of Legends. Account EUW preconfigurati: Deddy#616, Toni Bonji#PALLE, Bubbals#EUW. Interfaccia in italiano.

## Avvio

1. Serve Python 3.11 o successivo con Tcl/Tk. Se non presente, installalo da https://www.python.org/downloads/windows/ selezionando Tcl/Tk e Python Launcher. Nessuna installazione viene eseguita dall'app.
2. Per i fusi IANA su Windows può servire `py -m pip install tzdata`. In alternativa inserisci un offset esplicito nella data manuale: `2026-09-11 18:00:00+02:00`. L'offset esplicito prevale sul campo timezone.
3. Apri `start.cmd`, oppure esegui `py -m vodstamp` dalla cartella del progetto. Il launcher cerca anche il Python incluso in Codex, se disponibile: su questa macchina è stato usato per i test e non è servita un'installazione. Per uso indipendente da Codex è consigliata un'installazione Python standard.
4. Incolla Riot Personal API Key nel campo mascherato. La chiave resta solo nella memoria del processo. Puoi anche fornire `RIOT_API_KEY` nell'ambiente del processo, senza inserirla in file del repository.
5. La chiave YouTube è facoltativa: se lasci il campo vuoto, l'app cerca inizio e fine nei metadati pubblici della pagina del VOD, senza scaricare il video. Questa lettura non ufficiale può fallire per consenso, login, blocchi o modifiche YouTube. In quel caso usa Manuale oppure abilita YouTube Data API v3 nel tuo progetto Google Cloud e inserisci una API key limitata a tale API nel campo dedicato (o nell'ambiente `YOUTUBE_API_KEY`).
6. Inserisci URL YouTube di una live conclusa, oppure scegli Manuale e indica inizio e durata (12 ore predefinite).
7. Genera, controlla le righe, includi/escludi con Spazio o i pulsanti. Doppio clic modifica il titolo; doppio clic nella prima colonna cambia l'inclusione. Copia negli appunti.

Non incollare le chiavi in chat, sorgenti o comandi salvati nella cronologia. Le preferenze non sensibili vengono salvate quando premi Genera, in `%LOCALAPPDATA%\VodTimestamps\settings.json`, fuori dal repository. Nessuna chiave viene salvata né scritta nei log. Le chiavi vengono inviate esclusivamente via HTTPS ai rispettivi provider. Se vuoi conservarle tra sessioni, gestiscile esternamente; l'app non include un archivio persistente dei segreti.

## Comportamento

### Diagnostica

I pulsanti **Test Riot** e **Test YouTube**, accanto alle chiavi, eseguono richieste reali usando i valori attualmente inseriti. Non salvano le chiavi e non modificano la tabella dei risultati.

Test Riot controlla Account-v1, cronologia Match-v5 e, se disponibile, il dettaglio di una partita recente per ogni account. Si ferma al primo errore e indica il passaggio preciso. Non usa la data del VOD: una cronologia vuota non implica una chiave errata. Test YouTube controlla l'accesso ai metadati live del VOD inserito. Il rapporto si può copiare senza includere chiavi o risposte grezze.

- Con chiave, YouTube usa `liveStreamingDetails.actualStartTime` e `actualEndTime`; senza chiave cerca `liveBroadcastDetails.startTimestamp` e `endTimestamp` nella pagina pubblica. Richiede entrambi gli orari, con timezone e fine successiva all'inizio. Non usa data di pubblicazione né orari pianificati. Se i dati mancano mostra un errore; non inventa un intervallo. Anche Test YouTube funziona senza chiave.
- Account-v1 e Match-v5 usano il routing EUROPE, corretto per gli account EUW. Non viene applicato alcun filtro queue. Gli ID sono paginati, deduplicati fra gli account e poi ordinati per inizio partita.
- Include partite con inizio nell'intervallo `[inizio, fine)`. Una partita iniziata prima della live è esclusa, anche se termina durante la live. Una partita iniziata nella live è inclusa anche se termina dopo. Sono disponibili soltanto i match restituiti da Riot: VOD molto vecchi possono non avere una cronologia recuperabile.
- Timestamp basato su `gameStartTimestamp`, non sull'inizio della champion select. Correzione in secondi: positiva sposta i timestamp avanti, negativa indietro. Valori negativi finali vengono limitati a zero e segnalati.
- Su Summoner's Rift CLASSIC cerca un unico avversario con `teamPosition` corrispondente. È una stima Riot, non una verifica del lane swap reale. In caso incerto usa `Champion vs ?` e chiede revisione. ARAM e altre modalità usano `Champion - gameMode`.
- Se più account configurati sono nello stesso match, viene creata una sola riga e ha priorità il primo account configurato presente. Una nota segnala di verificare la prospettiva.
- Conversioni UTC con timezone IANA. Ore ambigue o inesistenti durante il cambio ora vengono rifiutate: inserisci un offset esplicito.
- Richieste in background, timeout 25 secondi, massimo quattro tentativi per rate limit ed errori server. Attese Retry-After superiori a 120 secondi richiedono un nuovo tentativo manuale. Un errore interrompe la generazione senza mostrare un elenco parziale come completo.
- Live ritagliate, pause o differenze tra stream e VOD possono richiedere correzioni. Un offset costante non risolve tagli multipli. Verifica il primo timestamp sul video.
- Il testo copiato è una lista timestamp. Per attivare i capitoli YouTube valgono ulteriori requisiti della piattaforma; l'app non aggiunge un capitolo iniziale artificiale.

## Test e struttura

Esegui `py -m unittest discover -s tests -v`. Test offline con risposte simulate: nessuna chiave richiesta, nessuna chiamata esterna.

- `vodstamp/core.py`: date, intervalli, matchup e formattazione.
- `vodstamp/api.py`: HTTP, YouTube e Riot.
- `vodstamp/settings.py`: preferenze senza segreti.
- `vodstamp/gui.py`: GUI e worker.
- `tests/`: regressioni logiche, API simulate e smoke test GUI.

Per verificare le API reali, configura localmente entrambe le chiavi e usa un VOD recente con una partita nota. Confronta orario e matchup con il VOD. Questa verifica richiede credenziali dell'utente e non è inclusa nei test offline.

## Fonti

- https://developer.riotgames.com/apis/ — Account-v1 e Match-v5.
- https://github.com/RiotGames/developer-relations/issues/554 — limiti di teamPosition.
- https://developers.google.com/youtube/v3/docs/videos — metadati live.
- https://developers.google.com/youtube/v3/docs/videos/list — endpoint videos.list.

Progetto personale non affiliato né approvato da Riot Games o YouTube.
