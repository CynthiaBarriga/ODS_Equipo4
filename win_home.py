import tkinter as tk
from tkinter import ttk, messagebox

def open_win_home(parent: tk.Tk):
    win = tk.Toplevel(parent)
    win.title("Home")
    win.geometry("360x220")
    frm = ttk.Frame(win, padding=16)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Saludos usuario, nos alegra tenerle de vuelta", font=("Segoe UI", 11, "bold")).pack(pady=(0, 8))
    ttk.Label(frm, text="Como empresa, nos importa su seguridad y la de sus visitantes.Seleccione la información a la que desea acceder ").pack(pady=(0, 12))
    ttk.Button(frm, text="Nuevo visitante",
               command=lambda: messagebox.showinfo("Info", "¡Equipo listo!")).pack()
    ttk.Button(frm, text="Visitas programadas",
                   command=lambda: messagebox.showinfo("Info", "¡Equipo listo!")).pack()
    ttk.Button(frm, text="Historial de visitantes",
                   command=lambda: messagebox.showinfo("Info", "¡Equipo listo!")).pack()
    ttk.Button(frm, text="Actualización de información de visitantes",
                   command=lambda: messagebox.showinfo("Info", "¡Equipo listo!")).pack()
    ttk.Button(frm, text="Cerrar", command=win.destroy).pack(pady=8)
