"""Quellen-Subkommando-Gruppen für ``rdc``.

Jede Quelle (Literatur, Varianten, Krankheits-Graph, Differentialdiagnose)
hängt sich über :func:`rdc.main.register` an die Top-Level-App und nutzt den
zentralen HTTP-Client, die SQLite-History und die Ausgabe-Helfer aus dem Kern.
"""
