import tkinter as tk
import tkinter.ttk as ttk
import threading
root = tk.Tk()
tview = ttk.Treeview(root)
tview["columns"] = ("SLOT_1", "SLOT_2")
tview.column("SLOT_1", width=100)
tview.column("SLOT_2", width=100)

tview.heading("#0", text="Column 0", anchor="w")
tview.heading("SLOT_1", text="Column 1")
tview.heading("SLOT_2", text="Column 2")

def test_program_thread():
    thread = threading.Thread(None, edit_item, None, (), {})
    thread.start()

def add_item():
    tview.insert("", "end", values=("", "bar"))


def edit_item():
    focused = tview.focus()
    x = input('Enter a Value you want to change')
    tview.item(focused, values=("", str(x)))

tview.pack()

add_item = tk.Button(root, text="Add item", command=add_item)
add_item.pack(expand=True, fill='both')

edit_item_button = tk.Button(root, text="Edit item", command=test_program_thread)
edit_item_button.pack(expand=True, fill='both')

root.mainloop()