"""Tkinter GUI: interactive map, Dijkstra animation, alternative routes, road closures."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from algorithms import dijkstra, edge_key, k_shortest
from graph import DataError, Graph

ROUTE_COLORS = ["#4f46e5", "#059669", "#d97706", "#db2777", "#0891b2"]
BG, ROAD, CLOSED, EXPLORE, NODE, TEXT = "#f8fafc", "#cbd5e1", "#ef4444", "#f59e0b", "#64748b", "#0f172a"


class App(tk.Tk):
    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self.title("Route Finder - Dijkstra")
        self.geometry("1240x780")
        self.minsize(900, 560)
        self.g = graph
        self.blocked: set[frozenset] = set()   # closed roads
        self.routes = []
        self.settled: set[str] = set()         # animation state
        self.relaxed: list[tuple[str, str]] = []
        self.anim_job = None
        self.scale, self.ox, self.oy = 1.0, 0.0, 0.0
        self.user_view = False
        self._press = None
        self._pick = 0
        self._build()
        self.refresh_data()
        self.bind("<Return>", lambda e: self.find())

    # ---------------------------------------------------------------- UI --
    def _build(self) -> None:
        side = ttk.Frame(self, padding=10)
        side.pack(side="left", fill="y")
        ttk.Label(side, text="Route Finder", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(side, text="Dijkstra shortest path", foreground="#64748b").pack(anchor="w", pady=(0, 10))

        box = ttk.LabelFrame(side, text="Route", padding=8)
        box.pack(fill="x")
        self.src, self.dst = tk.StringVar(), tk.StringVar()
        self.k, self.delay = tk.IntVar(value=3), tk.DoubleVar(value=60)
        ttk.Label(box, text="From").grid(row=0, column=0, sticky="w")
        self.cb_src = ttk.Combobox(box, textvariable=self.src, width=24)
        self.cb_src.grid(row=0, column=1, pady=2)
        ttk.Label(box, text="To").grid(row=1, column=0, sticky="w")
        self.cb_dst = ttk.Combobox(box, textvariable=self.dst, width=24)
        self.cb_dst.grid(row=1, column=1, pady=2)
        ttk.Button(box, text="Swap", command=self.swap).grid(row=2, column=1, sticky="e", pady=2)
        ttk.Label(box, text="Routes to show").grid(row=3, column=0, sticky="w")
        ttk.Spinbox(box, from_=1, to=5, textvariable=self.k, width=5).grid(row=3, column=1, sticky="w")
        ttk.Label(box, text="Animation delay").grid(row=4, column=0, sticky="w")
        ttk.Scale(box, from_=5, to=300, variable=self.delay).grid(row=4, column=1, sticky="ew")

        row = ttk.Frame(side)
        row.pack(fill="x", pady=8)
        ttk.Button(row, text="Find shortest route", command=self.find).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="Animate", command=self.animate).pack(side="left", padx=(6, 0))

        tools = ttk.Frame(side)
        tools.pack(fill="x")
        ttk.Button(tools, text="Load CSV files...", command=self.load_files).pack(fill="x", pady=1)
        ttk.Button(tools, text="Reopen closed roads", command=self.reopen).pack(fill="x", pady=1)
        ttk.Button(tools, text="Reset view", command=self.reset_view).pack(fill="x", pady=1)

        self.out = tk.Text(side, width=40, height=22, wrap="word", state="disabled", relief="flat",
                           bg="#f1f5f9", padx=8, pady=6, font=("Segoe UI", 9))
        self.out.pack(fill="both", expand=True, pady=(10, 0))
        self.out.tag_config("h", font=("Segoe UI", 10, "bold"))
        self.out.tag_config("dim", foreground="#64748b")
        for i, c in enumerate(ROUTE_COLORS):
            self.out.tag_config(f"r{i}", foreground=c, font=("Segoe UI", 10, "bold"))

        self.status = tk.StringVar(value="Click a city to set From, another to set To. Right-click a road to close it.")
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(8, 3)).pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        c = self.canvas
        c.bind("<Configure>", self.on_resize)
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Button-3>", self.on_right)
        c.bind("<Button-2>", self.on_right)          # right-click on macOS
        c.bind("<Motion>", self.on_motion)
        c.bind("<MouseWheel>", self.on_wheel)
        c.bind("<Button-4>", self.on_wheel)          # Linux scroll up
        c.bind("<Button-5>", self.on_wheel)          # Linux scroll down

    # -------------------------------------------------------- view / data --
    def refresh_data(self) -> None:
        names = sorted(self.g.adj)
        self.cb_src["values"] = self.cb_dst["values"] = names
        self.src.set(names[0])
        self.dst.set(names[-1])
        self.blocked.clear()
        self.clear_route()
        self.reset_view()
        self.status.set(f"Loaded {len(names)} cities and {len(self.g.roads())} roads.")

    def load_files(self) -> None:
        cities = filedialog.askopenfilename(title="Choose cities.csv", filetypes=[("CSV", "*.csv")])
        roads = cities and filedialog.askopenfilename(title="Choose roads.csv", filetypes=[("CSV", "*.csv")])
        if not (cities and roads):
            return
        try:
            self.g = Graph.from_csv(cities, roads)
        except (DataError, OSError) as e:
            messagebox.showerror("Could not load data", str(e))
            return
        self.refresh_data()

    def reset_view(self) -> None:
        self.user_view = False
        self.fit()
        self.redraw()

    def fit(self) -> None:
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 100 or h < 100:
            return
        xs = [p[0] for p in self.g.pos.values()]
        ys = [p[1] for p in self.g.pos.values()]
        pad, sw, sh = 60, max(max(xs) - min(xs), 1), max(max(ys) - min(ys), 1)
        self.scale = min((w - 2 * pad) / sw, (h - 2 * pad) / sh)
        self.ox = (w - sw * self.scale) / 2 - min(xs) * self.scale
        self.oy = (h - sh * self.scale) / 2 - min(ys) * self.scale

    def pt(self, name: str) -> tuple[float, float]:
        x, y = self.g.pos[name]
        return x * self.scale + self.ox, y * self.scale + self.oy

    # ------------------------------------------------------------ drawing --
    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        for a, b, km in self.g.roads():
            closed = edge_key(a, b) in self.blocked
            c.create_line(*self.pt(a), *self.pt(b), fill=CLOSED if closed else ROAD,
                          width=2 if closed else 1.5, dash=(5, 4) if closed else ())
        for a, b in self.relaxed:
            c.create_line(*self.pt(a), *self.pt(b), fill=EXPLORE, width=2)
        for i in reversed(range(len(self.routes))):
            pts = [v for n in self.routes[i].path for v in self.pt(n)]
            if len(pts) >= 4:
                c.create_line(*pts, fill=ROUTE_COLORS[i], width=6 if i == 0 else 3,
                              capstyle="round", joinstyle="round")
        if self.routes:
            p = self.routes[0].path
            for a, b in zip(p, p[1:]):
                (x1, y1), (x2, y2) = self.pt(a), self.pt(b)
                t = c.create_text((x1 + x2) / 2, (y1 + y2) / 2 - 9, text=f"{self.g.adj[a][b]:g}",
                                  fill=ROUTE_COLORS[0], font=("Segoe UI", 8, "bold"))
                c.tag_lower(c.create_rectangle(c.bbox(t), fill=BG, outline=""), t)
        best = set(self.routes[0].path) if self.routes else set()
        ends = {self.src.get(), self.dst.get()}
        for n in self.g.adj:
            x, y = self.pt(n)
            r = 8 if n in ends else 5
            fill = ROUTE_COLORS[0] if n in best else (EXPLORE if n in self.settled else "white")
            c.create_oval(x - r, y - r, x + r, y + r, fill=fill, width=2,
                          outline=ROUTE_COLORS[0] if n in ends or n in best else NODE)
            c.create_text(x, y + r + 8, text=n, fill=TEXT,
                          font=("Segoe UI", 8, "bold" if n in ends or n in best else "normal"))

    # --------------------------------------------------------- routing ----
    def _validated(self):
        s, d = self.src.get().strip(), self.dst.get().strip()
        if s not in self.g.adj or d not in self.g.adj:
            messagebox.showwarning("Unknown city", "Choose both cities from the list.")
            return None
        if s == d:
            messagebox.showinfo("Same city", "Pick two different cities.")
            return None
        return s, d

    def _k(self) -> int:
        try:
            return max(1, min(5, int(self.k.get())))
        except (tk.TclError, ValueError):
            return 3

    def clear_route(self) -> None:
        self.stop_anim()
        self.routes, self.settled, self.relaxed = [], set(), []
        self._write([])

    def find(self) -> None:
        pair = self._validated()
        if not pair:
            return
        self.stop_anim()
        self.settled, self.relaxed = set(), []
        self.show(k_shortest(self.g, *pair, self._k(), frozenset(self.blocked)), *pair)

    def show(self, routes, s, d) -> None:
        self.routes = routes
        self.redraw()
        if not routes:
            self._write([("No route exists between ", "h"), (f"{s} and {d}", "h"),
                         (".\nA closed road may be cutting the network.", "dim")])
            return
        parts = []
        for i, r in enumerate(routes):
            parts += [(f"Route {i + 1}: {r.distance:g} km", f"r{i}"), (f"  ({len(r.path) - 1} roads)\n", "dim")]
            for a, b in zip(r.path, r.path[1:]):
                parts.append((f"  {a} -> {b}   {self.g.adj[a][b]:g} km\n", ""))
            parts.append(("\n", ""))
        b = routes[0]
        parts.append((f"Dijkstra settled {b.settled} of {len(self.g.adj)} cities in {b.ms:.2f} ms", "dim"))
        self._write(parts)
        self.status.set(f"Shortest: {s} to {d} = {b.distance:g} km")

    def animate(self) -> None:
        pair = self._validated()
        if not pair:
            return
        self.stop_anim()
        res = dijkstra(self.g, *pair, frozenset(self.blocked), trace=True)
        self.routes, self.settled, self.relaxed = [], set(), []
        self._pair, self._steps, self._i = pair, (res.steps if res else []), 0
        if not res:
            self.show([], *pair)
            return
        self._tick()

    def _tick(self) -> None:
        if self._i >= len(self._steps):
            self.anim_job = None
            self.show(k_shortest(self.g, *self._pair, self._k(), frozenset(self.blocked)), *self._pair)
            return
        kind, a, b = self._steps[self._i]
        self._i += 1
        if kind == "settle":
            self.settled.add(a)
        else:
            self.relaxed.append((a, b))
        self.redraw()
        self.status.set(f"Dijkstra: settled {len(self.settled)} cities...")
        self.anim_job = self.after(int(self.delay.get()), self._tick)

    def stop_anim(self) -> None:
        if self.anim_job:
            self.after_cancel(self.anim_job)
            self.anim_job = None

    def swap(self) -> None:
        s, d = self.src.get(), self.dst.get()
        self.src.set(d)
        self.dst.set(s)
        if self.routes:
            self.find()

    def reopen(self) -> None:
        self.blocked.clear()
        self.status.set("All roads reopened.")
        self.find() if self.routes else self.redraw()

    def _write(self, parts) -> None:
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        for text, tag in parts:
            self.out.insert("end", text, tag)
        self.out.config(state="disabled")

    # ------------------------------------------------------------ mouse ---
    def node_at(self, x, y, tol=12):
        best = min(self.g.adj, key=lambda n: math.dist(self.pt(n), (x, y)))
        return best if math.dist(self.pt(best), (x, y)) <= tol else None

    def edge_at(self, x, y, tol=6):
        best, bd = None, tol
        for a, b, _ in self.g.roads():
            (x1, y1), (x2, y2) = self.pt(a), self.pt(b)
            dx, dy = x2 - x1, y2 - y1
            t = 0 if dx == dy == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
            d = math.dist((x, y), (x1 + t * dx, y1 + t * dy))
            if d < bd:
                best, bd = (a, b), d
        return best

    def on_resize(self, _e) -> None:
        if not self.user_view:
            self.fit()
        self.redraw()

    def on_press(self, e) -> None:
        self._press = (e.x, e.y, self.ox, self.oy, False)

    def on_drag(self, e) -> None:
        if not self._press:
            return
        x0, y0, ox, oy, moved = self._press
        if moved or math.dist((e.x, e.y), (x0, y0)) > 4:
            self._press = (x0, y0, ox, oy, True)
            self.ox, self.oy, self.user_view = ox + e.x - x0, oy + e.y - y0, True
            self.redraw()

    def on_release(self, e) -> None:
        if self._press and not self._press[4]:
            n = self.node_at(e.x, e.y)
            if n:
                self.pick(n)
        self._press = None

    def pick(self, n: str) -> None:
        if self._pick == 0:
            self.src.set(n)
            self.clear_route()
            self.redraw()
            self.status.set(f"From {n}. Click a destination.")
        else:
            self.dst.set(n)
            self.find()
        self._pick ^= 1

    def on_right(self, e) -> None:
        edge = self.edge_at(e.x, e.y)
        if not edge:
            return
        key = edge_key(*edge)
        self.blocked ^= {key}
        self.status.set(f"{edge[0]} - {edge[1]} {'closed' if key in self.blocked else 'reopened'}")
        pair = self._validated() if self.routes else None
        self.find() if pair else self.redraw()

    def on_motion(self, e) -> None:
        n = self.node_at(e.x, e.y)
        if n:
            self.status.set(f"{n}  ({len(self.g.adj[n])} roads)")
            return
        edge = self.edge_at(e.x, e.y)
        if edge:
            closed = " [closed]" if edge_key(*edge) in self.blocked else ""
            self.status.set(f"{edge[0]} - {edge[1]}: {self.g.adj[edge[0]][edge[1]]:g} km{closed}")

    def on_wheel(self, e) -> None:
        f = 1.15 if (getattr(e, "delta", 0) > 0 or e.num == 4) else 1 / 1.15
        self.ox, self.oy = e.x - (e.x - self.ox) * f, e.y - (e.y - self.oy) * f
        self.scale *= f
        self.user_view = True
        self.redraw()
