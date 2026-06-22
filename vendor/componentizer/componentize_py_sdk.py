"""Build SDK-mode (viewport-preview) Python Script components as .ghuser.

This module builds a **Rhino 8 Script component** (.ghuser) running **CPython
SDK / advanced mode** — a ``ghpythonlib.componentbase.executingcomponent``
subclass that overrides ``DrawViewportWires`` / ``get_ClippingBox`` to draw a
custom Rhino-viewport preview.

WHY A SEPARATE BUILDER
----------------------
``componentize_cpy.py`` emits the **old GHPython script schema** (LanguageSpec
Taxon ``*.*.python`` / Version ``3.-1``, minimal chunk set). That schema runs the
script procedurally and never wires the SDK preview overrides into Rhino's host
preview pipeline — which is why an earlier Python SDK port appeared "not to
register" and CurveDisplay was rebuilt in C# (see ``componentize_cs.py``).

The fix (verified by decoding a working hand-made ghuser) is the **new Rhino 8
Script-component schema**: same component BaseID ``c9b2d725-…`` but LanguageSpec
Taxon ``mcneel.pythonnet.python`` / Version ``3.9.10`` plus the fuller chunk set
(``ScriptComponentVersion=3``, ``Marsh{Guids,Inputs,Outputs}``,
``UsingScriptOutputParam``, ``ScriptParameterVersion=2``, per-param
``ConverterData``). This is the SAME archive structure ``componentize_cs.py``
already builds for C# — only the LanguageSpec and the embedded source language
differ. This module is therefore a near-clone of ``componentize_cs.py``.

DECODED REFERENCE (carcara-old/carcara/test-displaycurve.ghuser)
----------------------------------------------------------------
Root "UserObject": BaseID c9b2d725-… / Name / NickName / Category / SubCategory /
  Exposure / InstanceGuid / Icon / Object(→inner).
Inner "UserObject": Description / GraftStandardOutputLines=true / IconOverride /
  InstanceGuid / Marsh{Guids,Inputs,Outputs}=false / Name / NickName /
  ScriptComponentVersion=3 / Tooltip / Using{Library,Script}InputParam /
  UsingScriptOutputParam / UsingStandardOutputParam (all false).
  ParameterData: InputCount / InputId[..] / OutputCount / OutputId[..] /
    InputParam[i]: AllowTreeAccess / Description / InstanceGuid / Name / NickName /
      Optional / ScriptParamAccess / ScriptParameterVersion=2 / ShowTypeHints /
      SourceCount / ToolTip / TypeHintID / ConverterData(AssemblyName + TypeName).
  Script: Marsh{Guids,Inputs,Outputs}=false / Text(BASE64 UTF-8) / Title /
    LanguageSpec(Taxon="mcneel.pythonnet.python", Version="3.9.10").

Public API
----------
create_python_sdk_ghuser(source, target, version=None, prefix=None)
    Build <Name>.ghuser from a bundle with ``code.py`` (SDK class), ``metadata.json``
    (``ghpython.isAdvancedMode`` true), and ``icon.png``.
"""

import base64
import json
import os
from datetime import datetime


# Rhino 8 Script component BaseID (same GUID componentize_cpy uses; the new
# schema + LanguageSpec is what selects SDK mode, not the BaseID).
PY_SCRIPT_COMPONENT_GUID_STR = "c9b2d725-6f87-4b07-af90-bd9aefef68eb"
PY_TAXON = "mcneel.pythonnet.python"
PY_VERSION = "3.9.10"

