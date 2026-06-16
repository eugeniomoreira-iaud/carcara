"""Dedicated .ghuser builder for CRC_CurveDisplay (C# Script component).

This module builds a **C# Script component** (.ghuser) using the GH_Archive
format decoded from the legacy ``carcara_CurveDisplay_r02.ghuser``.

WHY C# INSTEAD OF PYTHON
-------------------------
The Python SDK-mode port (``GH_ScriptInstance`` subclass in ``code.py``) does
not register with Rhino's host preview pipeline when loaded through a .ghuser
UserObject — the ``DrawViewportWires`` / ``ClippingBox`` overrides are silently
ignored because the component is wrapped in a ``GH_UserObject`` proxy that does
not forward ``IGH_PreviewObject`` calls.  The original component was always a
**C# Script** component (BaseID ``b6ba1144-02d6-4a2d-b53c-ec62e290eeb7``,
LanguageSpec ``*.*.csharp`` / ``*.*``), which wires into the preview pipeline
correctly.  This builder reproduces that exact archive structure.

DECODED LEGACY FORMAT (from ``carcara_CurveDisplay_r02.ghuser``)
-----------------------------------------------------------------
Root chunk (GH_LooseChunk "UserObject"):
  BaseID        = b6ba1144-02d6-4a2d-b53c-ec62e290eeb7   ← C# Script GUID
  Name / NickName / Category / SubCategory / Exposure
  InstanceGuid
  Icon          (byte array, 24×24 PNG)
  Object        (byte array → inner GH_LooseChunk "UserObject")

Inner chunk items:
  Description / Tooltip / Name / NickName
  GraftStandardOutputLines = true
  MarshGuids / MarshInputs / MarshOutputs = false (note: no 'al' in 'Marsh')
  ScriptComponentVersion = 3
  UsingLibraryInputParam / UsingScriptInputParam / UsingScriptOutputParam /
  UsingStandardOutputParam = false
  InstanceGuid

Inner chunk sub-chunks:
  ParameterData:
    InputCount / InputId[0..3]
    OutputCount = 0
    InputParam[i]:
      Name / NickName / Description / Tooltip / Optional / AllowTreeAccess /
      ShowTypeHints / ScriptParamAccess / ScriptParameterVersion=2 /
      SourceCount / InstanceGuid / TypeHintID
      ConverterData sub-chunk: AssemblyName + TypeName (CLR type names)

  Script:
    MarshGuids / MarshInputs / MarshOutputs = false
    Text    = BASE64-encoded UTF-8 C# source
    Title   = "CrvDpl.cs"
    LanguageSpec sub-chunk:
      Taxon   = "*.*.csharp"
      Version = "*.*"

  ScriptEditor: (layout; not required for load — omit or include)

Public API
----------
create_curvedisplay_cs_ghuser(source, target, version=None, prefix=None)
    Build CRC_CurveDisplay.ghuser from a bundle containing ``code.cs``
    (not ``code.py``). Reads metadata.json and icon.png; ignores code.py if
    present.
"""

import base64
import json
import os
from datetime import datetime


def _replace_templates(code, version, name, ghuser_name, component_version=None):
    """Substitute the componentizer template tokens in the C# source.

    Mirrors componentize_cpy.replace_templates so the C# code can use
    ``{{version}}`` / ``{{component_version}}`` / ``{{date}}`` / ``{{name}}`` /
    ``{{ghuser_name}}`` in e.g. ``Component.Message``. Tokens are replaced at
    build time, before the source is base64-embedded into the archive.
    """
    if version:
        code = code.replace("{{version}}", version)
    if component_version:
        code = code.replace("{{component_version}}", component_version)
    code = code.replace("{{name}}", name)
    code = code.replace("{{ghuser_name}}", ghuser_name)
    code = code.replace("{{date}}", datetime.now().strftime("%Y/%m/%d"))
    return code

# clr / GH_IO / System must already be referenced by the caller
# (build_userobjects.py does this before the build loop).

# C# Script component BaseID (differs from the Python one c9b2d725-…)
CS_SCRIPT_COMPONENT_GUID_STR = "b6ba1144-02d6-4a2d-b53c-ec62e290eeb7"
CS_TAXON = "*.*.csharp"
CS_VERSION = "*.*"

