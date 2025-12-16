import argparse
import os
import re
import sys
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
import tarfile
import tkinter as tk
from tkinter import filedialog
import pyfiglet

## VERSIONE ##
JOURNALSCRIPT_VERSION = "1.2.1"

## FILE BLOCCATI ##
F_MAIN_INDEX = "main-index.md"
F_TAGS_INDEX = "tags-index.md"
F_CALENDAR_INDEX = "calendar-index.md"
F_STATISTICS_INFO = "satistics-info.md"

## DEFINES ##
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
VAULT_DIR = Path(os.path.join(SCRIPT_DIR, "..", "myjournal")).resolve()  # Directory del vault
today = date.today()
YEAR_DIR = Path(os.path.join(VAULT_DIR, str(today.year))).resolve()  # Directory dell'anno corrente
MAIN_INDEX_FILE = Path(os.path.join(VAULT_DIR, F_MAIN_INDEX)).resolve()  # Path del file principale
TAGS_INDEX_FILE = Path(os.path.join(VAULT_DIR, F_TAGS_INDEX)).resolve()
CALE_INDEX_FILE = Path(os.path.join(VAULT_DIR, F_CALENDAR_INDEX)).resolve()
STAT_INFO_FILE =  Path(os.path.join(VAULT_DIR, F_STATISTICS_INFO)).resolve()

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
        invalid_notes = []      # Lista per raccogliere i file con nomi errati
        note_names = set()      # Set per tracciare i nomi univoci delle note
        duplicate_notes = []    # Lista per raccogliere i file con nomi duplicati
        invalid_assets = []     # File asset con nomi errati

        for root, dirs, files in os.walk(VAULT_DIR):
            # Ignora la cartella weeks
            if D_WEEKS in root:
                continue
            
            for file in files:
                # Check per gli assets
                if D_ASSETS in root:
                    # Match per asset: YYYY-MM-DD-nomequalsiasi.estensione
                    if not re.match(r"\d{4}-\d{2}-\d{2}-.+\..+", file):
                        relative_path = os.path.relpath(os.path.join(root, file), VAULT_DIR)
                        invalid_assets.append(relative_path)
                    continue  # Skip al prossimo file, non serve processare altro
                
                # Escludi i file weekly
                if file.startswith("weekly") or re.match(r"\d{4}weekly\d{2}\.md", file):
                    continue
                
                if file.endswith(".md"):
                    if(file == F_MAIN_INDEX or file == F_TAGS_INDEX or file == F_CALENDAR_INDEX or file == F_STATISTICS_INFO):
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

        if invalid_assets:
            print("Sono stati trovati file asset con nomi non validi:")
            for asset in invalid_assets:
                print(f"- {asset}")
            print("\nRinomina manualmente gli asset sopra elencati per rispettare il formato YYYY-MM-DD-nome.estensione.")

        if invalid_notes or duplicate_notes or invalid_assets:
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

