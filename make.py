import argparse
import os
import re
import sys
import shutil
from datetime import date
from pathlib import Path

## DEFINES ##
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
VAULT_DIR = Path(os.path.join(SCRIPT_DIR, "..", "myjournal")).resolve()  # Directory del vault
today = date.today()
YEAR_DIR = Path(os.path.join(VAULT_DIR, str(today.year))).resolve()  # Directory dell'anno corrente
MAIN_INDEX_FILE = Path(os.path.join(VAULT_DIR, "main-index.md")).resolve()  # Path del file principale
TAGS_INDEX_FILE = Path(os.path.join(VAULT_DIR, "tags-index.md")).resolve()  # Path del file principale


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
        # Controlla se il file TAGS_INDEX_FILE esiste, altrimenti lo crea
        if not os.path.exists(TAGS_INDEX_FILE):
            with open(TAGS_INDEX_FILE, "w", encoding="utf-8") as tag_file:
                tag_file.write("# Indice dei Tag\n\n")

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
                        # print(f"La nota '{note_path}' è già presente sotto il tag '{tagname}'.")
                        return
                    j += 1
                # Aggiungi la nota all'elenco puntato
                content.insert(j, f"- [{os.path.basename(note_path)}]({note_path})\n")
                break

        # Se la sezione del tag non esiste, creala in fondo al file
        if not tag_section_found:
            content.append(f"\n## {tagname}\n")
            content.append(f"- [{os.path.basename(note_path)}]({note_path})\n")

        # Scrivi il contenuto aggiornato nel file
        with open(TAGS_INDEX_FILE, "w", encoding="utf-8") as tag_file:
            tag_file.writelines(content)

    except Exception as e:
        print(f"Errore durante l'aggiornamento del file dei tag: {e}")

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
            for file in files:
                if file.endswith(".md"):
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

