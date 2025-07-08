import argparse
import os
import re
import sys
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

## DEFINES ##
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
VAULT_DIR = Path(os.path.join(SCRIPT_DIR, "..", "myjournal")).resolve()  # Directory del vault
today = date.today()
YEAR_DIR = Path(os.path.join(VAULT_DIR, str(today.year))).resolve()  # Directory dell'anno corrente
MAIN_INDEX_FILE = Path(os.path.join(VAULT_DIR, "main-index.md")).resolve()  # Path del file principale
TAGS_INDEX_FILE = Path(os.path.join(VAULT_DIR, "tags-index.md")).resolve()  # Path del file principale

## TAGS BLOCCATI ##
# Questi sottotitoli in una nota non possono essere usati indipendentemente per separare le note
# perche' hanno valenza dentro lo script
B_SUBTITLE = "## "
B_UNSORTED = "## unsorted"  # Sezione per le note non ordinate (weekly)
B_NOTE = "## note"  # Sezione per le note giornaliere
B_TAGS = "## tags"  # Sezione dei tag
B_NEXT = "## next"  # Sezione per le note che verranno proiettate al giorno successivo
B_REFS = "## refs"  # Sezione per i riferimenti agli assets

## DIR BLOCCATE ##
D_ASSETS = "assets"
D_WEEKS = "weeks"

#######################
## UTILITY FUNCTIONS ##
#######################
def ValidateNoteName(notename):
    """
    Verifica che il file di output abbia un'estensione valida (.md).
    Se non è valido avverte che non puó essere inserito
    """
    ext = os.path.splitext(notename)[1].lower()
    if ext not in [".md"]:
        print(f"Errore: il file di scelto '{notename}' deve avere estensione .md .")
        sys.exit(1)
        
def GenerateNoteName(date_obj):
    """
    Genera il nome della nota nel formato YYYY-MM-DD.md.
    """
    year = date_obj.year
    month = f"{date_obj.month:02d}"  # Formatta il mese con due cifre
    day = f"{date_obj.day:02d}"      # Formatta il giorno con due cifre
    return f"{year}-{month}-{day}.md"

def UpdateTagIndex(tagname, note_path):
    """
    Aggiorna il file TAGS_INDEX_FILE con il tag specificato.
    Se il file non esiste, lo crea. Aggiunge il tag come titolo e un elenco puntato con i nomi delle note.
    Verifica che la nota non sia già presente sotto il tag.
    """
    try:
        # Leggi il contenuto esistente del file
        with open(TAGS_INDEX_FILE, "r", encoding="utf-8") as tag_file:
            content = tag_file.readlines()

        # Cerca la sezione del tag specificato
        tag_section_found = False
        for i, line in enumerate(content):
            if line.strip() == f"## {tagname}":
                tag_section_found = True
                # Controlla se la nota è già presente nell'elenco puntato
                j = i + 1
                while j < len(content) and content[j].startswith("- "):
                    if note_path in content[j]:
                        return
                    j += 1
                # Aggiungi la nota all'elenco puntato
                content.insert(j, f"- [{os.path.basename(note_path)}]({note_path})\n\n")
                break

        # Se la sezione del tag non esiste, creala in fondo al file
        if not tag_section_found:
            content.append(f"## {tagname}\n\n")
            content.append(f"- [{os.path.basename(note_path)}]({note_path})\n\n")

        # Scrivi il contenuto aggiornato nel file
        with open(TAGS_INDEX_FILE, "w", encoding="utf-8") as tag_file:
            tag_file.writelines(content)

    except Exception as e:
        print(f"Errore durante l'aggiornamento del file dei tag: {e}")

