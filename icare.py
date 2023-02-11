import tkinter as tk
import threading as thr
import time

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.creer_widgets()

    def creer_widgets(self):
        self.enable=1
        
        self.range_rouge = tk.Scale(self, from_=0, to=255, orient=tk.HORIZONTAL)
        self.range_rouge.pack()
        
        self.range_vert = tk.Scale(self, from_=0, to=255, orient=tk.HORIZONTAL)
        self.range_vert.pack()

        self.range_bleu = tk.Scale(self, from_=0, to=255, orient=tk.HORIZONTAL)
        self.range_bleu.pack()

        self.canvas = tk.Canvas(self, width = 500, height = 500)
        self.rectangle=self.canvas.create_rectangle(50, 110,300,280, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()) +"""""")
        self.canvas.pack()

        self.bouton_stop= tk.Button(self, text="Stop", command = self.stop)
        self.bouton_stop.pack()
        
        self.threading()
    

    def change_color(self):
        i=0
        while self.enable!=0:
            self.canvas.itemconfig(self.rectangle, fill=""""""+rgb_to_hex(self.range_rouge.get(), self.range_vert.get(),self.range_bleu.get()))
            i+=1
            time.sleep(0.1)
     
    def threading(self):
        t1=thr.Thread(target=self.change_color)
        t1.start()

    def stop(self):
        self.enable=0
        print("test")


if __name__ == "__main__":
    app = Application()
    app.title("Icare")
    app.geometry("750x750")
    app.mainloop()

