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
        font_size=24,  # Aumentado para mejor visibilidad
        color='black',
        font='arial'
    )

    # Información del modelo en la parte inferior (separada del borde)
    info_text = f"Nodos: {mesh.n_points:,} | Elementos: {mesh.n_cells:,}"
    plotter.add_text(
        info_text,
        position=(0.5, 0.02),  # Posición absoluta (x, y) normalizada
        font_size=16,  # Aumentado para mejor legibilidad
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
        font_size=24,  # Aumentado para mejor visibilidad
        color='black',
        font='arial'
    )

    # Estadísticas en la parte inferior (separadas del borde)
    info_text = f"Máx: {vmax:.2f} {unidades} | Mín: {vmin:.2f} {unidades} | Media: {data.mean():.2f} {unidades}"
    plotter.add_text(
        info_text,
        position=(0.45, 0.02),  # Posición absoluta, más centrada
        font_size=16,  # Aumentado para mejor legibilidad
        color='black',
        font='arial',
        viewport=True
    )

    # Renderizar
    plotter.screenshot(output_file, scale=3)
    plotter.close()

    print(f"✓ Vista de desplazamientos guardada: {output_file}")


def crear_vista_tensiones(mesh, campo, output_file, titulo="Tensiones Verticales",
                          unidades="kPa", cmap='RdBu_r'):
    """
    Crea una vista isométrica de tensiones (cell_data).

    Args:
        mesh: PyVista mesh con los datos
        campo: Nombre del campo de tensiones en cell_data
        output_file: Archivo de salida PNG
        titulo: Título de la visualización
        unidades: Unidades del campo
        cmap: Colormap (RdBu_r para tensiones: rojo=compresión, azul=tracción)
    """
    plotter = pv.Plotter(off_screen=True, window_size=[2400, 1800])
    plotter.set_background('white')

    # Iluminación profesional
    plotter.add_light(pv.Light(position=(10, 10, 10), intensity=0.8))
    plotter.add_light(pv.Light(position=(-10, -5, 5), intensity=0.3))
    plotter.add_light(pv.Light(intensity=0.3, light_type='headlight'))

    # Obtener rango de datos
    data = mesh.cell_data[campo]
    vmin, vmax = data.min(), data.max()

    # Agregar malla con escala de colores
    plotter.add_mesh(
        mesh,
        scalars=campo,
        cmap=cmap,
        show_edges=True,
        edge_color='black',
        line_width=0.5,
        opacity=1.0,
        smooth_shading=False,
        specular=0.15,
        clim=[vmin, vmax],
        scalar_bar_args={
            'title': f'Tensión ({unidades})',
            'title_font_size': 22,
            'label_font_size': 18,
            'n_labels': 8,
            'italic': False,
            'fmt': '%.1f',
            'font_family': 'arial',
            'vertical': True,
            'height': 0.65,
            'width': 0.10,
            'position_x': 0.86,
            'position_y': 0.17,
            'color': 'black'
        }
    )

    # Configurar cámara
    configurar_camara_isometrica(plotter, mesh)

    # Ejes
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

    # Título
    plotter.add_text(
        titulo,
        position='upper_edge',
        font_size=24,
        color='black',
        font='arial'
    )

    # Estadísticas
    info_text = f"Máx: {vmax:.1f} {unidades} | Mín: {vmin:.1f} {unidades} | Media: {data.mean():.1f} {unidades}"
    plotter.add_text(
        info_text,
        position=(0.45, 0.02),
        font_size=16,
        color='black',
        font='arial',
        viewport=True
    )

    # Renderizar
    plotter.screenshot(output_file, scale=3)
    plotter.close()

    print(f"✓ Vista de tensiones guardada: {output_file}")


