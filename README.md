# Documentation Stucture

Journal Documentation Structure
Consiglio: genera un repo vuoto, e iniserisci questo repo come un sottomodulo git, dopo potrai inizializzare la tua struttura del journal con il comando `--init` garantendo una struttura stabile. Questo ti permette anche di avere gli script e le tue note separate.
Per maggiori informazioni sulle operazioni che puó fare questo sottomodulo lanciare:

```bash
python JournalScript/make.py --help
```

## Guida all'inizializzazione

1. <span style="color: brown;">Creazione del repo personale</span>

   Su GitHub o in locale creare un repo git con:

   ```bash
   git init --bare MyDocumentation
   ```

2. <span style="color: brown;">Clonare il repo ed inserire il sottomodulo</span>

   ```bash
   git clone /path/to/MyDocumentation MyAgenda
   cd MyAgenda
   git submodules add https://github.com/BenettiFabio/JournalScript
   ```

3. <span style="color: brown;">Inizializzare il vault</span>

   A questo punto grazie agli script si puó inizializzare un vault in cui iniziare a scrivere la propria documentazione. Ricorda di stare dentro la cartella `MyAgenda/`.

   ```bash
   python JournalScript/make.py --help
   python JournalScript/make.py --init
   ```

   Verrá creato un **vault** con una struttura standard basata su **anni** con le varie note dei giorni al suo interno, una cartella **assets** per gli allegati e al di fuori i file per le indentazioni di **markdownlint** e **prettier**.

   Per maggiori informazioni sulla struttura base del progetto proseguire con la lettura.

# Struttura del progetto

0. **REGOLA FONDAMENTALE DELLE NOTE:** I nomi delle note devono essere tutti <span style="color:red">_date_</span>, le cifre separate da `-`. I nomi delle note sono **TUTTI** descrittivi del loro albero di posizione:

   _es:_

   ```bash
   myjournal/
   ├── main-index.md
   ├── tags-index.md
   ├── calendar-index.md
   ├── 2024/
   │   ├── assets/
   │   ├── weeks/
   │   ├── 2024-04-27.md
   │   ├── 2024-05-2.md
   │   └── 2024-05-31.md
   ├── 2025/
   │   ├── assets/
   │   ├── weeks/
   │   └── 2024-01-31.md
   └── YYYY/
       ├── assets/
       ├── weeks/
       │   └── YYYYweeklyWW.md
       └── YYYY-MM-DD.md
   ```

   In Questo modo la ricerca dei file e dei loro contenuti si semplifica e semplifica l'utilizzo anche di eventuali script che possono sfruttare il nome per eventuali automazioni.

   > <span style="color: red;">ATT!:</span> Ogni nuova pagina aggiunta viene inserita direttamente negli indici (`main/tags/calendar-index.md`) se viene creata mediante l'apposito comando `-n --new` altrimenti lanciare `-u --update` per aggiornare tutti gli indici automaticamente.

1. `main-index.md`, `tags-index` e `calendar-index.md`: Questi files contengono l'indice di tutta la struttura, andranno a linkare tutte le pagine del progetto in modo da poterle trovare facilmente nel tempo divise per anni e per tags.

2. **myjournal:** è il vault contenente tutte le note, i nomi delle note sono divisi per anno attraverso sottocartelle. Mediante i nomi strutturati come sopra vengono automaticamente ordinati alfabeticamente quindi giá facilmente individuabili.

3. **assets:** La cartella assets contiene tutti gli allegati (documenti e immagini) utili alle varie note, dentro la cartella `YYYY/assets` dove `YYYY` sono l'anno a cui fanno riferimento. ci sono i relativi docs, imgs, ...

4. **JournalScript:** Questo sottomodulo contiene tutti gli script e le automazioni che possono essere eseguiti nel progetto. in modo da aggiungere note standardizzate, comandi di "segnalazione" come TAG, note da portare al giorno successivo, log delle varie riunioni, e automazioni come la gestione dei weekly log.

# Dipendenze utili VSCode

1. **Markdown Preview Enhanced:** Questa serve ad utilizzare componenti di CSS e HTML direttamente nelle note, in questo modo è possibile vedere in preview parole colorate e indentate direttamente sull'editor e non conflitta con `pandoc` durante eventuali conversioni. Permette di sfruttare lo schema colori presente in "Legenda dei colori"

2. **Markdownlint** + **Prettier:** sono una combo di estensioni che permette di segnalare errori di formattazione all'interno di un md file attraverso regole presenti nel file `.markdownlint.json` nella root. Unito a Prettier per correggere direttamente la formattazione.

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
- `## next` Note che si vogliono portare al giorno successivo
  - (non vengono calcolate nei weekly)
- `## idea` Idea da esplorare
- `## refs` Riferimento esterno
  - (link, paper..., o documento dentro la cartella dell'anno specifico)
  - (non vengono calcolate nei weekly)
- `## logs` Log di un evento/azione/riunione
- `## bugs` Bug da correggere
- `## tags` Se si vuole taggare la nota con un certo evento
  - (vedi il comando `-t --tag` per maggiori info)
  - (non vengono calcolate nei weekly)

## Eseguire il make python

É un eseguibile che agisce direttamente sulle note, modificando il contenuto di alcuni blocchi come ad esempio `## tags` crea resoconti ed effettua check di consistenza.

```bash
# help
\scripts\make.py -h
# inizializzazione repo
\scripts\make.py -i
# aggiunta di una nota per il giorno corrente
\scripts\make.py -n
# esegui il backup dell'agenda in un file .tar
\scripts\make.py -b
# nel caso di aggiunte manuali é consigliato
\scripts\make.py -cc
\scripts\make.py -u
# aggiungere un tag alla nota corrente
\scripts\make.py -ft nometag
\scripts\make.py -t nometag nomenota
\scripts\make.py -lt
# crea e distruggi i resoconti settimanali
\scripts\make.py -w
\scripts\make.py -w YYYY
\scripts\make.py -cw
```
