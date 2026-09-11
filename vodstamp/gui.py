import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from zoneinfo import ZoneInfo
from .core import ACCOUNTS, output, stamp, video_id
from .api import Http, Riot, youtube_range, ApiError
from .credentials import load_riot_key
from .diagnostics import diagnose
from . import downloader
import re
from pathlib import Path

class App:
    def __init__(self, root):
        self.root, self.rows, self.events = root, [], queue.Queue()
        self.download_buttons = {}
        self.downloading = False
        root.title('LoL VOD · Timestamp YouTube')
        root.geometry('1080x760')
        root.minsize(850, 650)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Download.TButton', font=('Segoe UI', 9), padding=(4, 0))
        probe = ttk.Button(root, text='Download', style='Download.TButton')
        root.update_idletasks()
        style.configure('Treeview', rowheight=max(34, probe.winfo_reqheight() + 6))
        probe.destroy()
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        defaults = dict(twitch='', twitch_offset='0', url='', start='', end='', zone='Europe/Rome', offset='0', accounts='; '.join(ACCOUNTS))
        self.values = {k: tk.StringVar(value=v) for k, v in defaults.items()}
        try:
            initial_key = load_riot_key()
            key_status = 'Chiave Riot caricata dal file. Inserisci il link del VOD.'
        except ValueError as error:
            initial_key, key_status = '', str(error)
        self.values['riot'] = tk.StringVar(value=initial_key)
        self.test_buttons = []
        ttk.Label(frame, text='Timestamp delle tue partite', font=('Segoe UI', 19, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
        for row_index, label, left_key, right_key in [
                (1, 'URL VOD', 'url', 'twitch'),
                (2, 'Offset (in seconds)', 'offset', 'twitch_offset')]:
            ttk.Label(frame, text=label).grid(row=row_index, column=0, sticky='w', padx=(0, 12), pady=3)
            pair = ttk.Frame(frame)
            pair.grid(row=row_index, column=1, sticky='ew', pady=3)
            pair.columnconfigure(1, weight=1, uniform='pair')
            pair.columnconfigure(3, weight=1, uniform='pair')
            ttk.Label(pair, text='YouTube').grid(row=0, column=0, padx=(0, 8))
            ttk.Entry(pair, textvariable=self.values[left_key], width=12).grid(row=0, column=1, sticky='ew')
            ttk.Label(pair, text='Twitch').grid(row=0, column=2, padx=(16, 8))
            ttk.Entry(pair, textvariable=self.values[right_key], width=12).grid(row=0, column=3, sticky='ew')
        youtube_test = ttk.Button(frame, text='Test YouTube', command=lambda: self.test_api('YouTube'))
        youtube_test.grid(row=1, column=2, padx=(8, 0))
        self.test_buttons.append(youtube_test)
        fields = [('start', 'Start'), ('end', 'End'), ('zone', 'Timezone IANA'), ('accounts', 'Account EUW (separati da ;)'), ('riot', 'Riot Personal API Key')]
        for index, (key, label) in enumerate(fields, 3):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky='w', padx=(0, 12), pady=3)
            widget = ttk.Entry(frame, textvariable=self.values[key], show='•' if key == 'riot' else '', state='readonly' if key in ('start', 'end', 'riot') else 'normal')
            widget.grid(row=index, column=1, sticky='ew', pady=3)
            if key == 'riot':
                button = ttk.Button(frame, text='Test Riot', command=lambda: self.test_api('Riot'))
                button.grid(row=index, column=2, padx=(8, 0))
                self.test_buttons.append(button)
        ttk.Label(frame, text='Start / End: GG-MM-AAAA HH:MM:SS. Test YouTube legge gli orari. Nessuna preferenza salvata.').grid(row=10, column=0, columnspan=2, sticky='w', pady=8)
        actions = ttk.Frame(frame)
        actions.grid(row=11, column=0, columnspan=2, sticky='ew')
        self.generate = ttk.Button(actions, text='Genera timestamp', command=self.run)
        self.generate.pack(side='left')
        ttk.Button(actions, text='Includi/escludi righe', command=self.toggle).pack(side='left', padx=8)
        ttk.Button(actions, text='Seleziona tutti', command=lambda: self.select_all(True)).pack(side='left')
        ttk.Button(actions, text='Escludi tutti', command=lambda: self.select_all(False)).pack(side='left', padx=8)
        ttk.Button(actions, text='Copia', command=self.copy).pack(side='right')
        self.status = tk.StringVar(value=key_status)
        ttk.Label(frame, textvariable=self.status, wraplength=1000).grid(row=12, column=0, columnspan=2, sticky='w', pady=8)
        table = ttk.Frame(frame)
        table.grid(row=13, column=0, columnspan=2, sticky='nsew')
        frame.rowconfigure(13, weight=1)
        self.tree = ttk.Treeview(table, columns=('use', 'time', 'account', 'title', 'download'), show='headings', selectmode='extended')
        for key, title, width in [('use', 'Inclusa', 55), ('time', 'Timestamp', 90), ('account', 'Account', 140), ('title', 'Titolo', 240), ('download', 'Download', 180)]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=170 if key == 'download' else 45)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<space>', lambda _: self.toggle())
        self.tree.bind('<Double-1>', self.edit)
        self.preview = tk.Text(frame, height=6, wrap='word')
        self.preview.grid(row=14, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        self.values['url'].trace_add('write', self.clear_dates)
        root.after(100, self.poll)

    def place_download_buttons(self):
        enabled = {}
        for platform, key, offset_key, validator in [('Twitch', 'twitch', 'twitch_offset', downloader.twitch_id), ('Youtube', 'url', 'offset', video_id)]:
            try:
                validator(self.values[key].get())
                int(self.values[offset_key].get())
                enabled[platform] = not self.downloading
            except ValueError:
                enabled[platform] = False
        for item in list(self.download_buttons):
            if not self.tree.exists(item):
                for button in self.download_buttons.pop(item).values():
                    button.destroy()
        for item in self.tree.get_children():
            if item not in self.download_buttons:
                self.download_buttons[item] = {p: ttk.Button(self.tree, text=p, style='Download.TButton', command=lambda i=item, platform=p: self.download_row(i, platform)) for p in ('Youtube', 'Twitch')}
            box = self.tree.bbox(item, 'download')
            for index, (platform, button) in enumerate(self.download_buttons[item].items()):
                button.configure(state='normal' if enabled[platform] else 'disabled')
                if box:
                    x, y, width, height = box
                    half = (width-9)//2
                    button.place(x=x+3+index*(half+3), y=y+2, width=half, height=height-4)
                else:
                    button.place_forget()

    def download_row(self, item, platform='Twitch'):
        if self.downloading or not self.tree.exists(item):
            return
        row = self.rows[int(item)]
        youtube = platform == 'Youtube'
        url = self.values['url' if youtube else 'twitch'].get().strip()
        try:
            (video_id if youtube else downloader.twitch_id)(url)
            start, end = downloader.trim(row, self.values['offset' if youtube else 'twitch_offset'].get())
        except ValueError as error:
            messagebox.showerror('Download', str(error))
            return
        window = tk.Toplevel(self.root)
        window.title('Download ' + platform)
        window.transient(self.root)
        window.grab_set()
        ttk.Label(window, text=row.title, padding=12).pack()
        ttk.Label(window, text=f'Secondi nel VOD {platform}. Inclusi 10 s prima e 20 s dopo.').pack(padx=12)
        begin, finish = tk.StringVar(value=str(start)), tk.StringVar(value=str(end))
        for label, variable in [('Start (seconds)', begin), ('End (seconds)', finish)]:
            ttk.Label(window, text=label).pack(pady=(8, 0))
            ttk.Entry(window, textvariable=variable).pack(padx=12)
        ttk.Label(window, text=f'Ritaglio proposto: {stamp(start)} — {stamp(end)}').pack(padx=12, pady=8)
        def launch():
            try:
                a, b = int(begin.get()), int(finish.get())
                if a < 0 or b <= a:
                    raise ValueError('Start deve essere >= 0 ed End maggiore di Start.')
                filename = re.sub(r'[<>:"/\\|?*]', '_', row.title)[:100] + '_' + row.match_id + '_' + platform + '.mp4'
                target = filedialog.asksaveasfilename(parent=window, defaultextension='.mp4', filetypes=[('Video MP4', '*.mp4')], initialfile=filename)
                if not target:
                    return
                if Path(target).exists():
                    raise ValueError('Scegli un nome nuovo: i file esistenti non vengono sovrascritti.')
                args = (downloader.youtube_command if youtube else downloader.command)(url, a, b, target)
            except ValueError as error:
                messagebox.showerror('Download', str(error), parent=window)
                return
            window.destroy()
            self.downloading = True
            self.status.set('Download ' + platform + ' in corso…')
            def worker():
                try:
                    downloader.download(args, lambda text: self.events.put(('download_status', text)), target)
                    self.events.put(('download_done', target))
                except (ValueError, OSError) as error:
                    self.events.put(('download_error', str(error)))
            threading.Thread(target=worker, daemon=True).start()
        ttk.Button(window, text='Scegli destinazione e scarica', command=launch).pack(padx=12, pady=12)

    def refresh(self):
        for i, row in enumerate(self.rows):
            values = ('✓' if row.selected else '', stamp(row.seconds), row.account, row.title, '')
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
        if self.tree.identify_column(event.x) == '#5':
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

    def busy(self, value):
        for button in [self.generate] + self.test_buttons:
            button.configure(state='disabled' if value else 'normal')

    def clear_dates(self, *_):
        self.values['start'].set('')
        self.values['end'].set('')

    def display_bounds(self, start, end, zone):
        self.values['start'].set(start.astimezone(zone).strftime('%d-%m-%Y %H:%M:%S'))
        self.values['end'].set(end.astimezone(zone).strftime('%d-%m-%Y %H:%M:%S'))

    def test_api(self, provider):
        accounts, url = self.values['accounts'].get(), self.values['url'].get()
        try:
            key = load_riot_key() if provider == 'Riot' else ''
            if provider == 'Riot':
                self.values['riot'].set(key)
            zone = ZoneInfo(self.values['zone'].get())
        except (ValueError, KeyError):
            messagebox.showerror('Configurazione', 'Controlla Riot API.txt e la timezone IANA.')
            return
        self.busy(True)
        self.status.set('Test ' + provider + ' in corso…')
        def worker():
            if provider == 'YouTube':
                try:
                    start, end = youtube_range(Http(), url, '')
                    self.events.put(('bounds', (start, end, zone)))
                    self.events.put(('diagnostic', 'OK — Inizio e fine stream letti dalla pagina YouTube.'))
                except (ApiError, ValueError) as error:
                    self.events.put(('error', str(error)))
                except Exception:
                    self.events.put(('error', 'Lettura YouTube fallita. Riprova.'))
            else:
                self.events.put(('diagnostic', diagnose(provider, key, accounts, url)))
        threading.Thread(target=worker, daemon=True).start()

    def show_diagnostic(self, report):
        window = tk.Toplevel(self.root)
        window.title('Risultato test API')
        window.geometry('760x480')
        text = tk.Text(window, wrap='word', padx=12, pady=12)
        text.pack(fill='both', expand=True)
        text.insert('1.0', report)
        text.configure(state='disabled')
        def copy_report():
            self.root.clipboard_clear()
            self.root.clipboard_append(report)
        ttk.Button(window, text='Copia rapporto (senza chiavi)', command=copy_report).pack(pady=8)

    def run(self):
        values = {k: v.get().strip() for k, v in self.values.items()}
        try:
            accounts = [a.strip() for a in values['accounts'].split(';') if a.strip()]
            if not accounts or any('#' not in a or not all(a.rsplit('#', 1)) for a in accounts):
                raise ValueError('Account richiesti nel formato Nome#TAG, separati da ;')
            offset = int(values['offset'])
            zone = ZoneInfo(values['zone'])
            values['riot'] = load_riot_key()
            self.values['riot'].set(values['riot'])
        except (ValueError, OSError, KeyError) as error:
            messagebox.showerror('Configurazione', str(error))
            return
        self.rows = []
        self.tree.delete(*self.tree.get_children())
        self.refresh()
        self.busy(True)
        self.status.set('Recupero partite in corso…')
        def worker():
            try:
                http = Http()
                start, end = youtube_range(http, values['url'], '')
                self.events.put(('bounds', (start, end, zone)))
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
                if kind == 'download_status':
                    self.status.set(value)
                elif kind == 'download_done':
                    self.downloading = False
                    self.status.set('Download completato: ' + value)
                    messagebox.showinfo('Download completato', value)
                elif kind == 'download_error':
                    self.downloading = False
                    self.status.set('Download fallito')
                    messagebox.showerror('Download', value)
                elif kind == 'bounds':
                    self.display_bounds(*value)
                elif kind == 'status':
                    self.status.set(value)
                else:
                    self.busy(False)
                    if kind == 'diagnostic':
                        self.status.set('Test terminato. Consulta il rapporto diagnostico.')
                        self.show_diagnostic(value)
                    elif kind == 'error':
                        self.status.set(value)
                        messagebox.showerror('Recupero fallito', value)
                    else:
                        self.rows, start, end = value
                        self.refresh()
                        self.status.set(f'{len(self.rows)} partite · {start.strftime('%d-%m-%Y')} · orari nei campi Start / End · verifica matchup e correzione VOD.')
        except queue.Empty:
            pass
        self.place_download_buttons()
        self.root.after(100, self.poll)

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