def crear_vista_desplazamientos_con_bordes(mesh, campo, output_file, titulo="Desplazamientos",
                                            unidades="mm", cmap='coolwarm'):
    """
    Crea vista de desplazamientos con zapata mostrada solo como bordes negros.

    Args:
        mesh: PyVista mesh con los datos
        campo: Nombre del campo de desplazamientos en point_data
        output_file: Archivo de salida PNG
        titulo: Título de la visualización
        unidades: Unidades del campo
        cmap: Colormap
    """
    plotter = pv.Plotter(off_screen=True, window_size=[2400, 1800])
    plotter.set_background('white')

    # Iluminación profesional
    plotter.add_light(pv.Light(position=(10, 10, 10), intensity=0.8))
    plotter.add_light(pv.Light(position=(-10, -5, 5), intensity=0.3))
    plotter.add_light(pv.Light(intensity=0.3, light_type='headlight'))

    # Separar suelo y zapata
    suelo_mesh = mesh.threshold([1, 3], scalars='dominio')
    zapata_mesh = mesh.threshold([4, 4], scalars='dominio')

    # Agregar suelo con desplazamientos
    plotter.add_mesh(
        suelo_mesh,
        scalars=campo,
        cmap=cmap,
        show_edges=True,
        edge_color='black',
        line_width=0.5,
        opacity=1.0,
        smooth_shading=False,
        specular=0.15,
        scalar_bar_args={
            'title': f'{unidades}',
            'title_font_size': 22,
            'label_font_size': 18,
            'n_labels': 8,
            'italic': False,
            'fmt': '%.1f',
            'font_family': 'arial',
            'vertical': True,
            'height': 0.65,
            'width': 0.10,
            'position_x': 0.86,
            'position_y': 0.17,
            'color': 'black'
        }
    )

    # Agregar SOLO los bordes de la zapata en NEGRO
    plotter.add_mesh(
        zapata_mesh,
        style='wireframe',
        color='black',
        line_width=2.5,
        opacity=1.0
    )

    # Configurar cámara
    configurar_camara_isometrica(plotter, mesh)

    # Ejes
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

    # Título
    plotter.add_text(
        titulo,
        position='upper_edge',
        font_size=24,
        color='black',
        font='arial'
    )

    # Estadísticas
    data = mesh.point_data[campo]
    info_text = f"Máx: {data.max():.2f} {unidades} | Mín: {data.min():.2f} {unidades} | Media: {data.mean():.2f} {unidades}"
    plotter.add_text(
        info_text,
        position=(0.45, 0.02),
        font_size=16,
        color='black',
        font='arial',
        viewport=True
    )

    # Renderizar
    plotter.screenshot(output_file, scale=3)
    plotter.close()

    print(f"✓ Vista de desplazamientos con bordes guardada: {output_file}")


def crear_vista_bulbo_sin_zapata(mesh, campo, output_file, titulo="Bulbo de Presiones",
                                  unidades="kPa", cmap='RdBu_r', clim=None):
    """
    Crea vista del bulbo de presiones SIN zapata (solo suelo) con bordes de zapata en rojo.

    Args:
        mesh: PyVista mesh con los datos
        campo: Nombre del campo de tensiones en cell_data
        output_file: Archivo de salida PNG
        titulo: Título de la visualización
        unidades: Unidades del campo
        cmap: Colormap (RdBu_r para tensiones)
        clim: Rango personalizado [min, max] para escala de colores
    """
    plotter = pv.Plotter(off_screen=True, window_size=[2400, 1800])
    plotter.set_background('white')

    # Iluminación profesional
    plotter.add_light(pv.Light(position=(10, 10, 10), intensity=0.8))
    plotter.add_light(pv.Light(position=(-10, -5, 5), intensity=0.3))
    plotter.add_light(pv.Light(intensity=0.3, light_type='headlight'))

    # Separar zapata y suelo usando threshold
    # Suelo: dominios 1, 2, 3
    # Zapata: dominio 4

    # Extraer solo el suelo (dominios 1, 2, 3)
    suelo_mesh = mesh.threshold([1, 3], scalars='dominio')

    # Extraer solo la zapata para bordes
    zapata_mesh = mesh.threshold([4, 4], scalars='dominio')

    # Obtener datos de tensiones
    if campo in mesh.cell_data:
        data = mesh.cell_data[campo]
        vmin, vmax = data.min(), data.max()
    else:
        vmin, vmax = -300, 0

    # Si se proporciona rango personalizado, usarlo
    if clim is not None:
        vmin, vmax = clim

    # Agregar suelo con tensiones (colormap)
    plotter.add_mesh(
        suelo_mesh,
        scalars=campo,
        cmap=cmap,
        show_edges=True,
        edge_color='black',
        line_width=0.3,
        opacity=1.0,
        smooth_shading=False,
        specular=0.15,
        clim=[vmin, vmax],
        scalar_bar_args={
            'title': f'{unidades}',
            'title_font_size': 22,
            'label_font_size': 18,
            'n_labels': 8,
            'italic': False,
            'fmt': '%.1f',
            'font_family': 'arial',
            'vertical': True,
            'height': 0.65,
            'width': 0.10,
            'position_x': 0.86,
            'position_y': 0.17,
            'color': 'black'
        }
    )

    # Agregar SOLO los bordes de la zapata en ROJO
    plotter.add_mesh(
        zapata_mesh,
        style='wireframe',
        color='red',
        line_width=3.0,
        opacity=1.0,
        label='Zapata'
    )

    # Configurar cámara
    configurar_camara_isometrica(plotter, mesh)

    # Ejes
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

    # Título
    plotter.add_text(
        titulo,
        position='upper_edge',
        font_size=24,
        color='black',
        font='arial'
    )

    # Estadísticas (usando datos del suelo solamente)
    suelo_data = suelo_mesh.cell_data[campo]
    info_text = f"Máx: {suelo_data.max():.1f} {unidades} | Mín: {suelo_data.min():.1f} {unidades} | Media: {suelo_data.mean():.1f} {unidades}"
    plotter.add_text(
        info_text,
        position=(0.45, 0.02),
        font_size=16,
        color='black',
        font='arial',
        viewport=True
    )

    # Renderizar
    plotter.screenshot(output_file, scale=3)
    plotter.close()

    print(f"✓ Vista de bulbo sin zapata guardada: {output_file}")


