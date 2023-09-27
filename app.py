import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, session
import jinja2
import pdfkit
from io import BytesIO
import zipfile
import tempfile
import os
import shutil
import gspread


app = Flask(__name__)
app.secret_key = 'k19234213as'

spreadsheet_id = '11mnygQWtGF2ZRF4000tpST0rKrftqpjBOojSaNjunss'
worksheet_name = 'TASK SCHEDULED'

gc = gspread.service_account(filename='client_secret.json')        

spreadsheet = gc.open_by_key(spreadsheet_id)

worksheet = spreadsheet.worksheet(worksheet_name)

data_from_sheets = worksheet.get_all_values()

df = pd.DataFrame(data_from_sheets[1:], columns=data_from_sheets[0])
df.columns = df.columns.str.strip()


def generate_json(option_selected, df, listas_agrupadas, lista_options):
    indices_seleccionados = listas_agrupadas[lista_options[option_selected]]
    result_dict = {}  # Diccionario para almacenar los resultados
    
    for index in indices_seleccionados:
        row = df.loc[index]  # Obtener la fila seleccionada
        row_dict = {}
        
        # Recorrer las columnas y agregarlas al diccionario
        for column_name, value in row.items():
            row_dict[column_name] = value
        
        # Usar el valor de la columna 'DESCRIPTION' como clave para el diccionario principal
        result_dict[row['DESCRIPTION']] = row_dict
    
    return result_dict    

def generate_pdf(wo, c_name, c_adress, task_info): 
    # ToDo: aquí irán las variables que le pase cuando llame a la función
    context = {
        'wo': wo,
        'c_name': c_name,
        'c_adress': c_adress,
        'task_info': task_info
    }

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)
    html_template = 'templates/template.html'
    template = template_env.get_template(html_template)
    out_text = template.render(context)

    wkhtmltopdf_path = 'wkhtmltopdf/bin/wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    pdf_data_pdfkit = pdfkit.from_string(out_text, False, configuration=config, options={'enable-local-file-access': None})
    return pdf_data_pdfkit

def download_pdf(opcion_seleccionada, df, listas_agrupadas, lista_options):
    resultado = generate_json(opcion_seleccionada, df, listas_agrupadas, lista_options)

    primer_objeto = list(resultado.values())[0]
    wo = primer_objeto['WO']
    c_name = primer_objeto['CUSTOMER NAME']
    c_adress = primer_objeto['CUSTOMER ADDRESS']

    task_info = []

    for obj in resultado.values():
        task_info.append({
            'CODE': obj['CODE'],
            'DESCRIPTION': obj['DESCRIPTION'],
            'UNIT_WEEK': obj['UNIT / WEEK'],
            'QUANTITY': obj['QUANTITY'],
            'TYPE': obj['TYPE']
        })

    pdf_data_pdfkit = generate_pdf(wo, c_name, c_adress, task_info)

    response = Flask.response_class(
        response=pdf_data_pdfkit,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=work_order_{wo}.pdf'}
    )

    return response

def generate_zip(opcion_seleccionada, df, listas_agrupadas, lista_options):
    resultado = generate_json(opcion_seleccionada, df, listas_agrupadas, lista_options)

    primer_objeto = list(resultado.values())[0]
    wo = primer_objeto['WO']
    c_name = primer_objeto['CUSTOMER NAME']
    c_adress = primer_objeto['CUSTOMER ADDRESS']

    task_info = []

    for obj in resultado.values():
        task_info.append({
            'CODE': obj['CODE'],
            'DESCRIPTION': obj['DESCRIPTION'],
            'UNIT_WEEK': obj['UNIT / WEEK'],
            'QUANTITY': obj['QUANTITY'],
            'TYPE': obj['TYPE']
        })

    pdf_data_pdfkit = generate_pdf(wo, c_name, c_adress, task_info)

    pdf_data_bytesio = BytesIO(pdf_data_pdfkit)

    return pdf_data_bytesio 

def clean_format(cell):
    if isinstance(cell, str):
        # Si la celda es una cadena, quitar cualquier formato no deseado aquí
        # Por ejemplo, puedes eliminar espacios en blanco al principio y al final:
        return cell.strip()
    else:
        # Si la celda no es una cadena, mantener su valor sin cambios
        return cell


@app.route('/', methods=['GET', 'POST'])
def index():
    listas_agrupadas = {}

    for key, group in df[~df['WO'].str.contains('[xX]')].groupby('WO'):
        indices = group.index.tolist()
        listas_agrupadas[key] = indices

    lista = {}
    lista_options = list(listas_agrupadas.keys())

    for i, option in enumerate(lista_options, start=1):
        lista[i] = option

    if request.method == 'POST':

        if request.form['action'] == 'generate_single':
            opcion_seleccionada = int(request.form['opcion']) - 1        
            return download_pdf(opcion_seleccionada, df, listas_agrupadas, lista_options)
        
        elif request.form['action'] == 'generate_all':
            temp_dir = tempfile.mkdtemp()
            output_dir = 'output_pdfs'

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            pdf_filenames = []

            for clave, nombre in lista.items():
                opcion = clave - 1
                pdf_data_bytesio = generate_zip(opcion, df, listas_agrupadas, lista_options)
                pdf_filename = os.path.join(output_dir, f'{nombre}.pdf')

                with open(pdf_filename, 'wb') as pdf_file:
                    pdf_file.write(pdf_data_bytesio.read())

                pdf_filenames.append(pdf_filename)

            # Comprimir todos los PDFs en un archivo ZIP
            zip_filename = os.path.join(temp_dir, 'all_pdfs.zip')
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pdf_file in pdf_filenames:
                    zipf.write(pdf_file, os.path.basename(pdf_file))  # Agregar los archivos al ZIP

            # Mover el archivo ZIP a la carpeta de salida en el servidor
            shutil.move(zip_filename, os.path.join(output_dir, 'all_pdfs.zip'))

            shutil.rmtree(temp_dir)  # Elimina el directorio temporal y su contenido
            for pdf_file in pdf_filenames:
                os.remove(pdf_file)

            # Enviar el archivo ZIP como respuesta para su descarga
            return send_file(os.path.join(output_dir, 'all_pdfs.zip'), as_attachment=True)
        
    return render_template('index.html', lista=lista)

if __name__ == '__main__':
    app.run(debug=True)


