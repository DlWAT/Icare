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
            trv=ttk.Treeview(wrapper1,columns=(1,2,3,4))
            style = ttk.Style(trv)
            style.configure('Trerview',rowheight=30,height="5")
            trv.pack(expand=True, fill='both')
            
            
            xscroll=ttk.Scrollbar(wrapper1,orient="horizontal",command=trv.xview)
            xscroll.pack(side="bottom", fill="x")
            
            wrapper2 = tk.LabelFrame(self,text="Command")
            wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
            titles={'Id': [1,2,3,4,5, 6, 7, 8, 9,10,11,12,13], 'Names':['Tom', 'Rob', 'Tim', 'Jim', 'Kim', 'Kim', 'Kim', 'Kim', 'Kim', 'Jim', 'Jim', 'Jim', 'Jim'], 'Column': [1,2,3,4,5, 6, 7, 8, 9,10,11,12,13]}
            trv["columns"] = list(x for x in range(len(list(titles.keys()))))
            trv['show'] = 'headings'
            for x, y in enumerate(titles.keys()):
                  trv.column(x, minwidth=20, stretch=True,  anchor='c')
                  trv.heading(x, text=y)

            for args in zip(*list(titles.values())):
                  trv.insert("", 'end', values =args) 
          