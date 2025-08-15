## Boundify Offset Plug-in v0.8.15

This plugin can:

- **Create outlines/offset line** of shapes (Rectangle, Line, Circle, Ellipse, Path)
- Line caps and corner caps styles
- Minimal line profile
- Path Effects
- Rounded dash-array
- Dot to dot
- Stamping a group-shape along the path/Rectangle/line/Oval
---

## How to Use

### Outline Command

1. Select a shape(s) in VectorLayer  
2. Use this plug-in (from **Tools Menu > Outline**)  
3. The shape converts to outlined shape  

### Boundify Offset... Command

1. Select a shape(s) in VectorLayer  
2. Use this plug-in (from **Tools Menu > Boundify Offset...**)  
3. Dialog opens for settings  
4. Choose line styles (or Move Path)  
5. Preview, then click OK  
6. Append offsetted shape(s)  

---

## Support Line Join Styles

- miter  
- bevel  
- round  

---

## Support Line Cap Styles (Start/End)

- butt  
- square  
- round  
- arrow (Add an arrowhead to either line cap)  
- ribbon (Add a ribbon-style to either line cap)  
- brush  
- brush2 (+ Distorted brush effect for linear mode)  
- brush3  
- bell  
- sigma  

---

## Optional Features

- **FillView**: Offset Path with fill color  
- **Use Original Path**: Simple effect to a path (does not create outline)  
- **Stroke**: Offset Path with red stroke color (uncheck for fill only)  

- **Reverse**: Reverse offset Path order(direction)   

- ** Random size, Order size, Opacity **: Stamp mode only   


---

## Line Effects

- none: Default (offsetted line)  
- linear: Tapered line  
- linear_a: Tapered line (alternative)  
- organic: Floral streamline  
- chain: Line crossing  
- gear: Square wave style  
- sawtooth: Saw-tooth-ed line / Pointed zigzag  
- punk: Burst balloon or waved line  
- fluffy: Cloud-like or bubble-shaped line  
- rough: Rough-edged line  
- dot_to_dot: Plot numbered dots  
- round_dot_dash: Rounded dotted line  
- dynamic_dash: Dynamically created dash line  
- random_dash: For cyber/flat design  
- stamp_top_group: Duplicates and places the selected topmost group shape along the specified path shape. To use this function, select both the group shape and the path shape.
  
---

## 🐞 Known Issues or Bugs / Feature Notes

- Krita crashes on rare occasions when dragging the slider rapidly with very complex path shapes  
- Some paths deviate from the intended route  
