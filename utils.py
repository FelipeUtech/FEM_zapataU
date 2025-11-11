#!/usr/bin/env python3
"""
Utilidades para análisis de zapatas con OpenSeesPy.
"""

import openseespy.opensees as ops
import pandas as pd
import numpy as np


def extraer_asentamientos(node_coords):
    """
    Extrae los asentamientos de todos los nodos del modelo.

    Args:
        node_coords: Diccionario {node_id: np.array([x, y, z])}

    Returns:
        DataFrame con columnas: X, Y, Z, Settlement_mm
    """
    data = []

    for node_id, coords in node_coords.items():
        # Obtener desplazamientos del nodo
        disp = ops.nodeDisp(node_id)

        # Asentamiento = desplazamiento en Z (negativo porque hacia abajo)
        settlement_mm = -disp[2] * 1000.0  # Convertir a mm

        data.append({
            'X': coords[0],
            'Y': coords[1],
            'Z': coords[2],
            'Settlement_mm': settlement_mm
        })

    return pd.DataFrame(data)
