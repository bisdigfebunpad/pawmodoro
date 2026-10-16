import json, math, os, time
import tkinter as tk
from dataclasses import asdict, dataclass
from datetime import date, datetime
from tkinter import messagebox, ttk

SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pawmodoro_save.json")
DIFFICULTY = {"Mudah": (10, 5), "Sedang": (25, 12), "Sulit": (50, 25)}   
CATEGORIES = ["Kuliah", "Pribadi"]
STAGES, SCALE, STAGE_XP = ("Anak Kucing", "Kucing Remaja", "Kucing Dewasa"), (0.55, 0.78, 1.0), (100, 300)
FEED_COST, POMO_XP, POMO_COINS = 10, 20, 10
IDLE, FOCUS, BREAK = "IDLE", "FOCUS", "BREAK"
HINTS = {IDLE: "Siap fokus?", FOCUS: "Fokus... kucingmu tidur menemanimu", BREAK: "Istirahat, regangkan badan"}
LINE = {"outline": "#5d4037", "width": 2}

@dataclass
class Task:
    title: str
    category: str = "Pribadi"
    difficulty: str = "Sedang"
    due: str = ""
    done: bool = False

    @property
    def overdue(self):
        return bool(self.due) and not self.done and self.due < date.today().isoformat()

@dataclass
class Pet:
    name: str = "Paw"
    xp: int = 0
    hunger: float = 80.0

    @property
    def stage(self):
        return sum(self.xp >= t for t in STAGE_XP)

    @property
    def mood(self):
        return "happy" if self.hunger >= 40 else "sad"

class Game:

    def __init__(self):
        self.xp, self.level, self.coins = 0, 1, 0
        self.tasks, self.pet, self.last_seen = [], Pet(), time.time()

    @property
    def need(self):
        return 100 * self.level

    def complete_task(self, task):
        if task.done:
            return None
        task.done = True
        return self.reward(*DIFFICULTY[task.difficulty])

    def reward(self, xp, coins):
        stage = self.pet.stage
        self.xp += xp
        self.coins += coins
        self.pet.xp += xp
        note = f"+{xp} XP, +{coins} koin."
        while self.xp >= self.need:
            self.xp -= self.need
            self.level += 1
            self.coins += 20
            note += f" 🎉 Naik ke level {self.level}! (+20 koin)"
        if self.pet.stage > stage:
            note += f" ✨ {self.pet.name} tumbuh jadi {STAGES[self.pet.stage]}!"
        return note

    def feed(self):
        if self.pet.hunger >= 95:
            return "full"
        if self.coins < FEED_COST:
            return "poor"
        self.coins -= FEED_COST
        self.pet.hunger = min(100, self.pet.hunger + 30)
        return "ok"

    def tick_hunger(self):
        now = time.time()
        self.pet.hunger = max(0, self.pet.hunger - (now - self.last_seen) / 360)   
        self.last_seen = now

    def save(self):
        self.tick_hunger()
        data = {k: getattr(self, k) for k in ("xp", "level", "coins", "last_seen")}
        data.update(tasks=[asdict(t) for t in self.tasks], pet=asdict(self.pet))
        with open(SAVE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls):
        g = cls()
        try:
            with open(SAVE, encoding="utf-8") as f:
                d = json.load(f)
            g.xp, g.level, g.coins, g.last_seen = d["xp"], d["level"], d["coins"], d["last_seen"]
            g.tasks, g.pet = [Task(**t) for t in d["tasks"]], Pet(**d["pet"])
            g.tick_hunger()
        except (OSError, ValueError, KeyError, TypeError):
            return cls()
        return g

def oval(c, x, y, rx, ry=None, **kw):
    ry = rx if ry is None else ry
    return c.create_oval(x - rx, y - ry, x + rx, y + ry, **kw)