# ConverterData CLR type info per input parameter (name → (assembly, type))
# Extracted verbatim from the decoded legacy archive.
_CONVERTER_DATA = {
    "Curve":  ("RhinoCommon",              "Rhino.Geometry.Curve"),
    "Width":  ("System.Private.CoreLib",   "System.Int32"),
    "Colour": ("System.Drawing.Primitives","System.Drawing.Color"),
    "Dash":   ("System.Private.CoreLib",   "System.Object"),
}


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
    """Return System.Guid for the given type hint key or GUID string."""
    import System
    _types_map = dict(
        none="6a184b65-baa3-42d1-a548-3915b401de53",
        ghdoc="1c282eeb-dd16-439f-94e4-7d92b542fe8b",
        float="9d51e32e-c038-4352-9554-f4137ca91b9a",
        bool="d60527f5-b5af-4ef6-8970-5f96fe412559",
        int="48d01794-d3d8-4aef-990e-127168822244",
        str="3aceb454-6dbd-4c5b-9b6b-e71f8c1cdf88",
        color="24b1d1a3-ab79-498c-9e44-c5b14607c4d3",
        colour="24b1d1a3-ab79-498c-9e44-c5b14607c4d3",  # British alias
        curve="9ba89ec2-5315-435f-a621-b66c5fa2f301",
        int32="48d01794-d3d8-4aef-990e-127168822244",
    )
    guid_str = _types_map.get(str(type_hint_id).lower(), type_hint_id)
    return System.Guid.Parse(guid_str)


def create_curvedisplay_cs_ghuser(source: str, target: str,
                                   version: str | None = None,
                                   prefix: str | None = None) -> None:
    """Build CRC_CurveDisplay.ghuser as a C# Script component.

    Reads ``code.cs``, ``metadata.json``, and ``icon.png`` from *source*.
    Writes a binary GH_Archive to *target* whose structure matches
    the original ``carcara_CurveDisplay_r02.ghuser`` (C# Script, BaseID
    ``b6ba1144-…``, LanguageSpec ``*.*.csharp`` / ``*.*``, source BASE64).

    Parameters
    ----------
    source:
        Path to the ``CRC_CurveDisplay/`` bundle directory.
    target:
        Destination ``.ghuser`` file path.
    version:
        Ignored (C# source has its own version string). Accepted for
        interface symmetry with the Python builder.
    prefix:
        Optional name prefix (usually None).
    """
    import System
    import System.IO
    import System.Drawing
    from GH_IO.Serialization import GH_LooseChunk

    # --- validate bundle files ---
    icon_path = os.path.join(source, "icon.png")
    code_path = os.path.join(source, "code.cs")
    meta_path = os.path.join(source, "metadata.json")

    for p, label in [(icon_path, "icon.png"), (code_path, "code.cs"), (meta_path, "metadata.json")]:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"{label} missing from bundle: {source}")

    icon_bytes = _bitmap_from_image_path(icon_path)

    with open(code_path, "r", encoding="utf-8") as f:
        cs_source = f.read()

    with open(meta_path, "r", encoding="utf-8") as f:
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

    cs_component_guid = System.Guid.Parse(CS_SCRIPT_COMPONENT_GUID_STR)

    ghpython_data = data.get("ghpython", {})
    input_params = ghpython_data.get("inputParameters", [])
    output_params = ghpython_data.get("outputParameters", [])

    # --- substitute template tokens ({{version}}, {{component_version}}, …) then BASE64-encode ---
    component_version = data.get("componentVersion") or version
    cs_source = _replace_templates(cs_source, version, name, os.path.basename(target),
                                   component_version)
    cs_source_b64 = base64.b64encode(cs_source.encode("utf-8")).decode("ascii")

    # --- build inner chunk (mirrors the decoded legacy structure) ---
    inner = GH_LooseChunk("UserObject")
    inner.SetString("Description", description)
    inner.SetBoolean("GraftStandardOutputLines", True)
    bitmap_icon = System.Drawing.Bitmap.FromStream(System.IO.MemoryStream(icon_bytes))
    inner.SetDrawingBitmap("IconOverride", bitmap_icon)
    inner.SetGuid("InstanceGuid", instance_guid)
    inner.SetBoolean("MarshGuids", False)
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
        pi_chunk.SetGuid("TypeHintID",
                         _parse_type_hint_guid(pi.get("typeHintID", "ghdoc")))

        # ConverterData sub-chunk (CLR type used for marshaling)
        pname = pi["name"]
        if pname in _CONVERTER_DATA:
            asm_name, type_name = _CONVERTER_DATA[pname]
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
    script.SetString("Text", cs_source_b64)
    script.SetString("Title", nickname)
    lang = script.CreateChunk("LanguageSpec")
    lang.SetString("Taxon", CS_TAXON)
    lang.SetString("Version", CS_VERSION)

    # --- root chunk ---
    root = GH_LooseChunk("UserObject")
    root.SetGuid("BaseID", cs_component_guid)
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
