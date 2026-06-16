"""Rhino-dependent helpers for Grasshopper SDK-mode (advanced) preview pipelines.

WARNING: This module imports RhinoCommon (Rhino.Geometry, Rhino.Display) and
System.Drawing.  It must NEVER be imported from unit tests or plain CPython
environments.  All Rhino imports are **deferred inside methods** so that
``import crc_modules.rhino.preview`` succeeds in a headless CPython process
(imports only fail the moment a method body actually executes).  pytest must
never call any method defined here.

Typical usage inside a GH SDK-mode Script component
----------------------------------------------------
::

    from crc_modules.rhino.preview import PreviewPayload

    class MyScript(GH_ScriptInstance):
        def RunScript(self, ...):
            self._payload = PreviewPayload()
            self._payload.add_curve(some_curve, color, width=2)
            self._payload.add_filled_curve(closed_crv, fill_color)
            self._payload.add_text("Label", pt, 0.5, text_color)

        def DrawViewportWires(self, args):
            if self._payload:
                self._payload.draw_wires(args)

        def DrawViewportMeshes(self, args):
            if self._payload:
                self._payload.draw_meshes(args)

        def get_ClippingBox(self):
            if self._payload:
                return self._payload.clipping_box
            import Rhino.Geometry as rg  # noqa: PLC0415
            return rg.BoundingBox.Empty
"""

from __future__ import annotations


