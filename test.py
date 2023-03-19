import tkinter as tk
from tkinter import filedialog
import os
from tkinter import ttk
my_w = tk.Tk()
my_w.geometry("400x300")  # Size of the window 
my_w.title("www.plus2net.com")  #  title
my_dir='' # string to hold directory path 
def my_fun(): 
    path = filedialog.askdirectory() # select directory 
    l1.config(text=path) # update the text of Label with directory path
    root=next(os.walk(path))[0] # path 
    dirnames=next(os.walk(path))[1] # list of directories 
    files=next(os.walk(path))[2] # list of files 
    print(root) # D:\my_dir\my_dir0
    print(dirnames) # ['my_dir1']
    print(files) # ['my_file0.txt']
    for item in trv.get_children():
        trv.delete(item)
    i=1
    f2i=1 #sub directory id 
    for d in dirnames:
        trv.insert("", 'end',iid=i,values =d)
        path2=path+'/'+d # Path for sub directory 
        #print(path2)
        files2=next(os.walk(path2))[2] # file list of Sub directory 
        for f2 in files2:  # list of files 
            #print(f2)
            trv.insert(i, 'end',iid='sub'+str(f2i),values ="-" + f2)
            f2i=f2i+1
        i=i+1

    for f in files:  # list of files 
        trv.insert("", 'end',iid=i,values =f)
        i=i+1

b1=tk.Button(my_w,text='Select directory',font=22,
    command=lambda:my_fun(),bg='lightgreen')
b1.grid(row=0,column=0,padx=5,pady=10)

l1=tk.Label(my_w,text=my_dir,bg='yellow',font=16)
l1.grid(row=0,column=1,padx=0)

trv=ttk.Treeview(my_w,selectmode='browse',height=9)
trv.grid(row=1,column=0,columnspan=2,padx=10,pady=5)
trv["columns"]=("1")
trv['show']='tree headings'
trv.column("#0", width = 20, anchor ='c')
trv.column("1",width=300,anchor='w')
trv.heading("#0", text ="#")
trv.heading("1",text="Name",anchor='w')

my_w.mainloop()  # Keep the window open