# typeHintID alias/GUID -> GHPython internal type GUID.
_TYPES_MAP = dict(
    none="6a184b65-baa3-42d1-a548-3915b401de53",
    ghdoc="1c282eeb-dd16-439f-94e4-7d92b542fe8b",
    float="9d51e32e-c038-4352-9554-f4137ca91b9a",
    bool="d60527f5-b5af-4ef6-8970-5f96fe412559",
    int="48d01794-d3d8-4aef-990e-127168822244",
    complex="309690df-6229-4774-91bb-b1c9c0bfa54d",
    str="3aceb454-6dbd-4c5b-9b6b-e71f8c1cdf88",
    datetime="09bcf900-fe83-4efa-8d32-33d89f7a3e66",
    guid="5325b8e1-51d7-4d36-837a-d98394626c35",
    color="24b1d1a3-ab79-498c-9e44-c5b14607c4d3",
    colour="24b1d1a3-ab79-498c-9e44-c5b14607c4d3",  # British alias
    point="e1937b56-b1da-4c12-8bd8-e34ee81746ef",
    vector="15a50725-e3d3-4075-9f7c-142ba5f40747",
    plane="3897522d-58e9-4d60-b38c-978ddacfedd8",
    interval="589748aa-e558-4dd9-976f-78e3ab91fc77",
    uvinterval="74c906f3-db02-4cea-bd58-de375cb5ae73",
    box="f29cb021-de79-4e63-9f04-fc8e0df5f8b6",
    transform="c4b38e4c-21ff-415f-a0d1-406d282428dd",
    line="f802a8cd-e699-4a94-97ea-83b5406271de",
    circle="3c5409a1-3293-4181-a6fa-c24c37fc0c32",
    arc="9c80ec18-b48c-41b0-bc6e-cd93d9c916aa",
    polyline="66fa617b-e3e8-4480-9f1e-2c0688c1d21b",
    rectangle="83da014b-a550-4bf5-89ff-16e54225bd5d",
    curve="9ba89ec2-5315-435f-a621-b66c5fa2f301",
    mesh="794a1f9d-21d5-4379-b987-9e8bbf433912",
    surface="f4070a37-c822-410f-9057-100d2e22a22d",
    subd="20f4ca9c-6c90-4fd6-ba8a-5bf9ca79db08",
    brep="2ceb0405-fdfe-403d-a4d6-8786da45fb9d",
    pointcloud="d73c9fb0-365d-458f-9fb5-f4141399311f",
    geometrybase="c37956f4-d39c-49c7-af71-1e87f8031b26",
)

# typeHintID alias -> (AssemblyName, TypeName) for the per-param ConverterData
# sub-chunk (CLR type the host marshals the input to). Same assembly/type pairs
# proven by componentize_cs.py and the decoded reference ghuser. Anything not
# listed (ghdoc / none / unmapped) falls back to System.Object.
_CONVERTER_DATA = {
    "curve": ("RhinoCommon", "Rhino.Geometry.Curve"),
    "int": ("System.Private.CoreLib", "System.Int32"),
    "float": ("System.Private.CoreLib", "System.Double"),
    "bool": ("System.Private.CoreLib", "System.Boolean"),
    "str": ("System.Private.CoreLib", "System.String"),
    "color": ("System.Drawing.Primitives", "System.Drawing.Color"),
    "colour": ("System.Drawing.Primitives", "System.Drawing.Color"),
    "point": ("RhinoCommon", "Rhino.Geometry.Point3d"),
    "vector": ("RhinoCommon", "Rhino.Geometry.Vector3d"),
    "plane": ("RhinoCommon", "Rhino.Geometry.Plane"),
    "line": ("RhinoCommon", "Rhino.Geometry.Line"),
    "circle": ("RhinoCommon", "Rhino.Geometry.Circle"),
    "mesh": ("RhinoCommon", "Rhino.Geometry.Mesh"),
    "brep": ("RhinoCommon", "Rhino.Geometry.Brep"),
    "surface": ("RhinoCommon", "Rhino.Geometry.Surface"),
}
_CONVERTER_DEFAULT = ("System.Private.CoreLib", "System.Object")


def _replace_templates(code, version, name, ghuser_name, component_version=None, component_date=None):
    """Substitute componentizer template tokens in the source before embedding."""
    if version:
        code = code.replace("{{version}}", version)
    if component_version:
        code = code.replace("{{component_version}}", component_version)
    code = code.replace("{{name}}", name)
    code = code.replace("{{ghuser_name}}", ghuser_name)
    code = code.replace("{{date}}", component_date or datetime.now().strftime("%Y/%m/%d"))
    return code


def _bitmap_from_image_path(image_path):
    """Return a .NET System.Byte[] from a PNG file (via base64 round-trip)."""
    import System

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    return System.Convert.FromBase64String(img_b64)


