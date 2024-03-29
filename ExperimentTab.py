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

def ttk_scale_callback(value):
    # 'value' seems to be a string - bug or feature?
    value_label.config(text=round(float(value)))    
    
class ExperimentTab(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        self.creer_widgets()
        self.par_led1=pydmxlight.Par_Led_615_AFX(15,0)
        self.mydmx= pydmxIcare.DMX_Icare()
        
    def creer_widgets(self):
        self.enable=0
        self.enable_strobe=0
        self.enable_rand=0
        self.max=255
        list_group=[]
        wrapper1 = tk.LabelFrame(self,text="Test")
        wrapper1.pack(fill="both",expand="yes",padx=20,pady=10)
        wrapper2 = tk.LabelFrame(self,text="Poter")
        wrapper2.pack(fill="both",expand="yes",padx=20,pady=10)
        sel=tk.StringVar()
        self.cb1 = ttk.Combobox(self, values=list_group,width=7,textvariable=sel)
        #self.cb1.grid(row=0,column=0)
        
        self.l1=ttk.Label(self,text='New group')
        #self.l1.grid(row=0,column=1)

        self.e1=tk.Entry(self,bg='Yellow',width=10)
        #self.e1.grid(row=0,column=2)
        
        b1=ttk.Button(self,text='Add',command=self.my_insert)
        #b1.grid(row=0,column=3)
        
        self.range_rouge_label=ttk.Label(wrapper2, text="Rouge")
        slider_rouge = tk.StringVar()
        slider_rouge.set('0')
        self.range_rouge = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_rouge.set('%d' % float(s)))
        self.range_rouge_label_value=ttk.Label(wrapper2, textvariable=slider_rouge)
        self.range_rouge_label.grid(column=1, row=0)
        self.range_rouge.grid(column=1, row=1)
        self.range_rouge_label_value.grid(column=1, row=2)
        
        self.range_vert_label=ttk.Label(wrapper2, text="Vert")
        slider_vert = tk.StringVar()
        slider_vert.set('0')
        self.range_vert = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_vert.set('%d' % float(s)))
        self.range_vert_label_value=ttk.Label(wrapper2, textvariable=slider_vert)
        self.range_vert_label.grid(column=2, row=0)
        self.range_vert.grid(column=2, row=1)
        self.range_vert_label_value.grid(column=2, row=2)
        
        self.range_bleu_label=ttk.Label(wrapper2, text="Bleu")
        slider_bleu = tk.StringVar()
        slider_bleu.set('0')
        self.range_bleu = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_bleu.set('%d' % float(s)))
        self.range_bleu_label_value=ttk.Label(wrapper2, textvariable=slider_bleu)
        self.range_bleu_label.grid(column=3, row=0)
        self.range_bleu.grid(column=3, row=1)
        self.range_bleu_label_value.grid(column=3, row=2)
        
        self.freq_label=ttk.Label(wrapper2, text="Fréquence")
        slider_freq = tk.StringVar()
        slider_freq.set('20')        
        self.freq = ttk.Scale(wrapper2, from_=1000, to=20, orient='vertical', command=lambda s:slider_freq.set('%d' % float(s)))
        self.freq_label_value=ttk.Label(wrapper2, textvariable=slider_freq)
        self.freq_label.grid(column=4, row=0)
        self.freq.grid(column=4, row=1)
        self.freq_label_value.grid(column=4, row=2)
        
        self.amp_label=ttk.Label(wrapper2, text="Amplitude")
        slider_amp = tk.StringVar()
        slider_amp.set(0)
        self.amp = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_amp.set('%d' % float(s)))
        self.amp_label_value=ttk.Label(wrapper2, textvariable=slider_amp)
        self.amp_label.grid(column=5,row=0)
        self.amp.grid(column=5, row=1)
        self.amp_label_value.grid(column=5, row=2)
        
        self.shuffle = tk.Scale(wrapper2, from_=90, to=10, orient='vertical',label="Shuffle")
        self.shuffle.grid(column=6, row=1)
        
        
        self.range_pan_label=ttk.Label(wrapper2, text="Pan")
        slider_pan = tk.StringVar()
        slider_pan.set('0')
        self.range_pan = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_pan.set('%d' % float(s)))
        self.range_pan_label_value=ttk.Label(wrapper2, textvariable=slider_pan)
        self.range_pan_label.grid(column=7, row=0)
        self.range_pan.grid(column=7, row=1)
        self.range_pan_label_value.grid(column=7, row=2)
        
        self.range_tilt_label=ttk.Label(wrapper2, text="Tilt")
        slider_tilt = tk.StringVar()
        slider_tilt.set('0')
        self.range_tilt = ttk.Scale(wrapper2, from_=255, to=0, orient='vertical', command=lambda s:slider_tilt.set('%d' % float(s)))
        self.range_tilt_label_value=ttk.Label(wrapper2, textvariable=slider_tilt)
        self.range_tilt_label.grid(column=8, row=0)
        self.range_tilt.grid(column=8, row=1)
        self.range_tilt_label_value.grid(column=8, row=2)
        
        self.canvas = tk.Canvas(wrapper2, width = 500, height = 500)
        self.rectangle=self.canvas.create_rectangle(50, 110,300,280, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()) +"""""")
        self.canvas.grid(column=0, row=2)

        self.bouton_stop= ttk.Button(wrapper1, text="Stop", command = self.stop)
        self.bouton_stop.grid(column=2, row=3)
        
        self.bouton_start= ttk.Button(wrapper1, text="Start", command = self.start)
        self.bouton_start.grid(column=1, row=3)
        
        self.bouton_blackout= ttk.Button(wrapper1, text="Blackout", command = self.blackout)
        self.bouton_blackout.grid(column=3, row=3)
        
        self.bouton_rand= ttk.Button(wrapper1, text="Random", command = self.rand_light)
        self.bouton_rand.grid(column=4, row=3)
        
        self.bouton_strobe= ttk.Button(wrapper1, text="Strobe", command = self.strobe)
        self.bouton_strobe.grid(column=5, row=3)
        
        self.bouton_rand= ttk.Button(wrapper1, text="Connection", command = self.connection)
        self.bouton_rand.grid(column=0, row=4)
        
        self.bouton_color= ttk.Button(wrapper1, text="Color", command = self.ask_color)
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
                self.max=int(self.amp.get()+1)
                self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(int(self.range_rouge.get()), int(self.range_vert.get()),int(self.range_bleu.get())))
                self.mydmx.set_channel(0,255)
                self.mydmx.set_channel(8,0)
                
                self.mydmx.set_channel(1,int(self.amp.get()))
                
                self.mydmx.set_channel(9,int(self.range_rouge.get()))
                self.mydmx.set_channel(10,int(self.range_vert.get()))
                self.mydmx.set_channel(11,int(self.range_bleu.get()))
                
                self.mydmx.set_channel(3,int(self.range_pan.get()))
                self.mydmx.set_channel(5,int(self.range_tilt.get()))
                #self.mydmx.set_channel(11,int(self.range_bleu.get()))
                self.mydmx.send_data()
                #self.max=self.amp.get()
            if self.enable_rand:
                self.mydmx.set_channel(9,int(self.range_rouge.get()))
                self.mydmx.set_channel(10,int(self.range_vert.get()))
                self.mydmx.set_channel(11,int(self.range_bleu.get()))
                time.sleep(round(60*1/(self.freq.get()+1),3))
            
            if self.enable_strobe:
                
                self.mydmx.set_channel(9,int(self.range_rouge.get()))
                self.mydmx.set_channel(10,int(self.range_vert.get()))
                self.mydmx.set_channel(11,int(self.range_bleu.get()))
                #self.mydmx.set_data(self.par_led1.data,5,5)
                self.mydmx.send_data()
                time.sleep(round(60*1/self.freq.get()*(self.shuffle.get()/100),3))
                
                self.mydmx.set_channel(9,int(self.range_rouge.get()))
                self.mydmx.set_channel(10,int(self.range_vert.get()))
                self.mydmx.set_channel(11,int(self.range_bleu.get()))
                #self.mydmx.set_data(self.par_led1.data,5,5)
                self.mydmx.send_data()
                time.sleep(round(60*1/(self.freq.get()+1)*(1-self.shuffle.get()/100),3))
                
     
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
            self.mydmx.set_channel(10*i+0,0)
            self.mydmx.set_channel(10*i+1,0)
            self.mydmx.set_channel(10*i+2,0)
        #self.mydmx.set_data(self.par_led1.data,5,5)
        self.mydmx.send_data()
        self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(int(self.range_rouge.get()), int(self.range_vert.get()),int(self.range_bleu.get())))
        
    def newgroup(self):
        print("new group")
    
            