class Cat:
    fur, belly = "#f4b26b", "#fff1dc"

    def draw(self, c, cx, cy, s, mood, blink):
        hx, hy, r = cx, cy - 48 * s, 38 * s
        c.create_line(cx + 38 * s, cy + 44 * s, cx + 72 * s, cy + 36 * s, cx + 78 * s, cy - 6 * s,
                      smooth=True, width=11 * s, fill=self.fur, capstyle="round")                 
        for k in (-1, 1):                                                                          
            c.create_polygon(hx + k * r * .9, hy - r * .3, hx + k * r * .75, hy - r * 1.3, hx + k * r * .1,
                             hy - r * .85, fill=self.fur, **LINE)
            c.create_polygon(hx + k * r * .75, hy - r * .5, hx + k * r * .7, hy - r * 1.05, hx + k * r * .3,
                             hy - r * .8, fill="#f8bbd0", outline="")
        oval(c, cx, cy + 20 * s, 42 * s, 38 * s, fill=self.fur, **LINE)                          
        oval(c, cx, cy + 25 * s, 26 * s, 27 * s, fill=self.belly, outline="")                     
        for k in (-24, 24):
            oval(c, cx + k * s, cy + 58 * s, 14 * s, 10 * s, fill=self.fur, **LINE)                
        oval(c, hx, hy, r, fill=self.fur, **LINE)                                                 
        for dx in (-6, 0, 6):                                                                     
            c.create_line(hx + dx * s, hy - r * .95, hx + dx * s, hy - r * .6, fill="#c77d2e", width=2)
        for k in (-1, 1):
            ex, ey = hx + k * 14 * s, hy - 2 * s
            if blink:
                c.create_line(ex - 6 * s, ey, ex + 6 * s, ey, width=3, fill="#263238")
            else:
                oval(c, ex, ey, 5 * s, fill="#263238", outline="")
                oval(c, ex - s, ey - 2 * s, 1.5 * s, fill="white", outline="")
            for dy in (-3, 3):                                                                      
                c.create_line(hx + k * 14 * s, hy + (14 + dy) * s, hx + k * 42 * s, hy + (14 + dy * 2.5) * s,
                              fill="#5d4037")
        oval(c, hx, hy + 11 * s, 4 * s, 3 * s, fill="#d81b60", outline="")                        
        start, top = (200, 10) if mood == "happy" else (20, 24)                                    
        c.create_arc(hx - 10 * s, hy + top * s, hx + 10 * s, hy + (top + 16) * s, start=start, extent=140,
                     style="arc", width=2)

class PetView(tk.Canvas):
    W, H, GROUND = 320, 250, 220

    def __init__(self, master, game):
        super().__init__(master, width=self.W, height=self.H, bg="#cdeffd", highlightthickness=0)
        self.game, self.cat, self.t, self.hop, self.sleeping = game, Cat(), 0, 0, False

    def cheer(self):
        self.hop = 20

    def animate(self):
        self.t += 1
        self.hop = max(0, self.hop - 1)
        self.delete("all")
        oval(self, 275, 37, 25, fill="#fff59d", outline="")                                       
        self.create_rectangle(0, 205, self.W, self.H, fill="#8bc98b", outline="")                  
        for i in range(min(self.game.level + 1, 8)):                                               
            x, y = 20 + i * 40, 232 + (i % 3) * 5
            self.create_line(x, y, x, y + 10, fill="#2e7d32", width=2)
            oval(self, x, y, 5, fill=("#f48fb1", "#fff176", "#ce93d8")[i % 3], outline="")
        pet = self.game.pet
        s = SCALE[pet.stage]
        bob = math.sin(self.t * (0.06 if self.sleeping else 0.12)) * 3 * s
        up = abs(math.sin(math.pi * self.hop / 20)) * 38 if self.hop else 0
        cx, cy = self.W / 2 - 15, self.GROUND - 68 * s - up - bob
        oval(self, cx, self.GROUND, 44 * s, 6, fill="#6aa56a", outline="")                         
        self.cat.draw(self, cx, cy, s, "happy" if self.hop else pet.mood,
                      self.sleeping or self.t % 90 < 3)
        if self.sleeping:
            self.create_text(cx + 50 * s, cy - 90 * s, text="z Z", fill="#546e7a", font=("Arial", 14, "bold"))

