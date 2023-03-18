import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import time
import pydmxIcare
import pydmxlight
import random
from tkinter import colorchooser

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex):
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

class ExperimentTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
        self.par_led1=pydmxlight.Par_Led_615_AFX(5,0)
        self.mydmx= pydmxIcare.DMX_Icare()
        
    def creer_widgets(self):
        self.enable=0
        self.enable_strobe=0
        self.enable_rand=0
        self.max=255
        list_group=[]
        sel=tk.StringVar()
        self.cb1 = ttk.Combobox(self, values=list_group,width=7,textvariable=sel)
        self.cb1.grid(row=0,column=0)
        
        self.l1=ttk.Label(self,text='New group')
        self.l1.grid(row=0,column=1)

        self.e1=tk.Entry(self,bg='Yellow',width=10)
        self.e1.grid(row=0,column=2)
        
        b1=ttk.Button(self,text='Add',command=self.my_insert)
        b1.grid(row=0,column=3)
        
        self.range_rouge = ttk.Scale(self, from_=255, to=0, orient='vertical')
        self.range_rouge.grid(column=1, row=1)

        #self.Scale.grid(row=0, column=0, padx=(20, 10), pady=(20, 0), sticky="ew")
        
        self.range_vert = tk.Scale(self, from_=255, to=0, orient='vertical',label="GREEN")
        self.range_vert.grid(column=2, row=1)

        self.range_bleu = tk.Scale(self, from_=255, to=0, orient='vertical',label="BLUE")
        self.range_bleu.grid(column=3, row=1)
        
        self.freq = tk.Scale(self, from_=1000, to=20, orient='vertical',label="FREQ")
        self.freq.grid(column=4, row=1)
        
        self.amp = tk.Scale(self, from_=255, to=0, orient='vertical',label="AMP")
        self.amp.grid(column=5, row=1)
        self.amp.set(255)
        
        self.shuffle = tk.Scale(self, from_=90, to=10, orient='vertical',label="Shuffle")
        self.shuffle.grid(column=6, row=1)
        
        self.canvas = tk.Canvas(self, width = 500, height = 500)
        self.rectangle=self.canvas.create_rectangle(50, 110,300,280, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()) +"""""")
        self.canvas.grid(column=0, row=2)

        self.bouton_stop= ttk.Button(self, text="Stop", command = self.stop)
        self.bouton_stop.grid(column=2, row=3)
        
        self.bouton_start= ttk.Button(self, text="Start", command = self.start)
        self.bouton_start.grid(column=1, row=3)
        
        self.bouton_blackout= ttk.Button(self, text="Blackout", command = self.blackout)
        self.bouton_blackout.grid(column=3, row=3)
        
        self.bouton_rand= ttk.Button(self, text="Random", command = self.rand_light)
        self.bouton_rand.grid(column=4, row=3)
        
        self.bouton_strobe= ttk.Button(self, text="Strobe", command = self.strobe)
        self.bouton_strobe.grid(column=5, row=3)
        
        self.bouton_rand= ttk.Button(self, text="Connection", command = self.connection)
        self.bouton_rand.grid(column=0, row=4)
        
        self.bouton_color= ttk.Button(self, text="Color", command = self.ask_color)
        self.bouton_color.grid(column=1, row=2)
        
        #self.thread_rand()
    def connection(self):
        self.mydmx.connection()
    def ask_color(self):
        my_color=colorchooser.askcolor()
        self.canvas.itemconfig(self.rectangle, fill=""""""+my_color[1])
        self.range_rouge.set(my_color[0][0])
        self.range_vert.set(my_color[0][1])
        self.range_bleu.set(my_color[0][2])
        #return my_color
    
    def my_insert(self): # adding data to Combobox
        #if e1.get() not in cb1['values']:
        list_values=list(self.cb1['values'])
        list_values.append(self.e1.get())
        self.cb1['values']=tuple(list_values) # add option
        
    def change_color(self):
        while True :
            if self.enable:
                self.max=self.amp.get()
                self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()))
                self.mydmx.set_channel(0,self.range_rouge.get())
                self.mydmx.set_channel(1,self.range_vert.get())
                self.mydmx.set_channel(2,self.range_bleu.get())
                self.mydmx.send_data()
                #self.max=self.amp.get()
            if self.enable_rand:
                self.range_rouge.set(random.randint(1,self.max),)
                self.range_vert.set(random.randint(1,self.max))
                self.range_bleu.set(random.randint(1,self.max))
                time.sleep(round(60*1/self.freq.get(),3))
            
            if self.enable_strobe:
                
                self.mydmx.set_channel(0,self.range_rouge.get())
                self.mydmx.set_channel(1,self.range_vert.get())
                self.mydmx.set_channel(2,self.range_bleu.get())
                #self.mydmx.set_data(self.par_led1.data,5,5)
                self.mydmx.send_data()
                time.sleep(round(60*1/self.freq.get()*(self.shuffle.get()/100),3))
                
                self.mydmx.set_channel(0,0)
                self.mydmx.set_channel(1,0)
                self.mydmx.set_channel(2,0)
                #self.mydmx.set_data(self.par_led1.data,5,5)
                self.mydmx.send_data()
                time.sleep(round(60*1/self.freq.get()*(1-self.shuffle.get()/100),3))
                
     
    def threading(self):
        t1=thr.Thread(target=self.change_color)
        t1.start()
        
    def rand_light(self):
        self.enable_rand=1
        self.enable_strobe=0
    
    def strobe(self):
        self.enable_strobe=1
        self.enable_rand=0
         
    def stop(self):
        self.enable=0
        self.enable_rand=0
        self.enable_strobe=0
        
    def start(self):
        self.enable=1
        self.threading()

    def blackout(self):
        self.enable=0
        self.enable_rand=0
        self.enable_strobe=0
        self.range_rouge.set(0)
        self.range_vert.set(0)
        self.range_bleu.set(0)
        for i in range (7):
            self.mydmx.set_channel(16*i+0,0)
            self.mydmx.set_channel(16*i+1,0)
            self.mydmx.set_channel(16*i+2,0)
        #self.mydmx.set_data(self.par_led1.data,5,5)
        self.mydmx.send_data()
        self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()))
        
    def newgroup(self):
        print("new group")
    
            