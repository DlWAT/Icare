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
import numpy as np
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
            self.titles={'Line': ["1","2","3","4","5","6","7","8",'','','','',''],\
                    'Structure': ["Intro_x4","Intro_x4","Intro_x4","Intro_x4","Couplet1_A_x2","Couplet1_A_x2","Couplet1_A_x2","Couplet1_A_x2",'','','','',''],\
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
            self.trv["columns"] = list(x for x in range(len(list(self.titles.keys()))))
            self.trv['show'] = 'headings'
            for x, y in enumerate(self.titles.keys()):
                  self.trv.column(x, minwidth=20,width=50, stretch=True,  anchor='c')
                  self.trv.heading(x, text=y)

            for args in zip(*list(self.titles.values())):
                  self.trv.insert("", 'end', values =args) 
                       
            
            self.bouton_strobe= ttk.Button(wrapper2, text="Strobe", command = self.strobe)
            self.bouton_strobe.grid(column=0, row=2)
            
            self.fond= ttk.Button(wrapper2, text="Fondu", command = self.fondu)
            self.fond.grid(column=1, row=0)
            
            self.bouton_uni= ttk.Button(wrapper2, text="Uniform", command = self.uni)
            self.bouton_uni.grid(column=1, row=1)
            
            self.bouton_color= ttk.Button(wrapper2, text="Add row", command = self.add_item)
            self.bouton_color.grid(column=1, row=2)

            self.bouton_save_seq= ttk.Button(wrapper2, text="Save sequence", command = self.save_seq)
            self.bouton_save_seq.grid(column=1, row=3)
            
            self.list_group=['ParLED1','ParLED2','ParLED3','ParLED4','ParLED5','ParLED6','ParLED7','ParLED8','ParLED9','Strobe1','Strobe2']
            sel=tk.StringVar()
            self.cb1 = ttk.Combobox(wrapper2, values=self.list_group,width=20,textvariable=sel)
            self.cb1.grid(row=0,column=5)
            
            self.l1=tk.Label(wrapper2,text='#Line')
            self.l1.grid(row=0,column=6)
            self.e1=tk.Entry(wrapper2,width=10)
            self.e1.grid(row=0,column=7)
            
            self.l2=tk.Label(wrapper2,text='#tps')
            self.l2.grid(row=0,column=8)
            self.e2=tk.Entry(wrapper2,width=10)
            self.e2.grid(row=0,column=9)
            
            self.l3=tk.Label(wrapper2,text='Freq')
            self.l3.grid(row=0,column=10)
            self.e3=tk.Entry(wrapper2,width=10)
            self.e3.grid(row=0,column=11)
            
            self.l4=tk.Label(wrapper2,text='Amp')
            self.l4.grid(row=0,column=12)
            self.e4=tk.Entry(wrapper2,width=10)
            self.e4.grid(row=0,column=13)
            
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
        name=self.cb1.get()
        col=self.list_group.index(name)
        row=int(self.e1.get())
        nbrtps=int(self.e2.get())
        for i in range(nbrtps):
            if i==0:
                val="uni_"+str(nbrtps)+'_'+str(my_color[0][0])+'_'+str(my_color[0][1])+'_'+str(my_color[0][2])
                self.edit_item(row+i,col+2,val)
            else:
                val="|"
                self.edit_item(row+i,col+2,val)
                
    def fondu(self):
        my_color=colorchooser.askcolor()
        my_color2=colorchooser.askcolor()
        name=self.cb1.get()
        col=self.list_group.index(name)
        row=int(self.e1.get())
        nbrtps=int(self.e2.get())
        for i in range(nbrtps):
            if i==0:
                val="fond_"+str(nbrtps)+'_'+str(my_color[0][0])+'_'+str(my_color[0][1])+'_'+str(my_color[0][2])+'_'+str(my_color2[0][0])+'_'+str(my_color2[0][1])+'_'+str(my_color2[0][2])
                self.edit_item(row+i,col+2,val)
            else:
                val="|"
                self.edit_item(row+i,col+2,val)
    
    def strobe(self):
        my_color=colorchooser.askcolor()
        name=self.cb1.get()
        col=self.list_group.index(name)
        row=int(self.e1.get())
        nbrtps=int(self.e2.get())
        freq=int(self.e3.get())
        for i in range(nbrtps):
            if i==0:
                val="str_"+str(nbrtps)+'_'+str(my_color[0][0])+'_'+str(my_color[0][1])+'_'+str(my_color[0][2])+'_'+str(freq)
                self.edit_item(row+i,col+2,val)
            else:
                val="|"
                self.edit_item(row+i,col+2,val)
    
    
    def edit_item(self,row,col,val):
        
        item_details = self.trv.item("I00"+str(row))
        # The row's displayed text will be in the 'values' key.
        
        L_values=item_details.get("values")
        L_values[col]=val
        self.trv.item("I00"+str(row), text="blub", values=tuple(L_values))
        
    def save_seq(self):
        ar=[['Line','Structure','ParLED1','ParLED2','ParLED3','ParLED4','ParLED5','ParLED6','ParLED7','ParLED8','ParLED9','Strobe1','Strobe2']]
        for line in self.trv.get_children():
            ar_i=[]
            for value in self.trv.item(line)['values']:
                ar_i.append(value)
            ar.append(ar_i)
        y=np.array([np.array(xi) for xi in ar])
        output={}
        output["Header"]={"Structure":self.titles["Structure"]}
        output["Header"]["Tempo"]="60"
        output["data"]={}
        print(output)
        
            