def _parse_param_access(access):
    """Return int access code (0=item, 1=list, 2=tree)."""
    _map = {"item": 0, "list": 1, "tree": 2}
    try:
        return int(access)
    except (ValueError, TypeError):
        return _map.get(str(access).lower(), 0)


def _parse_type_hint_guid(type_hint_id):
    """Return System.Guid for the given type hint alias or GUID string."""
    import System

    guid_str = _TYPES_MAP.get(str(type_hint_id).lower(), type_hint_id)
    return System.Guid.Parse(guid_str)


def _converter_for(type_hint_id):
    """Return (AssemblyName, TypeName) for the param's ConverterData sub-chunk."""
    return _CONVERTER_DATA.get(str(type_hint_id).lower(), _CONVERTER_DEFAULT)


def create_python_sdk_ghuser(source: str, target: str,
                             version: "str | None" = None,
                             prefix: "str | None" = None) -> None:
    """Build <Name>.ghuser as a Rhino 8 CPython SDK-mode Script component.

    Reads ``code.py``, ``metadata.json``, ``icon.png`` from *source*. Writes a
    binary GH_Archive to *target* whose structure matches the decoded working
    reference (BaseID ``c9b2d725-…``, LanguageSpec ``mcneel.pythonnet.python`` /
    ``3.9.10``, ``ScriptComponentVersion=3``).

    Parameters
    ----------
    source:
        Path to the ``CRC_<Name>/`` bundle directory.
    target:
        Destination ``.ghuser`` file path.
    version:
        Substituted into ``{{version}}`` template tokens in ``code.py``.
    prefix:
        Optional name prefix (usually None).
    """
    import System
    import System.IO
    import System.Drawing
    from GH_IO.Serialization import GH_LooseChunk

    icon_path = os.path.join(source, "icon.png")
    code_path = os.path.join(source, "code.py")
    meta_path = os.path.join(source, "metadata.json")

    for p, label in [(icon_path, "icon.png"), (code_path, "code.py"),
                     (meta_path, "metadata.json")]:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"{label} missing from bundle: {source}")

    icon_bytes = _bitmap_from_image_path(icon_path)

    with open(code_path, "r", encoding="utf-8-sig") as f:
        py_source = f.read()

    with open(meta_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    prefix = prefix or ""
    name = data["name"]
    nickname = data.get("nickname", name)
    description = data.get("description", "")
    exposure = data.get("exposure", 2)
    category = data["category"]
    subcategory = data["subcategory"]

    instance_guid_str = data.get("instanceGuid")
    if instance_guid_str:
        instance_guid = System.Guid.Parse(instance_guid_str)
    else:
        instance_guid = System.Guid.NewGuid()

    py_component_guid = System.Guid.Parse(PY_SCRIPT_COMPONENT_GUID_STR)

    ghpython_data = data.get("ghpython", {})
    input_params = ghpython_data.get("inputParameters", [])
    output_params = ghpython_data.get("outputParameters", [])

    # Substitute template tokens, then BASE64-encode the source.
    component_version = data.get("componentVersion") or version
    component_date = data.get("date")
    py_source = _replace_templates(py_source, version, name, os.path.basename(target),
                                   component_version, component_date)
    py_source_b64 = base64.b64encode(py_source.encode("utf-8")).decode("ascii")

    # --- inner chunk (new Rhino 8 Script-component schema) ---
    inner = GH_LooseChunk("UserObject")
    inner.SetString("Description", description)
    inner.SetBoolean("GraftStandardOutputLines", True)
    bitmap_icon = System.Drawing.Bitmap.FromStream(System.IO.MemoryStream(icon_bytes))
    inner.SetDrawingBitmap("IconOverride", bitmap_icon)
    inner.SetGuid("InstanceGuid", instance_guid)
    inner.SetBoolean("MarshGuids", ghpython_data.get("marshalGuids", False))
    inner.SetBoolean("MarshInputs", False)
    inner.SetBoolean("MarshOutputs", False)
    inner.SetString("Name", prefix + name)
    inner.SetString("NickName", nickname)
    inner.SetInt32("ScriptComponentVersion", 3)
    inner.SetString("Tooltip", description)
    inner.SetBoolean("UsingLibraryInputParam", False)
    inner.SetBoolean("UsingScriptInputParam", False)
    inner.SetBoolean("UsingScriptOutputParam", False)
    inner.SetBoolean("UsingStandardOutputParam", False)

    # --- ParameterData ---
    params = inner.CreateChunk("ParameterData")
    params.SetInt32("InputCount", len(input_params))
    for i in range(len(input_params)):
        params.SetGuid("InputId", i,
                       System.Guid.Parse("08908df5-fa14-4982-9ab2-1aa0927566aa"))
    params.SetInt32("OutputCount", len(output_params))
    for i in range(len(output_params)):
        params.SetGuid("OutputId", i,
                       System.Guid.Parse("08908df5-fa14-4982-9ab2-1aa0927566aa"))

    for i, pi in enumerate(input_params):
        type_hint = pi.get("typeHintID", "ghdoc")
        pi_chunk = params.CreateChunk("InputParam", i)
        pi_chunk.SetBoolean("AllowTreeAccess", pi.get("allowTreeAccess", True))
        pi_chunk.SetString("Description", pi.get("description", ""))
        pi_chunk.SetGuid("InstanceGuid", System.Guid.NewGuid())
        pi_chunk.SetString("Name", pi["name"])
        pi_chunk.SetString("NickName", pi.get("nickname") or pi["name"])
        pi_chunk.SetBoolean("Optional", pi.get("optional", True))
        pi_chunk.SetInt32("ScriptParamAccess",
                          _parse_param_access(pi.get("scriptParamAccess", 0)))
        pi_chunk.SetInt32("ScriptParameterVersion", 2)
        pi_chunk.SetBoolean("ShowTypeHints", pi.get("showTypeHints", True))
        pi_chunk.SetInt32("SourceCount", pi.get("sourceCount", 0))
        pi_chunk.SetString("ToolTip", pi.get("description", ""))
        pi_chunk.SetGuid("TypeHintID", _parse_type_hint_guid(type_hint))

        asm_name, type_name = _converter_for(type_hint)
        conv = pi_chunk.CreateChunk("ConverterData")
        conv.SetString("AssemblyName", asm_name)
        conv.SetString("TypeName", type_name)

    for i, po in enumerate(output_params):
        po_chunk = params.CreateChunk("OutputParam", i)
        po_chunk.SetString("Name", po["name"])
        po_chunk.SetString("NickName", po.get("nickname") or po["name"])
        po_chunk.SetString("Description", po.get("description", ""))
        po_chunk.SetBoolean("Optional", po.get("optional", False))
        po_chunk.SetString("ToolTip", po.get("description", ""))
        po_chunk.SetInt32("SourceCount", po.get("sourceCount", 0))
        po_chunk.SetGuid("InstanceGuid", System.Guid.NewGuid())
        po_chunk.SetBoolean("ReverseData", po.get("reverse", False))
        po_chunk.SetBoolean("SimplifyData", po.get("simplify", False))

    # --- Script chunk ---
    script = inner.CreateChunk("Script")
    script.SetBoolean("MarshGuids", False)
    script.SetBoolean("MarshInputs", False)
    script.SetBoolean("MarshOutputs", False)
    script.SetString("Text", py_source_b64)
    script.SetString("Title", "Script")
    lang = script.CreateChunk("LanguageSpec")
    lang.SetString("Taxon", PY_TAXON)
    lang.SetString("Version", PY_VERSION)

    # --- root chunk ---
    root = GH_LooseChunk("UserObject")
    root.SetGuid("BaseID", py_component_guid)
    root.SetString("Name", prefix + name)
    root.SetString("NickName", nickname)
    root.SetString("Description", description)
    root.SetString("ToolTip", description)
    root.SetInt32("Exposure", exposure)
    root.SetString("Category", category)
    root.SetString("SubCategory", subcategory)
    root.SetGuid("InstanceGuid", instance_guid)
    root.SetByteArray("Icon", icon_bytes)
    root.SetByteArray("Object", inner.Serialize_Binary())

    System.IO.File.WriteAllBytes(target, root.Serialize_Binary())
