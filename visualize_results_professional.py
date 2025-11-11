#!/usr/bin/env python3
"""
================================================================================
VISUALIZACIÓN PROFESIONAL DE RESULTADOS FEM - ZAPATA
================================================================================
Genera visualizaciones de alta calidad en formato PDF para publicaciones
y reportes técnicos.

Características:
  - Renderizado de alta resolución (300 DPI)
  - Vistas isométricas profesionales
  - Escalas de color personalizadas
  - Anotaciones técnicas
  - Múltiples vistas en PDF multipágina
  - Iluminación optimizada para claridad

Uso:
    python visualize_results_professional.py

Salida:
    - modelo_isometrico.pdf
    - desplazamientos_total.pdf
    - modelo_completo_reporte.pdf (multipágina)
================================================================================
"""

import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from datetime import datetime
import config
import os

# Configurar backend de matplotlib para entorno sin display
plt.switch_backend('Agg')

# Configurar PyVista para renderizado off-screen
pv.OFF_SCREEN = True
pv.start_xvfb()  # Iniciar servidor X virtual si es necesario

# Configuración de calidad profesional
pv.set_plot_theme("document")  # Tema para publicaciones
pv.global_theme.font.family = 'arial'
pv.global_theme.font.size = 12
pv.global_theme.font.label_size = 10


def configurar_camara_isometrica(plotter, mesh):
    """
    Configura una vista isométrica mirando hacia el centro de la zapata.
    La cámara está posicionada para ver la zapata desde el primer cuadrante,
    con rotación de 180° para que el centro esté en primer plano.
    """
    bounds = mesh.bounds
    center = mesh.center

    # Calcular distancia de cámara basada en el tamaño del modelo
    diagonal = np.sqrt((bounds[1]-bounds[0])**2 +
                       (bounds[3]-bounds[2])**2 +
                       (bounds[5]-bounds[4])**2)

    # Posición isométrica mirando hacia la zapata (rotado 180°)
    # La cámara está en el lado NEGATIVO de X e Y para mirar hacia el origen
    distance = diagonal * 2.0
    camera_pos = [
        center[0] - distance * 0.7071,  # -cos(45°) - rotado 180°
        center[1] - distance * 0.7071,  # -cos(45°) - rotado 180°
        center[2] + distance * 0.5774   # sin(35.264°) - altura estándar
    ]

    plotter.camera_position = [
        camera_pos,      # Posición de cámara
        center,          # Punto focal (centro del modelo)
        (0, 0, 1)        # Vector up (Z hacia arriba)
    ]

    plotter.camera.zoom(1.2)


def crear_mapa_colores_materiales():
    """Crea un diccionario de colores para cada material."""
    # Colores profesionales para publicación (ColorBrewer-inspired)
    colores = {
        1: [0.90, 0.85, 0.70],  # Suelo Superior - beige claro
        2: [0.70, 0.60, 0.40],  # Suelo Intermedio - marrón medio
        3: [0.50, 0.40, 0.30],  # Suelo Profundo - marrón oscuro
        4: [0.70, 0.70, 0.75],  # Zapata - gris concreto
    }
    return colores