def FixNoteSpaces(notename):
    """
    Ottimizza gli spazi in una nota Markdown seguendo le regole:
    - Ogni blocco di testo (titolo, elenco o contenuto) deve essere circondato da una riga vuota.
    - Tra due titoli consecutivi (es. # e ##, ## e ##) senza contenuto in mezzo ci deve essere una riga vuota.
    """
    try:
        if not notename:
            print(f"Errore: La nota '{os.path.relpath(notename, VAULT_DIR)}' non è stata trovata.")
            return

        # Leggi il contenuto della nota
        with open(notename, "r", encoding="utf-8") as file:
            content = file.readlines()

        new_content = []
        previous_line = ""
        for i, line in enumerate(content):
            stripped_line = line.strip()

            # Gestisci righe vuote prima di un titolo
            if stripped_line.startswith("#"):
                if previous_line.strip():  # Se la riga precedente non è vuota, aggiungi una riga vuota
                    new_content.append("\n")
                new_content.append(line)
                previous_line = line
                continue

            # Gestisci righe vuote prima di un elenco
            if stripped_line.startswith("- ") or stripped_line.startswith("[ ]"):
                if previous_line.strip() and not previous_line.strip().startswith("- ") and not previous_line.strip().startswith("[ ]"):
                    new_content.append("\n")
                new_content.append(line)
                previous_line = line
                continue

            # Gestisci righe vuote dopo un titolo o un elenco
            if previous_line.strip().startswith("#") or previous_line.strip().startswith("- ") or previous_line.strip().startswith("[ ]"):
                if stripped_line:  # Se la riga corrente non è vuota, aggiungi una riga vuota
                    new_content.append("\n")

            # Gestisci righe vuote consecutive
            if not stripped_line:
                if previous_line.strip():  # Aggiungi una sola riga vuota
                    new_content.append(line)
                previous_line = line
                continue

            # Aggiungi la riga corrente
            new_content.append(line)
            previous_line = line

        # Scrivi il contenuto ottimizzato nella nota
        with open(notename, "w", encoding="utf-8") as file:
            file.writelines(new_content)

        # print(f"Spazi ottimizzati nella nota '{os.path.relpath(notename, VAULT_DIR)}'.")

    except Exception as e:
        print(f"Errore durante l'ottimizzazione degli spazi nella nota: {e}")

#########################
## PRINCIPAL FUNCTIONS ##
#########################
def CheckConsistency():
    """
    Controlla la consistenza dei nomi delle note nel vault.
    Verifica se i nomi delle note sono nel formato YYYY-MM-DD.md.
    Inoltre, verifica che non ci siano nomi duplicati.
    Stampa i nomi delle note con formato errato o duplicati per consentire la correzione manuale.
    """
    try:
        invalid_notes = []  # Lista per raccogliere i file con nomi errati
        note_names = set()  # Set per tracciare i nomi univoci delle note
        duplicate_notes = []  # Lista per raccogliere i file con nomi duplicati

        for root, dirs, files in os.walk(VAULT_DIR):
            # Ignora la cartella weeks
            if D_WEEKS in root:
                continue
            if D_ASSETS in root:
                continue # TODO aggiungere un check di consistenza per gli assets che devono iniziare con la data YYYY-MM-DD-nome-assets.* per rendere piú facile la ricerca
            for file in files:
                # Escludi i file weekly
                if file.startswith("weekly") or re.match(r"\d{4}weekly\d{2}\.md", file):
                    continue
                if file.endswith(".md"):
                    if(file == "main-index.md" or file == "tags-index.md"):
                        continue
                    # Controlla se il nome del file è nel formato YYYY-MM-DD.md
                    match = re.match(r"(\d{4})-(\d{2})-(\d{2})\.md", file)
                    relative_path = os.path.relpath(os.path.join(root, file), VAULT_DIR)
                    if not match:
                        invalid_notes.append(relative_path)  # Aggiungi il percorso relativo del file
                    else:
                        # Verifica se il nome della nota è già stato visto
                        if file in note_names:
                            duplicate_notes.append(relative_path)  # Aggiungi il percorso relativo del file duplicato
                        else:
                            note_names.add(file)
                else:
                    relative_path = os.path.relpath(os.path.join(root, file), VAULT_DIR)
                    invalid_notes.append(relative_path)

        # Stampa i risultati
        if invalid_notes:
            print("Sono state trovate note con nomi non validi:")
            for note in invalid_notes:
                print(f"- {note}")
            print("\nRinomina manualmente i file sopra elencati per rispettare il formato YYYY-MM-DD.md.")

        if duplicate_notes:
            print("Sono state trovate note con nomi duplicati:")
            for note in duplicate_notes:
                print(f"- {note}")
            print("\nRinomina manualmente i file sopra elencati per garantire che ogni nota abbia un nome univoco.")

        if invalid_notes or duplicate_notes:
            sys.exit(1)

    except Exception as e:
        print(f"Errore durante il controllo della consistenza: {e}")
        sys.exit(1)

