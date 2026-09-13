import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from zoneinfo import ZoneInfo
from .timezones import OPTIONS, DEFAULT, resolve
import webbrowser
from .core import ACCOUNTS, output, stamp, video_id
from .api import Http, Riot, youtube_range, ApiError
from .credentials import load_riot_key, save_riot_key
from .diagnostics import diagnose
from . import downloader
import re
from pathlib import Path

class App:
    def __init__(self, root):
        self.root, self.rows, self.events = root, [], queue.Queue()
        self.download_buttons = {}
        self.downloading = False
        root.title('Deddy’s Post Stream Suite')
        root.geometry('1180x820')
        root.minsize(980, 700)
        self.colors = {
            'bg': '#101419', 'panel': '#181e26', 'field': '#11171e',
            'raised': '#222c38', 'border': '#303b49', 'text': '#edf2f8',
            'muted': '#a4b0c0', 'blue': '#71b7ff', 'blue_dark': '#5199e5',
            'focus': '#9bd0ff', 'success': '#91c9b1',
        }
        root.configure(background=self.colors['bg'])
        self._configure_styles()
        style = ttk.Style(root)
        probe = ttk.Button(root, text='Download', style='Download.TButton')
        root.update_idletasks()
        style.configure('Treeview', rowheight=max(38, probe.winfo_reqheight() + 8))
        probe.destroy()

        frame = ttk.Frame(root, padding=(24, 12, 24, 12))
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)
        defaults = dict(twitch='', twitch_offset='0', url='', start='', end='', zone=DEFAULT, offset='0', accounts='; '.join(ACCOUNTS))
        self.values = {k: tk.StringVar(value=v) for k, v in defaults.items()}
        try:
            initial_key = load_riot_key()
            key_status = 'Riot key loaded. Enter your YouTube VOD URL.'
        except ValueError as error:
            initial_key, key_status = '', str(error)
        self.values['riot'] = tk.StringVar(value=initial_key)
        self._riot_dirty = False
        self._riot_loading = False
        self._riot_clean_value = initial_key
        self._riot_save_after = None
        self.test_buttons = []

        header = ttk.Frame(frame)
        header.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        header.columnconfigure(0, weight=1)
        title_box = ttk.Frame(header)
        title_box.grid(row=0, column=0, sticky='w')
        ttk.Label(title_box, text='Post Stream Suite', style='Title.TLabel').pack(anchor='w')
        self._link(title_box, 'Github page', 'https://github.com/Deddyn/deddys-post-stream-suite').pack(anchor='w', pady=(3, 0))
        socials = ttk.Frame(header)
        socials.grid(row=0, column=1, sticky='e')
        ttk.Label(socials, text='My socials:', style='Muted.TLabel').pack(side='left', padx=(0, 12))
        self._link(socials, 'Twitch', 'https://www.twitch.tv/deddy__/').pack(side='left', padx=(0, 18))
        self._link(socials, 'Youtube', 'https://www.youtube.com/@DeddynYT').pack(side='left')

        settings = ttk.Frame(frame, style='Panel.TFrame', padding=(14, 8))
        settings.grid(row=1, column=0, sticky='ew')
        settings.columnconfigure(0, weight=1, uniform='source')
        settings.columnconfigure(1, weight=1, uniform='source')
        ttk.Label(settings, text='Stream sources', style='PanelSection.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))
        youtube = ttk.Frame(settings, style='Panel.TFrame')
        twitch = ttk.Frame(settings, style='Panel.TFrame')
        youtube.grid(row=1, column=0, sticky='ew', padx=(0, 16))
        twitch.grid(row=1, column=1, sticky='ew')
        for box in (youtube, twitch):
            box.columnconfigure(0, weight=1)
        self._field(youtube, 0, 'YouTube VOD URL', 'url')
        self._field(twitch, 0, 'Twitch VOD URL · optional', 'twitch')
        self._offset_field(youtube, 'YouTube offset (s)', 'offset', 'Applied to timestamps and YouTube downloads')
        self._offset_field(twitch, 'Twitch offset (s)', 'twitch_offset', 'Applied to Twitch downloads')

        details = ttk.Frame(frame)
        details.grid(row=2, column=0, sticky='ew', pady=(8, 6))
        details.columnconfigure(0, weight=1, uniform='details')
        details.columnconfigure(1, weight=1, uniform='details')
        details.columnconfigure(2, weight=2, uniform='details')
        self._field(details, 0, 'Start · detected from YouTube', 'start', column=0, readonly=True, padx=(0, 12))
        self._field(details, 0, 'End · detected from YouTube', 'end', column=1, readonly=True, padx=(0, 12))
        self._field(details, 0, 'Timezone', 'zone', column=2, combo=True)
        ttk.Label(details, text='Daylight saving time adjusts automatically.', style='Caption.TLabel').grid(row=2, column=2, sticky='w', pady=(2, 0))

        account_row = ttk.Frame(frame)
        account_row.grid(row=3, column=0, sticky='ew', pady=(0, 6))
        account_row.columnconfigure(0, weight=1, uniform='account')
        account_row.columnconfigure(1, weight=1, uniform='account')
        accounts_box = ttk.Frame(account_row)
        accounts_box.grid(row=0, column=0, sticky='new', padx=(0, 16))
        accounts_box.columnconfigure(0, weight=1)
        self._field(accounts_box, 0, 'EUW accounts · separate with ;', 'accounts')
        key_box = ttk.Frame(account_row)
        key_box.grid(row=0, column=1, sticky='ew')
        key_box.columnconfigure(0, weight=1)
        self._link(key_box, 'Riot Personal API Key ↗', 'https://developer.riotgames.com/app-type').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 4))
        ttk.Entry(key_box, textvariable=self.values['riot'], show='•').grid(row=1, column=0, sticky='ew')
        button = ttk.Button(key_box, text='Test Riot', command=lambda: self.test_api('Riot'))
        button.grid(row=1, column=1, padx=(8, 0))
        self.test_buttons.append(button)
        self.riot_status = tk.StringVar(value='Loaded from Riot API.txt' if initial_key else 'Paste your key here; Riot API.txt is ready.')
        ttk.Label(key_box, textvariable=self.riot_status, style='Caption.TLabel', wraplength=440).grid(row=2, column=0, sticky='w', pady=(3, 0))

        workspace = ttk.Frame(frame)
        workspace.grid(row=4, column=0, sticky='nsew')
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(2, weight=1)
        action_bar = ttk.Frame(workspace, padding=(0, 6, 0, 5))
        action_bar.grid(row=0, column=0, sticky='ew')
        self.generate = ttk.Button(action_bar, text='Find Matches', style='Primary.TButton', command=self.run)
        self.generate.pack(side='left')
        self.status = tk.StringVar(value=key_status)
        ttk.Label(action_bar, textvariable=self.status, style='Status.TLabel', wraplength=760).pack(side='left', padx=(16, 0))

        match_header = ttk.Frame(workspace)
        match_header.grid(row=1, column=0, sticky='ew', pady=(2, 5))
        ttk.Label(match_header, text='Matches', style='Section.TLabel').pack(side='left')
        self.selected_count = tk.StringVar(value='0 selected')
        ttk.Label(match_header, textvariable=self.selected_count, style='Muted.TLabel').pack(side='left', padx=(14, 0))
        ttk.Button(match_header, text='Toggle selected', command=self.toggle).pack(side='right')
        ttk.Button(match_header, text='Exclude all', command=lambda: self.select_all(False)).pack(side='right', padx=8)
        ttk.Button(match_header, text='Select all', command=lambda: self.select_all(True)).pack(side='right')

        table = ttk.Frame(workspace, style='Table.TFrame')
        table.grid(row=2, column=0, sticky='nsew')
        self.tree = ttk.Treeview(table, columns=('use', 'time', 'account', 'title', 'download'), show='headings', selectmode='extended')
        for key, title, width, stretch in [('use', 'Include', 64, False), ('time', 'Timestamp', 110, False), ('account', 'Account', 170, False), ('title', 'Match', 360, True), ('download', 'Download', 220, False)]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=200 if key == 'download' else 55, stretch=stretch)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<space>', lambda _: self.toggle())
        self.tree.bind('<Double-1>', self.edit)
        preview_header = ttk.Frame(workspace)
        preview_header.grid(row=3, column=0, sticky='ew', pady=(6, 4))
        ttk.Label(preview_header, text='YouTube timestamps', style='Section.TLabel').pack(side='left')
        ttk.Label(preview_header, text='Double-click a match title to edit it.', style='Muted.TLabel').pack(side='left', padx=(16, 0))
        ttk.Button(preview_header, text='Copy timestamps', style='Primary.TButton', command=self.copy).pack(side='right')
        self.preview = tk.Text(
            workspace, height=3, wrap='word', background=self.colors['field'], foreground=self.colors['text'],
            insertbackground=self.colors['text'], selectbackground=self.colors['blue_dark'], relief='flat',
            borderwidth=1, highlightthickness=1, highlightbackground=self.colors['border'],
            highlightcolor=self.colors['focus'], padx=12, pady=6, font=('Consolas', 10), takefocus=True,
        )
        self.preview.grid(row=4, column=0, sticky='ew')
        self.values['url'].trace_add('write', self.clear_dates)
        self.values['riot'].trace_add('write', self._riot_edited)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def _set_riot_value(self, value):
        self._riot_loading = True
        try:
            self.values['riot'].set(value)
        finally:
            self._riot_loading = False
        self._riot_clean_value = value
        self._riot_dirty = False

    def _riot_edited(self, *_):
        if self._riot_loading:
            return
        if self.values['riot'].get() == self._riot_clean_value:
            self._riot_dirty = False
            if self._riot_save_after is not None:
                self.root.after_cancel(self._riot_save_after)
                self._riot_save_after = None
            return
        self._riot_dirty = True
        self.riot_status.set('Saving Riot key…')
        if self._riot_save_after is not None:
            self.root.after_cancel(self._riot_save_after)
        self._riot_save_after = self.root.after(450, self._save_riot_edit)

    def _save_riot_edit(self):
        self._riot_save_after = None
        if not self._riot_dirty:
            return True
        key = self.values['riot'].get().strip()
        try:
            save_riot_key(key)
        except (ValueError, OSError) as error:
            self.riot_status.set('Riot key not saved: ' + str(error))
            return False
        self._riot_dirty = False
        self._riot_clean_value = key
        self.riot_status.set('Riot key saved to Riot API.txt.')
        return True

    def _riot_key_for_action(self):
        if self._riot_dirty:
            key = self.values['riot'].get().strip()
            saved = self._save_riot_edit()
            if not key or any(character.isspace() for character in key):
                raise ValueError('Enter one Riot API key without spaces or extra lines.')
            if not saved:
                self.status.set('Using edited Riot key for this action; Riot API.txt was not saved.')
            return key
        key = load_riot_key()
        self._set_riot_value(key)
        self.riot_status.set('Loaded from Riot API.txt.')
        return key

    def close(self):
        if self._riot_save_after is not None:
            self.root.after_cancel(self._riot_save_after)
            self._riot_save_after = None
        if self._riot_dirty and not self._save_riot_edit():
            close_anyway = messagebox.askyesno(
                'Riot key not saved',
                'Riot API.txt could not be saved. Close without saving your edited key?',
                parent=self.root,
                icon='warning',
                default='no',
            )
            if not close_anyway:
                return
        self.root.destroy()

    def _configure_styles(self):
        c = self.colors
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', background=c['bg'], foreground=c['text'], font=('Segoe UI', 10))
        style.configure('TFrame', background=c['bg'])
        style.configure('Panel.TFrame', background=c['panel'])
        style.configure('Table.TFrame', background=c['border'], borderwidth=1, relief='solid')
        style.configure('TLabel', background=c['bg'], foreground=c['text'])
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'), foreground=c['text'])
        style.configure('Section.TLabel', font=('Segoe UI', 13, 'bold'), foreground=c['text'])
        style.configure('PanelSection.TLabel', background=c['panel'], foreground=c['text'], font=('Segoe UI', 13, 'bold'))
        style.configure('Muted.TLabel', foreground=c['muted'])
        style.configure('Caption.TLabel', foreground=c['muted'], font=('Segoe UI', 8))
        style.configure('Status.TLabel', foreground=c['success'])
        style.configure('Field.TLabel', background=c['panel'], foreground=c['muted'], font=('Segoe UI', 9))
        style.configure('PanelMuted.TLabel', background=c['panel'], foreground=c['muted'], font=('Segoe UI', 8))
        style.configure('TEntry', fieldbackground=c['field'], foreground=c['text'], bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'], padding=(8, 4))
        style.map('TEntry', fieldbackground=[('readonly', c['field']), ('disabled', c['field'])], foreground=[('readonly', c['text']), ('disabled', c['muted'])], bordercolor=[('focus', c['focus'])])
        style.configure('TCombobox', fieldbackground=c['field'], background=c['raised'], foreground=c['text'], arrowcolor=c['muted'], bordercolor=c['border'], padding=(8, 5))
        style.map('TCombobox', fieldbackground=[('readonly', c['field'])], foreground=[('readonly', c['text'])], bordercolor=[('focus', c['focus'])], arrowcolor=[('active', c['text'])])
        style.configure('TButton', background=c['raised'], foreground=c['text'], bordercolor=c['border'], focusthickness=2, focuscolor=c['focus'], padding=(12, 5), font=('Segoe UI', 9, 'bold'))
        style.map('TButton', background=[('active', '#2b3745'), ('pressed', c['field']), ('disabled', c['panel'])], foreground=[('disabled', '#6f7a88')], bordercolor=[('focus', c['focus'])])
        style.configure('Primary.TButton', background=c['blue'], foreground=c['bg'], bordercolor=c['blue'], padding=(18, 8), font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton', background=[('active', '#89c4ff'), ('pressed', c['blue_dark']), ('disabled', '#40566d')], foreground=[('disabled', '#8b9cad')], bordercolor=[('focus', c['focus'])])
        style.configure('Download.TButton', font=('Segoe UI', 9, 'bold'), padding=(4, 2), background=c['raised'], foreground=c['text'], bordercolor=c['border'])
        style.configure('Youtube.Download.TButton', foreground='#f4b6b6')
        style.configure('Twitch.Download.TButton', foreground='#cebaff')
        style.configure('Treeview', background=c['panel'], fieldbackground=c['panel'], foreground=c['text'], borderwidth=0, font=('Segoe UI', 10))
        style.map('Treeview', background=[('selected', '#1b3a55')], foreground=[('selected', c['text'])])
        style.configure('Treeview.Heading', background=c['raised'], foreground=c['muted'], bordercolor=c['border'], relief='flat', font=('Segoe UI', 9, 'bold'), padding=(8, 7))
        style.map('Treeview.Heading', background=[('active', '#293442')])
        style.configure('Vertical.TScrollbar', background=c['raised'], troughcolor=c['field'], bordercolor=c['field'], arrowcolor=c['muted'])

    def _link(self, parent, text, url):
        label = tk.Label(
            parent, text=text, background=self.colors['bg'], foreground=self.colors['blue'],
            activeforeground=self.colors['focus'], activebackground=self.colors['bg'],
            font=('Segoe UI', 10, 'underline'), cursor='hand2', takefocus=True,
            highlightthickness=2, highlightbackground=self.colors['bg'], highlightcolor=self.colors['focus'],
            borderwidth=0, padx=2, pady=1,
        )
        open_url = lambda _event=None: webbrowser.open(url)
        label.bind('<Button-1>', open_url)
        label.bind('<Return>', open_url)
        label.bind('<space>', open_url)
        return label

    def _field(self, parent, row, label, key, column=0, readonly=False, combo=False, padx=0):
        ttk.Label(parent, text=label, style='Field.TLabel' if parent.cget('style') == 'Panel.TFrame' else 'Muted.TLabel').grid(row=row, column=column, sticky='w', padx=padx, pady=(0, 4))
        if combo:
            widget = ttk.Combobox(parent, textvariable=self.values[key], values=list(OPTIONS), state='readonly', height=18)
        else:
            widget = ttk.Entry(parent, textvariable=self.values[key], state='readonly' if readonly else 'normal')
        widget.grid(row=row + 1, column=column, sticky='ew', padx=padx)
        return widget

    def _offset_field(self, parent, label, key, help_text):
        row = 2
        ttk.Label(parent, text=label, style='Field.TLabel').grid(row=row, column=0, sticky='w', pady=(7, 3))
        line = ttk.Frame(parent, style='Panel.TFrame')
        line.grid(row=row + 1, column=0, sticky='ew')
        ttk.Entry(line, textvariable=self.values[key], width=12).pack(side='left')
        ttk.Label(line, text=help_text, style='PanelMuted.TLabel').pack(side='left', padx=(12, 0))

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
                self.download_buttons[item] = {
                    p: ttk.Button(
                        self.tree, text=p, style=f'{p}.Download.TButton',
                        command=lambda i=item, platform=p: self.download_row(i, platform),
                    ) for p in ('Youtube', 'Twitch')
                }
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
        window.configure(background=self.colors['bg'])
        window.resizable(False, False)
        window.transient(self.root)
        window.grab_set()
        body = ttk.Frame(window, padding=20)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=row.title, style='Section.TLabel', wraplength=480).pack(anchor='w')
        ttk.Label(body, text=f'Seconds in the {platform} VOD. Includes 10 s before and 20 s after.', style='Muted.TLabel').pack(anchor='w', pady=(4, 12))
        begin, finish = tk.StringVar(value=str(start)), tk.StringVar(value=str(end))
        for label, variable in [('Start (seconds)', begin), ('End (seconds)', finish)]:
            ttk.Label(body, text=label, style='Muted.TLabel').pack(anchor='w', pady=(8, 4))
            ttk.Entry(body, textvariable=variable, width=44).pack(fill='x')
        ttk.Label(body, text=f'Suggested trim: {stamp(start)} — {stamp(end)}', style='Muted.TLabel').pack(anchor='w', pady=(10, 0))
        def launch():
            try:
                a, b = int(begin.get()), int(finish.get())
                if a < 0 or b <= a:
                    raise ValueError('Start must be >= 0 and End must be greater than Start.')
                filename = re.sub(r'[<>:"/\\|?*]', '_', row.title)[:100] + '_' + row.match_id + '_' + platform + '.mp4'
                target = filedialog.asksaveasfilename(parent=window, defaultextension='.mp4', filetypes=[('Video MP4', '*.mp4')], initialfile=filename)
                if not target:
                    return
                if Path(target).exists():
                    raise ValueError('Choose a new filename: existing files will not be overwritten.')
                args = (downloader.youtube_command if youtube else downloader.command)(url, a, b, target)
            except ValueError as error:
                messagebox.showerror('Download', str(error), parent=window)
                return
            window.destroy()
            self.downloading = True
            self.status.set('Download ' + platform + ' in progress…')
            def worker():
                try:
                    downloader.download(args, lambda text: self.events.put(('download_status', text)), target)
                    self.events.put(('download_done', target))
                except (ValueError, OSError) as error:
                    self.events.put(('download_error', str(error)))
            threading.Thread(target=worker, daemon=True).start()
        ttk.Button(body, text='Choose destination and download', style='Primary.TButton', command=launch).pack(anchor='e', pady=(16, 0))

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
        self.selected_count.set(f'{sum(row.selected for row in self.rows)} selected')

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
            title = simpledialog.askstring('Match title', 'Champion vs Champion or Champion - mode', initialvalue=row.title, parent=self.root)
            if title and title.strip():
                row.title = ' '.join(title.split())
        self.refresh()

    def copy(self):
        text = output(self.rows)
        if not text:
            messagebox.showinfo('Timestamp', 'No matches selected.')
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.set('Timestamps copied to clipboard.')

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
            key = self._riot_key_for_action() if provider == 'Riot' else ''
            zone = resolve(self.values['zone'].get())
        except (ValueError, KeyError):
            messagebox.showerror('Configuration', 'Check Riot API.txt and your timezone.')
            return
        self.busy(True)
        self.status.set('Test ' + provider + ' in progress…')
        def worker():
            if provider == 'YouTube':
                try:
                    start, end = youtube_range(Http(), url, '')
                    self.events.put(('bounds', (start, end, zone)))
                    self.events.put(('diagnostic', 'OK — Stream start and end read from YouTube.'))
                except (ApiError, ValueError) as error:
                    self.events.put(('error', str(error)))
                except Exception:
                    self.events.put(('error', 'Could not read YouTube metadata. Try again.'))
            else:
                self.events.put(('diagnostic', diagnose(provider, key, accounts, url)))
        threading.Thread(target=worker, daemon=True).start()

    def show_diagnostic(self, report):
        window = tk.Toplevel(self.root)
        window.title('API test results')
        window.geometry('760x480')
        window.minsize(560, 360)
        window.configure(background=self.colors['bg'])
        body = ttk.Frame(window, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='API test results', style='Section.TLabel').pack(anchor='w', pady=(0, 10))
        text = tk.Text(
            body, wrap='word', padx=12, pady=12, background=self.colors['field'],
            foreground=self.colors['text'], insertbackground=self.colors['text'],
            selectbackground=self.colors['blue_dark'], relief='flat', borderwidth=1,
            highlightthickness=1, highlightbackground=self.colors['border'],
            highlightcolor=self.colors['focus'], font=('Consolas', 10),
        )
        text.pack(fill='both', expand=True)
        text.insert('1.0', report)
        text.configure(state='disabled')
        def copy_report():
            self.root.clipboard_clear()
            self.root.clipboard_append(report)
        ttk.Button(body, text='Copy report (no keys)', style='Primary.TButton', command=copy_report).pack(anchor='e', pady=(10, 0))

    def run(self):
        values = {k: v.get().strip() for k, v in self.values.items()}
        try:
            accounts = [a.strip() for a in values['accounts'].split(';') if a.strip()]
            if not accounts or any('#' not in a or not all(a.rsplit('#', 1)) for a in accounts):
                raise ValueError('Enter accounts as Name#TAG, separated by ;')
            offset = int(values['offset'])
            zone = resolve(values['zone'])
            values['riot'] = self._riot_key_for_action()
        except (ValueError, OSError, KeyError) as error:
            messagebox.showerror('Configuration', str(error))
            return
        self.rows = []
        self.tree.delete(*self.tree.get_children())
        self.refresh()
        self.busy(True)
        self.status.set('Retrieving matches…')
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
                self.events.put(('error', 'Unexpected response. Check your settings and retry; no partial result was published.'))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'download_status':
                    self.status.set(value)
                elif kind == 'download_done':
                    self.downloading = False
                    self.status.set('Download complete: ' + value)
                    messagebox.showinfo('Download complete', value)
                elif kind == 'download_error':
                    self.downloading = False
                    self.status.set('Download failed')
                    messagebox.showerror('Download', value)
                elif kind == 'bounds':
                    self.display_bounds(*value)
                elif kind == 'status':
                    self.status.set(value)
                else:
                    self.busy(False)
                    if kind == 'diagnostic':
                        self.status.set('Test complete. See the diagnostic report.')
                        self.show_diagnostic(value)
                    elif kind == 'error':
                        self.status.set(value)
                        messagebox.showerror('Retrieval failed', value)
                    else:
                        self.rows, start, end = value
                        self.refresh()
                        self.status.set(f"{len(self.rows)} matches · {start.strftime('%d-%m-%Y')} · check matchups and VOD offsets.")
        except queue.Empty:
            pass
        self.place_download_buttons()
        self.root.after(100, self.poll)

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
