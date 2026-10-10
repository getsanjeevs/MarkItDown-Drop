"""Drag-and-drop window (customtkinter + tkinterdnd2)."""
import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from app import __version__

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title(f"MarkItDown Drop {__version__}")
        self.geometry("640x560")
        self.minsize(520, 480)

        self._events: queue.Queue = queue.Queue()
        self._busy = False
        self._ready = False
        self._output_dir: Path | None = None
        self._last_output_dir: Path | None = None

        self._build_widgets()
        self.after(100, self._poll_events)
        threading.Thread(target=self._warm_up, daemon=True).start()

    # ---- layout -------------------------------------------------------
    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.drop_zone = ctk.CTkLabel(
            self, text="Loading converter…", height=150, corner_radius=12,
            fg_color=("gray85", "gray20"), font=ctk.CTkFont(size=18),
        )
        self.drop_zone.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=1, column=0, padx=20, sticky="ew")
        ctk.CTkButton(buttons, text="Add files…", width=110, command=self._pick_files).pack(side="left")
        ctk.CTkButton(buttons, text="Add folder…", width=110, command=self._pick_folder).pack(side="left", padx=8)
        ctk.CTkButton(buttons, text="Open output folder", width=140, command=self._open_output,
                      fg_color="gray40", hover_color="gray30").pack(side="right")

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.tidy = ctk.CTkCheckBox(options, text="Tidy formatting (never removes content)")
        self.tidy.select()
        self.tidy.pack(anchor="w")
        self.front = ctk.CTkCheckBox(options, text="Add YAML front matter (title, source, date)")
        self.front.select()
        self.front.pack(anchor="w", pady=(6, 0))
        folder_row = ctk.CTkFrame(options, fg_color="transparent")
        folder_row.pack(fill="x", pady=(8, 0))
        self.folder_label = ctk.CTkLabel(folder_row, text="Output: 'markdown' folder next to each file", anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(folder_row, text="Change…", width=80, command=self._pick_output).pack(side="right")

        self.log = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log.grid(row=3, column=0, padx=20, sticky="nsew")
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, padx=20, pady=(10, 4), sticky="ew")
        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.grid(row=5, column=0, padx=20, pady=(0, 12), sticky="ew")

    # ---- input handling -----------------------------------------------
    def _on_drop(self, event) -> None:
        self._start(list(self.tk.splitlist(event.data)))

    def _pick_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Choose files to convert")
        if paths:
            self._start(list(paths))

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(title="Choose a folder to convert")
        if path:
            self._start([path])

    def _pick_output(self) -> None:
        path = filedialog.askdirectory(title="Where should the Markdown files go?")
        if path:
            self._output_dir = Path(path)
            self.folder_label.configure(text=f"Output: {path}")

    def _open_output(self) -> None:
        folder = self._output_dir or self._last_output_dir
        if folder and folder.exists():
            os.startfile(folder)

    # ---- background work ----------------------------------------------
    def _warm_up(self) -> None:
        from app.converter import _engine  # importing markitdown is slow
        _engine()
        self._events.put(("ready",))

    def _start(self, paths: list[str]) -> None:
        if self._busy or not self._ready:
            self._write("Please wait, the previous job or start-up is still running.\n")
            return
        self._busy = True
        self.progress.set(0)
        options = (self.tidy.get() == 1, self.front.get() == 1, self._output_dir)
        threading.Thread(target=self._work, args=(paths, options), daemon=True).start()

    def _work(self, paths, options) -> None:
        from app.pipeline import Options, expand_paths, process_file
        tidy, front, out_dir = options
        opts = Options(tidy=tidy, front_matter=front, output_dir=out_dir)
        files = expand_paths(paths)
        if not files:
            self._events.put(("log", "No supported files found.\n"))
        used: set = set()
        ok = failed = 0
        for i, f in enumerate(files, 1):
            self._events.put(("status", f"Converting {f.name} ({i}/{len(files)})"))
            try:
                r = process_file(f, opts, used)
            except Exception as exc:  # last-resort guard so one file never kills the batch
                self._events.put(("log", f"✗ {f.name}: unexpected error {exc}\n"))
                failed += 1
            else:
                if r.error:
                    failed += 1
                    self._events.put(("log", f"✗ {f.name}: {r.error}\n"))
                else:
                    ok += 1
                    self._events.put(("out", r.output.parent))
                    self._events.put(("log", f"✓ {f.name} → {r.output}\n"))
                    if r.warning:
                        self._events.put(("log", f"   ⚠ {r.warning}\n"))
            self._events.put(("progress", i / len(files)))
        self._events.put(("done", ok, failed))

    def _poll_events(self) -> None:
        """Runs on the UI thread; worker threads only post to the queue."""
        try:
            while True:
                kind, *args = self._events.get_nowait()
                if kind == "ready":
                    self._ready = True
                    self.drop_zone.configure(text="Drag & drop files or folders here")
                elif kind == "log":
                    self._write(args[0])
                elif kind == "status":
                    self.status.configure(text=args[0])
                elif kind == "progress":
                    self.progress.set(args[0])
                elif kind == "out":
                    self._last_output_dir = args[0]
                elif kind == "done":
                    self._busy = False
                    self.status.configure(text=f"Finished: {args[0]} converted, {args[1]} failed.")
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _write(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")