def UpdateMainIndex(notes_by_year):
    """
    Aggiorna il file MAIN_INDEX_FILE con tutte le note presenti nel vault, organizzate per anno.
    Le note più recenti saranno in cima alla lista di ogni anno.
    """

    # Controlla se MAIN_INDEX_FILE esiste, altrimenti crealo
    if not os.path.exists(MAIN_INDEX_FILE):
        with open(MAIN_INDEX_FILE, "w", encoding="utf-8") as index_file:
            index_file.write("# Indice Principale\n\n")
        print(f"File '{os.path.relpath(MAIN_INDEX_FILE, VAULT_DIR)}' creato con successo.")
        
    try:
        with open(MAIN_INDEX_FILE, "w", encoding="utf-8") as index_file:
            index_file.write("# Indice Principale\n\n")
            for year, notes in sorted(notes_by_year.items(), reverse=True):  # Anni dal più recente
                index_file.write(f"# {year}\n\n")
                for note_name, note_path in sorted(notes, reverse=True):  # Note dalla più recente
                    # Estrai MM-DD dal nome del file
                    date_part = note_name.split(".")[0][5:]  # Prende MM-DD
                    index_file.write(f"- [{date_part}]({note_path})\n")
                index_file.write("\n")  # Riga vuota tra gli anni
    except Exception as e:
        print(f"Errore durante l'aggiornamento del file principale: {e}")


def UpdateTagsIndex(tags_data):
    """
    Aggiorna il file TAGS_INDEX_FILE con tutti i tag presenti nel vault e le note associate.
    """
    
    # Controlla se TAGS_INDEX_FILE esiste, altrimenti crealo
    if not os.path.exists(TAGS_INDEX_FILE):
        with open(TAGS_INDEX_FILE, "w", encoding="utf-8") as tags_file:
            tags_file.write("# Indice TAGS\n\n")
        print(f"File '{os.path.relpath(TAGS_INDEX_FILE, VAULT_DIR)}' creato con successo.")

    try:
        with open(TAGS_INDEX_FILE, "w", encoding="utf-8") as tags_file:
            tags_file.write("# Indice TAGS\n\n")
            for tag, notes in sorted(tags_data.items()):
                tags_file.write(f"## {tag}\n\n")
                for note_path in sorted(notes):
                    tags_file.write(f"- [{os.path.basename(note_path)}]({note_path})\n")
                tags_file.write("\n")
        #print(f"Indice dei tag aggiornato con successo in '{os.path.relpath(TAGS_INDEX_FILE, VAULT_DIR)}'.")
    except Exception as e:
        print(f"Errore durante l'aggiornamento del file dei tag: {e}")


