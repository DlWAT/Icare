import tkinter as tk
import tkinter.ttk as ttk
import threading as thr
import time
import pydmxIcare
import pydmxlight

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.creer_widgets()
        
        self.mydmx= pydmxIcare.DMX_Icare()
        self.par_led1=pydmxlight.Par_Led_615_AFX(5,0)
        self.mydmx.connection()
    def creer_widgets(self):
        self.enable=0
        
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

        self.canvas = tk.Canvas(self, width = 500, height = 500)
        self.rectangle=self.canvas.create_rectangle(50, 110,300,280, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()) +"""""")
        self.canvas.grid(column=0, row=2)

        self.bouton_stop= tk.Button(self, text="Stop", command = self.stop)
        self.bouton_stop.grid(column=2, row=3)
        
        self.bouton_start= tk.Button(self, text="Start", command = self.start)
        self.bouton_start.grid(column=1, row=3)
        
        self.bouton_blackout= tk.Button(self, text="Blackout", command = self.blackout)
        self.bouton_blackout.grid(column=3, row=3)
        
        
        self.threading()
    
    def my_insert(self): # adding data to Combobox
        #if e1.get() not in cb1['values']:
        list_values=list(self.cb1['values'])
        list_values.append(self.e1.get())
        self.cb1['values']=tuple(list_values) # add option
        
    def change_color(self):
        i=0
        while True :
            if self.enable:
                self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()))
                i+=1
                try :
                    self.par_led1.set_channel(0,self.range_rouge.get())
                    self.par_led1.set_channel(1,self.range_vert.get())
                    self.par_led1.set_channel(2,self.range_bleu.get())
                except:
                    print("impossible to send data")
                time.sleep(0.1)
     
    def threading(self):
        t1=thr.Thread(target=self.change_color)
        t1.start()

    def stop(self):
        self.enable=0
        
    def start(self):
        self.enable=1

    def blackout(self):
        self.range_rouge.set(0)
        self.range_vert.set(0)
        self.range_bleu.set(0)
        
    def newgroup(self):
        print("new group")

if __name__ == "__main__":
    app = Application()
    app.title("Icare")
    app.geometry("750x750")
    app.mainloop()

