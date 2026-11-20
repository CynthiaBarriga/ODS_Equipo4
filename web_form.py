from __future__ import annotations
import json, sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, request, render_template_string, abort

BASE = Path(__file__).resolve().parent
DB = BASE / 'visitantes.db'
app = Flask(__name__)

ACTIVITIES = [
    'Trabajos en altura', 'Trabajos en caliente', 'Soldadura y corte',
    'Trabajos con presencia de gases y vapores de sustancias químicas',
    'Trabajos en espacios confinados', 'Trabajos de mantenimiento eléctrico',
    'Instalación y mantenimiento de maquinaria', 'Trabajos con uso de sustancias inflamables',
    'Trabajos de construcción', 'Trabajos con temperaturas altas o abatidas'
]
PPE = ['Lentes de seguridad', 'Gorra o casco', 'Tapones auditivos', 'Pantalón de mezclilla', 'Calzado de seguridad']

PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Registro de acceso</title>
<style>
:root{--blue:#145a96;--dark:#103b63;--pale:#eaf3fb;--text:#203448;--muted:#64788b;--border:#d7e3ed}
*{box-sizing:border-box}body{margin:0;background:#f3f7fb;color:var(--text);font:16px/1.5 Segoe UI,Arial,sans-serif}.wrap{max-width:900px;margin:28px auto;padding:0 16px}.card{background:white;border:1px solid var(--border);border-radius:14px;padding:clamp(18px,4vw,36px);box-shadow:0 8px 28px #173c5c12}.top{border-bottom:1px solid var(--border);padding-bottom:18px;margin-bottom:24px}.eyebrow{color:var(--blue);font-weight:700;font-size:13px;letter-spacing:.08em}.top h1{font-size:clamp(24px,4vw,34px);line-height:1.2;color:var(--dark);margin:6px 0}.muted{color:var(--muted)}h2{font-size:20px;color:var(--dark);margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.field{min-width:0}.full{grid-column:1/-1}label,.legend{display:block;font-weight:600;margin:0 0 6px}input,select,textarea{width:100%;border:1px solid #bdccd9;border-radius:8px;padding:11px 12px;font:inherit;background:white;color:var(--text)}textarea{min-height:88px;resize:vertical}.choices{display:grid;gap:9px;margin:8px 0 14px}.choice{display:flex;align-items:flex-start;gap:10px;font-weight:400;background:#f8fbfe;border:1px solid var(--border);padding:10px 12px;border-radius:8px}.choice input{width:auto;margin-top:5px}.hint{font-size:13px;color:var(--muted);margin-top:4px}.section{padding-top:4px}.notice{background:var(--pale);border-left:4px solid var(--blue);padding:14px 16px;border-radius:8px;margin:16px 0}.btn{border:0;border-radius:9px;background:var(--blue);color:white;padding:13px 22px;font-size:16px;font-weight:700;cursor:pointer}.btn:hover{background:var(--dark)}.actions{margin-top:26px;display:flex;justify-content:flex-end}.required{color:#b42318}#riskBlock[hidden]{display:none}.success{text-align:center;padding:48px 20px}.success h1{color:var(--dark)}@media(max-width:650px){.grid{grid-template-columns:1fr}.full{grid-column:auto}.wrap{margin:10px auto;padding:0 9px}.card{padding:18px}}
</style></head><body><div class="wrap"><main class="card">
{% if done %}<div class="success"><div class="eyebrow">REGISTRO RECIBIDO</div><h1>Gracias por completar el formulario</h1><p>La información fue enviada correctamente. El personal responsable revisará la solicitud.</p></div>
{% else %}<header class="top"><div class="eyebrow">FORMULARIO DE ACCESO</div><h1>Registro de visitantes y proveedores</h1><p class="muted">Complete personalmente la información solicitada. Los campos marcados con <span class="required">*</span> son obligatorios.</p>{% if organization %}<p><b>{{ organization }}</b></p>{% endif %}<p>La información se utilizará para gestionar el acceso y las medidas de seguridad durante su estancia. Consulte el aviso de privacidad que le proporcione la empresa.{% if privacy_url %} <a href="{{ privacy_url }}" target="_blank" rel="noopener">Consultar aviso de privacidad</a>{% endif %}</p></header>
<form method="post" id="registration">
<h2>1. Datos personales y de ingreso</h2><div class="grid">
<div class="field"><label>Nombre completo <span class="required">*</span></label><input name="nombre" required maxlength="180"></div>
<div class="field"><label>Correo electrónico <span class="required">*</span></label><input type="email" name="correo" required maxlength="180"></div>
<div class="field full"><label>Nombre o razón social de la empresa o institución que visita. Si es persona física, escriba nuevamente su nombre completo. <span class="required">*</span></label><input name="empresa" required maxlength="180"></div>
<div class="field"><label>Nombre de la persona con quien se dirige <span class="required">*</span></label><input name="anfitrion" required maxlength="180"></div>
<div class="field"><label>Contacto de emergencia: nombre, parentesco y teléfono <span class="required">*</span></label><input name="emergencia" required maxlength="240" placeholder="Nombre, parentesco y número celular"></div>
<div class="field"><label>Fecha de visita <span class="required">*</span></label><input type="date" name="fecha_inicio" required></div>
<div class="field"><label>Fecha de última salida <span class="required">*</span></label><input type="date" name="fecha_fin" required></div>
<div class="field full"><label>Confirmación de aviso de privacidad <span class="required">*</span></label><label class="choice"><input type="checkbox" name="privacidad" value="Sí" required> He sido informado sobre el tratamiento de mis datos personales y manifiesto mi conformidad con el aviso de privacidad proporcionado.</label></div>
</div>
<h2>2. Tipo de ingreso</h2><div class="choices"><label class="choice"><input type="radio" name="tipo" value="Visitante" required> Visitante</label><label class="choice"><input type="radio" name="tipo" value="Proveedor" required> Proveedor / contratista</label></div>
<div id="visitorBlock" hidden><h2>3. Información para visitantes</h2><div class="field"><label>Explique brevemente el motivo de su visita <span class="required">*</span></label><textarea name="motivo_visitante" data-required="true"></textarea></div>
<div class="notice"><b>Reglas básicas para visitantes</b><ul><li>No fumar ni iniciar fuentes de ignición dentro de las instalaciones.</li><li>Para ingresar a áreas productivas, portar el equipo de protección personal indicado.</li><li>No ingresar a espacios o áreas restringidas sin acompañamiento autorizado.</li><li>Seguir las indicaciones en caso de emergencia.</li><li>Completar y entregar la documentación requerida.</li><li>No tomar fotografías dentro del inmueble sin autorización.</li></ul></div>
<label class="choice"><input type="checkbox" name="reglas_visitante" value="Acepto" data-required="true"> He leído las reglas para visitantes y me comprometo a respetarlas. <span class="required">*</span></label>
</div>
<div id="providerBlock" hidden><h2>3. Información para proveedores y contratistas</h2><div class="field"><label>Selecciona el motivo de tu estancia <span class="required">*</span></label><div class="choices">
{% for v in ['Mantenimiento, instalación de equipos o trabajos específicos','Cotización','Entrega de bienes durante más de dos horas','Recolección de bienes durante más de dos horas','Otras'] %}<label class="choice"><input type="radio" name="motivo_proveedor" value="{{v}}" data-required="true"> {{v}}</label>{% endfor %}</div></div>
<div class="notice"><b>Reglas básicas para proveedores y contratistas</b><ul><li>Respetar la señalética de seguridad y el Sistema Globalmente Armonizado.</li><li>Prohibido fumar o iniciar fuentes de ignición dentro de las instalaciones.</li><li>Reportar inmediatamente accidentes o condiciones inseguras.</li><li>Separar y disponer correctamente los residuos.</li><li>Delimitar y señalizar el área de trabajo.</li><li>Utilizar el equipo de protección personal requerido para la actividad.</li><li>Prohibido ingresar alcohol, drogas, armas de fuego o cámaras sin autorización.</li><li>Realizar orden y limpieza al terminar las actividades.</li><li>No utilizar herramientas o equipos ajenos sin autorización.</li></ul></div>
<label class="choice"><input type="checkbox" name="reglas_proveedor" value="Acepto" data-required="true"> He leído las reglas para proveedores y contratistas y me comprometo a cumplirlas. <span class="required">*</span></label>
</div>
<div id="safetyBlock" hidden><h2>4. Información de seguridad para el ingreso</h2>
<div class="field"><label>Equipo de protección personal que utilizará al ingresar a áreas productivas <span class="required">*</span></label><div class="choices">{% for v in ['Lentes de seguridad','Gorra o casco','Tapones auditivos','Pantalón de mezclilla','Calzado de seguridad'] %}<label class="choice"><input type="checkbox" name="epp" value="{{v}}"> {{v}}</label>{% endfor %}</div><p class="hint">El equipo debe corresponder a los riesgos del área y a la actividad que realizará.</p></div>
<label class="choice"><input type="checkbox" name="matriz_riesgos" value="Acepto" required> He leído la matriz de riesgos, reconozco la señalización y me comprometo a respetar sus indicaciones. <span class="required">*</span></label>
<label class="choice"><input type="checkbox" name="brigadistas" value="Acepto" required> He identificado al personal brigadista y conozco cómo reconocerlo por el color de su casco: rojo (incendios), verde (comunicación y evacuación), azul (búsqueda y rescate) y blanco (primeros auxilios). <span class="required">*</span></label>
<label class="choice"><input type="checkbox" name="tuberias" value="Acepto" required> Reconozco la señalización de fluidos en tuberías: verde (aire comprimido), gris (conducciones eléctricas, según señalización local), azul (agua de uso general) y rojo (sistemas contra incendio, cuando exista). <span class="required">*</span></label>
<label class="choice"><input type="checkbox" name="sga" value="Acepto" required> He revisado y comprendido los pictogramas de seguridad, frases de peligro y consejos de prudencia del Sistema Globalmente Armonizado. <span class="required">*</span></label>
<label class="choice"><input type="checkbox" name="evacuacion" value="Acepto" required> Identifico las rutas principales de evacuación y me comprometo a seguirlas en caso de emergencia. <span class="required">*</span></label>
</div>
<div id="riskQuestion" hidden><h2>5. Trabajos de alto riesgo</h2><label>¿Realizará algún trabajo de alto riesgo en las instalaciones? <span class="required">*</span></label><div class="choices"><label class="choice"><input type="radio" name="alto_riesgo" value="Sí" data-required="true"> Sí</label><label class="choice"><input type="radio" name="alto_riesgo" value="No" data-required="true"> No</label></div></div>
<div id="riskBlock" hidden><h2>6. Información adicional para trabajos de alto riesgo</h2>
<div class="field"><label>Selecciona la o las actividades a realizar <span class="required">*</span></label><div class="choices">{% for v in activities %}<label class="choice"><input type="checkbox" name="actividades" value="{{v}}"> {{v}}</label>{% endfor %}</div></div>
<div class="grid"><div class="field full"><label>Descripción breve de la actividad <span class="required">*</span></label><textarea name="descripcion_riesgo" required></textarea></div>
<div class="field"><label>Número de Seguridad Social <span class="required">*</span></label><input name="nss" required maxlength="30"></div>
<div class="field"><label>Centro hospitalario donde recibe atención (clínica, UMF, HGZ u hospital privado) <span class="required">*</span></label><input name="hospital" required maxlength="180"></div>
<div class="field full"><label>¿Padece alguna enfermedad o condición médica? ¿Cuál? <span class="required">*</span></label><textarea name="condicion_medica" required></textarea></div>
<div class="field full"><label>¿Se encuentra en tratamiento con algún medicamento? ¿Cuál? <span class="required">*</span></label><textarea name="medicamentos" required></textarea></div>
<div class="field full"><label>¿Tiene alergias? ¿A qué? <span class="required">*</span></label><textarea name="alergias" required></textarea></div></div>
<div class="notice"><b>Documentación requerida</b><p>La documentación aplicable debe entregarse en tiempo y forma, al menos tres días antes de realizar el trabajo. Los requisitos pueden variar según la actividad: constancias de habilidades para el trabajo, vigencia de derechos del seguro social o seguro privado, certificado médico vigente, cotización u orden de trabajo e identificación oficial vigente.</p></div>
<label class="choice"><input type="checkbox" name="documentacion" value="Acepto" required> Me comprometo a entregar la documentación requerida en tiempo y forma y entiendo que, si no se entrega, no podré realizar el trabajo. <span class="required">*</span></label>
<div class="notice"><b>Medidas mínimas de prevención y control</b><ol><li>Bloqueo de energía y etiquetado LOTO.</li><li>Señalización y delimitación del área de trabajo.</li><li>Verificación del sistema de puesta a tierra.</li><li>Informar al personal alrededor del área.</li><li>Descontaminación del área.</li><li>Disposición de los residuos.</li><li>Orden y limpieza al iniciar y terminar labores.</li><li>Ventilación artificial del área.</li><li>Supervisión de la actividad.</li><li>Revisión médica del trabajador.</li></ol></div>
<label class="choice"><input type="checkbox" name="medidas" value="Acepto" required> Me comprometo a cumplir las medidas mínimas y las que se establezcan el día del trabajo. <span class="required">*</span></label>
<div class="notice"><b>Bloqueo de energía y etiquetado LOTO</b><ol><li>Desconecta y aísla las fuentes de energía.</li><li>Bloquea mediante candados y dispositivos adecuados.</li><li>Señaliza y etiqueta el trabajo, indicando responsable y motivo.</li><li>Libera energías residuales y verifica que el equipo no pueda operar.</li></ol></div>
<label class="choice"><input type="checkbox" name="loto" value="Acepto" required> Me comprometo a realizar correctamente el procedimiento de bloqueo de energías y señalizar el trabajo. <span class="required">*</span></label>
</div>
<div class="actions"><button class="btn" type="submit">Enviar registro</button></div>
</form>
<script>
const typeInputs=[...document.querySelectorAll('input[name="tipo"]')];
const visitor=document.getElementById('visitorBlock'), provider=document.getElementById('providerBlock'), safety=document.getElementById('safetyBlock'), riskQ=document.getElementById('riskQuestion'), risk=document.getElementById('riskBlock');
function requiredIn(box,on){box.querySelectorAll('input,textarea,select').forEach(e=>{if(e.hasAttribute('required')||e.dataset.required==='true')e.required=on;});}
function show(box,on){box.hidden=!on;requiredIn(box,on);}
function update(){const t=document.querySelector('input[name="tipo"]:checked')?.value;show(visitor,t==='Visitante');show(provider,t==='Proveedor');show(safety,!!t);show(riskQ,t==='Proveedor');if(t!=='Proveedor'){show(risk,false);return;}const v=document.querySelector('input[name="alto_riesgo"]:checked')?.value;show(risk,v==='Sí');}
typeInputs.forEach(x=>x.addEventListener('change',()=>{document.querySelectorAll('input[name="alto_riesgo"]').forEach(r=>r.checked=false);update()}));document.querySelectorAll('input[name="alto_riesgo"]').forEach(x=>x.addEventListener('change',update));
document.getElementById('registration').addEventListener('submit',e=>{if(!document.querySelector('input[name="tipo"]:checked')){e.preventDefault();alert('Seleccione si ingresa como visitante o proveedor.');return;}if(document.querySelector('input[name="tipo"]:checked').value==='Proveedor'&&!document.querySelector('input[name="motivo_proveedor"]:checked')){e.preventDefault();alert('Seleccione el motivo de su estancia.');return;}if(document.querySelector('input[name="alto_riesgo"]:checked')?.value==='Sí'){if(!document.querySelector('input[name="actividades"]:checked')){e.preventDefault();alert('Seleccione al menos una actividad de alto riesgo.');return;}for(const n of ['documentacion','medidas','loto'])if(!document.querySelector(`input[name="${n}"]`).checked){e.preventDefault();alert('Confirme todos los compromisos de trabajos de alto riesgo.');return;}}});
update();
</script>{% endif %}</main></div></body></html>'''


def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con

@app.get('/form/<token>')
def form(token):
    with db() as con: row=con.execute('SELECT * FROM form_tokens WHERE token=?',(token,)).fetchone()
    if not row: abort(404)
    with db() as con: cfg=con.execute('SELECT * FROM settings WHERE id=1').fetchone() if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'").fetchone() else None
    return render_template_string(PAGE,done=False,activities=ACTIVITIES,organization=(cfg['organization'] if cfg else ''),privacy_url=(cfg['privacy_url'] if cfg else ''))

@app.post('/form/<token>')
def submit(token):
    with db() as con:
        token_row=con.execute('SELECT * FROM form_tokens WHERE token=?',(token,)).fetchone()
        if not token_row: abort(404)
        if token_row['used']: return render_template_string(PAGE,done=True,activities=ACTIVITIES,organization='',privacy_url='')
        data={k:v for k,v in request.form.items() if k not in ('epp','actividades')}
        data['epp']=request.form.getlist('epp'); data['actividades']=request.form.getlist('actividades'); data.setdefault('alto_riesgo','No')
        data['recibido_en']=datetime.now().isoformat(timespec='seconds')
        nombre=data.get('nombre','').strip(); tipo=data.get('tipo','')
        if not nombre or tipo not in ('Visitante','Proveedor') or not data.get('correo'):
            abort(400)
        con.execute('''INSERT INTO submissions(token,tipo,nombre,empresa,correo,anfitrion,fecha_inicio,fecha_fin,alto_riesgo,estado,payload,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(token,tipo,nombre,data.get('empresa',''),data.get('correo',''),data.get('anfitrion',''),data.get('fecha_inicio',''),data.get('fecha_fin',''),data.get('alto_riesgo','No'), 'Pendiente',json.dumps(data,ensure_ascii=False),data['recibido_en']))
        con.execute('UPDATE form_tokens SET used=1,submitted_at=? WHERE token=?',(data['recibido_en'],token))
    return render_template_string(PAGE,done=True,activities=ACTIVITIES,organization='',privacy_url='')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=False)