def crear_vista_modelo(mesh, output_file, titulo="Modelo FEM - Vista Isométrica"):
    """
    Crea una vista isométrica profesional del modelo por materiales.

    Args:
        mesh: PyVista mesh con datos
        output_file: Nombre del archivo PNG de salida
        titulo: Título de la figura
    """
    plotter = pv.Plotter(off_screen=True, window_size=[3000, 2400])

    # Configurar iluminación profesional (3-point lighting)
    plotter.remove_all_lights()

    # Key light (principal)
    light1 = pv.Light(position=(10, 10, 10), intensity=0.8, light_type='scene light')
    plotter.add_light(light1)

    # Fill light (relleno)
    light2 = pv.Light(position=(-10, -5, 5), intensity=0.3, light_type='scene light')
    plotter.add_light(light2)

    # Back light (contraluz)
    light3 = pv.Light(position=(0, -10, -5), intensity=0.2, light_type='scene light')
    plotter.add_light(light3)

    # Luz ambiental suave
    plotter.add_light(pv.Light(intensity=0.2, light_type='headlight'))

    # Obtener datos de dominio
    if 'dominio' in mesh.cell_data:
        dominios = mesh.cell_data['dominio']
        colores_mat = crear_mapa_colores_materiales()

        # Crear array de colores para cada celda
        colors = np.zeros((mesh.n_cells, 3))
        for i, dom in enumerate(dominios):
            if dom in colores_mat:
                colors[i] = colores_mat[dom]

        # Agregar malla con colores por material
        # smooth_shading=False para mostrar aristas reales del dominio
        plotter.add_mesh(
            mesh,
            scalars=colors,
            rgb=True,
            show_edges=True,
            edge_color='black',
            line_width=0.8,
            opacity=1.0,
            smooth_shading=False,  # Aristas reales, no suavizado
            specular=0.2,
            specular_power=10
        )

        # Crear leyenda personalizada
        nombres_materiales = {
            1: 'Suelo Superior (E=5 MPa)',
            2: 'Suelo Intermedio (E=15 MPa)',
            3: 'Suelo Profundo (E=100 MPa)',
            4: 'Zapata de Concreto (E=25 GPa)'
        }

        legend_entries = []
        unique_doms = np.unique(dominios)
        for dom in sorted(unique_doms):
            if dom in colores_mat and dom in nombres_materiales:
                legend_entries.append([nombres_materiales[dom], colores_mat[dom]])

        if legend_entries:
            plotter.add_legend(legend_entries, bcolor='white', face='rectangle',
                             loc='upper right', size=[0.25, 0.15])
    else:
        # Sin datos de dominio, usar visualización simple
        plotter.add_mesh(mesh, show_edges=True, color='lightgray')

    # Configurar cámara isométrica
    configurar_camara_isometrica(plotter, mesh)

    # Agregar ejes de referencia en esquina inferior izquierda
    # Textos más pequeños para mejor legibilidad
    try:
        plotter.add_axes(
            xlabel='X',
            ylabel='Y',
            zlabel='Z',
            line_width=3,
            color='black',
            x_color='red',
            y_color='green',
            z_color='blue'
        )
    except Exception as e:
        print(f"  Advertencia: No se pudieron agregar ejes: {e}")

    # Título en la parte superior central (sin superposición)
    plotter.add_text(
        titulo,
        position='upper_edge',
        font_size=20,
        color='black',
        font='arial'
    )

    # Información del modelo en la parte inferior (separada del borde)
    info_text = f"Nodos: {mesh.n_points:,} | Elementos: {mesh.n_cells:,}"
    plotter.add_text(
        info_text,
        position=(0.5, 0.02),  # Posición absoluta (x, y) normalizada
        font_size=14,
        color='black',
        font='arial',
        viewport=True  # Usar coordenadas de viewport
    )

    # Renderizar y guardar
    plotter.screenshot(output_file, scale=3)  # 3x resolución para calidad print
    plotter.close()

    print(f"✓ Vista de modelo guardada: {output_file}")