def extraer_perfil_vertical(mesh, x_target, y_target, campo_point=None, campo_cell=None,
                            z_min=-30, z_max=0, n_levels=50):
    """
    Extrae un perfil vertical en una ubicación (x, y) específica.

    Args:
        mesh: PyVista UnstructuredGrid con los datos
        x_target: Coordenada X objetivo
        y_target: Coordenada Y objetivo
        campo_point: Nombre del campo en point_data (e.g., 'Settlement_carga_mm')
        campo_cell: Nombre del campo en cell_data (e.g., 'Sigma_v_carga_kPa')
        z_min: Profundidad mínima (más profundo)
        z_max: Profundidad máxima (superficie)
        n_levels: Número de niveles de profundidad a muestrear

    Returns:
        dict con 'z', 'settlement', 'stress' (los que apliquen)
    """
    # Crear niveles de profundidad
    z_levels = np.linspace(z_min, z_max, n_levels)

    # Arrays para almacenar resultados
    perfil = {'z': z_levels}

    # Extraer datos de punto (settlements)
    if campo_point and campo_point in mesh.point_data:
        values_point = []
        points = mesh.points
        point_data = mesh.point_data[campo_point]

        for z in z_levels:
            # Encontrar nodos cercanos a (x_target, y_target, z)
            target = np.array([x_target, y_target, z])

            # Calcular distancia horizontal (ignorar z para buscar en ese nivel)
            dist_xy = np.sqrt((points[:, 0] - x_target)**2 + (points[:, 1] - y_target)**2)
            dist_z = np.abs(points[:, 2] - z)

            # Filtrar nodos en una banda vertical cercana
            mask = (dist_xy < 0.3) & (dist_z < 0.3)  # Tolerancia de búsqueda

            if np.any(mask):
                # Tomar promedio de nodos cercanos
                values_point.append(np.mean(point_data[mask]))
            else:
                # Si no hay nodos cercanos, buscar el más cercano en 3D
                dist_3d = np.linalg.norm(points - target, axis=1)
                idx_min = np.argmin(dist_3d)
                values_point.append(point_data[idx_min])

        perfil['settlement'] = np.array(values_point)

    # Extraer datos de celda (stresses)
    if campo_cell and campo_cell in mesh.cell_data:
        values_cell = []
        cell_centers = mesh.cell_centers().points
        cell_data = mesh.cell_data[campo_cell]

        for z in z_levels:
            # Encontrar celdas cercanas a (x_target, y_target, z)
            dist_xy = np.sqrt((cell_centers[:, 0] - x_target)**2 +
                            (cell_centers[:, 1] - y_target)**2)
            dist_z = np.abs(cell_centers[:, 2] - z)

            # Filtrar celdas cercanas
            mask = (dist_xy < 0.3) & (dist_z < 0.3)

            if np.any(mask):
                # Tomar promedio de celdas cercanas
                values_cell.append(np.mean(cell_data[mask]))
            else:
                # Buscar celda más cercana en 3D
                target = np.array([x_target, y_target, z])
                dist_3d = np.linalg.norm(cell_centers - target, axis=1)
                idx_min = np.argmin(dist_3d)
                values_cell.append(cell_data[idx_min])

        perfil['stress'] = np.array(values_cell)

    return perfil


