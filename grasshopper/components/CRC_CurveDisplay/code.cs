using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using System.IO;
using System.Linq;
using Rhino;
using Rhino.Geometry;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;

public class Script_Instance : GH_ScriptInstance
{
  // Utility methods (implementation hidden)
  private void Print(string text) { /* Implementation hidden. */ }
  private void Print(string format, params object[] args) { /* Implementation hidden. */ }
  private void Reflect(object obj) { /* Implementation hidden. */ }
  private void Reflect(object obj, string method_name) { /* Implementation hidden. */ }

  private readonly RhinoDoc RhinoDocument;
  private readonly GH_Document GrasshopperDocument;
  private readonly IGH_Component Component;
  private readonly int Iteration;

  // The main execution method.
  // Note: Dash is now declared as object to match the new component's input,
  // and then cast to string.
  private void RunScript(Curve Curve, int Width, Color Colour, object Dash)
  {
    if (Curve == null) return;
    if (Width <= 0) return;

    // Cast Dash to string
    string dashStr = Dash as string;
    if(dashStr == null)
      dashStr = "";

    double[] pattern = ParseDashPattern(dashStr);
    IEnumerable<Curve> segments = ApplyDashPattern(Curve, pattern);

    _clip = BoundingBox.Union(_clip, Curve.GetBoundingBox(false));
    foreach (Curve segment in segments)
    {
      _curves.Add(segment);
      _colors.Add(Colour);
      _widths.Add(Width);
    }

    // Override component attributes
    Component.Name = "Curve Display";
    Component.NickName = "CrvDpl.cs";
    Component.Message = "v{{version}} - {{date}}";
    Component.Description = "This component creates a custom preview on Rhino's screen allowing control of the lineweights";

    // Update input parameter descriptions
    Component.Params.Input[0].Description = "Curves to preview";
    Component.Params.Input[1].Description = "Width of the curves";
    Component.Params.Input[2].Description = "Color of the curves";
    Component.Params.Input[3].Description = "Dash pattern: a text panel with a value for the dash, a space, and a value for the gap";
  }

  /// <summary>
  /// Parse a dash pattern.
  /// </summary>
  private double[] ParseDashPattern(string pattern)
  {
    if (string.IsNullOrWhiteSpace(pattern))
      return null;

    string[] fragments = pattern.Split(new char[] { ' ' });
    if (fragments == null || fragments.Length == 0)
      return null;

    double[] values = new double[fragments.Length];
    for (int i = 0; i < fragments.Length; i++)
    {
      double v;
      if (!double.TryParse(fragments[i], out v))
        throw new Exception(fragments[i] + " is not a valid number.");

      if (v <= 0.0)
        throw new Exception("Dashes or gaps must have a strictly positive length.");

      values[i] = v;
    }

    return values;
  }

  /// <summary>
  /// Apply a dash-gap pattern to a curve.
  /// </summary>
  private IEnumerable<Curve> ApplyDashPattern(Curve curve, double[] pattern)
  {
    if (pattern == null || pattern.Length == 0)
      return new Curve[] { curve };

    double curveLength = curve.GetLength();
    List<Curve> dashes = new List<Curve>();

    double offset0 = 0.0;
    int index = 0;
    while (true)
    {
      double dashLength = pattern[index++];
      if (index >= pattern.Length)
        index = 0;

      double offset1 = offset0 + dashLength;
      if (offset1 > curveLength)
        offset1 = curveLength;

      double t0, t1;
      curve.LengthParameter(offset0, out t0);
      curve.LengthParameter(offset1, out t1);

      Curve dash = curve.Trim(t0, t1);
      if (dash != null)
        dashes.Add(dash);

      double gapLength = pattern[index++];
      if (index >= pattern.Length)
        index = 0;

      offset0 = offset1 + gapLength;

      if (offset0 >= curveLength)
        break;
    }

    return dashes;
  }

  private BoundingBox _clip;
  private readonly List<Curve> _curves = new List<Curve>();
  private readonly List<Color> _colors = new List<Color>();
  private readonly List<int> _widths = new List<int>();

  // In the new component, BeforeRunScript() remains available.
  public override void BeforeRunScript()
  {
    _clip = BoundingBox.Empty;
    _curves.Clear();
    _colors.Clear();
    _widths.Clear();
  }

  public override BoundingBox ClippingBox
  {
    get { return _clip; }
  }

  public override void DrawViewportWires(IGH_PreviewArgs args)
  {
    for (int i = 0; i < _curves.Count; i++)
      args.Display.DrawCurve(_curves[i], _colors[i], _widths[i]);
  }
}
