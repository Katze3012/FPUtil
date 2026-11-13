from tkinter import filedialog, messagebox
import glob
import matplotlib
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import FPUtil as fp
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
import os
matplotlib.use('TkAgg')

DELIMITERS = {"Tab": "\t", "Semikolon ;": ";", "Komma ,": ",", "Leerzeichen": " "}
DECIMALS = {"Punkt .": ".", "Komma ,": ","}

class GUI:
    def __init__(self,root):

        self.root = root
        self.root.title("FPUtil")
        self.root.geometry("1920x1080")
        self.selectedFile = tk.StringVar(value="No file selected")
        self.controls = tk.Frame(root)
        self.controls.pack(side=tk.TOP, fill=tk.X)
        self.plots = {}
        self.view_data = {}
        self.view_selected = {}
        self.current_plot = tk.StringVar()

        self.delimiter_var=tk.StringVar(value="Tab")
        self.decimal_var=tk.StringVar(value="Punkt .")
        self.skiprows_var=tk.StringVar(value="6")

        import_bar = tk.Frame(root)
        import_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(import_bar, text="Delimiter:").pack(side=tk.LEFT,padx=(10,5))
        ttk.Combobox(import_bar, textvariable=self.delimiter_var, values=list(DELIMITERS), state="readonly",width=12).pack(side=tk.LEFT)

        ttk.Label(import_bar, text="Decimal Separator:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Combobox(import_bar, textvariable=self.decimal_var, values=list(DECIMALS), state="readonly",width=8).pack(side=tk.LEFT)

        ttk.Label(import_bar,text="Skipped Rows:").pack(side=tk.LEFT,padx=(20, 5))
        ttk.Spinbox(import_bar,from_=0, to=100, textvariable=self.skiprows_var,width=4).pack(side=tk.LEFT)

        self.view_controls = tk.Frame(root)
        self.view_controls.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(self.controls, text="View:").pack(side=tk.LEFT,padx=(20,5))
        self.plot_box= ttk.Combobox(self.controls,textvariable=self.current_plot, state="readonly",width=28)
        self.plot_box.pack(side=tk.LEFT)
        self.plot_box.bind("<<ComboboxSelected>>",lambda e: self.redraw())

        self.current_file=tk.StringVar()

        ttk.Label(self.controls, text="File:").pack(side=tk.LEFT, padx=(20, 5))
        self.file_box = ttk.Combobox(self.controls, textvariable=self.current_file, state="readonly",width=28)
        self.file_box.pack(side=tk.LEFT)
        self.file_box.bind("<<ComboboxSelected>>",self.on_file_selected)

        self.result_text=tk.Text(root,height=10,wrap="word",relief="flat",bg=root.cget("bg"),font=("Consolas",10))
        self.result_text.pack(side=tk.BOTTOM,fill=tk.X,padx=10,pady=(0,5))
        self.result_text.configure(state="disabled")

        menu= tk.Menu(self.result_text,tearoff=0)
        menu.add_command(label="Copy all",command=self.copy_results)
        self.result_text.bind("<Button-3>",lambda e: menu.tk_popup(e.x_root,e.y_root))

        tk.Button(self.controls, text="Select file...", command=self.choose_file).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(self.controls, text="Select folder...", command=self.choose_folder).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(self.controls, textvariable=self.selectedFile, wraplength=400).pack(side=tk.LEFT,padx=10, pady=(0, 10))

        self.fig = Figure(figsize=(10,4),dpi=100)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, root)

    def registerPlot(self,name,func,n_plots=1,dataKey=None,controls = None,allData=False):
        self.plots[name] = dict(func=func,n_plots=n_plots,controls=controls,dataKey=dataKey or name,allData=allData)
        self.plot_box["values"] = list(self.plots)
        if not self.current_plot.get():
            self.plot_box.current(0)

    def current_view(self):
        return self.plots.get(self.current_plot.get())

    def get_data(self):
        view=self.current_view()
        if view is None:
            return None
        key = view["dataKey"]
        name = self.view_selected.get(key)
        entry=self.view_data.get(key, {}).get(name)
        return entry[1] if entry else None

    def redraw(self):
        view=self.current_view()
        if view is None:
            return
        self.update_view_controls(view["controls"])
        self.update_file_box(view)

        if view["allData"]:
            payload=list(self.iter_all_data())
            empty = len(payload)==0
        else:
            payload=self.get_data()
            empty = payload is None
        self.fig.clf()
        axes = [self.fig.add_subplot(1,view["n_plots"],i+1)
                for i in range(view["n_plots"])]

        if empty:
            axes[0].text(0.5,0.5,"For this view please load a file",ha="center",va="center",transform=axes[0].transAxes)
        else:
            view["func"](axes, payload)

        self.fig.tight_layout()
        self.canvas.draw()

    def update_view_controls(self,controls):
        for child in self.view_controls.winfo_children():
            child.destroy()
        if controls:
            controls(self.view_controls,self)

    def load_paths(self,paths):
        view = self.current_view()
        if view is None or not paths:
            return
        delimiter = DELIMITERS[self.delimiter_var.get()]
        decimal = DECIMALS[self.decimal_var.get()]

        if delimiter==decimal:
            messagebox.showerror("Good Luck","Good Luck buddy cant help you with that")
            return

        try:
            skiprows = int(self.skiprows_var.get())
        except(tk.TclError,ValueError):
            messagebox.showerror("Error", "Skiprows must be an integer")

        key = view["dataKey"]
        files = self.view_data.setdefault(key, {})
        errors = []

        for path in paths:
            try:
                data = fp.csvImporterAndParser(path,delimiter=delimiter,decimal=decimal,skiprows=int(self.skiprows_var.get()))
                files[os.path.basename(path)]=(path, data)
                self.view_selected[key]=os.path.basename(path)
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
            self.redraw()

        if errors:
            messagebox.showwarning("Some files could not be parsed", "\n".join(errors[:10]))

    def on_file_selected(self,event=None):
        view = self.current_view()
        if view:
            self.view_selected[view["dataKey"]]=self.current_file.get()
        self.redraw()

    def update_file_box(self,view):
        key = view["dataKey"]
        names = list(self.view_data.get(key,{}))
        self.file_box["values"] = names
        self.current_file.set(self.view_selected.get(key,""))

    def iter_all_data(self):
        for key,files in self.view_data.items():
            for name, (path, data) in files.items():
                yield key, name, path, data

    def set_results(self,text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0,tk.END)
        self.result_text.insert("1.0",text)
        self.result_text.config(state=tk.DISABLED)

    def copy_results(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result_text.get("1.0",tk.END)).strip()

    def choose_file(self):
        path = filedialog.askopenfilenames(
            title = f"Choose files for '{self.current_file.get()}'",
            initialdir = os.getcwd(),
            filetypes = (("CSV, DAT and TXT files","*.csv *.dat *.txt"),("All files","*.*")),
        )
        self.load_paths(path)

    def choose_folder(self):
        folder = filedialog.askdirectory(title = "Choose folder", initialdir = os.getcwd())
        if not folder:
            return
        paths = []
        for ext in ("*.dat","*.txt","*.csv"):
            paths.extend(glob.glob(os.path.join(folder,ext)))
        paths.sort()

        if not paths:
            messagebox.showerror("Error", "No files to choose from")
            return
        self.load_paths(paths)