import pandas as pd
import json
import os

class GestorFichas:
    def __init__(self, ruta_excel, ruta_template):
        self.ruta_template = ruta_template
        
        # Cargar las hojas del Excel
        try:
            self.df_datos = pd.read_excel(ruta_excel, sheet_name='Datos')
            self.df_apoderado = pd.read_excel(ruta_excel, sheet_name='Apoderado')
            self.df_anotaciones = pd.read_excel(ruta_excel, sheet_name='Anotaciones')
            self.df_asignaturas = pd.read_excel(ruta_excel, sheet_name='Asignaturas')
        except Exception as e:
            print(f"Error al cargar BD.xlsx. Asegúrate de que las hojas existan: {e}")
            
    def buscar_estudiante(self, query):
        """Busca un estudiante por RUT o por Nombre"""
        query = str(query).strip().lower()
        
        mask = (
            self.df_datos['rut_estudiante'].astype(str).str.lower().str.contains(query) |
            self.df_datos['nombre'].astype(str).str.lower().str.contains(query)
        )
        return self.df_datos[mask]

    def buscar_por_especialidad(self, id_asignatura):
        """Filtra estudiantes según su especialidad TP (ID 25 en adelante)"""
        try:
            id_asig = int(id_asignatura)
            if id_asig < 25:
                return pd.DataFrame() # Retorna vacío si no es una especialidad válida
            
            # El campo especialidad_tp en la hoja Datos almacena este ID
            mask = self.df_datos['especialidad_tp'] == id_asig
            return self.df_datos[mask]
        except ValueError:
            return pd.DataFrame()

    def generar_json(self, rut_buscado, output_dir="docs"):
        """Genera el JSON final cruzando los datos vinculados por el RUT"""
        
        # 1. Obtener datos del estudiante
        estudiante_data = self.df_datos[self.df_datos['rut_estudiante'] == rut_buscado]
        if estudiante_data.empty:
            return None
        estudiante_row = estudiante_data.iloc[0]

        # 2. Obtener datos del apoderado
        apoderado_data = self.df_apoderado[self.df_apoderado['rut_estudiante'] == rut_buscado]
        apoderado_row = apoderado_data.iloc[0] if not apoderado_data.empty else None

        # 3. Obtener anotaciones
        anotaciones_data = self.df_anotaciones[self.df_anotaciones['rut_estudiante'] == rut_buscado]

        with open(self.ruta_template, 'r', encoding='utf-8') as file:
            ficha = json.load(file)

        # 4. Poblar Datos Principales
        ficha["estudiante"]["rut"] = str(estudiante_row.get('rut_estudiante', ''))
        ficha["estudiante"]["nombre"] = str(estudiante_row.get('nombre', ''))
        ficha["estudiante"]["apellido_paterno"] = str(estudiante_row.get('apellido_paterno', ''))
        ficha["estudiante"]["apellido_materno"] = str(estudiante_row.get('apellido_materno', ''))
        ficha["estudiante"]["nivel_academico"] = str(estudiante_row.get('nivel', ''))

        # 5. Mapear la Especialidad cruzándola con el Catálogo de Asignaturas
        especialidad_id = estudiante_row.get('especialidad_tp', '')
        if pd.notna(especialidad_id) and especialidad_id != "":
            match_esp = self.df_asignaturas[self.df_asignaturas['id_asignatura'] == especialidad_id]
            if not match_esp.empty:
                nombre_esp = match_esp.iloc[0]['nombre_asignatura']
                ficha["estudiante"]["especialidad_tp"] = f"[{int(especialidad_id)}] {nombre_esp}"
            else:
                ficha["estudiante"]["especialidad_tp"] = str(especialidad_id)

        # 6. Datos del Apoderado
        if apoderado_row is not None:
            ficha["apoderado"]["nombre"] = str(apoderado_row.get('nombre_apoderado', ''))
            ficha["apoderado"]["apellido"] = str(apoderado_row.get('apellido_apoderado', ''))
            ficha["apoderado"]["numero_contacto"] = str(apoderado_row.get('telefono_apoderado', ''))

        # 7. Asignaturas Electivas (Extraídas directamente de la tabla de Datos del alumno)
        ficha["asignaturas_electivas"]["electivo_1"] = str(estudiante_row.get('electivo_1', ''))
        ficha["asignaturas_electivas"]["electivo_2"] = str(estudiante_row.get('electivo_2', ''))
        ficha["asignaturas_electivas"]["electivo_3"] = str(estudiante_row.get('electivo_3', ''))
        ficha["asignaturas_electivas"]["electivo_4"] = str(estudiante_row.get('electivo_4', ''))

        # 8. Conteo Dinámico de Anotaciones
        if not anotaciones_data.empty:
            conteo = anotaciones_data['tipo_anotacion'].value_counts()
            ficha["resumen_anotaciones"]["positivas"] = int(conteo.get('Positiva', 0))
            ficha["resumen_anotaciones"]["negativas"] = int(conteo.get('Negativa', 0))
            ficha["resumen_anotaciones"]["neutras"] = int(conteo.get('Neutra', 0))

        # 9. Exportar
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"ficha_{rut_buscado}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ficha, f, indent=4, ensure_ascii=False)
            
        return output_file