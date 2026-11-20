"""Sistema de gestión de visitantes y proveedores. Interfaz de escritorio + formulario web."""
from __future__ import annotations
import csv, hashlib, json, secrets, socket, sqlite3, threading, webbrowser
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

BASE=Path(__file__).resolve().parent
DB=BASE/'visitantes.db'
BLUE='#145A96'; DARK='#103B63'; PALE='#EAF3FB'; WHITE='#FFFFFF'; TEXT='#203448'; MUTED='#64788B'; RED='#B94343'

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password_hash TEXT NOT NULL,display_name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS form_tokens(token TEXT PRIMARY KEY,created_at TEXT NOT NULL,used INTEGER DEFAULT 0,submitted_at TEXT);
        CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY AUTOINCREMENT,token TEXT,tipo TEXT,nombre TEXT,empresa TEXT,correo TEXT,anfitrion TEXT,fecha_inicio TEXT,fecha_fin TEXT,alto_riesgo TEXT,estado TEXT,payload TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),organization TEXT DEFAULT '',privacy_url TEXT DEFAULT '');
        ''')
        if not c.execute('SELECT id FROM users LIMIT 1').fetchone():
            c.execute('INSERT INTO users(username,password_hash,display_name) VALUES(?,?,?)',('admin',hashlib.sha256('admin123'.encode()).hexdigest(),'Administrador'))
        c.execute("INSERT OR IGNORE INTO settings(id,organization,privacy_url) VALUES(1,'','')")

def hash_password(s): return hashlib.sha256(s.encode()).hexdigest()


def scrollable(parent, bg=WHITE):
    shell = tk.Frame(parent, bg=bg)
    shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        shell,
        bg=bg,
        highlightthickness=0
    )

    sy = ttk.Scrollbar(
        shell,
        orient="vertical",
        command=canvas.yview
    )

    inner = tk.Frame(canvas, bg=bg)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    wid = canvas.create_window(
        (0, 0),
        window=inner,
        anchor="nw"
    )

    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfigure(
            wid,
            width=e.width
        )
    )

    canvas.configure(yscrollcommand=sy.set)

    canvas.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")

    # Desplazamiento con la rueda del mouse
    def wheel(e):
        try:
            canvas.yview_scroll(
                int(-1 * (e.delta / 120)),
                "units"
            )
        except tk.TclError:
            pass

    canvas.bind("<MouseWheel>", wheel)

    return shell, canvas, inner


class App:
    def __init__(self,root):
        self.root=root; self.home=None; self.user=None; self.server_started=False
        root.title('Sistema de gestión de accesos'); root.configure(bg=WHITE)
        self.style(); self.login()
    def style(self):
        s=ttk.Style(self.root)
        try:s.theme_use('clam')
        except tk.TclError:pass
        s.configure('.',font=('Segoe UI',10),foreground=TEXT)
        s.configure('TFrame',background=WHITE);s.configure('TLabel',background=WHITE,foreground=TEXT)
        s.configure('Title.TLabel',font=('Segoe UI',20,'bold'),foreground=DARK)
        s.configure('Sub.TLabel',foreground=MUTED)
        s.configure('TButton',padding=(12,8));s.configure('Primary.TButton',background=BLUE,foreground=WHITE,font=('Segoe UI',10,'bold'))
        s.map('Primary.TButton',background=[('active',DARK)],foreground=[('active',WHITE)])
        s.configure('Treeview',rowheight=30);s.configure('Treeview.Heading',font=('Segoe UI',9,'bold'),background=PALE,foreground=DARK)
    def geometry(self,w,h):
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        return f'{min(w,sw-80)}x{min(h,sh-100)}'
    def login(self):
        self.root.deiconify(); self.root.geometry(self.geometry(500,480)); self.root.minsize(420,420)
        for x in self.root.winfo_children():x.destroy()
        bg=tk.Frame(self.root,bg=PALE);bg.pack(fill='both',expand=True)
        card=tk.Frame(bg,bg=WHITE,padx=34,pady=30,highlightthickness=1,highlightbackground='#D5E4F0')
        card.place(relx=.5,rely=.5,anchor='center',width=390,height=360)
        tk.Label(card,text='SISTEMA DE GESTIÓN',bg=WHITE,fg=BLUE,font=('Segoe UI',10,'bold')).pack(pady=(5,8))
        tk.Label(card,text='Bienvenido',bg=WHITE,fg=DARK,font=('Segoe UI',24,'bold')).pack()
        tk.Label(card,text='Inicie sesión para administrar los accesos',bg=WHITE,fg=MUTED).pack(pady=(4,20))
        tk.Label(card,text='Usuario',bg=WHITE).pack(anchor='w');u=ttk.Entry(card);u.pack(fill='x',pady=(4,12),ipady=5)
        tk.Label(card,text='Contraseña',bg=WHITE).pack(anchor='w');p=ttk.Entry(card,show='•');p.pack(fill='x',pady=(4,18),ipady=5)
        def enter(event=None):
            with connect() as c:r=c.execute('SELECT * FROM users WHERE username=? AND password_hash=?',(u.get().strip(),hash_password(p.get()))).fetchone()
            if not r:messagebox.showerror('Acceso denegado','Usuario o contraseña incorrectos.',parent=self.root);return
            self.user=r['display_name'];self.open_home()
        ttk.Button(card,text='Iniciar sesión',style='Primary.TButton',command=enter).pack(fill='x')
        tk.Label(card,text='Acceso inicial de demostración: admin / admin123',bg=WHITE,fg=MUTED,font=('Segoe UI',8)).pack(pady=14)
        p.bind('<Return>',enter);u.focus_set()
    def open_home(self):
        self.root.withdraw()
        if self.home and self.home.winfo_exists():self.home.destroy()
        w=tk.Toplevel(self.root);self.home=w;w.title('Panel principal');w.geometry(self.geometry(1100,760));w.minsize(760,560);w.configure(bg=PALE)
        head=tk.Frame(w,bg=DARK,padx=30,pady=22);head.pack(fill='x')
        tk.Label(head,text='Panel de control',bg=DARK,fg=WHITE,font=('Segoe UI',23,'bold')).pack(anchor='w')
        tk.Label(head,text=f'Bienvenido, {self.user}. Administre formularios, agenda y resultados.',bg=DARK,fg='#D9EAF7').pack(anchor='w',pady=(4,0))
        body=tk.Frame(w,bg=PALE,padx=28,pady=24);body.pack(fill='both',expand=True)
        tk.Label(body,text='¿Qué desea hacer?',bg=PALE,fg=DARK,font=('Segoe UI',17,'bold')).pack(anchor='w',pady=(0,12))
        actions=[('＋','Generar enlace de registro','Crear un enlace para que el visitante o proveedor capture sus propios datos.',self.create_link),('▦','Visualizar agenda','Consultar solicitudes recibidas, fechas y estados.',self.open_list),('▤','Tabla de registros','Consultar y exportar respuestas completas.',self.open_table),('▥','Resultados','Indicadores de registros y trabajos de alto riesgo.',self.open_data),('⚙','Configuración','Definir nombre visible y aviso de privacidad.',self.settings)]
        grid=tk.Frame(body,bg=PALE);grid.pack(fill='both',expand=True)
        for i,(ico,title,desc,cmd) in enumerate(actions):
            r,col=divmod(i,2);grid.grid_columnconfigure(col,weight=1);grid.grid_rowconfigure(r,weight=1)
            card=tk.Frame(grid,bg=WHITE,padx=18,pady=16,highlightthickness=1,highlightbackground='#D7E5F0');card.grid(row=r,column=col,sticky='nsew',padx=8,pady=8)
            tk.Label(card,text=ico,bg=WHITE,fg=BLUE,font=('Segoe UI',22,'bold')).pack(anchor='w')
            tk.Label(card,text=title,bg=WHITE,fg=DARK,font=('Segoe UI',13,'bold')).pack(anchor='w',pady=(4,3))
            tk.Label(card,text=desc,bg=WHITE,fg=MUTED,wraplength=420,justify='left').pack(anchor='w',pady=(0,12))
            ttk.Button(card,text='Abrir',style='Primary.TButton',command=cmd).pack(anchor='w')
        ttk.Button(body,text='Cerrar sesión',command=self.logout).pack(anchor='e',pady=(12,0))
        w.protocol('WM_DELETE_WINDOW',self.logout)
    def logout(self):
        if self.home and self.home.winfo_exists():self.home.destroy()
        self.user=None;self.login()
    def child(self,title,w=1000,h=720):
        win=tk.Toplevel(self.home or self.root);win.title(title);win.geometry(self.geometry(w,h));win.minsize(700,500);win.configure(bg=WHITE)
        return win
    def header(self,win,title,subtitle):
        bar=tk.Frame(win,bg=PALE,padx=24,pady=17);bar.pack(fill='x')
        tk.Label(bar,text=title,bg=PALE,fg=DARK,font=('Segoe UI',19,'bold')).pack(anchor='w')
        tk.Label(bar,text=subtitle,bg=PALE,fg=MUTED,wraplength=1000,justify='left').pack(anchor='w',pady=(3,0))
    def ensure_server(self):
        if self.server_started:return True
        try:
            from werkzeug.serving import make_server
            from web_form import app as flask_app
            self.httpd=make_server('0.0.0.0',5000,flask_app,threaded=True)
            threading.Thread(target=self.httpd.serve_forever,daemon=True).start();self.server_started=True;return True
        except OSError as e:
            messagebox.showerror('Servidor ocupado',f'No se pudo iniciar el formulario web en el puerto 5000.\n{e}');return False
        except Exception as e:
            messagebox.showerror('Error del formulario web',str(e));return False
    def local_ip(self):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
        except Exception:return '127.0.0.1'
    def create_link(self):
        if not self.ensure_server():return
        token=secrets.token_urlsafe(18)
        with connect() as c:c.execute('INSERT INTO form_tokens(token,created_at) VALUES(?,?)',(token,datetime.now().isoformat(timespec='seconds')))
        ip=self.local_ip();url=f'http://{ip}:5000/form/{token}'
        w=self.child('Enlace de registro',700,510);self.header(w,'Enlace generado','Comparta este enlace para que la persona visitante o proveedora complete su registro.')
        f=ttk.Frame(w,padding=24);f.pack(fill='both',expand=True)
        ttk.Label(f,text='Enlace para compartir',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ent=ttk.Entry(f,font=('Segoe UI',10));ent.pack(fill='x',pady=8);ent.insert(0,url);ent.selection_range(0,'end')
        row=ttk.Frame(f);row.pack(fill='x',pady=8)
        ttk.Button(row,text='Copiar enlace',style='Primary.TButton',command=lambda:(w.clipboard_clear(),w.clipboard_append(url),messagebox.showinfo('Copiado','Enlace copiado al portapapeles.',parent=w))).pack(side='left',padx=(0,8))
        ttk.Button(row,text='Abrir formulario',command=lambda:webbrowser.open(url)).pack(side='left')
        ttk.Label(f,text='Importante: este enlace funciona en esta computadora y, normalmente, en dispositivos conectados a la misma red local. Para recibir respuestas desde fuera de la red, el componente web debe publicarse en un servidor con HTTPS y un dominio accesible.',wraplength=620,style='Sub.TLabel').pack(anchor='w',pady=(20,8))
        ttk.Label(f,text='No cierre la aplicación mientras se estén recibiendo respuestas. La computadora debe permanecer encendida y conectada a la red.',wraplength=620,style='Sub.TLabel').pack(anchor='w')
    def settings(self):
        with connect() as c:r=c.execute('SELECT * FROM settings WHERE id=1').fetchone()
        w=self.child('Configuración',720,520);self.header(w,'Configuración','Personalice los datos visibles sin incorporar nombres de la organización de referencia.')
        f=ttk.Frame(w,padding=24);f.pack(fill='both',expand=True)
        ttk.Label(f,text='Nombre de la empresa (opcional)').pack(anchor='w');org=ttk.Entry(f);org.pack(fill='x',pady=(5,16));org.insert(0,r['organization'] or '')
        ttk.Label(f,text='URL del aviso de privacidad (opcional)').pack(anchor='w');url=ttk.Entry(f);url.pack(fill='x',pady=(5,16));url.insert(0,r['privacy_url'] or '')
        ttk.Label(f,text='El formulario no muestra marcas, logotipos ni nombres de la organización original.').pack(anchor='w',pady=8)
        def save():
            with connect() as c:c.execute('UPDATE settings SET organization=?,privacy_url=? WHERE id=1',(org.get().strip(),url.get().strip()))
            messagebox.showinfo('Guardado','Configuración actualizada.',parent=w);w.destroy()
        ttk.Button(f,text='Guardar cambios',style='Primary.TButton',command=save).pack(anchor='e',pady=18)
    def submissions(self,search=''):
        with connect() as c:rows=c.execute('SELECT * FROM submissions ORDER BY id DESC').fetchall()
        return [r for r in rows if not search or search.lower() in ' '.join(str(r[k] or '') for k in ('nombre','empresa','correo','anfitrion','tipo')).lower()]
    def open_list(self):
        w=self.child('Agenda de registros',1100,730);self.header(w,'Agenda de registros','Solicitudes enviadas por visitantes y proveedores. Puede actualizar el estado después de revisar cada solicitud.')
        f=ttk.Frame(w,padding=16);f.pack(fill='both',expand=True)
        top=ttk.Frame(f);top.pack(fill='x',pady=(0,10));q=tk.StringVar();st=tk.StringVar(value='Todos')
        ttk.Label(top,text='Buscar:').pack(side='left');ttk.Entry(top,textvariable=q,width=28).pack(side='left',padx=7)
        ttk.Combobox(top,textvariable=st,values=['Todos','Pendiente','Autorizado','Rechazado','Realizada','Cancelada'],state='readonly',width=15).pack(side='left')
        cols=('id','tipo','nombre','empresa','fecha_inicio','fecha_fin','alto_riesgo','estado')
        tv=ttk.Treeview(f,columns=cols,show='headings');heads=['ID','Tipo','Nombre','Empresa','Desde','Hasta','Alto riesgo','Estado'];widths=[50,100,170,160,100,100,100,110]
        for c,h,wd in zip(cols,heads,widths):tv.heading(c,text=h);tv.column(c,width=wd,anchor='center')
        y=ttk.Scrollbar(f,orient='vertical',command=tv.yview);x=ttk.Scrollbar(f,orient='horizontal',command=tv.xview);tv.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        tv.pack(side='top',fill='both',expand=True);y.place(relx=1,rely=.06,relheight=.83,anchor='ne');x.pack(fill='x')
        def refresh():
            tv.delete(*tv.get_children())
            for r in self.submissions(q.get()):
                if st.get()!='Todos' and r['estado']!=st.get():continue
                tv.insert('','end',values=tuple(r[k] for k in cols))
        def chosen():
            s=tv.selection()
            if not s:messagebox.showwarning('Seleccione','Seleccione un registro.',parent=w);return None
            return tv.item(s[0],'values')[0]
        def detail():
            rid=chosen()
            if not rid:return
            with connect() as c:r=c.execute('SELECT * FROM submissions WHERE id=?',(rid,)).fetchone()
            payload=json.loads(r['payload'] or '{}');d=self.child('Detalle de solicitud',850,760);self.header(d,f"Solicitud #{rid}",f"{r['tipo']} · {r['nombre']} · {r['fecha_inicio']} a {r['fecha_fin']}")
            inner=scrollable(d);inner.configure(padx=24,pady=16)
            for k,v in payload.items():
                if isinstance(v,list):v=', '.join(v)
                ttk.Label(inner,text=k.replace('_',' ').title(),font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(8,0))
                ttk.Label(inner,text=str(v),wraplength=760,justify='left').pack(anchor='w')
            ttk.Label(inner,text='Estado de revisión').pack(anchor='w',pady=(18,4));sv=tk.StringVar(value=r['estado']);cb=ttk.Combobox(inner,textvariable=sv,values=['Pendiente','Autorizado','Rechazado','Realizada','Cancelada'],state='readonly');cb.pack(anchor='w')
            def save():
                with connect() as c:c.execute('UPDATE submissions SET estado=? WHERE id=?',(sv.get(),rid))
                d.destroy();refresh()
            ttk.Button(inner,text='Guardar estado',style='Primary.TButton',command=save).pack(anchor='e',pady=18)
        buttons=ttk.Frame(f);buttons.pack(fill='x',pady=10);ttk.Button(buttons,text='Actualizar',command=refresh).pack(side='left');ttk.Button(buttons,text='Ver solicitud seleccionada',style='Primary.TButton',command=detail).pack(side='left',padx=8)
        q.trace_add('write',lambda *_:refresh());st.trace_add('write',lambda *_:refresh());refresh()
    def open_table(self):
        w=self.child('Tabla general',1150,740);self.header(w,'Tabla general de registros','Vista tabular y exportación CSV compatible con Excel.')
        f=ttk.Frame(w,padding=16);f.pack(fill='both',expand=True);q=tk.StringVar();top=ttk.Frame(f);top.pack(fill='x',pady=(0,10));ttk.Label(top,text='Buscar:').pack(side='left');ttk.Entry(top,textvariable=q,width=32).pack(side='left',padx=8)
        cols=('id','tipo','nombre','empresa','correo','anfitrion','fecha_inicio','fecha_fin','alto_riesgo','estado')
        tv=ttk.Treeview(f,columns=cols,show='headings');
        for c in cols:tv.heading(c,text=c.replace('_',' ').title());tv.column(c,width=125,anchor='center')
        sy=ttk.Scrollbar(f,orient='vertical',command=tv.yview);sx=ttk.Scrollbar(f,orient='horizontal',command=tv.xview);tv.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);tv.pack(fill='both',expand=True);sy.pack(side='right',fill='y');sx.pack(fill='x')
        current=[]
        def refresh():
            nonlocal current
            tv.delete(*tv.get_children());current=self.submissions(q.get())
            for r in current:tv.insert('','end',values=tuple(r[k] for k in cols))
        def export():
            path=filedialog.asksaveasfilename(parent=w,defaultextension='.csv',filetypes=[('CSV','*.csv')])
            if not path:return
            with open(path,'w',newline='',encoding='utf-8-sig') as fp:
                wr=csv.writer(fp);wr.writerow(cols)
                for r in current:wr.writerow([r[k] for k in cols])
            messagebox.showinfo('Exportación','Archivo CSV guardado. Puede abrirlo con Excel.',parent=w)
        ttk.Button(top,text='Exportar CSV para Excel',command=export).pack(side='right');q.trace_add('write',lambda *_:refresh());refresh()
    def open_data(self):
        w=self.child('Resultados',1050,760);self.header(w,'Resultados e indicadores','Indicadores calculados con las solicitudes recibidas. No representan una certificación de seguridad.')
        area=scrollable(w);area.configure(padx=20,pady=18)
        with connect() as c:rows=c.execute('SELECT * FROM submissions').fetchall()
        total=len(rows);vis=sum(r['tipo']=='Visitante' for r in rows);prov=sum(r['tipo']=='Proveedor' for r in rows);risk=sum(r['alto_riesgo']=='Sí' for r in rows);pending=sum(r['estado']=='Pendiente' for r in rows)
        cards=tk.Frame(area,bg=WHITE);cards.pack(fill='x')
        for title,val in [('Registros',total),('Visitantes',vis),('Proveedores',prov),('Alto riesgo',risk),('Pendientes',pending)]:
            box=tk.Frame(cards,bg=PALE,padx=14,pady=12);box.pack(side='left',fill='x',expand=True,padx=4);tk.Label(box,text=title,bg=PALE,fg=MUTED).pack(anchor='w');tk.Label(box,text=str(val),bg=PALE,fg=BLUE,font=('Segoe UI',20,'bold')).pack(anchor='w')
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            fig=Figure(figsize=(9,4.2),dpi=95);ax=fig.add_subplot(121);bx=fig.add_subplot(122)
            months={}
            for r in rows:
                m=(r['fecha_inicio'] or '')[:7]
                if m:months[m]=months.get(m,0)+1
            labs=sorted(months)[-8:];ax.bar(labs,[months[x] for x in labs]);ax.set_title('Solicitudes por mes');ax.tick_params(axis='x',rotation=35)
            bx.bar(['Visitantes','Proveedores','Alto riesgo','Pendientes'],[vis,prov,risk,pending]);bx.set_title('Distribución de registros');bx.tick_params(axis='x',rotation=15)
            fig.tight_layout();canvas=FigureCanvasTkAgg(fig,master=area);canvas.draw();canvas.get_tk_widget().pack(fill='both',expand=True,pady=20)
        except ImportError:ttk.Label(area,text='Para visualizar las gráficas instale matplotlib.').pack(pady=30)
        ttk.Label(area,text='Las solicitudes de alto riesgo requieren revisión documental y autorización antes de permitir el trabajo.',wraplength=900,style='Sub.TLabel').pack(anchor='w',pady=10)

def main():
    init_db();root=tk.Tk();App(root);root.mainloop()
if __name__=='__main__':main()