def UpdateIndex():
    """
    Aggiorna l'indice MAIN_INDEX_FILE con tutte le note presenti nel vault.
    L'indice è strutturato per anno e include i link alle note.
    Aggiorna il TAGS_INDEX_FILE leggendo i tag da ogni nota che contiene il blocco "## tags".
    """
    # Check di consistenza del nome preventivo per evitare nomi di file manuali non corretti
    CheckConsistency()
    
    try:
        # Controlla se VAULT_DIR esiste
        if not os.path.exists(VAULT_DIR):
            print(f"Errore: La directory '{VAULT_DIR}' non esiste.")
            return

        # Controlla se MAIN_INDEX_FILE esiste, altrimenti crealo
        if not os.path.exists(MAIN_INDEX_FILE):
            with open(MAIN_INDEX_FILE, "w", encoding="utf-8") as index_file:
                index_file.write("# Indice Principale\n\n")
            print(f"File '{MAIN_INDEX_FILE}' creato con successo.")

        # Dizionario per organizzare le note per anno
        notes_by_year = {}
        tags_data = {}  # Dizionario per organizzare i tag e le note associate

        # Scansiona il VAULT_DIR per trovare tutte le note
        for root, dirs, files in os.walk(VAULT_DIR):
            for file in files:
                if file.endswith(".md"):  # Considera solo i file Markdown
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, VAULT_DIR)
                    
                    # Estrai anno e nome del file
                    parts = relative_path.split(os.sep)
                    if len(parts) >= 2:  # Assicura che ci sia almeno una cartella (anno)
                        year = parts[0]
                        note_name = parts[-1]
                        if year not in notes_by_year:
                            notes_by_year[year] = []
                        notes_by_year[year].append((note_name, relative_path.replace("\\", "/")))

                    # Leggi i tag dalla nota se contiene il blocco "## tags"
                    with open(file_path, "r", encoding="utf-8") as note_file:
                        content = note_file.readlines()
                        tags_section_found = False
                        for i, line in enumerate(content):
                            if line.strip() == "## tags":
                                tags_section_found = True
                                j = i + 1
                                while j < len(content) and content[j].startswith("- "):
                                    tag = content[j].strip().lstrip("- ").strip()
                                    if tag not in tags_data:
                                        tags_data[tag] = []
                                    tags_data[tag].append(relative_path.replace("\\", "/"))
                                    j += 1
                                break

        # Scrivi l'indice in MAIN_INDEX_FILE
        with open(MAIN_INDEX_FILE, "w", encoding="utf-8") as index_file:
            for year, notes in sorted(notes_by_year.items()):
                # Scrivi il titolo dell'anno
                index_file.write(f"# {year}\n\n")
                for note_name, note_path in sorted(notes):
                    # Estrai MM-DD dal nome del file
                    date_part = note_name.split(".")[0][5:]  # Prende MM-DD
                    index_file.write(f"- [{date_part}]({note_path})\n")
                index_file.write("\n")  # Aggiungi una riga vuota tra gli anni

        print(f"Indice aggiornato con successo in '{MAIN_INDEX_FILE}'.")

        # Scrivi l'indice dei tag in TAGS_INDEX_FILE
        for tag, notes in sorted(tags_data.items()):
            for note_path in sorted(notes):
                # Usa la funzione UpdateTagIndex per aggiornare il file TAGS_INDEX_FILE
                UpdateTagIndex(tag, note_path)

        print(f"Indice dei tag aggiornato con successo in '{TAGS_INDEX_FILE}'.")

    except Exception as e:
        print(f"Errore durante l'aggiornamento dell'indice: {e}")

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
        print(f"La nota '{note_path}' esiste già. Nessuna azione necessaria.")
        return

    # Copia il template nella posizione della nuova nota
    try:
        shutil.copy(template_path, note_path)

        # Modifica il contenuto della nota per aggiornare il titolo
        with open(note_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Sostituisci #TITOLO con #DD-MM-YYYY
        new_title = f"# {day}-{month}-{year}"
        content = content.replace("# TITOLO", new_title)

        # Scrivi il contenuto aggiornato nella nota
        with open(note_path, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"Nota creata con successo: {note_path}")

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
            print(f"La cartella '{vault_dir}' è stata creata con successo.")
        else:
            print(f"La cartella '{vault_dir}' esiste già.")

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
                    print(f"Il file '{dest_file}' esiste già. Salto la copia.")
                    continue
                shutil.copy(src_file, dest_file)
        print(f"File di setup per VSCode copiati con successo")
        
        print(f"Enjoy your new journal vault! <3 ")
    
    except Exception as e:
        print(f"Errore durante la costruzione del Vault: {e}")
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
        print(f"Errore: La nota '{notename}' non è stata trovata nel repository.")
        sys.exit(1)

    try:
        # Leggi il contenuto della nota
        with open(note_path, "r", encoding="utf-8") as file:
            content = file.readlines()

        # Cerca la sezione ## tags
        tags_section_found = False
        for i, line in enumerate(content):
            if line.strip() == "## tags":
                tags_section_found = True
                # Controlla se ci sono già tag sotto la sezione ##tags
                j = i + 1
                while j < len(content) and content[j].startswith("- "):
                    j += 1
                # Aggiungi il nuovo tag all'elenco puntato
                content.insert(j, f"- {tagname}\n")
                break

        # Se la sezione ## tags non esiste, creala in fondo al file
        if not tags_section_found:
            content.append("\n## tags\n\n")
            content.append(f"- {tagname}\n")

        # Scrivi il contenuto aggiornato nella nota
        with open(note_path, "w", encoding="utf-8") as file:
            file.writelines(content)
            
        
        # Aggiorna il tag-index.md con le note che contengono il tag
        UpdateTagIndex(tagname, note_path)

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
            if line.startswith("## "):  # Identifica i titoli dei tag
                tagname = line.strip().replace("## ", "")
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
    
    # Parsing degli argomenti
    args = parser.parse_args()

    # Gestione delle opzioni
    if args.init:
        print(f"Creazione di un vault di partenza...")
        InitVault()
    
    elif args.new:
        print("Creazione di una nuova nota...")
        AddNewNote()
        
    elif args.update:
        print("Aggiornamento dell'indice...")
        UpdateIndex()
    
    elif args.check_consistency:
        print("Check dei nomi in corso...")
        CheckConsistency()
        print("Check completato. All fine! >(^_^)>")
        
    elif args.fast_tag:
        if not args.custom:
            print("Errore: l'opzione --fast-tag richiede un argomento TAGNAME")
            sys.exit(1)
        print(f"Aggiunta del tag '{args.fast_tag}' alla nota di oggi...")
        AddTagToTodayNote(args.fast_tag)
                
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
    
    
    else:
        print("Errore: nessuna opzione valida selezionata.")
        parser.print_help()

if __name__ == "__main__":
    main()