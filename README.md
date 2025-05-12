# Documentation Stucture

Journal Documentation Structure
Consiglio: genera un repo vuoto, e iniserisci questo repo come un sottomodulo git, dopo potrai inizializzare la tua struttura del journal con il comando `--init` garantendo una struttura stabile. Questo ti permette anche di avere gli script e le tue note separate.

# Struttura del progetto

0. **REGOLA FONDAMENTALE DELLE NOTE:** I nomi delle note devono essere tutti <span style="color:red">_date_</span>, le cifre separate da `-`. I nomi delle note sono **TUTTI** descrittivi del loro albero di posizione:

   _es:_

   ```bash
   myjournal/
   ├── main-index.md
   ├── 2024/
   │   ├── weeks/
   │   ├── 2024-04-27.md
   │   ├── 2024-05-2.md
   │   └── 2024-05-31.md
   ├── 2025/
   │   ├── weeks/
   │   └── 2024-01-31.md
   └── YYYY/
       ├── weeks/
       │   └── YYYYweeklyWW.md
       └── YYYY-MM-DD.md
   ```

   In Questo modo la ricerca dei file e dei loro contenuti si semplifica e semplifica l'utilizzo anche di eventuali script che possono sfruttare il nome per eventuali automazioni.

   > <span style="color: red;">ATT!:</span> Ogni nuova pagina aggiunta viene inserita direttamente nell'indice totale (`main-index.md`) se viene creata mediante l'apposito comando `-n --new` altrimenti lanciare `-u --update` per aggiornare l'indice automaticamente.

1. `main-index.md` e `tags-index`: Questi files contengono l'indice di tutta la struttura, andranno a linkare tutte le pagine del progetto in modo da poterle trovare facilmente nel tempo divise per anni e per tags.

2. **myjournal:** è il vault contenente tutte le note, i nomi delle note sono divisi per anno attraverso sottocartelle. Mediante i nomi strutturati come sopra vengono automaticamente ordinati alfabeticamente quindi giá facilmente individuabili.

3. **Assets:** La cartella assets contiene tutti gli allegati (documenti e immagini) utili alle varie note, dentro la cartella `assets/YYYY/` dove `YYYY` sono l'anno a cui fanno riferimento. ci sono i relativi docs, imgs, ... la struttura della cartella `assets/` deve essere identica a quella fuori in modo da mantenere semplice il ritrovamento dei file e documenti salvati.

4. **JournalScript:** Questo sottomodulo contiene tutti gli script e le automazioni che possono essere eseguiti nel progetto. in modo da aggiungere note standardizzate, comandi di "segnalazione" come TAG, e automazioni come la gestione dei weekly log.

# Dipendenze utili VSCode

1. **Markdown Preview Enhanced:** Questa serve ad utilizzare componenti di CSS e HTML direttamente nelle note, in questo modo è possibile vedere in preview parole colorate e indentate direttamente sull'editor e non conflitta con `pandoc` durante eventuali conversioni. Permette di sfruttare lo schema colori presente in "Legenda dei colori"

2. **Markdown Preview Mermaid Support:** Usare il mermaid per creare grafici, i file .md devono chiamarsi con lo stesso nome dell'immagine che andranno a generare e saranno nella cartella vault/assets/macro-argomento/mermaid/.

   > <span style="color: orange;">NOTA:</span> Una volta creata l'immagine del grafico desiderata, tasto destro ed esporta come png e ritagliarla di conseguenza.

   In Questo modo se si vuole modificare una immagine si può avere direttamente il file generatore con estensione del nome -mermaid.md e l'immagine generata per poter fare modifiche rapide se necessarie. Nel caso in cui si trovasse una immagine inserita nel progetto è anche semplice capire se è una immagine scaricata e aggiunta o una generata e quindi modificabile guardando semplicemente il link.

3. **Markdownlint** + **Prettier:** sono una combo di estensioni che permette di segnalare errori di formattazione all'interno di un md file attraverso regole presenti nel file `.markdownlint.json` nella root. Unito a Prettier per correggere direttamente la formattazione.

   > <span style="color: darkviolet;">OSS:</span> per implementarli, dopo aver installato le
   > estensioni seguire i seguenti passaggisu `VSCode`:
   >
   > 1. `Ctrl+,` per aprire le impostazioni
   > 2. cerca: `default formatter`
   > 3. imposta `esbenp.prettier-vscode`
   > 4. cerca `format on save` e attiva l'impostazione A questo punto ogni salvataggio della nota verrá automaticamente formattata secondo le regole contenute nel file `.prettierrc`.

# Legenda ed aiuto alla coerenza

Per come é strutturata l'architettura possono essere utilizzati TAG e indici di diversa importanza per facilitare l'utilizzo e la comprensione per l'utente e

All'interno di una nota é supportato un solo titolo iniziale contenente la data del giorno a cui é riferito ma possono esserci anche altri sottotitoli per fare riferimento a specificitá referite a quel giorno

- `## note` Nota generica
- `## idea` Idea da esplorare
- `## ref` Riferimento esterno (link, paper...)
- `## log` Log di un evento/azione/riunione
- `## bug` Bug da correggere
- `## tags` Se si vuole taggare la nota con un certo evento (vedi il comando `-t --tag` per maggiori info)

## Eseguire il make python

É un eseguibile che agisce direttamente sulle note, modificando il contenuto di alcuni blocchi come ad esempio `## tags` crea resoconti ed effettua check di consistenza.

```bash
# help
\scripts\make.py -h
# inizializzazione repo
\scripts\make.py -i
# aggiunta di una nota per il giorno corrente
\scripts\make.py -n
# nel caso di aggiunte manuali é consigliato
\scripts\make.py -cc
\scripts\make.py -u
# aggiungere un tag alla nota corrente
\scripts\make.py -ft nometag
\scripts\make.py -t nometag nomenota
\scripts\make.py -lt
# crea e distruggi i resoconti settimanali
\scripts\make.py -w
\scripts\make.py -cw
```