class PawmodoroApp:
    def __init__(self, root):
        self.root = root
        root.title("Pawmodoro — Task Manager")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.game, self.frame_no = Game.load(), 0
        self.state, self.end, self.total = IDLE, 0.0, 1
        self.build_ui()
        self.refresh()
        self.loop()

    def build_ui(self):
        pad = {"padx": 6, "pady": 4}
        outer = ttk.Frame(self.root)
        outer.grid(padx=10, pady=10)
        left = ttk.Frame(outer)
        left.grid(row=0, column=0, sticky="n")
        self.header, self.pet_info = tk.StringVar(), tk.StringVar()
        ttk.Label(left, textvariable=self.header, font=("Arial", 10, "bold")).pack(anchor="w", **pad)
        self.xp_bar = ttk.Progressbar(left, length=320, maximum=100)
        self.xp_bar.pack(**pad)
        self.pet_view = PetView(left, self.game)
        self.pet_view.pack(**pad)
        ttk.Label(left, textvariable=self.pet_info).pack()
        self.hunger_bar = ttk.Progressbar(left, length=320, maximum=100)
        self.hunger_bar.pack(**pad)
        row = ttk.Frame(left)
        row.pack()
        ttk.Button(row, text=f"🍎 Beri Makan ({FEED_COST} koin)", command=self.feed).grid(row=0, column=0, padx=4)
        ttk.Button(row, text="🤚 Elus", command=self.pet_view.cheer).grid(row=0, column=1, padx=4)
        nb = ttk.Notebook(outer)
        nb.grid(row=0, column=1, sticky="n", padx=(12, 0))
        nb.add(self.build_tasks(ttk.Frame(nb)), text="📋 Tugas")
        nb.add(self.build_pomodoro(ttk.Frame(nb)), text="⏱ Pomodoro")
        self.msg = tk.StringVar(value="Selamat datang di Pawmodoro! Selesaikan tugas untuk merawat kucingmu.")
        ttk.Label(outer, textvariable=self.msg, foreground="#2e7d32", font=("Arial", 10, "bold"), wraplength=720
                  ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def build_tasks(self, f):
        self.title_var, self.cat_var = tk.StringVar(), tk.StringVar(value=CATEGORIES[0])
        self.diff_var, self.due_var = tk.StringVar(value="Sedang"), tk.StringVar()
        form = ttk.Frame(f)
        form.pack(padx=6, pady=6, fill="x")
        entry = ttk.Entry(form, textvariable=self.title_var, width=40)
        entry.grid(row=0, column=0, columnspan=3, sticky="we", pady=2)
        entry.bind("<Return>", lambda _e: self.add_task())
        ttk.Combobox(form, textvariable=self.cat_var, values=CATEGORIES, width=10, state="readonly").grid(row=1, column=0)
        ttk.Combobox(form, textvariable=self.diff_var, values=list(DIFFICULTY), width=8, state="readonly").grid(row=1, column=1)
        ttk.Entry(form, textvariable=self.due_var, width=12).grid(row=1, column=2, pady=2)
        ttk.Button(form, text="➕ Tambah", command=self.add_task).grid(row=0, column=3, padx=4)
        ttk.Label(form, text="Kategori · Kesulitan · Tenggat (YYYY-MM-DD, opsional)", font=("Arial", 8)).grid(
            row=2, column=0, columnspan=4, sticky="w")
        self.tree = ttk.Treeview(f, columns=("title", "cat", "diff", "due"), show="tree headings", height=13)
        self.tree.column("#0", width=30, stretch=False)
        for col, text, w in (("title", "Tugas", 190), ("cat", "Kategori", 75), ("diff", "Level", 60), ("due", "Tenggat", 80)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w)
        self.tree.tag_configure("done", foreground="#9e9e9e")
        self.tree.tag_configure("late", foreground="#c62828")
        self.tree.pack(padx=6)
        self.summary = tk.StringVar()
        ttk.Label(f, textvariable=self.summary).pack(anchor="w", padx=8)
        row = ttk.Frame(f)
        row.pack(pady=6)
        for i, (text, cmd) in enumerate((("✔ Selesaikan", self.complete_task), ("🗑 Hapus", self.delete_task),
                                         ("Bersihkan yang selesai", self.clear_done), ("↺ Reset", self.reset_game))):
            ttk.Button(row, text=text, command=cmd).grid(row=0, column=i, padx=4)
        return f

    def say(self, text):
        self.msg.set(text)

    def refresh(self):
        g, pet = self.game, self.game.pet
        self.header.set(f"Level {g.level}   ✨ XP {g.xp}/{g.need}   💰 {g.coins} koin")
        self.xp_bar["value"] = 100 * g.xp / g.need
        self.pet_info.set(f"🐱 {pet.name} — {STAGES[pet.stage]} (XP {pet.xp})")
        self.hunger_bar["value"] = pet.hunger
        self.tree.delete(*self.tree.get_children())
        for i in sorted(range(len(g.tasks)), key=lambda i: (g.tasks[i].done, g.tasks[i].due or "9999")):
            t = g.tasks[i]
            tag = "done" if t.done else "late" if t.overdue else ""
            self.tree.insert("", "end", iid=str(i), text="✔" if t.done else "☐", tags=(tag,),
                             values=(t.title, t.category, t.difficulty, t.due or "-"))
        self.summary.set(f"Selesai {sum(t.done for t in g.tasks)} dari {len(g.tasks)} tugas")

    def done(self, note=""):
        if note:
            self.say(note)
            self.pet_view.cheer()
        self.refresh()
        self.game.save()

    def selected(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def quit(self):
        self.game.save()
        self.root.destroy()

    def reset_game(self):
        if messagebox.askyesno("Reset", "Hapus semua progres dan mulai dari awal?"):
            self.game.__init__(); self.done("Progres direset. Selamat memulai lagi!")

    def add_task(self):
        title, due = self.title_var.get().strip(), self.due_var.get().strip()
        if not title:
            return
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                return self.say("⚠ Format tenggat harus YYYY-MM-DD, contoh 2026-12-31.")
        self.game.tasks.append(Task(title, self.cat_var.get(), self.diff_var.get(), due))
        self.title_var.set("")
        self.due_var.set("")
        self.done(f"Tugas '{title}' ditambahkan.")

    def complete_task(self):
        idx = self.selected()
        if idx is None:
            return self.say("⚠ Pilih tugas dulu.")
        task = self.game.tasks[idx]
        note = self.game.complete_task(task)
        self.done(f"Tugas '{task.title}' selesai! {note}" if note else "Tugas ini sudah selesai.")

    def delete_task(self):
        idx = self.selected()
        if idx is not None:
            self.game.tasks.pop(idx)
            self.done()

    def clear_done(self):
        self.game.tasks = [t for t in self.game.tasks if not t.done]
        self.done()

    def feed(self):
        name = self.game.pet.name
        self.done({"ok": f"Nyam! {name} kenyang. (-{FEED_COST} koin)", "full": f"{name} masih kenyang.",
                   "poor": "⚠ Koin belum cukup. Selesaikan tugas dulu!"}[self.game.feed()])

    def build_pomodoro(self, f):
        self.clock, self.hint = tk.StringVar(value="25:00"), tk.StringVar(value=HINTS[IDLE])
        self.work_var, self.break_var, self.demo_var = tk.IntVar(value=25), tk.IntVar(value=5), tk.BooleanVar()
        ttk.Label(f, textvariable=self.clock, font=("Arial", 44, "bold"), foreground="#37474f").pack(pady=(30, 4))
        ttk.Label(f, textvariable=self.hint, font=("Arial", 11, "italic")).pack()
        self.pomo_bar = ttk.Progressbar(f, length=300, maximum=100)
        self.pomo_bar.pack(pady=14)
        box = ttk.Frame(f)
        box.pack()
        for i, (txt, var, hi) in enumerate((("Fokus (mnt):", self.work_var, 120), ("Istirahat (mnt):", self.break_var, 60))):
            ttk.Label(box, text=txt).grid(row=0, column=2 * i)
            ttk.Spinbox(box, from_=1, to=hi, width=4, textvariable=var).grid(row=0, column=2 * i + 1, padx=4)
        ttk.Checkbutton(box, text="Mode demo (1 menit = 1 detik)", variable=self.demo_var).grid(
            row=1, column=0, columnspan=4, pady=6)
        row = ttk.Frame(f)
        row.pack(pady=4)
        ttk.Button(row, text="▶ Mulai Fokus", command=self.start_pomodoro).grid(row=0, column=0, padx=4)
        ttk.Button(row, text="■ Berhenti", command=self.stop_pomodoro).grid(row=0, column=1, padx=4)
        return f

    def seconds(self, var):
        try:
            minutes = max(1, int(var.get()))
        except (tk.TclError, ValueError):
            minutes = 25
        return minutes if self.demo_var.get() else minutes * 60

    def begin(self, state, secs):
        self.state, self.total = state, secs
        self.end = time.monotonic() + secs

    def start_pomodoro(self):
        if self.state == IDLE:
            self.begin(FOCUS, self.seconds(self.work_var))
            self.say("🌿 Fokus dimulai. Kucingmu tidur menemanimu.")

    def stop_pomodoro(self):
        self.state = IDLE
        self.say("Sesi dihentikan. Tidak apa-apa, coba lagi kapan pun kamu siap.")

    def update_timer(self):
        idle = self.state == IDLE
        remaining = self.seconds(self.work_var) if idle else max(0.0, self.end - time.monotonic())
        sec = int(remaining + 0.999)
        self.clock.set(f"{sec // 60:02d}:{sec % 60:02d}")
        self.hint.set(HINTS[self.state])
        self.pomo_bar["value"] = 0 if idle else 100 * (1 - remaining / self.total)
        if not idle and remaining <= 0:
            self.root.bell()
            if self.state == FOCUS:
                self.done(f"Sesi fokus selesai! {self.game.reward(POMO_XP, POMO_COINS)}")
                self.begin(BREAK, self.seconds(self.break_var))
            else:
                self.state = IDLE
                self.say("Istirahat selesai. Siap untuk sesi berikutnya?")

    def loop(self):
        self.frame_no += 1
        self.pet_view.sleeping = self.state == FOCUS
        self.pet_view.animate()
        self.update_timer()
        if self.frame_no % 100 == 0:                 
            self.game.tick_hunger()
            self.refresh()
        self.root.after(50, self.loop)

if __name__ == "__main__":
    root = tk.Tk()
    PawmodoroApp(root)
    root.mainloop()
