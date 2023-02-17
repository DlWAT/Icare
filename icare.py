import tkinter as tk
import tkinter.ttk as ttk
import ExperimentTab

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        
        tabControl=ttk.Notebook(self)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ExperimentTab.ExperimentTab()
        
        tabControl.add(self.tab1, text='Tab 1')
        tabControl.add(self.tab2, text='Tab 2') 
        tabControl.pack(expand=1, fill="both")
        
if __name__ == "__main__":
    app = Application()
    app.title("Icare")
    app.geometry("950x750")
    app.mainloop()

