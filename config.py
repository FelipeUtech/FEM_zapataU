#!/usr/bin/env python3
"""
Archivo de configuración para la generación de mallas de zapatas.
"""

# Nombre de la estructura
NOMBRE_ESTRUCTURA = "CHANCADO PRIMARIO"

# Parámetros de la zapata - CHANCADO PRIMARIO
ZAPATA = {
    'B': 1.8,      # Ancho (m)
    'L': 2.0,      # Largo (m)
    'h': 0.5,      # Altura/espesor (m)
    'Df': 0.5,     # Profundidad de desplante (m)
}

# Estratos de suelo - CHANCADO PRIMARIO (de arriba hacia abajo)
ESTRATOS_SUELO = [
    {
        'nombre': 'Estrato 1',
        'espesor': 2.35,  # metros (profundidad: 0 a 2.35 m)
        'E': 50e6,        # Módulo de Young (Pa) - 50 MPa
        'nu': 0.30,       # Coeficiente de Poisson
        'rho': 2039,      # Densidad (kg/m³) - convertido de 20 kN/m³
        'color': [0.9, 0.85, 0.7],  # Color claro (RGB)
    },
    {
        'nombre': 'Estrato 2',
        'espesor': 12.65,  # metros (profundidad: 2.35 a 15.00 m)
        'E': 100e6,       # 100 MPa
        'nu': 0.25,       # Coeficiente de Poisson
        'rho': 2141,      # Densidad (kg/m³) - convertido de 21 kN/m³
        'color': [0.7, 0.6, 0.4],   # Color medio
    },
]

# Propiedades de la zapata (concreto)
PROPIEDADES_ZAPATA = {
    'E': 25e9,      # 25 GPa
    'nu': 0.2,
    'rho': 2400,    # kg/m³
}

# Alias para compatibilidad con run_analysis_2phases.py
MATERIAL_ZAPATA = PROPIEDADES_ZAPATA
MATERIAL_SUELO = ESTRATOS_SUELO  # Lista de estratos

# Configuración del dominio
DOMINIO = {
    'usar_cuarto_modelo': True,  # Usar modelo 1/4 con simetría
    'factor_horizontal': 5,      # Factor para dimensiones horizontales (ya aplicado en obtener_dimensiones_dominio)
    'profundidad': sum(e['espesor'] for e in ESTRATOS_SUELO),  # Profundidad total (suma de estratos)
}

# Cargas aplicadas - CHANCADO PRIMARIO
CARGAS = {
    'P_column': 414.0,  # Carga de columna en kN (presión: 115 kPa, se divide automáticamente para modelo 1/4)
}

# Configuración del análisis
ANALISIS = {
    'solver': 'BandGeneral',
    'numberer': 'RCM',
    'constraints': 'Plain',
    'algorithm': 'Linear',
    'tipo': 'Static',
}

# Criterios de diseño
CRITERIOS = {
    'asentamiento_maximo_admisible': 25.0,  # mm
    'asentamiento_diferencial_admisible': 0.002,  # Relación diferencial/máximo
}

# Configuración de salida
SALIDA = {
    'guardar_csv': True,
    'csv_surface': 'settlements_surface.csv',
    'generar_reporte': True,
    'generar_graficas': False,  # Requiere visualize_zapata.py
}

# Parámetros de malla
MALLA = {
    'graded': {
        'dx_min': min(ZAPATA['B'], ZAPATA['L']) / 10,   # Tamaño mínimo cerca de la zapata (m)
        'dx_max': 2.0,    # Tamaño máximo en fronteras (m)
    }
}

def obtener_dimensiones_dominio():
    """
    Calcula las dimensiones del dominio completo.
    Regla: dominio 5*B en X y 5*L en Y
    """
    B = ZAPATA['B']
    L = ZAPATA['L']

    # Dimensiones del dominio (valores completos)
    Lx = 5 * B
    Ly = 5 * L

    # Profundidad total
    Lz = sum(e['espesor'] for e in ESTRATOS_SUELO)

    return {
        'Lx': Lx,
        'Ly': Ly,
        'Lz': Lz
    }

def validar_configuracion():
    """
    Valida la configuración del modelo.
    Retorna True si todo está OK, False si hay errores.
    """
    errores = []

    # Validar zapata
    if ZAPATA['B'] <= 0 or ZAPATA['L'] <= 0 or ZAPATA['h'] <= 0:
        errores.append("Dimensiones de zapata deben ser positivas")

    if ZAPATA['Df'] <= 0:
        errores.append("Profundidad de desplante debe ser positiva")

    # Validar estratos
    if len(ESTRATOS_SUELO) == 0:
        errores.append("Debe haber al menos un estrato de suelo")

    for i, estrato in enumerate(ESTRATOS_SUELO, 1):
        if estrato['espesor'] <= 0:
            errores.append(f"Estrato {i}: espesor debe ser positivo")
        if estrato['E'] <= 0:
            errores.append(f"Estrato {i}: módulo de Young debe ser positivo")
        if not (0 <= estrato['nu'] < 0.5):
            errores.append(f"Estrato {i}: coeficiente de Poisson debe estar entre 0 y 0.5")

    # Validar cargas
    if CARGAS['P_column'] < 0:
        errores.append("Carga de columna no puede ser negativa")

    if errores:
        print("\n❌ Errores de validación:")
        for error in errores:
            print(f"  • {error}")
        return False

    return True

def imprimir_resumen():
    """Imprime un resumen de la configuración."""
    print("\n" + "="*70)
    print("CONFIGURACIÓN DEL MODELO")
    print("="*70)

    print("\n📐 ZAPATA:")
    print(f"  Dimensiones: {ZAPATA['B']}m × {ZAPATA['L']}m × {ZAPATA['h']}m")
    print(f"  Profundidad de desplante: {ZAPATA['Df']}m")

    dims = obtener_dimensiones_dominio()
    print(f"\n🌍 DOMINIO:")
    print(f"  Dimensiones: {dims['Lx']}m × {dims['Ly']}m × {dims['Lz']}m")
    print(f"  Modelo: {'Cuarto (1/4)' if DOMINIO['usar_cuarto_modelo'] else 'Completo'}")

    print(f"\n🏔️  ESTRATOS DE SUELO:")
    for i, est in enumerate(ESTRATOS_SUELO, 1):
        print(f"  {i}. {est['nombre']}: {est['espesor']}m, E={est['E']/1e6:.0f} MPa")

    print(f"\n🏗️  MATERIAL ZAPATA:")
    print(f"  Concreto: E={PROPIEDADES_ZAPATA['E']/1e9:.0f} GPa, ν={PROPIEDADES_ZAPATA['nu']}")

    print(f"\n⚡ CARGAS:")
    print(f"  Carga de columna: {CARGAS['P_column']:.1f} kN")

    print(f"\n🔧 MALLA:")
    print(f"  dx_min: {MALLA['graded']['dx_min']:.3f}m")
    print(f"  dx_max: {MALLA['graded']['dx_max']:.3f}m")

    print("="*70)

if __name__ == "__main__":
    # Test de configuración
    imprimir_resumen()

    print("\n" + "="*70)
    print("VALIDACIÓN")
    print("="*70)
    if validar_configuracion():
        print("\n✓ Configuración válida")
    else:
        print("\n❌ Hay errores en la configuración")
    print("="*70)
