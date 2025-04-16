import tkinter as tk
from controller.graphicsEditor import GraphicsEditor
if __name__ == "__main__":
    root = tk.Tk()
    app = GraphicsEditor(root)
    root.mainloop()
