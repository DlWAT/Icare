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
from tkinter import colorchooser

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
            style = ttk.Style(self.trv)
            style.configure('Trerview',rowheight=30,height="5")
            self.trv.pack(expand=True, fill='both')
            
            
            xscroll=ttk.Scrollbar(wrapper1,orient="horizontal",command=self.trv.xview)
            xscroll.pack(side="bottom", fill="x")
            
            wrapper2 = tk.LabelFrame(self,text="Command")
            wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
            titles={'Structure': ["Intro_x4","Intro_x4","Intro_x4","Intro_x4","Couplet1_A_x2","Couplet1_A_x2","Couplet1_A_x2","Couplet1_A_x2",'','','','',''],\
                    'ParLED1':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED2':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED3':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED4':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED5':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED6':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED7':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED8':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'ParLED9':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'Strobe1':['','', '', '', '', '', '', '', '', '', '', '', ''],\
                    'Strobe2':['','', '', '', '', '', '', '', '', '', '', '', '']}
            self.trv["columns"] = list(x for x in range(len(list(titles.keys()))))
            self.trv['show'] = 'headings'
            for x, y in enumerate(titles.keys()):
                  self.trv.column(x, minwidth=20,width=50, stretch=True,  anchor='c')
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
            
            self.bouton_color= tk.Button(wrapper2, text="Add row", command = self.add_item)
            self.bouton_color.grid(column=1, row=2)
        
    def add_item(self):
        self.trv.insert("", "end", values=("", ""))
    
    def add_columns(self, columns, **kwargs):
        # Preserve current column headers and their settings
        current_columns = list(self.view['columns'])
        current_columns = {key:self.view.heading(key) for key in current_columns}

        # Update with new columns
        self.view['columns'] = list(current_columns.keys()) + list(columns)
        for key in columns:
            self.view.heading(key, text=key, **kwargs)

        # Set saved column values for the already existing columns
        for key in current_columns:
            # State is not valid to set with heading
            state = current_columns[key].pop('state')
            self.view.heading(key, **current_columns[key])
            
    def uni(self):
        my_color=colorchooser.askcolor()
        print(my_color[0][0])
        print(my_color[0][1])
        print(my_color[0][2])
            