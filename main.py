from tkinter import ttk 
import tkinter as tk 

titles={'Id': [1,2,3,4,5, 6, 7, 8, 9], 'Names':['Tom', 'Rob', 'Tim', 'Jim', 'Kim', 'Kim', 'Kim', 'Kim', 'Kim'], 'Column': [1,2,3,4,5, 6, 7, 8, 9]}

  
window = tk.Tk() 

treev = ttk.Treeview(window, selectmode ='browse') 
treev.pack(side='left',expand=True, fill='both') 
  

verscrlbar = ttk.Scrollbar(window,  
                           orient ="vertical",  
                           command = treev.yview) 
  
verscrlbar.pack(side ='right', fill ='y')   
treev.configure(yscrollcommand = verscrlbar.set) 

treev["columns"] = list(x for x in range(len(list(titles.keys()))))
treev['show'] = 'headings'

  
for x, y in enumerate(titles.keys()):
    treev.column(x, minwidth=20, stretch=True,  anchor='c')
    treev.heading(x, text=y)

for args in zip(*list(titles.values())):
    treev.insert("", 'end', values =args) 

window.mainloop() 