def UpdateIndex():
    """
    Aggiorna gli indici principali e dei tag leggendo le note presenti nel vault.
    """
    # Check di consistenza del nome preventivo per evitare nomi di file manuali non corretti
    CheckConsistency()

    try:
        # Controlla se VAULT_DIR esiste
        if not os.path.exists(VAULT_DIR):
            print(f"Errore: La directory '{VAULT_DIR}' non esiste.")
            return

        # Dizionario per organizzare le note per anno
        notes_by_year = {}
        tags_data = {}  # Dizionario per organizzare i tag e le note associate

        # Scansiona il VAULT_DIR per trovare tutte le note
        for root, dirs, files in os.walk(VAULT_DIR):
            # Ignora la cartella weeks
            if D_WEEKS in root:
                continue
            if D_ASSETS in root:
                continue
            for file in files:
                # Escludi i file weekly
                if file.startswith("weekly") or re.match(r"\d{4}weekly\d{2}\.md", file):
                    continue
                if file.endswith(".md"):  # Considera solo i file Markdown
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, VAULT_DIR).replace("\\", "/")

                    # Estrai anno e nome del file
                    parts = relative_path.split("/")
                    if len(parts) >= 2:  # Assicura che ci sia almeno una cartella (anno)
                        year = parts[0]
                        note_name = parts[-1]
                        if year not in notes_by_year:
                            notes_by_year[year] = []
                        notes_by_year[year].append((note_name, relative_path))

                    # Leggi i tag dalla nota se contiene il blocco "## tags"
                    with open(file_path, "r", encoding="utf-8") as note_file:
                        content = note_file.readlines()
                        tags_section_found = False
                        for i, line in enumerate(content):
                            if line.strip() == B_TAGS:
                                tags_section_found = True
                                j = i + 1
                                while j < len(content):
                                    if content[j].startswith("- "):  # Considera solo gli elenchi puntati
                                        tag = content[j].strip().lstrip("- ").strip()
                                        if tag not in tags_data:
                                            tags_data[tag] = []
                                        tags_data[tag].append(relative_path)
                                    elif content[j].strip().startswith(B_SUBTITLE):  # Fine del blocco ## tags
                                        break
                                    j += 1
                                break

        # Aggiorna i file degli indici
        UpdateMainIndex(notes_by_year)
        UpdateTagsIndex(tags_data)

    except Exception as e:
        print(f"Errore durante l'aggiornamento degli indici: {e}")

def AddNewNote():
    """
    Aggiunge una nuova nota al path YYYY/YYYY-MM-DD.md.
    Se l'anno esiste ma la nota no, aggiunge la nota del giorno.
    La nota è una copia di templates/void-notes.md con il titolo modificato.
    """
    # Ottieni la data di oggi
    today = date.today()
    note_filename = GenerateNoteName(today)
    year, month, day = note_filename.split(".")[0].split("-")
    year_dir = YEAR_DIR
    note_path = os.path.join(year_dir, note_filename)

    # Path del template
    template_path = os.path.join(SCRIPT_DIR, "templates", "void-notes.md")

    # Controlla se la directory dell'anno esiste, altrimenti creala
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)

    # Controlla se la nota esiste già
    if os.path.exists(note_path):
        print(f"La nota '{os.path.relpath(note_path, VAULT_DIR)}' esiste già. Nessuna azione necessaria.")
        return
    
    # Prima di copiare il template estrae dalla nota piú recente il blocco ## next per le note che si vogliono ricordare dal giorno prima
    md_files = []
    for file in os.listdir(year_dir):
        if file.endswith(".md") and file != note_filename:
            match = re.match(r"(\d{4})-(\d{2})-(\d{2})\.md", file)
            if match:
                md_files.append(file)
    md_files = sorted(md_files)
    prev_note = None
    for f in reversed(md_files):
        if f < note_filename:
            prev_note = os.path.join(year_dir, f)
            break
        
    # Estrai il contenuto della sezione B_NEXT dalla nota precedente
    next_content = []
    if prev_note:
        with open(prev_note, "r", encoding="utf-8") as prev_file:
            lines = prev_file.readlines()
        in_next = False
        for line in lines:
            if line.strip() == B_NEXT:
                in_next = True
                continue
            if in_next and line.strip().startswith(B_SUBTITLE) and line.strip() != B_NEXT:
                break
            if in_next:
                next_content.append(line)
        if next_content and next_content[-1].strip() != "":
            next_content.append("\n")

    # Copia il template nella posizione della nuova nota
    try:
        shutil.copy(template_path, note_path)
        with open(note_path, "r", encoding="utf-8") as file:
            content = file.readlines()

        # Sostituisci #TITOLO con #DD-MM-YYYY
        new_title = f"# {day}-{month}-{year}"
        content = [line.replace("# TITOLO", new_title) for line in content]

        # Inserisci il contenuto di B_NEXT prima di ## note
        if next_content:
            for idx, line in enumerate(content):
                if line.strip() == B_NOTE:
                    content = content[:idx] + [B_NEXT + "\n"] + next_content + content[idx:]
                    break

        # Scrivi il contenuto aggiornato nella nota
        with open(note_path, "w", encoding="utf-8") as file:
            file.writelines(content)

        print(f"Nota creata con successo: {os.path.relpath(note_path, VAULT_DIR)}")

    except Exception as e:
        print(f"Errore durante la creazione della nota: {e}")
        
    # Aggiorna istantaneamente l'indice
    UpdateIndex()

