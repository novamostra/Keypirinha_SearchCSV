import keypirinha as kp
import keypirinha_util as kpu
import csv, json
import os

# EDIT PROPERTIES BASED ON YOUR OWN FILE AND REQUIREMENTS
# specify columns to search, leaving it empty will search every column
# less columns will result in faster resolve times
SEARCH_COLUMNS = ['first_name', 'last_name']
CASE_SENSITIVE = False
# suggestions will appear after typing 3 characters
MINIMUM_CHARACTERS_INPUT = 3
# maximum number of suggestions to display
MAX_RESULTS = 5

# Each result has two rows, the first one is the label and the second the description. If you define more than one columns it will join them using space
LABEL_COLUMNS = ['first_name','last_name']
DESCRIPTION_COLUMNS = ['phone_number','email', 'company']
# when you hit enter or double click this column will be copied to clipboard
TARGET_COLUMNS = ['phone_number']

# Where your CSV file is located
RELATIVE_FILEPATH = "data.csv" # set it to None and it will use the FILEPATH instead
FILEPATH = "c:\data.csv" # is not used if RELATIVE_FILEPATH is defined
# ------------------- END OF PROPERTIES -------------------

class PhoneBook(kp.Plugin):

    def __init__(self):
        super().__init__()
        self._debug = True
        self.csv_data = []

    def on_start(self):
        self.dbg("PhoneBook started")
        if(RELATIVE_FILEPATH):
            self.csv_data = self._load_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), RELATIVE_FILEPATH))
        else:
            self.csv_data = self._load_csv(FILEPATH)
            
        if self.csv_data:
            self.dbg("CSV file loaded successfully.")
        else:
            self.warn("Failed to load CSV file.")

    def on_catalog(self):
        self.dbg("on_catalog called")
        self.set_catalog([self.create_item(
            category=kp.ItemCategory.USER_BASE,
            label="Search CSV",
            short_desc="Search CSV file",
            target="search_csv",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.KEEPALL
        )])

    def on_suggest(self, user_input, items_chain):
        count = 0
        if len(user_input) < MINIMUM_CHARACTERS_INPUT:
            return
            
        if not CASE_SENSITIVE:
            search_term = user_input.lower()
        else:
            search_term = user_input
           
        if not items_chain and search_term:
            suggestions = []
 
            for row in self.csv_data:
                # Early termination if we've reached our limit
                if len(suggestions) >= MAX_RESULTS:
                    break
                
                for col in self.search_columns:
                    cell_value = row[col] if CASE_SENSITIVE else row[col].lower()
                    if search_term in cell_value:
                        label = ' '.join(str(row[col]) for col in LABEL_COLUMNS if col in row)
                        description = ' '.join(str(row[col]) for col in DESCRIPTION_COLUMNS if col in row)
                        suggestions.append(self.create_item(
                            category=kp.ItemCategory.USER_BASE,
                            label=label,
                            short_desc=description,
                            target=json.dumps(row),
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.KEEPALL 
                        ))
                        break            
                            
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        self.dbg(f"Selected row: {item.target()}")
        # Handle cases where modifier is None
        row = json.loads(item.target())

        clipboard = ' '.join(str(row[col]) for col in TARGET_COLUMNS if col in row)
        
        kpu.set_clipboard(clipboard)

    def _load_csv(self, path):
        self.dbg(f"Loading CSV file from: {path}")
        if(not os.path.exists(path)):
            self.warn(f"CSV file: {path} does not exist")
            raise RuntimeError("Plugin loading aborted because CSV file does not exist")            
        try:
            with open(path, newline='', encoding='utf-8') as csvfile:
                # Peek at the first line to determine if we have headers
                first_line = csvfile.readline()
                csvfile.seek(0)  # Rewind to beginning
                
                if first_line.strip():  # If file is not empty
                    # Try to determine if first line contains headers
                    sniffer = csv.Sniffer()
                    has_header = sniffer.has_header(first_line)
                    
                    if has_header:
                        # Use DictReader if we have headers
                        csvreader = csv.DictReader(csvfile)
                        self.headers = csvreader.fieldnames
                        data = list(csvreader)
                        all_columns = list(set(SEARCH_COLUMNS + LABEL_COLUMNS + DESCRIPTION_COLUMNS + TARGET_COLUMNS))
                        for col in all_columns:
                            if not col in self.headers:
                               self.warn(f"CSV File does not contain column: {col}")
                               raise RuntimeError("Plugin loading aborted due to missing column")                                
                    else:
                       self.warn("CSV File has no headers! Plugin will not load")
                       raise RuntimeError("Plugin loading aborted due to missing headers")
 
                    # Set search columns
                    if len(SEARCH_COLUMNS)==0:
                        self.search_columns = self.headers if self.headers else list(range(len(data[0])))
                    else:
                        self.search_columns = SEARCH_COLUMNS
                    
                    self.dbg(f"Will search in the following columns:  {self.search_columns}")
                    
                    return data
                else:
                   self.warn("CSV File os empty")
                   raise RuntimeError("Plugin loading aborted because CSV file is empty")
                    
        except Exception as e:
            self.warn(f"Error loading CSV file: {e}")
            raise RuntimeError("Plugin loading aborted")