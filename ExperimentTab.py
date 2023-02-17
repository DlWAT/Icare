import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import time
import pydmxIcare
import pydmxlight
import random
def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class ExperimentTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
        self.par_led1=pydmxlight.Par_Led_615_AFX(5,0)
        self.mydmx= pydmxIcare.DMX_Icare()
        self.mydmx.connection()
    def creer_widgets(self):
        self.enable=0
        self.enable_rand=0
        self.max=255
        list_group=[]
        sel=tk.StringVar()
        self.cb1 = ttk.Combobox(self, values=list_group,width=7,textvariable=sel)
        self.cb1.grid(row=0,column=0)
        
        self.l1=tk.Label(self,text='New group')
        self.l1.grid(row=0,column=1)

        self.e1=tk.Entry(self,bg='Yellow',width=10)
        self.e1.grid(row=0,column=2)
        
        b1=tk.Button(self,text='Add',command=self.my_insert)
        b1.grid(row=0,column=3)
        
        self.range_rouge = tk.Scale(self, from_=255, to=0, orient='vertical',label="RED")
        self.range_rouge.grid(column=1, row=1)
        
        self.range_vert = tk.Scale(self, from_=255, to=0, orient='vertical',label="GREEN")
        self.range_vert.grid(column=2, row=1)

        self.range_bleu = tk.Scale(self, from_=255, to=0, orient='vertical',label="BLUE")
        self.range_bleu.grid(column=3, row=1)
        
        self.freq = tk.Scale(self, from_=1000, to=20, orient='vertical',label="FREQ")
        self.freq.grid(column=4, row=1)
        
        self.amp = tk.Scale(self, from_=255, to=0, orient='vertical',label="AMP")
        self.amp.grid(column=5, row=1)
        self.amp.set(255)
        
        
        self.canvas = tk.Canvas(self, width = 500, height = 500)
        self.rectangle=self.canvas.create_rectangle(50, 110,300,280, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()) +"""""")
        self.canvas.grid(column=0, row=2)

        self.bouton_stop= tk.Button(self, text="Stop", command = self.stop)
        self.bouton_stop.grid(column=2, row=3)
        
        self.bouton_start= tk.Button(self, text="Start", command = self.start)
        self.bouton_start.grid(column=1, row=3)
        
        self.bouton_blackout= tk.Button(self, text="Blackout", command = self.blackout)
        self.bouton_blackout.grid(column=3, row=3)
        
        self.bouton_rand= tk.Button(self, text="Random", command = self.rand_light)
        self.bouton_rand.grid(column=4, row=3)
        
        self.threading()
        #self.thread_rand()
    
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
                #self.par_led1.set_channel(0,self.range_rouge.get())
                #self.par_led1.set_channel(1,self.range_vert.get())
                #self.par_led1.set_channel(2,self.range_bleu.get())
                self.mydmx.set_channel(0,self.range_rouge.get())
                self.mydmx.set_channel(1,self.range_vert.get())
                self.mydmx.set_channel(2,self.range_bleu.get())
                #self.mydmx.set_data(self.par_led1.data,5,5)
                self.mydmx.send_data()
                #self.max=self.amp.get()
            if self.enable_rand:
                self.range_rouge.set(random.randint(1,self.max),)
                self.range_vert.set(random.randint(1,self.max))
                self.range_bleu.set(random.randint(1,self.max))
                time.sleep(round(60*1/self.freq.get(),3))
     
    def threading(self):
        t1=thr.Thread(target=self.change_color)
        t1.start()
        
    def rand_light(self):
        self.enable_rand=1
        
    def stop(self):
        self.enable=0
        self.enable_rand=0
        
    def start(self):
        self.enable=1

    def blackout(self):
        self.enable=0
        self.enable_rand=0
        self.range_rouge.set(0)
        self.range_vert.set(0)
        self.range_bleu.set(0)
        self.mydmx.set_channel(0,self.range_rouge.get())
        self.mydmx.set_channel(1,self.range_vert.get())
        self.mydmx.set_channel(2,self.range_bleu.get())
        #self.mydmx.set_data(self.par_led1.data,5,5)
        self.mydmx.send_data()
        self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()))
        
    def newgroup(self):
        print("new group")
    
            