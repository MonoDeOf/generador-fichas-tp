import os
from src.generador_fichas import GestorFichas

def main():
    print("=== Sistema de Gestión de Fichas Estudiantiles ===")
    
    ruta_excel = "BD.xlsx"
    ruta_template = os.path.join("src", "ficha_template.json")
    
    if not os.path.exists(ruta_excel):
        print(f"Error: No se encontró el archivo '{ruta_excel}' en el directorio raíz.")
        return

    gestor = GestorFichas(ruta_excel, ruta_template)
    
    while True:
        print("\nOpciones:")
        print("1. Buscar estudiante por RUT o Nombre")
        print("2. Filtrar estudiantes por Especialidad TP (ID_Asignatura 25 en adelante)")
        print("3. Salir")
        
        opcion = input("Elige una opción (1, 2 o 3): ")
        
        if opcion == '3':
            print("Saliendo del sistema...")
            break
            
        elif opcion == '1':
            query = input("Ingresa el RUT o Nombre del estudiante a buscar: ")
            resultados = gestor.buscar_estudiante(query)
            procesar_resultados(gestor, resultados)
            
        elif opcion == '2':
            # Se presentan las IDs principales para ayudar a la búsqueda
            print("\nIDs de Especialidades TP: 25 (Admin Logística), 26 (RRHH), 27 (Contabilidad), 28 (Redes), 29 (Turismo)")
            id_asig = input("Ingresa el ID de la especialidad (solo números 25 en adelante): ")
            
            if not id_asig.isdigit() or int(id_asig) < 25:
                print("Error: El filtro requiere que ingreses un ID numérico válido de especialidad (25 o superior).")
                continue
                
            resultados = gestor.buscar_por_especialidad(id_asig)
            procesar_resultados(gestor, resultados)
            
        else:
            print("Opción inválida.")

def procesar_resultados(gestor, resultados):
    """Muestra los resultados formateados y permite generar la ficha en la carpeta docs/"""
    if resultados.empty:
        print("No se encontraron estudiantes con ese criterio.")
    else:
        print(f"\nSe encontraron {len(resultados)} coincidencia(s):")
        # Mostrar el RUT, nombre y la especialidad para facilitar la identificación
        for index, row in resultados.iterrows():
            print(f"- RUT: {row['rut_estudiante']} | Nombre: {row['nombre']} {row['apellido_paterno']} | ID Esp: {row['especialidad_tp']}")
        
        rut_elegido = input("\nCopia y pega el RUT exacto para generar su ficha (o presiona Enter para cancelar): ")
        
        if rut_elegido.strip():
            archivo_creado = gestor.generar_json(rut_elegido.strip())
            if archivo_creado:
                print(f"¡Éxito! Ficha generada correctamente y guardada en: {archivo_creado}")
            else:
                print("Error: El RUT ingresado no coincide con los registros exactos.")

if __name__ == "__main__":
    main()