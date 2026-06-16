"""Rhino-dependent submodules for Carcara.

Everything under ``crc_modules.rhino`` imports Rhino / Eto / scriptcontext and
runs ONLY inside Rhino 8's Grasshopper Python 3 environment. These modules are
intentionally OUTSIDE the pure-Python contract that the rest of ``crc_modules/``
follows, and they are excluded from pytest (they cannot be imported without a
running Rhino). Do not import this package from unit tests or from any code
that must run in plain CPython.
"""