def crear_vista_desplazamientos(mesh, campo, output_file,
                                titulo="Desplazamientos Verticales",
                                unidades="mm",
                                cmap='rainbow'):
    """
    Crea una vista isométrica con escala de colores de desplazamientos.

    Args:
        mesh: PyVista mesh
        campo: Nombre del campo de datos
        output_file: Archivo PNG de salida
        titulo: Título de la figura
        unidades: Unidades del campo
        cmap: Mapa de colores de matplotlib
    """
    if campo not in mesh.point_data:
        print(f"⚠️  Campo '{campo}' no encontrado en los datos")
        return

    plotter = pv.Plotter(off_screen=True, window_size=[3000, 2400])

    # Configurar iluminación
    plotter.remove_all_lights()
    plotter.add_light(pv.Light(position=(10, 10, 10), intensity=0.6))
    plotter.add_light(pv.Light(position=(-10, -5, 5), intensity=0.3))
    plotter.add_light(pv.Light(intensity=0.3, light_type='headlight'))

    # Obtener rango de datos
    data = mesh.point_data[campo]
    vmin, vmax = data.min(), data.max()

    # Agregar malla con escala de colores
    # smooth_shading=False para mostrar aristas reales
    plotter.add_mesh(
        mesh,
        scalars=campo,
        cmap=cmap,
        show_edges=True,
        edge_color='black',
        line_width=0.5,
        opacity=1.0,
        smooth_shading=False,  # Aristas reales, no suavizado
        specular=0.15,
        clim=[vmin, vmax],
        scalar_bar_args={
            'title': f'Desplazamiento ({unidades})',
            'title_font_size': 22,  # Aumentado para mejor legibilidad
            'label_font_size': 18,  # Aumentado para mejor legibilidad
            'n_labels': 8,
            'italic': False,
            'fmt': '%.2f',
            'font_family': 'arial',
            'vertical': True,
            'height': 0.65,
            'width': 0.10,  # Ligeramente más ancho para acomodar texto
            'position_x': 0.86,
            'position_y': 0.17,
            'color': 'black'
        }
    )

    # Configurar cámara
    configurar_camara_isometrica(plotter, mesh)

    # Ejes con colores diferenciados y textos más pequeños
    try:
        plotter.add_axes(
            xlabel='X',
            ylabel='Y',
            zlabel='Z',
            line_width=3,
            color='black',
            x_color='red',
            y_color='green',
            z_color='blue'
        )
    except Exception as e:
        print(f"  Advertencia: No se pudieron agregar ejes: {e}")

    # Título en la parte superior (sin superposición con barra de colores)
    plotter.add_text(
        titulo,
        position='upper_edge',
        font_size=20,
        color='black',
        font='arial'
    )

    # Estadísticas en la parte inferior (separadas del borde)
    info_text = f"Máx: {vmax:.2f} {unidades} | Mín: {vmin:.2f} {unidades} | Media: {data.mean():.2f} {unidades}"
    plotter.add_text(
        info_text,
        position=(0.45, 0.02),  # Posición absoluta, más centrada
        font_size=14,
        color='black',
        font='arial',
        viewport=True
    )

    # Renderizar
    plotter.screenshot(output_file, scale=3)
    plotter.close()

    print(f"✓ Vista de desplazamientos guardada: {output_file}")