def UpdateCalendarIndex(notes_by_year):
    """
    Aggiorna il file CALENDAR_INDEX_FILE con i calendari annuali.
    I mesi sono ordinati in modo decrescente (da dicembre a gennaio) per avere l'ultimo mese sempre in alto.
    """

    # Se non esiste, crealo
    if not os.path.exists(CALE_INDEX_FILE):
        with open(CALE_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write("# Calendar Index\n\n")
        print(f"File '{os.path.relpath(CALE_INDEX_FILE, VAULT_DIR)}' creato con successo.")

    try:
        import calendar
        from datetime import datetime

        with open(CALE_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write("# Calendar Index\n\n")

            # Anni in ordine decrescente (imita ai due anni più recenti)
            sorted_years = sorted(notes_by_year.keys(), reverse=True)
            recent_years = set(sorted_years[:2])
            for year, notes in sorted(notes_by_year.items(), reverse=True):
                if year not in recent_years:
                    continue
                
                f.write(f"# {year}\n\n")

                # Estrai tutte le date valide dall'anno
                dates = []
                for note_name, note_path in notes:
                    try:
                        d = datetime.strptime(note_name.replace(".md", ""), "%Y-%m-%d")
                        dates.append((d, note_path))
                    except ValueError:
                        continue

                if not dates:
                    continue

                last_month = max(d.month for d, _ in dates)
                cal = calendar.Calendar(firstweekday=0)  # Lunedì

                # ---- Indice dei mesi ----
                f.write("### Indice dei mesi\n")
                for month in range(last_month, 0, -1):
                    mese_nome = calendar.month_name[month].capitalize()
                    # Link Markdown al titolo del mese
                    link = f"#{mese_nome.lower()}-{year}"
                    f.write(f"- [{mese_nome}](#{mese_nome.lower()}-{year})\n")
                f.write("\n")
                
                # Ciclo mesi in ordine decrescente
                for month in range(last_month, 0, -1):
                    mese_nome = calendar.month_name[month].capitalize()
                    f.write(f"## {mese_nome} {year}\n\n")
                    f.write("| Lu | Ma | Me | Gi | Ve | Sa | Do |\n")
                    f.write("|----|----|----|----|----|----|----|\n")

                    month_days = cal.monthdayscalendar(int(year), month)

                    for week in month_days:
                        row = []
                        for day in week:
                            if day == 0:
                                row.append(" ")
                            else:
                                note_file = f"{year}-{month:02d}-{day:02d}.md"
                                # Verifica se la nota c’è in notes_by_year
                                note_path = None
                                for d, relpath in dates:
                                    if d.year == int(year) and d.month == month and d.day == day:
                                        note_path = relpath
                                        break
                                if note_path:
                                    row.append(f"[{day}]({note_path})")
                                else:
                                    row.append(str(day))
                        f.write("| " + " | ".join(row) + " |\n")
                    f.write("\n")  # Riga vuota tra i mesi

    except Exception as e:
        print(f"Errore durante l'aggiornamento del calendario: {e}")

def UpdateStatistics():
    """
    Aggiorna il file STATISTICS_FILE con tutte le statistiche del vault.
    Include:
    - Numero di note per anno
    - Numero di parole per mese nell'ultimo anno
    - Media parole per nota
    """
    # Dizionari per raccogliere dati
    notes_by_year = {}
    words_by_year_month = {}
    all_dates = []

    # Scansiona il VAULT_DIR
    for root, dirs, files in os.walk(VAULT_DIR):
        if D_WEEKS in root or D_ASSETS in root:
            continue

        for file in files:
            if file.endswith(".md") and not file.startswith("weekly"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, VAULT_DIR).replace("\\", "/")
                
                # Estrai anno e mese
                match = re.match(r"(\d{4})-(\d{2})-(\d{2})\.md", file)
                if match:
                    year, month, day = match.groups()
                    year = int(year)
                    month = int(month)
                    day = int(day)

                    # Aggiungi nota all'anno
                    if year not in notes_by_year:
                        notes_by_year[year] = []
                    notes_by_year[year].append(relative_path)

                    # Conta parole
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        word_count = len(content.split())
                    if year not in words_by_year_month:
                        words_by_year_month[year] = {}
                    if month not in words_by_year_month[year]:
                        words_by_year_month[year][month] = 0
                    words_by_year_month[year][month] += word_count

                    # Memorizza date per streak
                    all_dates.append(datetime(year, month, int(day)))

    # Calcola streak di giorni consecutivi
    all_dates = sorted(all_dates)
    max_streak = 0
    current_streak = 1
    streak_now = 1
    for i in range(1, len(all_dates)):
        delta = (all_dates[i] - all_dates[i-1]).days
        if delta == 1:
            current_streak += 1
        else:
            current_streak = 1
        max_streak = max(max_streak, current_streak)
    if all_dates:
        streak_now = 1
        last_date = all_dates[-1]
        for d in reversed(all_dates[:-1]):
            if (last_date - d).days == 1:
                streak_now += 1
                last_date = d
            else:
                break

    # Calcola media parole per nota
    total_words = sum(sum(words_by_year_month[y].values()) for y in words_by_year_month)
    total_notes = sum(len(notes_by_year[y]) for y in notes_by_year)
    avg_words_per_note = total_words // total_notes if total_notes else 0

    # Scrive statistics.md
    try:
        with open(STAT_INFO_FILE, "w", encoding="utf-8") as f:
            f.write("# Statistiche complessive\n\n")

            # Note per anno
            f.write("## Note per anno\n")
            for year in sorted(notes_by_year.keys(), reverse=True):
                count = len(notes_by_year[year])
                bar = "█" * (count // 3)  # scala semplice
                f.write(f"{year}: {bar} {count} note\n")
            f.write("\n")

            # Statistiche mensili ultimo anno
            last_year = max(notes_by_year.keys())
            f.write(f"## Statistiche mensili {last_year}\n")
            for month in range(1, 13):
                words = words_by_year_month.get(last_year, {}).get(month, 0)
                note_count = sum(1 for n in notes_by_year[last_year] if f"{last_year}-{month:02}" in n)
                bar = "█" * (words // 1000 if words else 0)
                month_name = datetime(last_year, month, 1).strftime("%B")
                f.write(f"{month_name:<9} | {bar:<10} {words} parole, {note_count} note\n")
            f.write("\n")

            # Streak di scrittura
            # f.write("## Giorni consecutivi di scrittura\n")
            # f.write(f"Streak massimo: {max_streak} giorni\n")
            # f.write(f"Streak attuale: {streak_now} giorni\n\n")

            # Media parole per nota
            f.write("## Media parole per nota\n")
            f.write(f"Media generale: {avg_words_per_note} parole per nota\n\n")

        # print(f"File '{os.path.relpath(STAT_INFO_FILE, VAULT_DIR)}' aggiornato con successo.")
    except Exception as e:
        print(f"Errore durante l'aggiornamento delle statistiche: {e}")

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
        UpdateCalendarIndex(notes_by_year)
        UpdateStatistics()

    except Exception as e:
        print(f"Errore durante l'aggiornamento degli indici: {e}")

def AddNewNote():
    """
    Aggiunge una nuova nota al path YYYY/YYYY-MM-DD.md.
    Se l'anno esiste ma la nota no, aggiunge la nota del giorno.
    La nota è una copia di templates/void-notes.md con il titolo modificato.
    """
    # ######################## # 
    # Ottieni la data di oggi
    # ######################## # 
    today = date.today()
    note_filename = GenerateNoteName(today)
    year, month, day = note_filename.split(".")[0].split("-")
    year_dir = YEAR_DIR
    note_path = os.path.join(year_dir, note_filename)

    # ######################## # 
    # Path del template
    # ######################## # 
    template_path = os.path.join(SCRIPT_DIR, "templates", "void-notes.md")

    # ######################## # 
    # Controlla se la directory dell'anno esiste, altrimenti creala
    # ######################## # 
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)

    # ######################## # 
    # Controlla se la nota esiste già
    # ######################## # 
    if os.path.exists(note_path):
        print(f"La nota '{os.path.relpath(note_path, VAULT_DIR)}' esiste già. Nessuna azione necessaria.")
        return
    
    # ######################## # 
    # Prima di copiare il template estrae dalla nota piú recente il blocco ## next per le note che si vogliono ricordare dal giorno prima
    # ######################## # 
    md_files = []
    for file in os.listdir(year_dir):
        if file.endswith(".md") and file != note_filename:
            if re.match(r"\d{4}-\d{2}-\d{2}\.md", file):
                md_files.append(file)

    md_files = sorted(md_files)
    prev_note = None

    # 1. Cerca nell'anno corrente
    for f in reversed(md_files):
        if f < note_filename:
            prev_note = os.path.join(year_dir, f)
            break

    # 2. Se non trovata, cerca nell'anno precedente
    if prev_note is None:
        current_year = int(note_filename[:4])
        prev_year_dir = os.path.join(os.path.dirname(year_dir), str(current_year - 1))

        if os.path.exists(prev_year_dir):
            prev_md_files = []
            for file in os.listdir(prev_year_dir):
                if re.match(r"\d{4}-\d{2}-\d{2}\.md", file):
                    prev_md_files.append(file)

            if prev_md_files:
                prev_md_files = sorted(prev_md_files)
                prev_note = os.path.join(prev_year_dir, prev_md_files[-1])
    
    # ######################## #
    # Estrai il contenuto della sezione B_NEXT dalla nota precedente
    # ######################## #
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

    # ######################## #
    # Copia il template nella posizione della nuova nota
    # ######################## #
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
    
    # ######################## #
    # Aggiorna istantaneamente l'indice
    # ######################## #
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
                            if stripped_line == B_TAGS or stripped_line == B_NEXT:  # Salta la sezione ## tags e ## next
                                current_section = None
                                continue
                            current_section = stripped_line
                            if current_section not in sections:
                                sections[current_section] = []
                            continue  # Non aggiungere il titolo della sezione al contenuto
                        if current_section:  # Aggiungi contenuto solo se la sezione è valida
                            # Correggi i link Markdown che puntano a file asset
                            line = re.sub(r'\]\((assets/[^)]+)\)', r'](../\1)', line) # Trasforma i link markdown da `](assets/file.md)` a `](../assets/file.md)`
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

def DoBackup(includeAssets):
    """
    Crea un backup in formato .tar del diario.
    Mostra una finestra grafica per scegliere nome e percorso di salvataggio.
    
    :param include_assets: se False esclude assets/ e weeks/
    """

    # Nasconde la finestra principale Tk
    root = tk.Tk()
    root.withdraw()
    
    root.attributes('-topmost', True) # sempre in primo piano

    # Data odierna in formato YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")

    # Nome file con data inclusa
    default_name = f"backup-journal-{today}.tar"
    
    # Finestra "Salva con nome"
    file_path = filedialog.asksaveasfilename(
        title="Salva backup",
        defaultextension=".tar",
        filetypes=[("Tar archive", "*.tar")],
        initialdir=os.getcwd(),
        initialfile=default_name
    )

    if not file_path:
        print("Backup annullato.")
        sys.exit(1)

    # Creazione archivio tar
    with tarfile.open(file_path, "w") as tar:
        for root_dir, dirs, files in os.walk(VAULT_DIR):
            # Se non vogliamo includere assets e weeks → li escludiamo
            if not includeAssets:
                # Escludi cartelle "assets" e "weeks"
                dirs[:] = [d for d in dirs if d not in [D_ASSETS, D_WEEKS]]
            else:
                dirs[:] = [d for d in dirs if d not in [D_WEEKS]]

            for file in files:
                full_path = os.path.join(root_dir, file)
                # Path relativo per mantenere struttura dentro il tar
                arcname = os.path.relpath(full_path, start=os.path.dirname(VAULT_DIR))
                tar.add(full_path, arcname=arcname)


## MAIN FUNCTION ##
def main():  
    # Creazione del parser
    parser = argparse.ArgumentParser(
        prog="JournalScript.py",
        description="Make script per gestire la conversione di note in PDF. Tips: genera un repo git vuoto e inserisci questo come un sottomodulo prima di lanciare un --init",
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio",
        add_help=False
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
    parser.add_argument("-b", "--backup",     action="store_true",  help="Effettua il backup in formato tar di tutta la cartella myjournal, con richiesta di salvare o meno gli assets")
    parser.add_argument("-v", "--version",    action="store_true",  help="Mostra la versione dello script")
    parser.add_argument("-h", "--help",       action="store_true",  help="Mostra questo messaggio di aiuto")

    # Parsing degli argomenti
    args = parser.parse_args()

    # Gestione delle opzioni
    if args.init:
        print(f"Creazione di un vault di partenza...")
        InitVault()
        print(f"Enjoy your new journal vault! =^._.^=ﾉ")
    
    if args.version:
        print("JournalScript v"+JOURNALSCRIPT_VERSION)
    
    elif args.new:
        print("Creazione di una nuova nota...")
        AddNewNote()
        
    elif args.update:
        print("Aggiornamento dell'indice...")
        UpdateIndex()
        print("Indici (main, tags e calendar) aggiornati! (=^･ｪ･^=)ﾉ")
    
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
        
    elif args.backup:
        include_assets = False
        print("Generazione del backup...")
        
        assets_choice = input("Inserire anche gli assets? [YySs/Nn] (vuoto per saltarli): ")
        
        if assets_choice.lower() not in ["y", "s", "n", ""]:
            print("Scelta non valida, backup annullato...")
            sys.exit(1)
        elif assets_choice.lower() in ["y", "s"]:
            include_assets = True
        
        DoBackup(include_assets)
        print("Backup Eseguito con successo!")
        
    elif args.help:
        print(pyfiglet.figlet_format("Journal Script", font="chunky"))
        parser.print_help()
        sys.exit(0)
    else:
        print("Errore: nessuna opzione valida selezionata.")
        print(pyfiglet.figlet_format("Journal Script", font="chunky"))
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()