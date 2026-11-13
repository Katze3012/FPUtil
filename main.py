import tkinter as tk
from FPUtilGUI import GUI

import fp4point9a

if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    fp4point9a.main(app)
    root.mainloop()