class PreviewPayload:
    """Accumulator for Grasshopper viewport-preview geometry.

    Collects curves, filled regions (planar meshes), pre-colored meshes, and
    3-D text annotations.  Call ``draw_wires`` / ``draw_meshes`` from the
    component's ``DrawViewportWires`` / ``DrawViewportMeshes`` overrides, and
    return ``clipping_box`` from ``get_ClippingBox``.

    All ``add_*`` methods are silent on invalid input (None guards) so callers
    do not have to pre-validate geometry before handing it to the payload.
    """

    def __init__(self) -> None:
        # (curve, System.Drawing.Color, int)
        self._curves: list = []
        # Rhino.Geometry.Mesh (vertex-colored)
        self._meshes: list = []
        # (Rhino.Display.Text3d, System.Drawing.Color)
        self._texts: list = []
        # Rhino.Geometry.BoundingBox | None  — lazily initialised
        self._bbox = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _union_bbox(self, other_bbox) -> None:
        """Merge *other_bbox* into the accumulated union bounding box."""
        if not other_bbox.IsValid:
            return
        if self._bbox is None:
            self._bbox = other_bbox
        else:
            self._bbox.Union(other_bbox)

    # ------------------------------------------------------------------
    # Public add_* API
    # ------------------------------------------------------------------

    def add_curve(self, curve, color, width: int = 1) -> None:
        """Store a wire curve to draw in ``DrawViewportWires``.

        Parameters
        ----------
        curve:
            A ``Rhino.Geometry.Curve`` instance.
        color:
            A ``System.Drawing.Color`` value.
        width:
            Line width in pixels (default 1).
        """
        if curve is None or color is None:
            return
        self._curves.append((curve, color, int(width)))
        try:
            self._union_bbox(curve.GetBoundingBox(False))
        except Exception:
            pass

    def add_filled_curve(self, closed_curve, fill_color) -> None:
        """Build a planar mesh from a closed curve and store it for mesh drawing.

        Uses ``Rhino.Geometry.Mesh.CreateFromPlanarBoundary`` with
        ``MeshingParameters.Default``.  Non-planar or open curves are skipped
        silently (``CreateFromPlanarBoundary`` returns ``None`` for those).
        Every vertex is colored with *fill_color*.

        Parameters
        ----------
        closed_curve:
            A closed ``Rhino.Geometry.Curve``.
        fill_color:
            A ``System.Drawing.Color`` value applied to all mesh vertices.
        """
        if closed_curve is None or fill_color is None:
            return

        import Rhino  # noqa: PLC0415 — deferred Rhino import
        import Rhino.Geometry as rg  # noqa: PLC0415 — deferred Rhino import

        try:
            tolerance = 0.001
            try:
                tolerance = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
            except Exception:
                pass

            mesh = rg.Mesh.CreateFromPlanarBoundary(
                closed_curve,
                rg.MeshingParameters.Default,
                tolerance,
            )
            if mesh is None:
                return

            for i in range(mesh.Vertices.Count):
                mesh.VertexColors.Add(fill_color)

            self._meshes.append(mesh)
            self._union_bbox(mesh.GetBoundingBox(False))
        except Exception:
            pass

    def add_mesh(self, mesh) -> None:
        """Store an already-vertex-colored mesh (e.g. a legend mesh).

        Parameters
        ----------
        mesh:
            A ``Rhino.Geometry.Mesh`` with vertex colors already applied.
        """
        if mesh is None:
            return
        self._meshes.append(mesh)
        try:
            self._union_bbox(mesh.GetBoundingBox(False))
        except Exception:
            pass

    def add_text(
        self,
        text,
        point_or_plane,
        height: float,
        color,
        h_align=None,
        v_align=None,
    ) -> None:
        """Build and store a ``Rhino.Display.Text3d`` annotation.

        Parameters
        ----------
        text:
            String content.  Empty strings and ``None`` are skipped.
        point_or_plane:
            Either a ``Rhino.Geometry.Plane`` or a ``Rhino.Geometry.Point3d``.
            Duck-typed: objects with ``.Origin`` and ``.XAxis`` are treated as
            planes; objects with ``.X`` / ``.Y`` / ``.Z`` are treated as points
            and promoted to a world-XY-aligned plane at that location.
        height:
            Text height in model units.
        color:
            A ``System.Drawing.Color`` value.
        h_align:
            Optional ``Rhino.DocObjects.TextHorizontalAlignment`` enum value.
        v_align:
            Optional ``Rhino.DocObjects.TextVerticalAlignment`` enum value.
        """
        if not text or color is None:
            return
        text_str = str(text)
        if not text_str.strip():
            return

        import Rhino.Geometry as rg  # noqa: PLC0415 — deferred Rhino import
        import Rhino.Display as rd  # noqa: PLC0415 — deferred Rhino import

        try:
            # Resolve plane from point_or_plane
            if hasattr(point_or_plane, "Origin") and hasattr(point_or_plane, "XAxis"):
                plane = point_or_plane
            elif hasattr(point_or_plane, "X") and hasattr(point_or_plane, "Y") and hasattr(point_or_plane, "Z"):
                pt = rg.Point3d(point_or_plane.X, point_or_plane.Y, point_or_plane.Z)
                plane = rg.Plane(pt, rg.Vector3d.ZAxis)
            else:
                return

            text3d = rd.Text3d(text_str, plane, float(height))

            if h_align is not None:
                text3d.HorizontalAlignment = h_align
            if v_align is not None:
                text3d.VerticalAlignment = v_align

            self._texts.append((text3d, color))

            try:
                # Text3d.BoundingBox is a property (a BoundingBox struct), not a method.
                self._union_bbox(text3d.BoundingBox)
            except Exception:
                pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Draw methods — call from GH DrawViewport* overrides
    # ------------------------------------------------------------------

    def draw_wires(self, args) -> None:
        """Draw all stored curves and text annotations.

        Call from ``DrawViewportWires(self, args)``.  Each item is drawn
        inside its own try/except so one bad entry never kills the pipeline.

        Parameters
        ----------
        args:
            The ``IGH_PreviewArgs`` passed to ``DrawViewportWires``.
        """
        for item in self._curves:
            try:
                curve, color, width = item
                args.Display.DrawCurve(curve, color, int(width))
            except Exception:
                pass

        for item in self._texts:
            try:
                text3d, color = item
                args.Display.Draw3dText(text3d, color)
            except Exception:
                pass

    def draw_meshes(self, args) -> None:
        """Draw all stored vertex-colored meshes using false-colour rendering.

        Call from ``DrawViewportMeshes(self, args)``.  Each mesh is rendered
        with ``DrawMeshFalseColors`` so per-vertex colours are respected.

        Parameters
        ----------
        args:
            The ``IGH_PreviewArgs`` passed to ``DrawViewportMeshes``.
        """
        for mesh in self._meshes:
            try:
                args.Display.DrawMeshFalseColors(mesh)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Clipping box
    # ------------------------------------------------------------------

    @property
    def clipping_box(self):
        """Return the accumulated union ``Rhino.Geometry.BoundingBox``.

        Returns ``Rhino.Geometry.BoundingBox.Empty`` when nothing has been
        added yet, matching the expected return type for ``get_ClippingBox``.
        """
        import Rhino.Geometry as rg  # noqa: PLC0415 — deferred Rhino import

        if self._bbox is None:
            return rg.BoundingBox.Empty
        return self._bbox


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def color_to_hex(color) -> str | None:
    """Convert a ``System.Drawing.Color`` to an ``"#RRGGBB"`` hex string.

    Parameters
    ----------
    color:
        A ``System.Drawing.Color`` instance, or ``None``.

    Returns
    -------
    str or None
        Uppercase hex string such as ``"#FF8800"``, or ``None`` if *color* is
        ``None``.

    Notes
    -----
    No Rhino import is needed here; ``System.Drawing.Color`` is a .NET BCL
    type available whenever pythonnet is active.  The method is still defined
    at module level so callers can import it without instantiating a payload.
    """
    if color is None:
        return None
    # If the object is a GH_Colour goo it has no .R — fall back to .Value
    # which is the underlying System.Drawing.Color.
    if not hasattr(color, "R"):
        color = color.Value
    return "#%02X%02X%02X" % (color.R, color.G, color.B)
