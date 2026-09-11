import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from .core import ACCOUNTS, manual_range, output, stamp
from .api import Http, Riot, youtube_range, ApiError
from . import settings

class App:
    def __init__(self, root):
        self.root, self.rows, self.events = root, [], queue.Queue()
        root.title('LoL VOD · Timestamp YouTube')
        root.geometry('1080x760')
        root.minsize(850, 650)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Treeview', rowheight=29)
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        defaults = dict(source='YouTube', url='', start=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), hours='12', zone='Europe/Rome', offset='0', accounts='; '.join(ACCOUNTS))
        defaults.update(settings.load())
        if defaults['source'] not in ('YouTube', 'Manuale'):
            defaults['source'] = 'YouTube'
        self.values = {k: tk.StringVar(value=v) for k, v in defaults.items()}
        self.values['riot'] = tk.StringVar(value=os.environ.get('RIOT_API_KEY', ''))
        self.values['youtube'] = tk.StringVar(value=os.environ.get('YOUTUBE_API_KEY', ''))
        ttk.Label(frame, text='Timestamp delle tue partite', font=('Segoe UI', 19, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
        fields = [('source', 'Sorgente'), ('url', 'URL VOD YouTube'), ('start', 'Inizio manuale (AAAA-MM-GG HH:MM:SS)'), ('hours', 'Durata manuale (ore)'), ('zone', 'Timezone IANA'), ('offset', 'Correzione timestamp (secondi, anche negativa)'), ('accounts', 'Account EUW (separati da ;)'), ('riot', 'Riot Personal API Key'), ('youtube', 'YouTube Data API key')]
        for index, (key, label) in enumerate(fields, 1):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky='w', padx=(0, 12), pady=3)
            widget = ttk.Combobox(frame, textvariable=self.values[key], values=['YouTube', 'Manuale'], state='readonly') if key == 'source' else ttk.Entry(frame, textvariable=self.values[key], show='•' if key in ('riot', 'youtube') else '')
            widget.grid(row=index, column=1, sticky='ew', pady=3)
        ttk.Label(frame, text='Le chiavi non vengono salvate. Doppio clic su una riga: modifica titolo. Spazio: includi/escludi.').grid(row=10, column=0, columnspan=2, sticky='w', pady=8)
        actions = ttk.Frame(frame)
        actions.grid(row=11, column=0, columnspan=2, sticky='ew')
        self.generate = ttk.Button(actions, text='Genera timestamp', command=self.run)
        self.generate.pack(side='left')
        ttk.Button(actions, text='Includi/escludi righe', command=self.toggle).pack(side='left', padx=8)
        ttk.Button(actions, text='Seleziona tutti', command=lambda: self.select_all(True)).pack(side='left')
        ttk.Button(actions, text='Escludi tutti', command=lambda: self.select_all(False)).pack(side='left', padx=8)
        ttk.Button(actions, text='Copia', command=self.copy).pack(side='right')
        self.status = tk.StringVar(value='Pronto. Inserisci le chiavi e scegli un VOD oppure Manuale.')
        ttk.Label(frame, textvariable=self.status, wraplength=1000).grid(row=12, column=0, columnspan=2, sticky='w', pady=8)
        table = ttk.Frame(frame)
        table.grid(row=13, column=0, columnspan=2, sticky='nsew')
        frame.rowconfigure(13, weight=1)
        self.tree = ttk.Treeview(table, columns=('use', 'time', 'account', 'title', 'note'), show='headings', selectmode='extended')
        for key, title, width in [('use', 'Inclusa', 55), ('time', 'Timestamp', 90), ('account', 'Account', 140), ('title', 'Titolo', 240), ('note', 'Verifica', 350)]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=45)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<space>', lambda _: self.toggle())
        self.tree.bind('<Double-1>', self.edit)
        self.preview = tk.Text(frame, height=6, wrap='word')
        self.preview.grid(row=14, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        root.after(100, self.poll)

    def refresh(self):
        for i, row in enumerate(self.rows):
            values = ('✓' if row.selected else '', stamp(row.seconds), row.account, row.title, row.note)
            if self.tree.exists(str(i)):
                self.tree.item(str(i), values=values)
            else:
                self.tree.insert('', 'end', iid=str(i), values=values)
        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        self.preview.insert('1.0', output(self.rows))
        self.preview.configure(state='disabled')

    def toggle(self):
        for item in self.tree.selection():
            self.rows[int(item)].selected = not self.rows[int(item)].selected
        self.refresh()

    def select_all(self, selected):
        for row in self.rows:
            row.selected = selected
        self.refresh()

    def edit(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        if self.tree.identify_column(event.x) == '#1':
            self.rows[int(item)].selected = not self.rows[int(item)].selected
        else:
            row = self.rows[int(item)]
            title = simpledialog.askstring('Titolo partita', 'Champion vs Champion oppure Champion - modalità', initialvalue=row.title, parent=self.root)
            if title and title.strip():
                row.title = ' '.join(title.split())
        self.refresh()

    def copy(self):
        text = output(self.rows)
        if not text:
            messagebox.showinfo('Timestamp', 'Nessuna partita inclusa.')
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.set('Timestamp copiati negli appunti.')

    def run(self):
        values = {k: v.get().strip() for k, v in self.values.items()}
        try:
            accounts = [a.strip() for a in values['accounts'].split(';') if a.strip()]
            if not accounts or any('#' not in a or not all(a.rsplit('#', 1)) for a in accounts):
                raise ValueError('Account richiesti nel formato Nome#TAG, separati da ;')
            offset = int(values['offset'])
            bounds = manual_range(values['start'], values['zone'], values['hours']) if values['source'] == 'Manuale' else None
            settings.save(values)
        except (ValueError, OSError) as error:
            messagebox.showerror('Configurazione', str(error))
            return
        self.rows = []
        self.tree.delete(*self.tree.get_children())
        self.refresh()
        self.generate.configure(state='disabled')
        self.status.set('Recupero partite in corso…')
        def worker():
            try:
                http = Http()
                start, end = bounds or youtube_range(http, values['url'], values['youtube'])
                rows = Riot(http, values['riot']).collect(accounts, start, end, offset, lambda msg: self.events.put(('status', msg)))
                self.events.put(('done', (rows, start, end)))
            except (ApiError, ValueError) as error:
                self.events.put(('error', str(error)))
            except Exception:
                self.events.put(('error', 'Risposta inattesa. Verifica configurazione e riprova; nessun risultato parziale pubblicato.'))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'status':
                    self.status.set(value)
                else:
                    self.generate.configure(state='normal')
                    if kind == 'error':
                        self.status.set(value)
                        messagebox.showerror('Recupero fallito', value)
                    else:
                        self.rows, start, end = value
                        self.refresh()
                        self.status.set(f'{len(self.rows)} partite · {start.isoformat()} — {end.isoformat()} · verifica matchup e correzione VOD.')
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
