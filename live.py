import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import numpy as np
from tkinter import colorchooser
import json

class LiveTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
    
    
    def creer_widgets(self):
            wrapper1 = tk.LabelFrame(self,text="Sequence")
            wrapper1.pack(fill="both",expand="yes",padx=20,pady=10)
            
            wrapper2 = tk.LabelFrame(self,text="Player")
            wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
            
            wrapper3 = tk.LabelFrame(wrapper2,text="Control")
            wrapper3.grid(column=0, row=0)
            
            self.bouton_play= ttk.Button(wrapper3, text="Play")#, command = self.strobe)
            self.bouton_play.grid(column=0, row=0)
            
            self.bouton_pause= ttk.Button(wrapper3, text="Pause")#, command = self.strobe)
            self.bouton_pause.grid(column=1, row=0)
            
            self.bouton_reset= ttk.Button(wrapper3, text="Reset",)# command = self.strobe)
            self.bouton_reset.grid(column=2, row=0)
            
            self.bouton_next= ttk.Button(wrapper3, text="Next",)# command = self.strobe)
            self.bouton_next.grid(column=1, row=1)
            
            self.bouton_prev= ttk.Button(wrapper3, text="Previous",)# command = self.strobe)
            self.bouton_prev.grid(column=0, row=1)
            
            wrapper4 = tk.LabelFrame(wrapper2,text="Mods")
            wrapper4.grid(column=0, row=2)
            self.bouton_back= ttk.Button(wrapper4, text="Blackout",)# command = self.strobe)
            self.bouton_back.grid(column=0, row=0)
            
            self.bouton_back= ttk.Button(wrapper4, text="Solo",)# command = self.strobe)
            self.bouton_back.grid(column=1, row=0)
            
            self.bouton_back= ttk.Button(wrapper4, text="Random_fondu",)# command = self.strobe)
            self.bouton_back.grid(column=2, row=0)