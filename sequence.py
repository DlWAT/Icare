# import json 

# dict={"headers":{"structure":["intro","Couplet1","Refrain1","Couplet2","Refrain2","Solo"]},
#       "data":{"intro":[],"Couplet1":[],"Refrain1":[],"Couplet2":[],"Refrain2":[],"Solo":[]} }

# dict["data"]["intro"]=[[2,125,20,35],
#                        [2,20,53,128]]

# dict["data"]["Refrain1"]=[[0.5,125,20,35],
#                           [0.5,20,53,128]]

# with open("esquence_example.json", "w") as outfile:
#     json.dump(dict, outfile)

import tkinter as tk
import tkinter.ttk as ttk
import threading as thr

class SequenceTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
        #self.par_led1=pydmxlight.Par_Led_615_AFX(5,0)
        #self.mydmx= pydmxIcare.DMX_Icare()
        
    def creer_widgets(self):
            wrapper1 = tk.LabelFrame(self,text="Sequence")
            wrapper1.pack(fill="both",expand="yes",padx=20,pady=10)
            self.trv=ttk.Treeview(wrapper1,columns=(1,2,3,4))
            style = ttk.Style(trv)
            style.configure('Trerview',rowheight=30,height="5")
            self.trv.pack(expand=True, fill='both')
            
            
            xscroll=ttk.Scrollbar(wrapper1,orient="horizontal",command=trv.xview)
            xscroll.pack(side="bottom", fill="x")
            
            wrapper2 = tk.LabelFrame(self,text="Command")
            wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
            titles={'ParLED1': [1,2,3,4,5, 6, 7, 8, 9,10,11,12,13], 'Names':['Tom','', 'Tim', 'Jim', 'Kim', 'Kim', 'Kim', 'Kim', 'Kim', 'Jim', 'Jim', 'Jim', 'Jim'], 'Column': [1,2,3,4,5, 6, 7, 8, 9,10,11,12,13]}
            self.trv["columns"] = list(x for x in range(len(list(titles.keys()))))
            self.trv['show'] = 'headings'
            for x, y in enumerate(titles.keys()):
                  self.trv.column(x, minwidth=20, stretch=True,  anchor='c')
                  self.trv.heading(x, text=y)

            for args in zip(*list(titles.values())):
                  self.trv.insert("", 'end', values =args) 
            self.bouton_blackout= tk.Button(wrapper2, text="Blackout")#, command = self.blackout)
            self.bouton_blackout.grid(column=0, row=0)
            
            self.bouton_rand= tk.Button(wrapper2, text="Random")#, command = self.rand_light)
            self.bouton_rand.grid(column=0, row=1)
            
            self.bouton_strobe= tk.Button(wrapper2, text="Strobe")#, command = self.strobe)
            self.bouton_strobe.grid(column=0, row=2)
            
            self.bouton_rand= tk.Button(wrapper2, text="Connection")#, command = self.connection)
            self.bouton_rand.grid(column=1, row=0)
            
            self.bouton_co= tk.Button(wrapper2, text="Connection")#, command = self.connection)
            self.bouton_co.grid(column=1, row=1)
            
            self.bouton_color= tk.Button(wrapper2, text="Color")#, command = self.ask_color)
            self.bouton_color.grid(column=1, row=2)
        
    def add_item(self):
        self.trv.insert("", "end", values=("", "bar"))
            