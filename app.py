"""Tkinter desktop application for Earthquake Shake-Down."""

from __future__ import annotations

import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from calculations import best_successful_trial, maximum_acceleration, maximum_speed
from catalog import CATALOG
from models import PlacedPiece, Structure, SupportRelation, TrialRecord, TrialState
from physics import PIXELS_PER_INCH, TABLE_Y_IN, ShakeSimulation
from workfiles import structure_from_dict, structure_to_dict


ROOT = Path(__file__).resolve().parent
SCORE_FILE = ROOT / "scores.json"


class ShakeDownApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Earthquake Shake-Down")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#1b2430")

        # Start with an empty board so the player designs the structure.
        self.structure = Structure()
        self.simulation: ShakeSimulation | None = None
        self.trial_state = TrialState.EDITING
        self.trial_started_at = 0.0
        self.paused_elapsed = 0.0
        self.last_tick = 0.0
        self.failed_piece_id: int | None = None
        self.failure_reason = ""
        self.trials: list[TrialRecord] = self._load_scores()
        self.selected_piece_id: int | None = None
        self.drag_offset = (0.0, 0.0)
        self.next_piece_id = max((piece.piece_id for piece in self.structure.pieces), default=0) + 1

        self.amplitude_var = tk.DoubleVar(value=2.0)
        self.frequency_var = tk.DoubleVar(value=2.0)
        self.amplitude_text = tk.StringVar(value="2.00")
        self.frequency_text = tk.StringVar(value="2.00")
        self.piece_var = tk.StringVar(value="Foundation")
        self.status_var = tk.StringVar(value="Build your structure, then start a trial.")
        self.elapsed_var = tk.StringVar(value="Elapsed: 0.00 s")
        self.metric_var = tk.StringVar(value="Max acceleration: 0.00 ft/s²")
        self.cost_var = tk.StringVar()
        self.score_var = tk.StringVar()

        self._build_ui()
        self._sync_piece_details()
        self._refresh()

    def _build_ui(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Open work…", command=self._open_work)
        file_menu.add_command(label="Save work…", command=self._save_work)
        file_menu.add_separator()
        file_menu.add_command(label="New empty work", command=self._new_work)
        menu.add_cascade(label="File", menu=file_menu)
        self.configure(menu=menu)

        header = tk.Frame(self, bg="#16202b", padx=18, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="EARTHQUAKE SHAKE-DOWN", fg="#ffd166", bg="#16202b",
                 font=("Arial", 22, "bold")).pack(side="left")
        tk.Label(header, text="Build smart. Shake safely. Learn why.", fg="#b9c7d6",
                 bg="#16202b", font=("Arial", 11)).pack(side="left", padx=18, pady=5)
        ttk.Button(header, text="Open", command=self._open_work).pack(side="right", padx=3)
        ttk.Button(header, text="Save", command=self._save_work).pack(side="right", padx=3)
        ttk.Button(header, text="Score board", command=self._show_scores).pack(side="right")

        main = tk.Frame(self, bg="#1b2430")
        main.pack(fill="both", expand=True, padx=12, pady=12)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self.controls = tk.Frame(main, bg="#263445", padx=14, pady=14, width=280)
        self.controls.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        self.controls.grid_propagate(False)
        tk.Label(self.controls, text="CONTROLS", fg="#ffffff", bg="#263445",
                 font=("Arial", 14, "bold")).pack(anchor="w")
        self._make_shake_control("Amplitude", self.amplitude_var, self.amplitude_text,
                                 0, 12, "inches", "Peak horizontal table displacement.")
        self._make_shake_control("Frequency", self.frequency_var, self.frequency_text,
                                 0, 8, "hertz", "Cycles per second; higher values accelerate faster.")
        ttk.Separator(self.controls).pack(fill="x", pady=12)

        tk.Label(self.controls, text="PIECE CATALOG", fg="#ffffff", bg="#263445",
                 font=("Arial", 12, "bold")).pack(anchor="w")
        names = [definition.name for definition in CATALOG.values()]
        self.piece_combo = ttk.Combobox(self.controls, values=names, textvariable=self.piece_var,
                                        state="readonly")
        self.piece_combo.pack(fill="x", pady=6)
        self.piece_combo.bind("<<ComboboxSelected>>", lambda _event: self._sync_piece_details())
        self.details_label = tk.Label(self.controls, justify="left", anchor="w", fg="#d7e3ef",
                                      bg="#263445", wraplength=240)
        self.details_label.pack(fill="x", pady=(2, 8))
        ttk.Button(self.controls, text="Add piece", command=self._add_piece).pack(fill="x")
        ttk.Button(self.controls, text="Remove selected", command=self._remove_selected).pack(fill="x", pady=5)
        ttk.Button(self.controls, text="Clear structure", command=self._clear_structure).pack(fill="x")
        ttk.Separator(self.controls).pack(fill="x", pady=12)
        tk.Label(self.controls, text="Support relationships are tracked for every placed piece.",
                 fg="#b9c7d6", bg="#263445", wraplength=240, justify="left").pack(anchor="w")

        stage = tk.Frame(main, bg="#dfe8ee", padx=10, pady=10)
        stage.grid(row=0, column=1, sticky="nsew")
        stage.rowconfigure(1, weight=1)
        stage.columnconfigure(0, weight=1)
        bar = tk.Frame(stage, bg="#dfe8ee")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(bar, text="SIMULATION", bg="#dfe8ee", fg="#1b2430",
                 font=("Arial", 14, "bold")).pack(side="left")
        self.start_button = ttk.Button(bar, text="Start trial", command=self._start_trial)
        self.start_button.pack(side="right", padx=4)
        self.pause_button = ttk.Button(bar, text="Pause", command=self._pause_resume, state="disabled")
        self.pause_button.pack(side="right", padx=4)
        ttk.Button(bar, text="Reset trial", command=self._reset_trial).pack(side="right", padx=4)

        content = tk.Frame(stage, bg="#dfe8ee")
        content.grid(row=1, column=0, sticky="nsew")
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        self.canvas = tk.Canvas(content, bg="#b8d5e5", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.canvas.bind("<Button-1>", self._select_piece)
        self.canvas.bind("<B1-Motion>", self._drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self._release_piece)
        chart_frame = tk.Frame(content, bg="#ffffff")
        chart_frame.grid(row=0, column=1, sticky="nsew")
        self.figure = Figure(figsize=(2.4, 3), dpi=90)
        self.chart = self.figure.add_subplot(111)
        self.chart.set_title("Pieces by type", fontsize=9)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.figure_canvas.get_tk_widget().pack(fill="both", expand=True)

        results = tk.Frame(stage, bg="#172533", padx=12, pady=8)
        results.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        tk.Label(results, textvariable=self.status_var, fg="#ffd166", bg="#172533",
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(results, textvariable=self.elapsed_var, fg="#ffffff", bg="#172533",
                 anchor="w").pack(side="left", padx=(0, 20))
        tk.Label(results, textvariable=self.metric_var, fg="#ffffff", bg="#172533",
                 anchor="w").pack(side="left")
        tk.Label(results, textvariable=self.cost_var, fg="#ffffff", bg="#172533",
                 anchor="e").pack(side="right")
        tk.Label(self, textvariable=self.score_var, bg="#1b2430", fg="#ffd166",
                 anchor="w", padx=15, pady=5).pack(fill="x")

    def _make_shake_control(self, title, variable, text_variable, low, high, unit, helper) -> None:
        tk.Label(self.controls, text=f"{title} ({unit})", fg="#ffffff", bg="#263445",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(12, 0))
        scale = tk.Scale(self.controls, from_=low, to=high, resolution=0.1, orient="horizontal",
                         variable=variable, command=lambda _value: self._sync_input(variable, text_variable),
                         bg="#263445", fg="#ffffff", troughcolor="#14202b", highlightthickness=0)
        scale.pack(fill="x")
        entry = ttk.Entry(self.controls, textvariable=text_variable, width=8)
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda _event: self._sync_scale(variable, text_variable, low, high))
        entry.bind("<FocusOut>", lambda _event: self._sync_scale(variable, text_variable, low, high))
        tk.Label(self.controls, text=helper, fg="#b9c7d6", bg="#263445", wraplength=240,
                 justify="left", font=("Arial", 8)).pack(anchor="w")

    def _sync_input(self, variable, text_variable) -> None:
        text_variable.set(f"{variable.get():.2f}")
        self._refresh_metrics()

    def _sync_scale(self, variable, text_variable, low, high) -> None:
        try:
            value = min(high, max(low, float(text_variable.get())))
        except ValueError:
            value = variable.get()
        variable.set(value)
        text_variable.set(f"{value:.2f}")
        self._refresh_metrics()

    def _selected_definition(self):
        return next(definition for definition in CATALOG.values() if definition.name == self.piece_var.get())

    def _sync_piece_details(self) -> None:
        definition = self._selected_definition()
        self.details_label.config(text=(f"{definition.name}\n"
                                        f"Dimensions: {definition.width_in:g} × {definition.height_in:g} in\n"
                                        f"Mass: {definition.mass_lb:g} lb\n"
                                        f"Price: ${definition.price:.2f}\n"
                                        f"Material: {definition.material}"))

    def _add_piece(self) -> None:
        if self.trial_state in {TrialState.RUNNING, TrialState.PAUSED, TrialState.CHECKPOINT}:
            return
        definition = self._selected_definition()
        y = max(50, 180 - len(self.structure.pieces) * 8)
        piece = PlacedPiece(self.next_piece_id, definition, 180, y)
        self.next_piece_id += 1
        self.structure.pieces.append(piece)
        parent = min(self.structure.pieces[:-1], key=lambda item: abs(item.y_in - (y + 30)), default=None)
        self.structure.supports.append(SupportRelation(
            piece.piece_id,
            parent.piece_id if parent else None,
            "contact" if parent else "table",
        ))
        self._refresh()

    def _remove_selected(self) -> None:
        if self.selected_piece_id is None or self.trial_state != TrialState.EDITING:
            return
        removed = self.selected_piece_id
        self.structure.pieces = [piece for piece in self.structure.pieces if piece.piece_id != removed]
        self.structure.supports = [relation for relation in self.structure.supports
                                   if relation.child_id != removed and relation.parent_id != removed]
        self.structure.welds = [weld for weld in self.structure.welds
                                if removed not in (weld.first_id, weld.second_id)]
        self.selected_piece_id = None
        self._refresh()

    def _clear_structure(self) -> None:
        if self.trial_state != TrialState.EDITING:
            return
        self.structure.pieces.clear()
        self.structure.supports.clear()
        self.structure.welds.clear()
        self.selected_piece_id = None
        self._refresh()

    def _new_work(self) -> None:
        if self.trial_state != TrialState.EDITING:
            messagebox.showinfo("Trial running", "Reset the trial before starting a new work file.")
            return
        self.structure = Structure()
        self.selected_piece_id = None
        self.next_piece_id = 1
        self.status_var.set("New empty work created.")
        self._refresh()

    def _save_work(self) -> None:
        if self.trial_state != TrialState.EDITING:
            messagebox.showinfo("Trial running", "Reset the trial before saving your work.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Earthquake Shake-Down work",
            defaultextension=".json",
            filetypes=[("Shake-Down work", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        data = structure_to_dict(self.structure)
        data["shake"] = {
            "amplitude_in": self.amplitude_var.get(),
            "frequency_hz": self.frequency_var.get(),
        }
        try:
            Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Save failed", str(error))
            return
        self.status_var.set(f"Work saved: {Path(path).name}")

    def _open_work(self) -> None:
        if self.trial_state != TrialState.EDITING:
            messagebox.showinfo("Trial running", "Reset the trial before opening a work file.")
            return
        path = filedialog.askopenfilename(
            title="Open Earthquake Shake-Down work",
            filetypes=[("Shake-Down work", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            structure = structure_from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            messagebox.showerror("Open failed", str(error))
            return
        self.structure = structure
        shake = data.get("shake", {})
        self.amplitude_var.set(float(shake.get("amplitude_in", self.amplitude_var.get())))
        self.frequency_var.set(float(shake.get("frequency_hz", self.frequency_var.get())))
        self.amplitude_text.set(f"{self.amplitude_var.get():.2f}")
        self.frequency_text.set(f"{self.frequency_var.get():.2f}")
        self.selected_piece_id = None
        self.next_piece_id = max((piece.piece_id for piece in self.structure.pieces), default=0) + 1
        self.status_var.set(f"Work opened: {Path(path).name}")
        self._refresh()

    def _select_piece(self, event) -> None:
        if self.trial_state != TrialState.EDITING:
            return
        x, y = self._canvas_to_world(event.x, event.y)
        self.selected_piece_id = None
        for piece in reversed(self.structure.pieces):
            if abs(x - piece.x_in) <= piece.definition.width_in / 2 and abs(y - piece.y_in) <= piece.definition.height_in / 2:
                self.selected_piece_id = piece.piece_id
                self.drag_offset = (piece.x_in - x, piece.y_in - y)
                break
        self._refresh()

    def _drag_piece(self, event) -> None:
        if self.trial_state != TrialState.EDITING or self.selected_piece_id is None:
            return
        x, y = self._canvas_to_world(event.x, event.y)
        for piece in self.structure.pieces:
            if piece.piece_id == self.selected_piece_id:
                piece.x_in = min(345.0, max(15.0, x + self.drag_offset[0]))
                piece.y_in = min(TABLE_Y_IN - 5.0, max(20.0, y + self.drag_offset[1]))
                break
        self._refresh()

    def _release_piece(self, _event) -> None:
        self.drag_offset = (0.0, 0.0)

    def _view_geometry(self) -> tuple[float, float, float]:
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        scale = min((width - 40) / 360.0, (height - 40) / 390.0)
        return max(0.5, scale), 20.0, 20.0

    def _canvas_to_world(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        scale, offset_x, offset_y = self._view_geometry()
        return ((canvas_x - offset_x) / scale, (canvas_y - offset_y) / scale)

    def _start_trial(self) -> None:
        if len(self.structure.pieces) == 0:
            messagebox.showinfo("Add pieces", "Add at least one piece before starting.")
            return
        self.simulation = ShakeSimulation(self.structure)
        self.trial_state = TrialState.RUNNING
        self.failed_piece_id = None
        self.failure_reason = ""
        self.paused_elapsed = 0.0
        self.trial_started_at = time.perf_counter()
        self.last_tick = self.trial_started_at
        self._set_editing(False)
        self._tick()

    def _tick(self) -> None:
        if self.trial_state not in {TrialState.RUNNING, TrialState.CHECKPOINT} or self.simulation is None:
            return
        now = time.perf_counter()
        elapsed = self.paused_elapsed + now - self.trial_started_at
        dt = min(0.05, max(0.001, now - self.last_tick))
        self.last_tick = now
        failure = self.simulation.step(elapsed, dt, self.amplitude_var.get(), self.frequency_var.get())
        if failure:
            self.failed_piece_id = failure.piece_id
            self.failure_reason = failure.reason
            self.paused_elapsed = elapsed
            self.trial_state = TrialState.FAILED
            self._finish_trial(elapsed)
        elif elapsed >= 10 and self.trial_state == TrialState.RUNNING:
            self.trial_state = TrialState.CHECKPOINT
            self.status_var.set("10-second checkpoint reached — keep shaking to test further.")
        self._refresh()
        if self.trial_state in {TrialState.RUNNING, TrialState.CHECKPOINT}:
            self.after(20, self._tick)

    def _pause_resume(self) -> None:
        if self.trial_state == TrialState.RUNNING or self.trial_state == TrialState.CHECKPOINT:
            self.paused_elapsed += time.perf_counter() - self.trial_started_at
            self.trial_state = TrialState.PAUSED
            self.status_var.set("Trial paused.")
        elif self.trial_state == TrialState.PAUSED:
            self.trial_started_at = time.perf_counter()
            self.last_tick = self.trial_started_at
            self.trial_state = TrialState.CHECKPOINT if self.paused_elapsed >= 10 else TrialState.RUNNING
            self._tick()
        self._refresh()

    def _reset_trial(self) -> None:
        if self.trial_state in {TrialState.CHECKPOINT, TrialState.PAUSED}:
            elapsed = self.paused_elapsed
            if self.trial_state == TrialState.CHECKPOINT:
                elapsed += time.perf_counter() - self.trial_started_at
            if elapsed >= 10:
                self._finish_trial(elapsed)
        self.trial_state = TrialState.EDITING
        self.simulation = None
        self.paused_elapsed = 0.0
        self.failed_piece_id = None
        self.failure_reason = ""
        self._set_editing(True)
        self.status_var.set("Build your structure, then start a trial.")
        self._refresh()

    def _finish_trial(self, elapsed: float) -> None:
        record = TrialRecord(self.amplitude_var.get(), self.frequency_var.get(),
                             maximum_speed(self.amplitude_var.get(), self.frequency_var.get()),
                             maximum_acceleration(self.amplitude_var.get(), self.frequency_var.get()),
                             elapsed >= 10, elapsed, self.failed_piece_id, self.failure_reason)
        self.trials.append(record)
        self._save_scores()

    def _set_editing(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for child in self.controls.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Combobox, ttk.Entry, tk.Scale)):
                child.configure(state=state)
        self.start_button.configure(state="normal" if enabled else "disabled")
        self.pause_button.configure(state="disabled" if enabled else "normal")

    def _refresh_metrics(self) -> None:
        self.metric_var.set(f"Max acceleration: {maximum_acceleration(self.amplitude_var.get(), self.frequency_var.get()):.2f} ft/s²")

    def _refresh(self) -> None:
        self._refresh_metrics()
        elapsed = self.paused_elapsed
        if self.trial_state in {TrialState.RUNNING, TrialState.CHECKPOINT}:
            elapsed += time.perf_counter() - self.trial_started_at
        self.elapsed_var.set(f"Elapsed: {elapsed:.2f} s   Status: {self.trial_state.value}")
        self.cost_var.set(f"Total cost: ${self.structure.total_cost():.2f}")
        best = best_successful_trial(self.trials)
        self.score_var.set("Top score: no qualifying trial yet" if best is None else
                           f"Top score: {best.max_acceleration_ft_s2:.2f} ft/s² at {best.amplitude_in:.1f} in / {best.frequency_hz:.1f} Hz")
        self._draw_simulation()
        self._draw_chart()

    def _draw_simulation(self) -> None:
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        scale, offset_x, offset_y = self._view_geometry()
        self.canvas.create_rectangle(0, 0, width, height, fill="#b8d5e5", outline="")
        self.canvas.create_text(18, 18, anchor="nw", text="Shake table / building view",
                               fill="#263445", font=("Arial", 12, "bold"))
        table_x = 180.0
        if self.simulation is not None:
            table_x = self.simulation.table_body.position.x / PIXELS_PER_INCH
        table_left = (table_x - 110) * scale + offset_x
        table_right = (table_x + 110) * scale + offset_x
        table_y = TABLE_Y_IN * scale + offset_y
        self.canvas.create_rectangle(table_left, table_y, table_right, table_y + max(8, 10 * scale),
                                     fill="#4b5563", outline="#202733", width=2)
        self.canvas.create_text(table_x * scale + offset_x, table_y + max(8, 10 * scale) + 5,
                                text="SHAKE TABLE", fill="#263445", font=("Arial", 8, "bold"))
        positions = self.simulation.positions_in_inches() if self.simulation else {
            piece.piece_id: (piece.x_in, piece.y_in, piece.angle_deg) for piece in self.structure.pieces
        }
        for piece in self.structure.pieces:
            x, y, angle = positions.get(piece.piece_id, (piece.x_in, piece.y_in, piece.angle_deg))
            w, h = piece.definition.width_in, piece.definition.height_in
            selected = piece.piece_id == self.selected_piece_id
            self.canvas.create_rectangle((x - w / 2) * scale + offset_x, (y - h / 2) * scale + offset_y,
                                         (x + w / 2) * scale + offset_x, (y + h / 2) * scale + offset_y,
                                         fill=piece.definition.color, outline="#ffdf70" if selected else "#263445",
                                         width=3 if selected else 1)
            self.canvas.create_text(x * scale + offset_x, y * scale + offset_y,
                                   text=str(piece.piece_id), fill="#ffffff", font=("Arial", 9, "bold"))

    def _draw_chart(self) -> None:
        counts = {definition.name: 0 for definition in CATALOG.values()}
        for piece in self.structure.pieces:
            counts[piece.definition.name] += 1
        self.chart.clear()
        self.chart.bar(list(counts), list(counts.values()), color="#5b8fb9")
        self.chart.tick_params(axis="x", labelrotation=65, labelsize=7)
        self.chart.set_ylim(0, max(2, max(counts.values(), default=0) + 1))
        self.chart.set_title("Pieces by type", fontsize=9)
        self.figure.tight_layout()
        self.figure_canvas.draw_idle()

    def _load_scores(self):
        try:
            data = json.loads(SCORE_FILE.read_text(encoding="utf-8"))
            return [TrialRecord(**record) for record in data]
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return []

    def _save_scores(self) -> None:
        SCORE_FILE.write_text(json.dumps([record.__dict__ for record in self.trials], indent=2), encoding="utf-8")

    def _show_scores(self) -> None:
        window = tk.Toplevel(self)
        window.title("Score board")
        window.transient(self)
        window.geometry("560x360")
        tk.Label(window, text="Completed trials", font=("Arial", 14, "bold")).pack(anchor="w", padx=15, pady=12)
        box = tk.Listbox(window, width=75, height=14)
        box.pack(fill="both", expand=True, padx=15)
        for index, record in enumerate(self.trials, 1):
            outcome = "qualified" if record.checkpoint_reached else f"failed: {record.failure_reason or 'unknown'}"
            box.insert("end", f"{index}. {record.amplitude_in:.1f} in / {record.frequency_hz:.1f} Hz — {outcome}")


if __name__ == "__main__":
    ShakeDownApp().mainloop()

