import os
from src.generador_fichas import GestorFichas

def seleccionar_rol():
    """Simula un inicio de sesión seleccionando el perfil de usuario"""
    print("\n--- SIMULACIÓN DE INICIO DE SESIÓN ---")
    print("Selecciona tu rol en el sistema para determinar tus permisos:")
    print("1. Director / Equipo de Gestión (Acceso Total)")
    print("2. Profesor Jefe (Acceso Total)")
    print("3. Dupla Psicosocial (Acceso Total)")
    print("4. Inspector (Acceso a Contactos y Convivencia)")
    print("5. Profesor de Asignatura regular (Acceso Restringido)")
    
    opciones = {
        '1': 'director',            #acceso total
        '2': 'profesor_jefe',       #acceso total
        '3': 'dupla_psicosocial',   #acceso total
        '4': 'inspector',           #acceso a contactos y convivencia
        '5': 'profesor_asignatura'  #acceso restringido
    }
    
    while True:
        seleccion = input("Ingresa el número de tu rol: ")
        if seleccion in opciones:
            rol = opciones[seleccion]
            print(f"\n[!] Sesión iniciada como: {rol.upper()}")
            return rol
        print("Opción inválida. Intenta nuevamente.")

def main():
    print("=== Sistema de Gestión de Fichas Estudiantiles ===")
    
    ruta_excel = "BD.xlsx"
    ruta_template = os.path.join("src", "ficha_template.json")
    
    if not os.path.exists(ruta_excel):
        print(f"Error: No se encontró el archivo '{ruta_excel}' en el directorio raíz.")
        return

    gestor = GestorFichas(ruta_excel, ruta_template)
    
    # Iniciar sesión obteniendo el rol
    rol_actual = seleccionar_rol()
    
    while True:
        print("\nOpciones de Búsqueda:")
        print("1. Buscar estudiante por RUT o Nombre")
        print("2. Filtrar estudiantes por Especialidad TP (ID_Asignatura 25 en adelante)")
        print("3. Cambiar de Usuario (Rol)")
        print("4. Salir")
        
        opcion = input("Elige una opción: ")
        
        if opcion == '4':
            print("Saliendo del sistema...")
            break
            
        elif opcion == '3':
            rol_actual = seleccionar_rol()
            
        elif opcion == '1':
            query = input("Ingresa el RUT o Nombre del estudiante a buscar: ")
            resultados = gestor.buscar_estudiante(query)
            procesar_resultados(gestor, resultados, rol_actual)
            
        elif opcion == '2':
            print("\nIDs de Especialidades TP: 25 (Admin Logística), 26 (RRHH), 27 (Contabilidad), 28 (Redes), 29 (Turismo)")
            id_asig = input("Ingresa el ID de la especialidad: ")
            
            if not id_asig.isdigit() or int(id_asig) < 25:
                print("Error: Ingresa un ID numérico válido de especialidad (25 o superior).")
                continue
                
            resultados = gestor.buscar_por_especialidad(id_asig)
            procesar_resultados(gestor, resultados, rol_actual)
            
        else:
            print("Opción inválida.")

def procesar_resultados(gestor, resultados, rol_actual):
    """Procesa los resultados y genera la ficha respetando el rol"""
    if resultados.empty:
        print("No se encontraron estudiantes con ese criterio.")
    else:
        print(f"\nSe encontraron {len(resultados)} coincidencia(s):")
        for index, row in resultados.iterrows():
            print(f"- RUT: {row['rut_estudiante']} | Nombre: {row['nombre']} {row['apellido_paterno']} | ID Esp: {row['especialidad_tp']}")
        
        rut_elegido = input("\nCopia y pega el RUT exacto para generar su ficha (o presiona Enter para cancelar): ")
        
        if rut_elegido.strip():
            # Pasamos el rol actual a la función generadora
            archivo_creado = gestor.generar_json(rut_elegido.strip(), rol_actual)
            if archivo_creado:
                print(f"¡Éxito! Ficha generada respetando permisos de datos, guardada en: {archivo_creado}")
            else:
                print("Error: El RUT ingresado no coincide con los registros exactos.")

if __name__ == "__main__":
    main()