#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lanzador del empaquetado del cliente (Weapon Detection System).

Este script tenia su propio generador de .spec, pero ese .spec no incluia dos
cosas que el empaquetado necesita de verdad:

  1. sys.setrecursionlimit(...): sin esto PyInstaller aborta mientras analiza
     torch y ultralytics con "RecursionError: maximum recursion depth exceeded".
  2. La copia de las DLL de Intel MKL (mkl_core, mkl_avx*, mkl_vml_*,
     libiomp5md): sin ellas el .exe llega a compilarse, pero al arrancar
     revienta con 0xc06d007e porque torch_cpu.dll no encuentra sus dependencias.

Las dos correcciones ya viven en build_exe_fixed.py. Para no mantener dos
generadores que se van separando con el tiempo, este archivo delega en aquel:

    python build_exe.py         ->  llama a build_exe_fixed.py
    python build_exe_fixed.py   ->  equivalente, llamada directa
"""

import os
import runpy
import sys

DESTINO = 'build_exe_fixed.py'

if __name__ == '__main__':
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(aqui, DESTINO)

    if not os.path.isfile(destino):
        sys.stderr.write(
            "ERROR: no se encontro %s junto a este script.\n"
            "Ese archivo contiene el empaquetado corregido.\n" % DESTINO
        )
        sys.exit(2)

    print("=" * 60)
    print("build_exe.py delega en %s (empaquetado corregido)" % DESTINO)
    print("=" * 60)

    os.chdir(aqui)
    runpy.run_path(destino, run_name='__main__')