def InitVault():
    """
    Inizializza la struttura del vault copiando i file e le cartelle necessarie.
    """
    setup_dir = Path(os.path.join(SCRIPT_DIR, "templates", "setup-vault")).resolve()
    parent_dir = Path(os.path.join(SCRIPT_DIR, "..")).resolve()
    vault_dir = VAULT_DIR

    # Controlla se esiste già una cartella chiamata 'myjournal'
    if os.path.exists(vault_dir):
        # Ottieni il contenuto della cartella 'myjournal'
        vault_contents = os.listdir(vault_dir)
        
        # Check di un repo già inizializzato, non si vuole cancellare ciò che già esiste
        if vault_contents:
            print("Errore: Il Vault contiene già file, non è necessario inizializzare.")
            sys.exit(1)

    try:
        # Crea la cartella 'myjournal' se non esiste
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)
            print(f"La cartella '{os.path.relpath(vault_dir, SCRIPT_DIR)}' è stata creata con successo.")
        else:
            print(f"La cartella '{os.path.relpath(vault_dir, SCRIPT_DIR)}' esiste già.")

        # Copia tutto il contenuto della cartella setup-vault fuori dalla cartella 'myjournal'
        for root, dirs, files in os.walk(setup_dir):
            relative_path = os.path.relpath(root, setup_dir)
            target_dir = os.path.join(parent_dir, relative_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(target_dir, file)
                # Controlla se il file esiste già nella destinazione
                if os.path.exists(dest_file):
                    print(f"Il file '{os.path.relpath(dest_file, VAULT_DIR)}' esiste già. Salto la copia.")
                    continue
                shutil.copy(src_file, dest_file)
        print(f"File di setup per VSCode copiati con successo")
    
    except Exception as e:
        print(f"Errore durante la costruzione del Vault: {os.path.relpath(e.filename, VAULT_DIR)}")
        sys.exit(1)
        
    # Aggiunge la prima nota
    AddNewNote()
    
def AddTagToNoteName(tagname, notename):
    """
    Aggiunge un tag a una nota specificata.
    Cerca la nota nel repository, se non la trova si ferma.
    Se la trova, aggiunge il tag nella sezione ## tags. Se la sezione non esiste, la crea.
    """
    # Cerca la nota nel repository
    note_path = None
    for root, dirs, files in os.walk(VAULT_DIR):
        # Controlla se la directory corrente rappresenta un anno (YYYY)
        relative_path = os.path.relpath(root, VAULT_DIR)
        if not relative_path.isdigit() or len(relative_path) != 4:
            continue  # Salta le directory che non rappresentano un anno

        for file in files:
            if file == notename:
                note_path = os.path.join(root, file)
                break
        if note_path:
            break

    # Se la nota non è stata trovata, interrompi
    if not note_path:
        print(f"Errore: La nota '{os.path.relpath(notename, VAULT_DIR)}' non è stata trovata nel repository.")
        sys.exit(1)

    try:
        # Leggi il contenuto della nota
        with open(note_path, "r", encoding="utf-8") as file:
            content = file.readlines()

        # Cerca la sezione ## tags
        tags_section_found = False
        for i, line in enumerate(content):
            if line.strip() == B_TAGS:
                tags_section_found = True
                # Controlla se il tag è già presente
                j = i + 1
                while j < len(content):
                    line = content[j].strip()  # Rimuove spazi e caratteri di nuova linea
                    if not line:  # Salta le righe vuote
                        j += 1
                        continue
                    if line.startswith("- "):  # Controlla se la riga è un elemento dell'elenco
                        existing_tag = line.lstrip("- ").strip()
                        if existing_tag.lower() == tagname.lower():  # Confronto case-insensitive
                            print(f"Il tag '{tagname}' è già presente nella nota '{notename}'. Nessuna azione necessaria.")
                            return
                    elif line.startswith(B_SUBTITLE):  # Fine del blocco ## tags
                        break
                    j += 1
                # Aggiungi il nuovo tag all'elenco puntato
                content.insert(j, f"\n- {tagname}")
                break

        # Se la sezione ## tags non esiste, creala in fondo al file
        if not tags_section_found:
            content.append("\n## tags\n\n")
            content.append(f"- {tagname}\n")

        # Scrivi il contenuto aggiornato nella nota
        with open(note_path, "w", encoding="utf-8") as file:
            file.writelines(content)

        # Aggiorna il tag-index.md con le note che contengono il tag
        UpdateIndex()
        FixNoteSpaces(note_path)

        print(f"Tag '{tagname}' aggiunto con successo alla nota '{notename}'.")

    except Exception as e:
        print(f"Errore durante l'aggiunta del tag: {e}")
        
def AddTagToTodayNote(tagname):
    """
    Aggiunge un tag alla nota di oggi.
    """	
    note_name = GenerateNoteName(date.today())
    AddTagToNoteName(tagname, note_name)
    
def TagList():
    """
    Legge il file TAGS_INDEX_FILE e restituisce la lista di tutti i tag presenti.
    """
    
    # Prima aggiorna tutti i tag verificare che si siano tutti aggiornati
    # UpdateAllTags()
    
    try:
        # Controlla se il file TAGS_INDEX_FILE esiste
        if not os.path.exists(TAGS_INDEX_FILE):
            print(f"Errore: Il file '{TAGS_INDEX_FILE}' non esiste. Nessun tag trovato.")
            return

        # Leggi il contenuto del file
        with open(TAGS_INDEX_FILE, "r", encoding="utf-8") as tag_file:
            content = tag_file.readlines()

        # Cerca i titoli dei tag (## {tagname})
        tags = []
        for line in content:
            if line.startswith(B_SUBTITLE):  # Identifica i titoli dei tag
                tagname = line.strip().replace(B_SUBTITLE, "")
                tags.append(tagname)

        # Stampa la lista dei tag
        if tags:
            print("Tag presenti nel vault:")
            for tag in tags:
                print(f"- {tag}")
        else:
            print("Nessun tag trovato nel file TAGS_INDEX_FILE.")

    except Exception as e:
        print(f"Errore durante la lettura dei tag: {e}")
        
def WeekLog(year=None):
    """
    Genera file settimanali con le note raggruppate per settimana (da lunedì a domenica).
    Crea un file per ogni settimana presente nel vault, unendo il contenuto delle note della settimana.
    Se l'anno non é specificato, usa l'anno corrente.
    """
    # Check di consistenza preventivo
    CheckConsistency()

    try:
        # Dizionario per raggruppare le note per settimana
        weeks_data = {}
        # Determina l'anno da processare
        if year is None:
            year = date.today().year
        year = str(year)

        # Scansiona solo la cartella dell'anno specificato
        year_dir = os.path.join(VAULT_DIR, year)
        if not os.path.exists(year_dir):
            print(f"Nessuna nota trovata per l'anno {year}.")
            return

        for root, dirs, files in os.walk(year_dir):
            if D_WEEKS in root:
                continue
            if D_ASSETS in root:
                continue
            for file in files:
                # Escludi i file weekly
                if file.startswith("weekly") or re.match(r"\d{4}weekly\d{2}\.md", file):
                    continue
                if file.endswith(".md"):  # Considera solo i file Markdown
                    file_path = os.path.join(root, file)
                    file_date_str = os.path.basename(file).split(".")[0]  # Estrai YYYY-MM-DD
                    try:
                        # Converte la data del file in un oggetto datetime
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                        # Calcola il lunedì della settimana corrente
                        start_of_week = file_date - timedelta(days=file_date.weekday())
                        # Raggruppa le note per settimana
                        if start_of_week not in weeks_data:
                            weeks_data[start_of_week] = []
                        weeks_data[start_of_week].append(file_path)
                    except ValueError:
                        continue  # Ignora file con nomi non validi

        # Se non ci sono note, interrompi
        if not weeks_data:
            print(f"Nessuna nota trovata per l'anno {year}.")
            return

        # Ordina le settimane
        sorted_weeks = sorted(weeks_data.keys())

        # Genera un file settimanale per ogni settimana
        for start_of_week in sorted_weeks:
            end_of_week = start_of_week + timedelta(days=6) # Calcola la domenica della settimana
            week_number = start_of_week.isocalendar()[1] # Ottiene il numero della settimana corrente
            weeks_dir = os.path.join(VAULT_DIR, year, D_WEEKS)
            os.makedirs(weeks_dir, exist_ok=True)

            # Nome del file settimanale
            weekly_filename = f"{year}weekly{week_number:02d}.md"
            weekly_file_path = os.path.join(weeks_dir, weekly_filename)

            # Dizionario per raggruppare il contenuto delle note per sezione
            sections = {}

            # Unisci il contenuto delle note della settimana
            notes_in_week = sorted(weeks_data[start_of_week])
            for note_path in notes_in_week:
                with open(note_path, "r", encoding="utf-8") as note_file:
                    current_section = B_UNSORTED  # Sezione predefinita per contenuti senza intestazione
                    for line in note_file:
                        stripped_line = line.strip()
                        if stripped_line.startswith("# "):  # Ignora i titoli delle note giornaliere
                            continue
                        if stripped_line.startswith(B_SUBTITLE):  # Identifica una nuova sezione
                            if stripped_line == B_TAGS or stripped_line == B_NEXT or stripped_line == B_REFS:  # Salta la sezione ## tags, ## next e ## refs
                                current_section = None
                                continue
                            current_section = stripped_line
                            if current_section not in sections:
                                sections[current_section] = []
                            continue  # Non aggiungere il titolo della sezione al contenuto
                        if current_section:  # Aggiungi contenuto solo se la sezione è valida
                            sections.setdefault(current_section, []).append(line)

            # Scrivi il contenuto unito nel file settimanale
            with open(weekly_file_path, "w", encoding="utf-8") as weekly_file:
                # Scrivi il titolo della settimana
                weekly_file.write(f"# Week {week_number} ({start_of_week} - {end_of_week})\n\n")
                
                # Aggiungi l'elenco puntato con i link alle note della settimana
                for note_path in notes_in_week:
                    note_name = os.path.basename(note_path)
                    relative_path = os.path.relpath(note_path, weeks_dir).replace("\\", "/")
                    weekly_file.write(f"- [{note_name.split('.')[0]}]({relative_path})\n")
                weekly_file.write("\n")
                
                # Scrivi le sezioni raggruppate
                written_sections = set()  # Traccia delle sezioni già scritte
                for section, content in sections.items():
                    if section not in written_sections:  # Scrivi la sezione solo se non è già stata scritta
                        weekly_file.write(f"{section}\n")
                        written_sections.add(section)  # Aggiungi la sezione al set
                    weekly_file.writelines(content)
            FixNoteSpaces(weekly_file_path)

            print(f"File settimanale aggiornato: {os.path.relpath(weekly_file_path, VAULT_DIR)}")

    except Exception as e:
        print(f"Errore durante la generazione dei file settimanali: {e}")

def DeleteWeekLog():
    """
    Elimina tutte le cartelle 'weeks' presenti all'interno delle cartelle 'YYYY/'.
    """
    try:
        # Scansiona il VAULT_DIR per trovare tutte le cartelle 'weeks'
        for root, dirs, files in os.walk(VAULT_DIR):
            for dir_name in dirs:
                if dir_name == D_WEEKS:
                    weeks_dir_path = os.path.join(root, dir_name)
                    # Elimina la cartella 'weeks' e tutto il suo contenuto
                    shutil.rmtree(weeks_dir_path)
                    print(f"Cartella eliminata: {os.path.relpath(weeks_dir_path, VAULT_DIR)}")
    except Exception as e:
        print(f"Errore durante l'eliminazione delle cartelle 'weeks': {e}")


## MAIN FUNCTION ##
def main():  
    # Creazione del parser
    parser = argparse.ArgumentParser(
        prog="make.py",
        description="Make script per gestire la conversione di note in PDF. Tips: genera un repo git vuoto e inserisci questo come un sottomodulo prima di lanciare un --init",
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio"
    )
    # Aggiunta delle opzioni
    parser.add_argument("-i", "--init",     action="store_true",    help="Inizializza la struttura del vault in modo che sia consistente per journal il make.py")
    parser.add_argument("-n", "--new",      action="store_true",    help="Aggiunge una nota vuota al giorno corrente (se non esiste già)")
    parser.add_argument("-u", "--update",   action="store_true",    help="Aggiorna l'indice in main-index.md con tutte le note presenti ed eventuali tag aggiunti manualmente")
    parser.add_argument("-cc", "--check-consistency",   action="store_true",    help="Check di consistenza dei nomi delle note nel vault")
    parser.add_argument("-ft", "--fast-tag",                        nargs=1,        metavar="TAGNAME",  help="Inserisce alla nota di oggi")
    parser.add_argument("-t", "--tag",                              nargs=2,        metavar=("TAGNAME", "DAY-NOTE"),  help="Inserisce alla nota specificata il tag scelto")
    parser.add_argument("-lt", "--list-tag",action="store_true",    help="lista dei tag presenti in tutto il vault")
    parser.add_argument("-w", "--week", nargs="?", const="current", metavar="YYYY", help="Genera i weekly log solo per l'anno corrente o per l'anno specificato (es: -w YYYY)")
    parser.add_argument("-cw", "--clean-week",action="store_true",  help="effettua una pulizia di tutte le note settimanali per pulire il repo dai resoconti ripetitivi")
    
    # Parsing degli argomenti
    args = parser.parse_args()

    # Gestione delle opzioni
    if args.init:
        print(f"Creazione di un vault di partenza...")
        InitVault()
        print(f"Enjoy your new journal vault! =^._.^=ﾉ")
    
    elif args.new:
        print("Creazione di una nuova nota...")
        AddNewNote()
        
    elif args.update:
        print("Aggiornamento dell'indice...")
        UpdateIndex()
        print("Indici (main e tags) aggiornati! (=^･ｪ･^=)ﾉ")
    
    elif args.check_consistency:
        print("Check dei nomi in corso...")
        CheckConsistency()
        print("Check completato. All fine! ₍^..^₎𐒡")
        
    elif args.fast_tag:
        if not args.fast_tag:
            print("Errore: l'opzione --fast-tag richiede un argomento TAGNAME")
            sys.exit(1)
        print(f"Aggiunta del tag '{args.fast_tag[0]}' alla nota di oggi...")
        AddTagToTodayNote(args.fast_tag[0])
                
    elif args.tag:
        if len(args.tag) < 2:
            print("Errore: l'opzione --tag richiede due argomenti: TAGNAME e NOTENAME (in formato .md).")
            sys.exit(1)
        tagname, notename = args.tag
        ValidateNoteName(notename)
        print(f"Aggiunta del tag '{tagname}' alla nota '{notename}'...")
        AddTagToNoteName(tagname, notename)
    
    elif args.list_tag:
        print("Elenco dei tag presenti nel vault...")
        TagList()
    
    elif args.week:
        success = True
        if args.week == "current":
            print("Genero i Weekly log per l'anno corrente...")
            WeekLog()
        else:
            year_dir = os.path.join(VAULT_DIR, str(args.week))
            if not os.path.exists(year_dir):
                print(f"Anno {args.week} non presente nel vault, nessun weekly generato.")
                success = False
            else:
                print(f"Genero i Weekly log per l'anno {args.week}...")
                WeekLog(args.week)
        
        if success:
            print("Weekly Log generati! =^._.^=ﾉ")
        
    elif args.clean_week:
        print("Pulizia dei Weekly log...")
        DeleteWeekLog()
        print("Weekly log eliminati!. (=^･ｪ･^=)ﾉ")

        
    else:
        print("Errore: nessuna opzione valida selezionata.")
        parser.print_help()

if __name__ == "__main__":
    main()