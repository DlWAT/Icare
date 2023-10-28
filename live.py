import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import numpy as np
from tkinter import colorchooser
import json
import emoji
import os 
from tkinter import filedialog
import time
class LiveTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
    
    def creer_widgets(self):
            self.paus=0
            self.pla=0
            self.all_sel=0
            self.freq=60
            wrapper1 = ttk.LabelFrame(self,text="Sequence")
            wrapper1.pack(fill="both",expand="yes",padx=20,pady=10)
            
            wrapper_time=ttk.LabelFrame(self,text="Time",height=10,width=2000)
            wrapper_time.pack(fill="both",expand="no",padx=10,pady=10)
            
            self.progress_bar=ttk.Progressbar(wrapper_time, orient='horizontal', length=1800)
            self.progress_bar.pack(padx=10,pady=10)
            
            wrapper2 = ttk.LabelFrame(self,text="Player")
            wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
            
            wrapper3 = ttk.LabelFrame(wrapper2,text="Control")
            wrapper3.grid(column=0, row=0,padx=10,pady=10)
            wrapper5 = ttk.LabelFrame(wrapper1,text="Parameters")
            wrapper5.grid(column=4, row=1)            
            
            self.freq_label=ttk.Label(wrapper5,text='Frequence : ')
            self.freq_label.grid(column=0, row=0,padx=5,pady=5)
            self.freq_entry=ttk.Entry(wrapper5)
            self.freq_entry.grid(column=1, row=0,padx=5,pady=5)
            
            self.amp_label=ttk.Label(wrapper5,text='Amplitude : ')
            self.amp_label.grid(column=0, row=1,padx=5,pady=5)
            self.amp_label=ttk.Entry(wrapper5)
            self.amp_label.grid(column=1, row=1,padx=5,pady=5)
            
            self.bouton_load_song= ttk.Button(wrapper1, text="Load song", command = self.load_song)
            self.bouton_load_song.grid(column=1, row=0,padx=5,pady=5)
            
            self.bouton_enable= ttk.Button(wrapper1, text="Select/Unselect module", command = self.enable)
            self.bouton_enable.grid(column=2, row=0,padx=5,pady=5) 
            
            self.bouton_allselect= ttk.Button(wrapper1, text="Select all", command = self.allselect)
            self.bouton_allselect.grid(column=3, row=0,padx=5,pady=5)            
            
            self.bouton_play= ttk.Button(wrapper3, text="     "+f'{emoji.emojize(":play_button:")}', command = self.threading)
            self.bouton_play.grid(column=0, row=0,padx=5,pady=5)
            
            self.bouton_pause= ttk.Button(wrapper3, text=f'{emoji.emojize(":pause_button:")}', command = self.pause)
            self.bouton_pause.grid(column=1, row=0,padx=5,pady=5)
            
            self.bouton_stop= ttk.Button(wrapper3, text=f'{emoji.emojize(":stop_button:")}', command = self.stop)
            self.bouton_stop.grid(column=2, row=0,padx=5,pady=5)
            
            self.bouton_next= ttk.Button(wrapper3, text=f'{emoji.emojize(":fast-forward_button:")}',)# command = self.strobe)
            self.bouton_next.grid(column=1, row=1,padx=5,pady=5)
            
            self.bouton_prev= ttk.Button(wrapper3, text=f'{emoji.emojize(":fast_reverse_button:")}',)# command = self.strobe)
            self.bouton_prev.grid(column=0, row=1,padx=5,pady=5)
            
            wrapper4 = ttk.LabelFrame(wrapper2,text="Mods")
            wrapper4.grid(column=1, row=0,padx=10,pady=10)
            self.bouton_back= ttk.Button(wrapper4, text="Blackout",)# command = self.strobe)
            self.bouton_back.grid(column=0, row=0,padx=5,pady=5)
            
            self.bouton_back= ttk.Button(wrapper4, text="Solo",)# command = self.strobe)
            self.bouton_back.grid(column=0, row=1,padx=5,pady=5)
            
            self.bouton_back= ttk.Button(wrapper4, text="Random_fondu",)# command = self.strobe)
            self.bouton_back.grid(column=1, row=0,padx=5,pady=5)
            
            wrapper6 = ttk.LabelFrame(wrapper2,text="Display")
            wrapper6.grid(column=2, row=0,padx=10,pady=10)
            
            self.section_label=ttk.Label(wrapper6,text='Section : ')
            self.section_label.grid(column=0, row=0,padx=5,pady=5)
            
            self.section_val=ttk.Label(wrapper6,text='         ')
            self.section_val.grid(column=1, row=0,padx=5,pady=5)
            
            
            self.trv=ttk.Treeview(wrapper1,selectmode='browse',height=9)
            self.trv.grid(row=1,column=0,columnspan=2,padx=5,pady=10)
            self.trv["columns"]=("1","2")
            self.trv['show']='tree headings'
            self.trv.column("#0", width = 20, anchor ='c')
            self.trv.column("1",width=20,anchor='w')
            self.trv.column("2",width=300,anchor='w')
            self.trv.heading("#0", text ="")
            self.trv.heading("1",text="#",anchor='w')
            self.trv.heading("2",text="Songs",anchor='w')
            
            
            self.trv2=ttk.Treeview(wrapper1,selectmode='browse',height=9)
            self.trv2.grid(row=1,column=2,columnspan=2,padx=10,pady=5)
            self.trv2["columns"]=("1","2")
            self.trv2['show']='tree headings'
            self.trv2.column("#0", width = 20, anchor ='c')
            self.trv2.column("1",width=20,anchor='c')
            self.trv2.column("2",width=300,anchor='w')
            self.trv2.heading("#0", text ="")
            self.trv2.heading("1",text=f'{emoji.emojize(":check_mark_button:")}',anchor='c')
            self.trv2.heading("2",text="Modules",anchor='w')
            
            b1=ttk.Button(wrapper1,text='Select a song',command=self.my_fun)
            b1.grid(row=0,column=0,padx=5,pady=10)
            
            
            
    def my_fun(self): 
        #path = filedialog.askdirectory() # select directory 
        self.file = filedialog.askopenfilename()
        # Split the filepath to get the directory
        self.path = os.path.split(self.file)[0]
        root=next(os.walk(self.path))[0] # path 
        dirnames=next(os.walk(self.path))[1] # list of directories 
        files=next(os.walk(self.path))[2] # list of files 
        for item in self.trv.get_children():
            self.trv.delete(item)
        i=1
        f2i=1 #sub directory id 
        for d in dirnames:
            self.trv.insert("", 'end',iid=i,values =d)
            path2=self.path+'/'+d # Path for sub directory 
            #print(path2)
            files2=next(os.walk(path2))[2] # file list of Sub directory 
            for f2 in files2:  # list of files 
                print(f2)
                self.trv.insert(i, 'end',iid='sub'+str(f2i),values=(f2i,f2))
                f2i=f2i+1
            i=i+1
        for f in files:  # list of files 
            self.trv.insert("", 'end',iid=i,values =(i,f[:-5]))
            i=i+1
        le=len(os.path.split(self.file)[0])
        self.search(self.file[le+1:-5])
        
    def load_song(self):
        curItem = self.trv.focus()
        file=self.path+'/'+self.trv.item(curItem)["values"][1]+'.json'
        with open(file) as json_file:
            self.data = json.load(json_file)
        list_modules=self.data["Header"]["Modules"]
        i=0
        for module in list_modules:  # list of files 
            self.trv2.insert("", 'end',iid=i,values =(f'{emoji.emojize(":black_square_button:")}',module))
            i=i+1
            
    def search(self,query):
        selections = []
        for child in self.trv.get_children():
            if query in self.trv.item(child)['values']:   # compare strings in  lower cases.
                selections.append(child)
        print(query+' open')
        self.trv.selection_set(selections)
    
    def threading(self):
        self.paus=0
        if self.paus==0 and self.pla==0:
            self.pla=1
            t1=thr.Thread(target=self.play)
            t1.daemon = True
            t1.start()
        
    def play(self):
        le=len(self.data["data"])
        self.i=1
        if self.freq_entry.get():
            self.freq=int(self.freq_entry.get())
            print(self.freq)
        while self.i<le+1 :
            if self.paus==0:
                sect=self.data["data"][str(self.i)]["section"]
                self.progress_bar['value']=int(100*(self.i)/le)
                self.section_val.configure(text=sect)
                self.i+=1
                time.sleep(60/self.freq)
                
    def pause(self):
        if self.paus==0:
            self.paus=1
        else :
            self.paus=0
    
    def stop(self):
        if self.paus==0:
            self.pause()
        self.progress_bar['value']=0
        self.i=0

    def enable(self):
        curItem = self.trv2.focus()        
        selected_item = self.trv2.selection()[0]
        if self.trv2.item(selected_item)['values'][0]==f'{emoji.emojize(":check_mark_button:")}':
        
            self.trv2.item(selected_item, values=(f'{emoji.emojize(":black_square_button:")}', self.trv2.item(curItem)["values"][1]))
        else :
            self.trv2.item(selected_item, values=(f'{emoji.emojize(":check_mark_button:")}', self.trv2.item(curItem)["values"][1]))
            
    def allselect(self):
        item_count = len (self.trv2.get_children())
        if self.all_sel==0:
            for i in range(item_count):
                self.trv2.item(i, values=(f'{emoji.emojize(":check_mark_button:")}', self.trv2.item(i)["values"][1]))
                self.all_sel=1
                self.bouton_allselect.configure(text="Unselect all")
                
        else:
            for i in range(item_count):
                self.trv2.item(i, values=(f'{emoji.emojize(":black_square_button:")}', self.trv2.item(i)["values"][1]))
                self.all_sel=0
                self.bouton_allselect.configure(text="Select all")
                