def crear_grafica_perfiles_cientifica(perfiles, campo_tipo, output_file, titulo,
                                        xlabel, ylabel="Profundidad (m)"):
    """
    Crea gráfica científica de perfiles verticales con calidad profesional.

    Args:
        perfiles: Lista de diccionarios con 'z' y datos, cada uno con 'label'
        campo_tipo: 'settlement' o 'stress'
        output_file: Archivo PNG de salida
        titulo: Título de la gráfica
        xlabel: Etiqueta del eje X con unidades
        ylabel: Etiqueta del eje Y (profundidad)
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Colores y estilos profesionales para cada ubicación
    colores = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e']  # Rojo, azul, verde, naranja
    markers = ['o', 's', '^', 'D']  # Círculo, cuadrado, triángulo, diamante
    linestyles = ['-', '--', '-.', ':']

    # Graficar cada perfil
    for i, perfil in enumerate(perfiles):
        z_data = perfil['z']
        values = perfil[campo_tipo]
        label = perfil['label']

        ax.plot(values, z_data,
               color=colores[i],
               marker=markers[i],
               markersize=6,
               linewidth=2.5,
               linestyle=linestyles[i],
               label=label,
               markevery=3,  # Mostrar marcador cada 3 puntos para claridad
               alpha=0.9)

    # Agregar línea horizontal en Df (profundidad de desplante)
    import config
    Df = config.ZAPATA['Df']
    ax.axhline(y=-Df, color='black', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(ax.get_xlim()[1] * 0.95, -Df, f'  Df = {Df:.1f} m',
           verticalalignment='bottom', horizontalalignment='right',
           fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                    edgecolor='black', alpha=0.8))

    # Configuración de ejes
    ax.set_xlabel(xlabel, fontsize=16, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=16, fontweight='bold')
    ax.set_title(titulo, fontsize=18, fontweight='bold', pad=20)

    # Grid profesional
    ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.3, color='gray')
    ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.2, color='gray')
    ax.minorticks_on()

    # Leyenda profesional
    ax.legend(loc='best', fontsize=13, frameon=True, shadow=True,
             fancybox=True, framealpha=0.95, edgecolor='black')

    # Configuración de ticks
    ax.tick_params(axis='both', which='major', labelsize=13, width=1.5, length=6)
    ax.tick_params(axis='both', which='minor', width=1, length=3)

    # Formato de números en ejes
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.1f}'))

    # Borde del gráfico
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor('black')

    # Ajustar layout
    plt.tight_layout()

    # Guardar con alta resolución
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✓ Gráfica científica guardada: {output_file}")


def crear_grafica_carga_desplazamiento(csv_file, output_file):
    """
    Crea gráfica de carga vs desplazamiento incremental (sin gravedad) desde CSV.

    Args:
        csv_file: Archivo CSV con datos de carga vs desplazamiento
        output_file: Archivo PNG de salida
    """
    import csv

    fig, ax = plt.subplots(figsize=(10, 8))

    # Leer datos del CSV
    cargas = []
    asentamientos = []

    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cargas.append(float(row['Carga_kN']))
                # Convertir a positivo (asentamiento hacia abajo = positivo)
                asentamientos.append(abs(float(row['Desplazamiento_incremental_mm'])))

        print(f"✓ Datos leídos desde {csv_file}: {len(cargas)} puntos")
    except FileNotFoundError:
        print(f"⚠️  Archivo {csv_file} no encontrado. Creando gráfico vacío.")
        cargas = [0, 1000]
        asentamientos = [0, 50]

    # Graficar puntos y línea (EJES INTERCAMBIADOS: X=asentamiento, Y=carga)
    ax.plot(asentamientos, cargas,
            marker='o',
            markersize=10,
            linewidth=3.0,
            color='#d62728',  # Rojo
            linestyle='-',
            label='Curva Carga-Asentamiento Incremental',
            markerfacecolor='#d62728',
            markeredgecolor='black',
            markeredgewidth=2,
            alpha=0.9)

    # Agregar etiqueta profesional en el último punto
    if len(cargas) > 0:
        ultimo_asentamiento = asentamientos[-1]
        ultima_carga = cargas[-1]

        # Etiqueta en el último punto (ubicación inteligente para no tapar)
        ax.annotate(
            f'Final:\nP = {ultima_carga:.1f} kN\ns = {ultimo_asentamiento:.2f} mm',
            xy=(ultimo_asentamiento, ultima_carga),
            xytext=(15, -40),  # Offset hacia abajo-derecha
            textcoords='offset points',
            fontsize=13,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.6',
                     facecolor='lightyellow',
                     alpha=0.9,
                     edgecolor='black',
                     linewidth=2),
            ha='left',
            va='top'
        )

    # Calcular y mostrar rigidez (stiffness) como pendiente promedio
    if len(cargas) > 1 and asentamientos[-1] - asentamientos[0] > 0:
        delta_carga = cargas[-1] - cargas[0]
        delta_asentamiento = asentamientos[-1] - asentamientos[0]
        rigidez = delta_carga / delta_asentamiento  # kN/mm

        # Agregar texto con rigidez y número de pasos
        ax.text(0.05, 0.95,
               f'Pasos de carga: {len(cargas)}\n'
               f'Rigidez promedio (k): {rigidez:.2f} kN/mm\n'
               f'Δs/ΔP: {1/rigidez:.4f} mm/kN',
               transform=ax.transAxes,
               fontsize=14,
               verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.7',
                       facecolor='lightblue',
                       alpha=0.85,
                       edgecolor='black',
                       linewidth=1.5))

    # Configuración de ejes (INTERCAMBIADOS)
    ax.set_xlabel('Asentamiento Incremental (mm)', fontsize=18, fontweight='bold')
    ax.set_ylabel('Carga de Columna (kN)', fontsize=18, fontweight='bold')
    ax.set_title('Curva Carga-Asentamiento Incremental\nCentro de Zapata (Sin Gravedad)',
                fontsize=20, fontweight='bold', pad=20)

    # Grid profesional
    ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.3, color='gray')
    ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.2, color='gray')
    ax.minorticks_on()

    # Leyenda
    ax.legend(loc='lower right', fontsize=15, frameon=True, shadow=True,
             fancybox=True, framealpha=0.95, edgecolor='black')

    # Configuración de ticks
    ax.tick_params(axis='both', which='major', labelsize=15, width=1.5, length=6)
    ax.tick_params(axis='both', which='minor', width=1, length=3)

    # Establecer límites con margen (EJES INTERCAMBIADOS)
    if len(cargas) > 0:
        # X = asentamiento
        x_min = min(asentamientos)
        x_max = max(asentamientos)
        x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 1

        # Y = carga
        y_margin = max(cargas) * 0.05 if max(cargas) > 0 else 10

        ax.set_xlim([x_min - x_margin, x_max + x_margin])
        ax.set_ylim([-y_margin, max(cargas) + y_margin])

    # Borde del gráfico
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor('black')

    # Ajustar layout
    plt.tight_layout()

    # Guardar con alta resolución
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✓ Gráfica de carga-asentamiento guardada: {output_file}")
    if len(cargas) > 0:
        print(f"  Rango de asentamiento: {asentamientos[0]:.3f} → {asentamientos[-1]:.3f} mm (horizontal)")
        print(f"  Rango de carga: 0 → {cargas[-1]:.1f} kN (vertical)")


def crear_pdf_multipagina(imagenes, output_pdf, configuracion):
    """
    Crea un PDF multipágina profesional con las imágenes generadas.

    Args:
        imagenes: Lista de tuplas (archivo_imagen, título, descripción)
        output_pdf: Nombre del archivo PDF de salida
        configuracion: Diccionario con parámetros del modelo
    """
    with PdfPages(output_pdf) as pdf:
        # Página 1: Portada Profesional
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Encabezado principal
        fig.text(0.5, 0.88, 'ANÁLISIS DE ELEMENTOS FINITOS',
                ha='center', fontsize=32, fontweight='bold', color='#1f4788')

        # Nombre de la estructura
        fig.text(0.5, 0.81, configuracion.get('nombre_estructura', ''),
                ha='center', fontsize=24, fontweight='bold', color='#d62728')

        fig.text(0.5, 0.75, 'Zapata de Concreto sobre Estratos de Suelo',
                ha='center', fontsize=18, fontweight='normal', color='#2c5aa0')

        # Línea decorativa
        fig.text(0.5, 0.70, '━' * 60,
                ha='center', fontsize=12, color='#1f4788')

        # Información del proyecto en secciones
        info_zapata = f"""GEOMETRÍA DE LA ZAPATA