def crear_pdf_multipagina(imagenes, output_pdf, configuracion):
    """
    Crea un PDF multipágina profesional con las imágenes generadas.

    Args:
        imagenes: Lista de tuplas (archivo_imagen, título, descripción)
        output_pdf: Nombre del archivo PDF de salida
        configuracion: Diccionario con parámetros del modelo
    """
    with PdfPages(output_pdf) as pdf:
        # Página 1: Portada
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('ANÁLISIS DE ELEMENTO FINITO\nZAPATA DE CONCRETO',
                    fontsize=24, fontweight='bold', y=0.7)

        # Información del proyecto
        info_texto = f"""
Configuración del Modelo:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zapata: {configuracion['B']}m × {configuracion['L']}m × {configuracion['h']}m
Profundidad de desplante: {configuracion['Df']}m
Carga de columna: {configuracion['P_column']:.0f} kN

Estratos de Suelo:
{chr(10).join([f"  • {e['nombre']}: {e['espesor']}m, E={e['E']/1e6:.0f} MPa" for e in configuracion['estratos']])}

Material Zapata:
  • Concreto: E={configuracion['E_zapata']/1e9:.0f} GPa

Análisis:
  • Tipo: 2 Fases (Gravedad + Carga)
  • Modelo: 1/4 con simetría
  • Elementos: Tetraédricos lineales

Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        plt.text(0.5, 0.4, info_texto,
                ha='center', va='center',
                fontsize=11, fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.axis('off')
        pdf.savefig(fig, bbox_inches='tight', dpi=300)
        plt.close()

        # Páginas con imágenes
        for img_file, titulo, descripcion in imagenes:
            try:
                img = plt.imread(img_file)

                fig, ax = plt.subplots(figsize=(11, 8.5))
                ax.imshow(img)
                ax.axis('off')

                # Título en la parte superior
                fig.suptitle(titulo, fontsize=16, fontweight='bold', y=0.98)

                # Descripción en la parte inferior
                if descripcion:
                    fig.text(0.5, 0.02, descripcion,
                            ha='center', fontsize=10, style='italic')

                pdf.savefig(fig, bbox_inches='tight', dpi=300)
                plt.close()
            except Exception as e:
                print(f"⚠️  Error al agregar {img_file} al PDF: {e}")

        # Metadata del PDF
        d = pdf.infodict()
        d['Title'] = 'Análisis FEM - Zapata de Concreto'
        d['Author'] = 'Sistema de Análisis FEM'
        d['Subject'] = 'Resultados de Análisis por Elementos Finitos'
        d['Keywords'] = 'FEM, Zapata, OpenSees, Análisis Estructural'
        d['CreationDate'] = datetime.now()

    print(f"✓ PDF multipágina creado: {output_pdf}")


def main():
    """Función principal para generar todas las visualizaciones."""

    print("\n" + "="*80)
    print("GENERACIÓN DE VISUALIZACIONES PROFESIONALES")
    print("="*80)

    # Archivo de entrada
    vtu_file = "resultados_2phases.vtu"

    print(f"\nLeyendo archivo: {vtu_file}")
    try:
        mesh = pv.read(vtu_file)
        print(f"✓ Malla cargada: {mesh.n_points:,} nodos, {mesh.n_cells:,} elementos")
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return

    # Crear directorio para imágenes temporales
    os.makedirs('visualizaciones', exist_ok=True)

    # Lista de imágenes generadas
    imagenes_generadas = []

    # SOLO GENERAR: Desplazamientos fase 2 (carga)
    # Mapa de calor: azul (mínimo) a rojo (máximo)
    if 'Settlement_carga_mm' in mesh.point_data:
        print("\n1. Generando vista de desplazamientos por carga incremental...")
        img_carga = 'visualizaciones/desplazamientos_carga.png'
        crear_vista_desplazamientos(
            mesh,
            'Settlement_carga_mm',
            img_carga,
            titulo="Asentamientos por Carga de Columna (Fase 2)",
            unidades="mm",
            cmap='coolwarm'  # Azul (mínimo) -> Blanco (medio) -> Rojo (máximo)
        )
        imagenes_generadas.append((
            img_carga,
            "Fase 2: Asentamientos por Carga de Columna",
            "Desplazamientos adicionales inducidos por la carga de 250 kN (modelo 1/4)"
        ))
    else:
        print("⚠️  Campo 'Settlement_carga_mm' no encontrado en los datos")
        return

    # Preparar configuración para PDF
    configuracion = {
        'B': config.ZAPATA['B'],
        'L': config.ZAPATA['L'],
        'h': config.ZAPATA['h'],
        'Df': config.ZAPATA['Df'],
        'P_column': config.CARGAS['P_column'],
        'estratos': config.ESTRATOS_SUELO,
        'E_zapata': config.PROPIEDADES_ZAPATA['E']
    }

    # Crear PDF individual
    print("\n2. Generando PDF de alta resolución...")
    for img_file, titulo, descripcion in imagenes_generadas:
        pdf_individual = img_file.replace('.png', '.pdf')
        with PdfPages(pdf_individual) as pdf:
            img = plt.imread(img_file)
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.imshow(img)
            ax.axis('off')
            fig.suptitle(titulo, fontsize=16, fontweight='bold')
            # Agregar descripción
            fig.text(0.5, 0.02, descripcion, ha='center', fontsize=11, style='italic')
            pdf.savefig(fig, bbox_inches='tight', dpi=300)
            plt.close()
        print(f"  ✓ {pdf_individual}")

    print("\n" + "="*80)
    print("VISUALIZACIÓN COMPLETADA")
    print("="*80)
    print("\nArchivos generados:")
    print(f"  • visualizaciones/desplazamientos_carga.pdf (PDF de alta resolución)")
    print(f"  • visualizaciones/desplazamientos_carga.png (imagen PNG 3x)")
    print("\nCaracterísticas:")
    print("  • Mapa de calor: Azul (mínimo) → Rojo (máximo)")
    print("  • Ejes: Textos optimizados para legibilidad")
    print("  • Leyenda: Textos aumentados (22pt título, 18pt etiquetas)")
    print("  • Aristas reales visibles (sin suavizado)")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
