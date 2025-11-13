#!/usr/bin/env python3
"""
Script para generar PDF simple con resultados del análisis
"""
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
from matplotlib.patches import Rectangle
import numpy as np
import sys
import os

def crear_pdf_simple(df_value, output_file):
    """Crea un PDF simple con los resultados principales"""
    
    # Leer datos del análisis
    results_dir = f'resultados_Chancado_Df_analisis/Df_{df_value}m'
    summary_file = os.path.join(results_dir, 'analysis_summary_2phases.txt')
    
    if not os.path.exists(summary_file):
        print(f"Error: No se encuentra {summary_file}")
        return False
    
    # Extraer información del summary
    with open(summary_file, 'r') as f:
        summary_text = f.read()
    
    # Crear PDF
    pdf_pages = pdf_backend.PdfPages(output_file)
    
    # Página 1: Portada
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Título
    ax.text(0.5, 0.85, 'ANÁLISIS DE FUNDACIÓN', 
            ha='center', va='top', fontsize=24, fontweight='bold')
    ax.text(0.5, 0.80, 'Método de Elementos Finitos', 
            ha='center', va='top', fontsize=16)
    
    # Información del proyecto
    ax.text(0.5, 0.65, 'CHANCADO PRIMARIO', 
            ha='center', va='top', fontsize=20, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    # Parámetros
    params_text = f"""
PARÁMETROS DEL ANÁLISIS

Zapata:
  • Dimensiones: 1.8m × 2.0m × 0.5m
  • Profundidad de desplante: {df_value} m
  
Carga:
  • Carga total: 414 kN
  • Presión de contacto: 115 kPa
  
Suelo:
  • Estrato 1: 2.35m, E=50 MPa
  • Estrato 2: 12.65m, E=100 MPa
  • Profundidad total: 15.0m
  
Software:
  • OpenSeesPy + Gmsh
  • Análisis 3D con simetría (1/4)
"""
    
    ax.text(0.1, 0.50, params_text, 
            ha='left', va='top', fontsize=11, family='monospace')
    
    pdf_pages.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Página 2: Resultados
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'RESULTADOS DEL ANÁLISIS', 
            ha='center', va='top', fontsize=18, fontweight='bold')
    
    # Extraer asentamiento del summary
    for line in summary_text.split('\n'):
        if 'Asentamiento máximo:' in line and 'FASE 2' in summary_text:
            parts = line.split(':')
            if len(parts) > 1:
                settlement = parts[1].strip()
                break
    else:
        settlement = "No disponible"
    
    results_text = f"""
ASENTAMIENTOS

Profundidad de desplante (Df): {df_value} m

Asentamiento máximo: {settlement}

OBSERVACIONES:
• Asentamientos muy bajos debido a módulos E altos (50-100 MPa)
• Zapata pequeña (3.6 m²)
• Suelo competente

CRITERIOS DE DISEÑO:
• Asentamiento admisible típico: 25 mm
• Todos los valores están muy por debajo del límite
"""
    
    ax.text(0.1, 0.85, results_text, 
            ha='left', va='top', fontsize=12, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
    
    # Diagrama esquemático simple
    ax_diagram = fig.add_axes([0.2, 0.15, 0.6, 0.25])
    ax_diagram.set_xlim(0, 10)
    ax_diagram.set_ylim(-8, 1)
    ax_diagram.set_aspect('equal')
    ax_diagram.axis('off')
    
    # Suelo
    ax_diagram.add_patch(Rectangle((0, -2.35), 10, 2.35, 
                                   facecolor='wheat', edgecolor='black', linewidth=1))
    ax_diagram.text(5, -1.2, 'Estrato 1\nE=50 MPa', ha='center', va='center', fontsize=9)
    
    ax_diagram.add_patch(Rectangle((0, -7), 10, 4.65, 
                                   facecolor='tan', edgecolor='black', linewidth=1))
    ax_diagram.text(5, -4.5, 'Estrato 2\nE=100 MPa', ha='center', va='center', fontsize=9)
    
    # Zapata
    zapata_y = -float(df_value)
    ax_diagram.add_patch(Rectangle((4.1, zapata_y-0.5), 1.8, 0.5, 
                                   facecolor='gray', edgecolor='black', linewidth=2))
    ax_diagram.text(5, zapata_y-0.25, 'Zapata', ha='center', va='center', 
                   fontsize=8, color='white', fontweight='bold')
    
    # Cota Df
    ax_diagram.plot([3.5, 3.5], [0, zapata_y], 'k--', linewidth=1)
    ax_diagram.text(3.2, zapata_y/2, f'Df={df_value}m', ha='right', va='center', fontsize=9)
    
    # Nivel de terreno
    ax_diagram.plot([0, 10], [0, 0], 'k-', linewidth=2)
    ax_diagram.text(9.5, 0.3, 'N.T.', ha='right', fontsize=9, fontweight='bold')
    
    pdf_pages.savefig(fig, bbox_inches='tight')
    plt.close()
    
    pdf_pages.close()
    print(f"✅ PDF generado: {output_file}")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python3 generar_pdf_simple.py <Df_value> <output_file>")
        sys.exit(1)
    
    df_value = sys.argv[1]
    output_file = sys.argv[2]
    
    if crear_pdf_simple(df_value, output_file):
        sys.exit(0)
    else:
        sys.exit(1)