Dimensiones: {configuracion['B']}m × {configuracion['L']}m × {configuracion['h']}m
Profundidad de desplante: {configuracion['Df']}m
Material: Concreto E={configuracion['E_zapata']/1e9:.0f} GPa"""

        info_suelo = f"""ESTRATIFICACIÓN DEL SUELO
{chr(10).join([f"{e['nombre']}: h={e['espesor']}m, E={e['E']/1e6:.0f} MPa" for e in configuracion['estratos']])}"""

        info_analisis = f"""ANÁLISIS Y CARGAS
Tipo de análisis: 2 Fases (Gravedad + Carga Incremental)
Carga de columna: {configuracion['P_column']:.0f} kN
Modelo: 1/4 con condiciones de simetría
Elemento: Tetraédrico lineal (FourNodeTetrahedron)"""

        # Colocar información en bloques
        fig.text(0.5, 0.57, info_zapata,
                ha='center', va='top',
                fontsize=13, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#e8f4f8',
                         edgecolor='#1f4788', linewidth=1.5))

        fig.text(0.5, 0.39, info_suelo,
                ha='center', va='top',
                fontsize=13, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#f0f8e8',
                         edgecolor='#2c5aa0', linewidth=1.5))

        fig.text(0.5, 0.19, info_analisis,
                ha='center', va='top',
                fontsize=13, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#fff8e8',
                         edgecolor='#1f4788', linewidth=1.5))

        # Pie de página
        fig.text(0.5, 0.05, f'Fecha: {datetime.now().strftime("%d de %B de %Y")}',
                ha='center', fontsize=11, style='italic', color='#555555')

        pdf.savefig(fig, bbox_inches='tight', dpi=300)
        plt.close()

        # Páginas con imágenes
        for img_file, titulo, descripcion in imagenes:
            try:
                img = plt.imread(img_file)

                fig, ax = plt.subplots(figsize=(11, 8.5))
                ax.imshow(img)
                ax.axis('off')

                # Título en la parte superior (aumentado)
                fig.suptitle(titulo, fontsize=20, fontweight='bold', y=0.98)

                # Descripción en la parte inferior (aumentada)
                if descripcion:
                    fig.text(0.5, 0.02, descripcion,
                            ha='center', fontsize=13, style='italic')

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
    vtu_file = "resultados_2phases_v1_1.vtu"

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

    # 1. Vista del modelo por materiales (estratificación)
    print("\n1. Generando vista de estratificación por materiales...")
    img_modelo = 'visualizaciones/modelo_estratificacion.png'
    crear_vista_modelo(mesh, img_modelo,
                      titulo="Modelo FEM - Estratificación del Suelo")
    imagenes_generadas.append((
        img_modelo,
        "Estratificación del Modelo",
        "Vista isométrica mostrando los estratos de suelo y zapata de concreto"
    ))

    # 2. Asentamientos por carga (Fase 2) - CON BORDES NEGROS DE ZAPATA
    if 'Settlement_carga_mm' in mesh.point_data:
        print("\n2. Generando vista de asentamientos por carga (zapata con bordes negros)...")
        img_carga = 'visualizaciones/desplazamientos_carga.png'
        crear_vista_desplazamientos_con_bordes(
            mesh,
            'Settlement_carga_mm',
            img_carga,
            titulo="Asentamientos por Carga de Columna (Fase 2)",
            unidades="mm",
            cmap='coolwarm'
        )
        imagenes_generadas.append((
            img_carga,
            "Fase 2: Asentamientos por Carga de Columna",
            "Desplazamientos adicionales inducidos por la carga de 250 kN (zapata: bordes negros)"
        ))
    else:
        print("⚠️  Campo 'Settlement_carga_mm' no encontrado en los datos")
        return

    # 3. Tensiones verticales por gravedad (Fase 1)
    if 'Sigma_v_gravedad_kPa' in mesh.cell_data:
        print("\n3. Generando vista de tensiones verticales por gravedad...")
        img_sigma_grav = 'visualizaciones/tensiones_gravedad.png'
        crear_vista_tensiones(
            mesh,
            'Sigma_v_gravedad_kPa',
            img_sigma_grav,
            titulo="Tensiones Verticales σv - Fase 1: Gravedad",
            unidades="kPa",
            cmap='RdBu_r'
        )
        imagenes_generadas.append((
            img_sigma_grav,
            "Fase 1: Tensiones Verticales por Gravedad",
            "Campo de tensiones verticales σv generado por peso propio del suelo y zapata"
        ))

    # 4. BULBO DE PRESIONES (sin zapata, solo bordes rojos)
    if 'Sigma_v_carga_kPa' in mesh.cell_data:
        print("\n4. Generando vista del bulbo de presiones (sin zapata)...")
        img_bulbo = 'visualizaciones/bulbo_presiones.png'
        crear_vista_bulbo_sin_zapata(
            mesh,
            'Sigma_v_carga_kPa',
            img_bulbo,
            titulo="Bulbo de Presiones σv - Solo Suelo (Bordes de Zapata en Rojo)",
            unidades="kPa",
            cmap='RdBu_r',
            clim=[-300, 0]
        )
        imagenes_generadas.append((
            img_bulbo,
            "Bulbo de Presiones en el Suelo",
            "Distribución de tensiones verticales σv en el suelo por carga de columna (zapata: bordes rojos)"
        ))

    # 5. PERFILES VERTICALES - Asentamientos
    print("\n5. Generando perfiles verticales de asentamientos...")

    # Definir ubicaciones de interés (modelo 1/4)
    # B = 2.0m, L = 3.0m en el modelo completo
    # B/2 = 1.0m, L/2 = 1.5m en el modelo 1/4
    B_cuarto = config.ZAPATA['B'] / 2  # 1.0m
    L_cuarto = config.ZAPATA['L'] / 2  # 1.5m

    ubicaciones = [
        {'x': B_cuarto/2, 'y': L_cuarto/2, 'label': 'Centro Zapata'},
        {'x': 0.0, 'y': 0.0, 'label': 'Esquina (0, 0)'},
        {'x': B_cuarto, 'y': 0.0, 'label': f'Esquina ({B_cuarto:.1f}, 0)'},
        {'x': 0.0, 'y': L_cuarto, 'label': f'Esquina (0, {L_cuarto:.1f})'}
    ]

    # Calcular profundidad de inicio (desde -Df hacia abajo)
    Df = config.ZAPATA['Df']
    profundidad_total = sum(e['espesor'] for e in config.ESTRATOS_SUELO)

    # Extraer perfiles de asentamientos (desde -Df hacia abajo)
    perfiles_settlement = []
    for ubi in ubicaciones:
        perfil = extraer_perfil_vertical(
            mesh,
            ubi['x'],
            ubi['y'],
            campo_point='Settlement_carga_mm',
            z_min=-profundidad_total,
            z_max=-Df,
            n_levels=60
        )
        perfil['label'] = ubi['label']
        perfiles_settlement.append(perfil)
        print(f"  ✓ Perfil extraído en {ubi['label']}: ({ubi['x']:.2f}, {ubi['y']:.2f})")

    # Crear gráfica de asentamientos
    img_perfil_settlement = 'visualizaciones/perfil_asentamientos.png'
    crear_grafica_perfiles_cientifica(
        perfiles_settlement,
        campo_tipo='settlement',
        output_file=img_perfil_settlement,
        titulo='Perfiles Verticales de Asentamiento',
        xlabel='Asentamiento (mm)',
        ylabel='Profundidad (m)'
    )
    imagenes_generadas.append((
        img_perfil_settlement,
        "Perfiles Verticales de Asentamiento",
        "Variación del asentamiento con la profundidad en el centro y esquinas de la zapata"
    ))

    # 6. PERFILES VERTICALES - Tensiones Incrementales
    print("\n6. Generando perfiles verticales de tensiones incrementales...")

    # Extraer perfiles de tensiones (desde -Df hacia abajo)
    perfiles_stress = []
    for ubi in ubicaciones:
        perfil = extraer_perfil_vertical(
            mesh,
            ubi['x'],
            ubi['y'],
            campo_cell='Sigma_v_carga_kPa',
            z_min=-profundidad_total,
            z_max=-Df,
            n_levels=60
        )
        perfil['label'] = ubi['label']
        perfiles_stress.append(perfil)
        print(f"  ✓ Perfil extraído en {ubi['label']}: ({ubi['x']:.2f}, {ubi['y']:.2f})")

    # Crear gráfica de tensiones incrementales
    img_perfil_stress = 'visualizaciones/perfil_tensiones_incrementales.png'
    crear_grafica_perfiles_cientifica(
        perfiles_stress,
        campo_tipo='stress',
        output_file=img_perfil_stress,
        titulo='Perfiles Verticales de Tensiones Incrementales Δσv',
        xlabel='Tensión Incremental Δσv (kPa)',
        ylabel='Profundidad (m)'
    )
    imagenes_generadas.append((
        img_perfil_stress,
        "Perfiles Verticales de Tensiones Incrementales",
        "Variación de tensiones verticales incrementales Δσv con la profundidad"
    ))

    # 7. CURVA CARGA-ASENTAMIENTO INCREMENTAL (10 pasos)
    print("\n7. Generando curva carga-asentamiento incremental (10 pasos)...")

    # Archivo CSV con datos de carga vs desplazamiento
    csv_carga = 'carga_desplazamiento_pasos.csv'
    img_carga_asentamiento = 'visualizaciones/curva_carga_asentamiento.png'

    crear_grafica_carga_desplazamiento(
        csv_file=csv_carga,
        output_file=img_carga_asentamiento
    )
    imagenes_generadas.append((
        img_carga_asentamiento,
        "Curva Carga-Asentamiento Incremental",
        "Relación carga-desplazamiento incremental en 10 pasos (sin considerar gravedad)"
    ))

    # Preparar configuración para PDF
    configuracion = {
        'nombre_estructura': config.NOMBRE_ESTRUCTURA,
        'B': config.ZAPATA['B'],
        'L': config.ZAPATA['L'],
        'h': config.ZAPATA['h'],
        'Df': config.ZAPATA['Df'],
        'P_column': config.CARGAS['P_column'],
        'estratos': config.ESTRATOS_SUELO,
        'E_zapata': config.PROPIEDADES_ZAPATA['E']
    }

    # Crear PDF multipágina con portada
    print("\n3. Generando PDF multipágina con portada profesional...")
    crear_pdf_multipagina(
        imagenes_generadas,
        'Reporte_Analisis_FEM.pdf',
        configuracion
    )

    # También crear PDFs individuales
    print("\n4. Generando PDFs individuales...")
    for img_file, titulo, descripcion in imagenes_generadas:
        pdf_individual = img_file.replace('.png', '.pdf')
        with PdfPages(pdf_individual) as pdf:
            img = plt.imread(img_file)
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.imshow(img)
            ax.axis('off')
            fig.suptitle(titulo, fontsize=18, fontweight='bold')
            # Agregar descripción
            fig.text(0.5, 0.02, descripcion, ha='center', fontsize=12, style='italic')
            pdf.savefig(fig, bbox_inches='tight', dpi=300)
            plt.close()
        print(f"  ✓ {pdf_individual}")

    print("\n" + "="*80)
    print("VISUALIZACIONES COMPLETADAS")
    print("="*80)
    print("\nArchivos generados:")
    print(f"  • Reporte_Analisis_FEM.pdf (PDF multipágina con 8 páginas)")
    print(f"\n  PDFs individuales:")
    print(f"  • visualizaciones/modelo_estratificacion.pdf")
    print(f"  • visualizaciones/desplazamientos_carga.pdf")
    print(f"  • visualizaciones/tensiones_gravedad.pdf")
    print(f"  • visualizaciones/bulbo_presiones.pdf")
    print(f"  • visualizaciones/perfil_asentamientos.pdf")
    print(f"  • visualizaciones/perfil_tensiones_incrementales.pdf")
    print(f"  • visualizaciones/curva_carga_asentamiento.pdf")
    print(f"\n  Imágenes PNG de alta resolución (300 DPI):")
    print(f"  • {len(imagenes_generadas)} archivos en visualizaciones/")
    print("\nContenido del reporte:")
    print("  • Página 1: Portada profesional con información del modelo")
    print("  • Página 2: Estratificación del modelo")
    print("  • Página 3: Asentamientos por carga (zapata: bordes negros)")
    print("  • Página 4: Tensiones verticales σv por gravedad")
    print("  • Página 5: Bulbo de presiones σv (zapata: bordes rojos)")
    print("  • Página 6: Perfiles verticales de asentamiento")
    print("  • Página 7: Perfiles verticales de tensiones incrementales Δσv")
    print("  • Página 8: Curva carga-asentamiento incremental (10 pasos)")
    print("\nCaracterísticas:")
    print("  • Zapata en asentamientos: solo bordes negros (sin elementos de malla)")
    print("  • Zapata en bulbo: solo bordes rojos (sin volumen)")
    print("  • Escala bulbo ajustada: [-300, 0] kPa para resaltar distribución")
    print("  • Perfiles científicos: 4 ubicaciones (centro + 3 esquinas)")
    print("  • Curva carga-asentamiento: 10 pasos incrementales sin gravedad")
    print("  • Rigidez promedio k (kN/mm) calculada desde datos incrementales")
    print("  • Gráficas con grid, leyenda profesional, y formato científico")
    print("  • Textos aumentados: Títulos 24pt, Info 16pt")
    print("  • Leyenda: 22pt título, 18pt etiquetas")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
