import tkinter as tk
import tkinter.ttk as ttk
import ExperimentTab
import sequence
import live
class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        
        tabControl=ttk.Notebook(self)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ExperimentTab.ExperimentTab()
        self.tab3 = sequence.SequenceTab()
        self.tab4 = live.LiveTab()
        #tabControl.add(self.tab1, text='Home')
        tabControl.add(self.tab2, text='Direct') 
        tabControl.add(self.tab3, text='Sequence') 
        tabControl.add(self.tab4, text='Live') 
        tabControl.pack(expand=1, fill="both")
        style = ttk.Style(self)
        self.tk.call("source", "Azure-ttk-theme-main/azure.tcl")
        self.tk.call("set_theme", "dark")
        #style.theme_use('azure')
        # Set the theme with the theme_use method
        
if __name__ == "__main__":
    app = Application()
    app.title("Icare")
    app.geometry("1280x720")
    app.mainloop()

