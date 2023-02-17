import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import time
import pydmxIcare
import pydmxlight
import ExperimentTab
def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        
        self.mydmx= pydmxIcare.DMX_Icare()
        self.par_led1=pydmxlight.Par_Led_615_AFX(5,0)
        self.mydmx.connection()
        
        tabControl=ttk.Notebook(self)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ExperimentTab.ExperimentTab()
        
        tabControl.add(self.tab1, text='Tab 1')
        tabControl.add(self.tab2, text='Tab 2') 
        tabControl.pack(expand=1, fill="both")
        

if __name__ == "__main__":
    app = Application()
    app.title("Icare")
    app.geometry("750x750")
    app.mainloop()

