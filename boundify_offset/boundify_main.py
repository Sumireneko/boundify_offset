# ======================================
# Krita Boundify Offset plug-in v0.8.15
# ======================================
# Copyright (C) 2025 L.Sumireneko.M
# This program is free software: you can redistribute it and/or modify it under the 
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>. 

from krita import *
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element
import traceback
from decimal import Decimal, getcontext
import re
import math
import random
from datetime import datetime
import uuid
from typing import Dict, List, Union, Tuple

import faulthandler
faulthandler.enable()  # stacktrace
faulthandler.dump_traceback_later(timeout=5)

info = []
total_pts = 1
parent_dialog = None
dbg = None
debug_plot = True
debug = False
debug_path = False # Show red colored path for debug

# Update issue resolution
is_updating = False
reinit_requested = False
is_offsetting = False

"""



params = {
    "mode": "offset",
    "debug_path": True,
    "ofs": -1.0,
    "mitl": 4.0,
    "fo_mode": True,
    "line_cap": "butt", # "butt,square,round,arrow,brush"
    "line_join": "miter", # "miter,bevel,round,"
    "delete_orig": False ,
    "taper_mode" : "none", # "none,linear,linear_a,organic,chain,gear,sawtooth,punk,fluffy,rough,dot_to_dot"
    "cap_a": "miter" ,# "butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"
    "cap_b": "arrow" ,# 
    "preview": True,
    "preview_id_prefix": "preview_shapes_" ,
    "factor": 50 ,
    "previewcolor": "#ff0000" ,
    "single_path": False ,
    "dash": "none", # "none","dynamic_dash","random_dash","round_dot_dash"
    "reverse": False ,
    "original": False ,
    "fillview": False 
}
"""

#-------------------
# Debug plot
#-------------------
"""
    Usage Example: 
    if dbg and debug_plot:
        #dbg.plot_dot_param2({x:100, y:200}, "Sample Text",r = 2.0,"red","0.8em")
        dbg.plot_dot_param2(original_path_data[0], "0","black", 2.0,"2.8em")
        dbg.plot_dot_param2(original_path_data[1], "1","black", 2.0,"2.8em")
"""

class DebugPlot:
    def __init__(self, transform=""):
        self.transform = transform
        self.svg_elms = []  # svg data list

    def set_transf(self, transform):
        self.transform = transform



    # plot coorinates  label(cy,xy)
    def plot_point_coord(self, point, label,color, r=4, size="0.5em"):
        circle = ET.Element("circle", {
            "cx": str(point['x']),
            "cy": str(point['y']),
            "r": str(r),
            "fill": color,
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        circle_str = ET.tostring(circle, encoding="utf-8").decode("utf-8")
        self.svg_elms.append(circle_str)

        text = ET.Element("text", {
            "x": str(point['x']),
            "y": str(point['y'] + 8),
            "font-size": size,
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        text.text = f"{label} ({point['x']},{point['y']})"
        text_str = ET.tostring(text, encoding="utf-8").decode("utf-8")
        self.svg_elms.append(text_str)

    # Dot
    def plot_dot(self,point, color="red", r=4):
        dot = ET.Element("circle", {
            "cx": str(point['x']),
            "cy": str(point['y']),
            "r": str(r),
            "fill": color,
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        dot_str = ET.tostring(dot, encoding="utf-8").decode("utf-8")
        self.svg_elms.append(dot_str)

    # Line
    def plot_line(self, p1, p2, color="red",width="2"):
        line = ET.Element("line", {
            "x1": str(p1['x']),
            "y1": str(p1['y']),
            "x2": str(p2['x']),
            "y2": str(p2['y']),
            "stroke": color,
            "stroke-width": str(width),
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        #howw print(f"miter debugline: {p1['x']},{p1['y']}--{p2['x']},{p2['y']}")
        line_str = ET.tostring(line, encoding="utf-8").decode("utf-8")
        self.svg_elms.append(line_str)

    # Text and Dot (for dot_to_dot mode etc)
    def plot_dot_param2(self, point, label, color="red", r=2, size="8px",spacing=0):
        uid=str(uuid.uuid4())[:8]
        px = point['x'];
        py = point['y'];
        px = str(px)
        circle = ET.Element("circle", {
            "cx": px,
            "cy": str(py),
            "r": str(r),
            "fill": color,
            "id": "preview_shapes_"+uid+"c",
            "transform" : self.transform
        })
        circle_str = ET.tostring(circle, encoding="utf-8").decode("utf-8")

        font_families = ["Noto Sans", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"]
        font_family_str = ", ".join(font_families)  # Convert to a string split by camma

        text = ET.Element("text", {
            "x": px,
            "y": str(py + r + spacing + r*2.45),
            "fill": color,
            "font-size": size,
            "font-family": font_family_str,
            "id": "preview_shapes_"+uid+"t",
            "transform" : self.transform,
            "style": "white-space: pre;"
        })
        text.text = label
        text_str = ET.tostring(text, encoding="utf-8").decode("utf-8")

        self.svg_elms.extend([circle_str, text_str])

    def plot_dot_param3(self, point, label, color="red", r=2, shift=4 , size="0.5em"):
        circle = ET.Element("circle", {
            "cx": str(point['x']),
            "cy": str(point['y']),
            "r": str(r),
            "fill": color,
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        circle_str = ET.tostring(circle, encoding="utf-8").decode("utf-8")
        self.svg_elms.append(circle_str)  

        font_families = ["Noto Sans", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"]
        font_family_str = ", ".join(font_families) # Convert to a string split by camma


        lx,ly = self.set_text_pos(point,shift,r,0.8)

        text = ET.Element("text", {
            "x": str(point['x']),
            "y": str(point['y'] + r + shift ),
            "fill": color,
            "font-size": size,
            "font-family": font_family_str,
            "id": "preview_shapes_"+str(uuid.uuid4()),
            "transform" : self.transform
        })
        text.text = label
        text_str = ET.tostring(text, encoding="utf-8").decode("utf-8")

        self.svg_elms.append(text_str) 


    def set_text_pos(self,point,shift,r,rgap=0.35):
        # Convert clockwise shift to radian 
        angle_deg = (shift % 12) * 30  # 1-12h converted to 0-330 deg
        angle_rad = math.radians(angle_deg - 90)  # Based on y axis direction made 0 deg, so -90 deg
    
        # distance from center
        gap = r * 2 * rgap
        distance = r + gap
    
        # label
        lx = point["x"] + distance * math.cos(angle_rad)
        ly = point["y"] + distance * math.sin(angle_rad)
        return lx,ly


    def get_plot_elems(self):
        """ Return `self.svg_elms`  """
        return self.svg_elms

def debug_cap_direction(dase_dir_array):
    dbg.plot_line( {'x': base_dir['baseX'],'y':base_dir['baseY']},{'x':base_dir['offsetX'],'y':base_dir['offsetY']})



# Initialize Dictorary for shape property data
def initialize_shape_data(tag_name):
    """
    # Example
    shape_data = initialize_shape_data("path")
    print(shape_data)

    """
    return {"tagName": tag_name}



def parse_shape_attributes(shape_string):

    # Extract a tag name
    tag_match = re.match(r'<(\w+)', shape_string)
    tag_name = tag_match.group(1) if tag_match else "unknown"

    # Extract an attributes
    attributes = re.findall(r'([\w-]+)="([^"]*)"', shape_string)

    # Set tag-name to a dictionary
    attribute_dict = {attr[0]: attr[1] for attr in attributes}
    attribute_dict["tagName"] = tag_name  # Set a tag-name
    return attribute_dict


def generate_shape_tag(attributes):
    # Get a tag-name
    tag_name = attributes.pop("tagName", "unknown")  # Default:"unknown"

    # Parse an attribute as string
    attribute_strings = [f'{key}="{value}"' for key, value in attributes.items()]
    attributes_text = " ".join(attribute_strings)

    # Generate SVG tag
    tag_string = f'<{tag_name} {attributes_text}/>'
    return tag_string


#----------------------------
# Preview routine
#----------------------------

#app = Krita.instance()

def rm_shape(shape,prefix):
    try:
        if shape is None:
            print("Error: shape is None")
            return

        if not hasattr(shape, "name") or not callable(shape.name):
            print("Error: shape object missing 'name' method")
            return

        sname = shape.name()

        if not isinstance(sname, str):
            print("Error: shape.name() did not return string")
            return

        if sname.startswith(prefix):
            if hasattr(shape, 'remove') and callable(shape.remove):
                #print(f"Removing shape: {sname}")
                shape.remove()
            else:
                print(f"Cannot remove shape: {sname} — method missing or not callable")



    except Exception as e:
        print(f"Error removing shape : {e}")#{shape.name()}

def re_init(prefix):
    global is_updating, reinit_requested
    print("begin_re_init")
    if is_updating:
        print("Now re_init() running.")
        if not reinit_requested:
            print("Setting reinit_requested=True")
            reinit_requested = True
        else:
            print("Reinit already requested")
        return
    try:
        app = Krita.instance()
        doc = app.activeDocument()
        view = app.activeWindow().activeView()
        selected_layers = view.selectedNodes()
        
        if doc is None:
            print("No active document found.")
            return

        for node in selected_layers:
            if not node:continue
            if node.type() == "vectorlayer":
                shapes = node.shapes()
                for shape in shapes:
                    rm_shape(shape,prefix)

    except Exception as e:
        print(f"[re_init] Exception occurred: {e}")
    finally:
        is_updating = False
        print("[re_init] is_updating=False")
        #if reinit_requested:
        #    print("[re_init] Running deferred re_init.")
        #    reinit_requested = False
        #    re_init(prefix)


def re_show(prefix,flg):

    app = Krita.instance()
    doc = app.activeDocument()
    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    
    if doc is None:
        print("No active document found.")
        return

    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                #if shape.isSelected():
                sname = shape.name()
                if sname.startswith(prefix): shape.setVisible(flg) # show or hide


def re_z_index(prefix,level=9999):

    app = Krita.instance()
    doc = app.activeDocument()
    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    
    if doc is None:
        print("No active document found.")
        return

    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                # if shape.isSelected():
                sname = shape.name()
                if sname.startswith(prefix): shape.setZIndex(level) # show or hide


def determine(prefix):
    new_prefix = "shape"
    app = Krita.instance()
    doc = app.activeDocument()

    if doc is None:
        print("No active document found.")
        return

    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    prefix_len = len(prefix)

    version = app.version()
    des = True
    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                if des == True and shape.isSelected():
                    shape.deselect()
                sname = shape.name()
                # if sname.startswith(prefix):shape.setName("shape"+str(uuid.uuid4())[:8]) # rename 
                if sname.startswith(prefix):
                    new_name = new_prefix + sname[prefix_len:]
                    shape.setName(new_name)

def deselectAll():
    app = Krita.instance()
    doc = app.activeDocument()

    if doc is None:
        print("No active document found.(deselection)")
        return

    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()

    version = app.version()
    des = True
    if des == False:return
    for node in selected_layers:
        if node.type() == "vectorlayer":
            [shape.deselect() for shape in node.shapes() if shape.isSelected()]

#----------------------------
# main routine
#----------------------------
# Return a selected shape(s) to main function
def process_selected_shapes(params):
    global is_offsetting
    if is_offsetting:
        print("Offset processing is in progress. Will retry later.")
        return
    is_offsetting = True

    #print("running2")
    process_main(params)
    try:
        pass
    except Exception as e:
        print(f"[process_selected_shapes] Exception occurred: {e}")
    finally:
        print("running_finary")
        is_offsetting = False



def process_main(params):
    global dbg,total_pts
    total_pts = 1

    app = Krita.instance()
    doc = app.activeDocument()
    view = app.activeWindow().activeView()

    if doc is None:
        print("No active document found.")
        return

    selected_vector_layer = view.selectedNodes()

    if not selected_vector_layer:
        print("No nodes selected in the document.")
        return


    # Check the selection state in the node
    has_selected_shapes = any(
        shape.isSelected() for node in selected_vector_layer if node.type() == "vectorlayer" for shape in node.shapes()
    )


    if not has_selected_shapes:
        print("No shapes selected in the current vector layers.")
        return

    ofs_shapes = []  # Initialization of an array for uppdate
    wpt = doc.width()*0.72
    hpt = doc.height()*0.72
    newtag = f' width="{wpt}pt" height="{hpt}pt" viewBox="0 0 {wpt} {hpt}" '
    
    remove_shapes_reserve = [] # Array storing deletion candidates
    cnt=0
    if debug_plot== True: dbg = DebugPlot()
    # params['taper_mode']="stamp_top_group" # for debug

    params['stamp_along']={
        'flg': False,
        'id': "",
        'original': "",
        'center'  : {'x':0,'y':0},
        'data'    : [],
        'abst'    : "",
        'width' : 0 ,
        'height': 0
    }

    sym_name = ""

    # Apply to shapes
    for node in selected_vector_layer:
        if node.type() == "vectorlayer":
            shapes = node.shapes()

            if params['taper_mode']=="stamp_top_group":
                sel_layer = []
                
                for l in shapes:
                    if l.isSelected():sel_layer.append(l)
                top_shape = max(sel_layer, key=lambda s: s.zIndex())

                if top_shape.type() == "groupshape":
                    sym_name = top_shape.name()
                    print(f" Group for put array is found: {top_shape.name()}")
                    groups_abst = top_shape.absoluteTransformation()
                    groups_abst_svg = qtransform_to_svg_transform(groups_abst)
                    gid="preview_shapes_g"+str(uuid.uuid4())[:8]
                    group_tag = f'  transform="{groups_abst_svg}"'# reserved
                    group_tag = ""
                    bounds = get_groupshape_bounds(top_shape)
                    center = {}
                    b_width = b_height = 0
                    if bounds:
                        min_x, min_y, max_x, max_y, cx, cy = bounds
                        center={'x':cx,'y':cy}
                        b_width = abs(min_x - max_x)
                        b_height = abs(min_y - max_y)
                    else:
                        center={'x':0,'y':0}

                    params['stamp_along']['name']=sym_name
                    params['stamp_along']['flg']=True
                    params['stamp_along']['original']=top_shape.toSvg()
                    params['stamp_along']['center']=center
                    params['stamp_along']['height']=b_height
                    params['stamp_along']['width']=b_width
                    # ex=center
                    # print(f"Center point: {ex}")

                    if params['mode'] == "outline":
                        remove_shapes_reserve.append(top_shape)



            for shape in shapes:
                if shape.isSelected():
                    cnt=cnt+1;params['cnt']=cnt;
                    # print(f"Read {cnt} : {shape.name()}")

                    if shape.type() == "groupshape":
                        if params['taper_mode']=="stamp_top_group" and shape.name() == sym_name:
                            print('stamp mode:skip');continue

                        print(f"Group found: {shape.name()}")
                        groups_abst = shape.absoluteTransformation()
                        groups_abst_svg = qtransform_to_svg_transform(groups_abst)
                        gid="preview_shapes_g"+str(uuid.uuid4())[:8]
                        group_tag = f'  transform="{groups_abst_svg}"'# reserved
                        group_tag = ""
                        g_shapes=[]
                        for child in shape.children():
                            g_path = processShape_g(node, child, params)
                            if g_path is not None:# For dot_to_dot mode 
                                g_shapes.append(g_path)
                        # group shape
                        if g_shapes is not None and params['stamp_along']['flg'] == False:
                            #print(f"g_shapes:{g_shapes}")
                            g_all_path = "\n".join(g_shapes)
                            # if params['taper_mode']=='dot_to_dot':continue;
                            if ofs_shapes is not None:
                                ofs_shapes.append(f'<svg{newtag}><g id="{gid}" {group_tag}>{g_all_path}</g></svg>')
                        else:
                            print("Warning:ofs_shapes is None  ")
                        if params['mode'] == "outline":
                            remove_shapes_reserve.append(shape)
                    else:
                        # single shape(s)
                        if params['taper_mode']=="stamp_top_group" and shape.name() == sym_name:
                            print('symbol_mode:skip');continue
                        ofs_shapes=processShape(node, shape, params, ofs_shapes, remove_shapes_reserve, newtag)


    # Stamp topmost-group along the path 
    if params['stamp_along']['flg'] == True:
        plot_shapes = dbg.get_plot_elems()
        s = "\n".join(params['stamp_along']['data']) # Combine all shapes
        node.addShapesFromSvg(f'<svg {newtag}>{s}</svg>') # Why happend Segmentation fault in here orz...
        params['stamp_along']['flg'] = False


    #debug
    if debug_plot == True:
        plot_shapes = dbg.get_plot_elems()
        for s in  plot_shapes:
            #debug_message(s)
            node.addShapesFromSvg(f'<svg {newtag}>{s}</svg>')

    #debug_message(f"param:"+str(params))
    if ofs_shapes is not None: # For dot_to_dot mode
        for s in ofs_shapes:
            node.addShapesFromSvg(s)
    else:
        print("Warning:ofs_shapes is None")

    # Put preview shapes to front
    if params['mode']=="offset":
        re_z_index(params['preview_id_prefix'],9999)

    # if outline mode, remove the original shapes 
    if params['mode']=="outline":
        for s in remove_shapes_reserve:
            s.remove()


    print(f"Shape updated")

    # debug info
    for item in info:
        print(item)

def processShape_g(node, shape, params):
    ofs_path = main(node, shape, params)
    if not ofs_path:
        return
    return ofs_path




def processShape(node, shape, params, ofs_shapes, remove_shapes_reserve, newtag):
    ofs_path = main(node, shape, params)
    if not ofs_path:
        return
    ofs_shapes.append(f'<svg {newtag}>{ofs_path}</svg>')
    if params['mode'] == "outline":
        remove_shapes_reserve.append(shape)
    return ofs_shapes





def extract_common_path_attributes(elm ):
    s = {
        "miter_limit" : elm.get("stroke-miterlimit", 4.0),
        "line_cap"    : elm.get("stroke-linecap", "butt"),
        "line_join"   : elm.get("stroke-linejoin", "miter"),
        "stroke_color": elm.get("stroke", "pink"),
        "fill_color"  : elm.get("fill", "none"),
        "stroke_width": float(elm.get("stroke-width", 1.0))
    }
    return s['line_cap'],s['line_join'],s['miter_limit'],s['stroke_color'],s['fill_color'],s['stroke_width']

def map_s_scale(value, min_val=0, max_val=100, min_scale=0.25, max_scale=2.0):
    """
    Slide to value
    value: 0..100 
    Return: 0.25..1.5 scale
    """
    ratio = (value - min_val) / (max_val - min_val)
    scale = min_scale + ratio * (max_scale - min_scale)
    scale = max(min_scale, min(scale, max_scale))
    return scale



# Apply parameters to the shape
def main(node, shape, params):
    global dbg
    # userset attributes
    mode = params.get("mode","outline")# mode outline or offset
    delete_orig = params.get("delete_orig", False)
    if mode=="outline":fo_mode = False

    # A string data from SVG shape for get shape attributes
    svg_data = shape.toSvg()
    #print(svg_data)

    # transf
    inv_transf, invertible = shape.absoluteTransformation().inverted()
    local_rect = inv_transf.mapRect(shape.boundingBox())
    
    params['bb']={
        'x' : local_rect.x(),
        'y' : local_rect.y(),
        'w' : local_rect.width(),
        'h' : local_rect.height(),
    }

    params['bb_short'] =  max(params['bb']['w'],params['bb']['h'])

    abst = shape.absoluteTransformation()
    abst_svg = qtransform_to_svg_transform(abst)
    #print(f"abst:{abst_svg}")
    params['stamp_along']['abst']=abst_svg

    raw_shape_elm  = parse_shape_attributes(svg_data)
    #print(f"RawShapeElm: {raw_shape_elm}")
    #print(f"Shape: {raw_shape_elm['tagName']}, Transformation: {transform}")
    #print("stroke_width:"+str(raw_shape_elm['stroke-width']))

    # original shape attributes
    raw_shape_elm['transform'] = abst_svg
    transform = raw_shape_elm .get("transform", "")

    #debug
    if debug_plot== True: dbg.set_transf(abst_svg)
    
    
    pid = ""
    # Generate a unique ID for preview; append raw ID only if total length is within safe limits
    MAX_ID_LENGTH = 128  # safty limit
    if params['preview']:
        prefix = params['preview_id_prefix']
        uid = f'{prefix}{str(uuid.uuid4())[:8]}'
        raw_id = raw_shape_elm.get('id', '')
        
        # Doesn't use 'raw_id' if the len over than MAX_ID_LENGTH
        if raw_id and len(uid + raw_id) <= MAX_ID_LENGTH:
            pid = uid + raw_id
        else:
            pid = uid

    new_node =  apply_offset(raw_shape_elm,params)

    if new_node == None or new_node == "":
        # print("Warning: No offset shape was created.")
        return ""

    if transform == "": pass
    else: new_node['transform'] = transform
    
    if pid == "": pass
    else: new_node['id'] = pid

    # update SVG data( dict -> output tag data )
    updated_svg_data = generate_shape_tag(new_node)

    #print(updated_svg_data)
    #print(f"Shape '{shape.objectName()}' creation successfully.")
    return updated_svg_data



# ------------------------------------------------------
# Convert functions ,Coordianates to path command 
# ------------------------------------------------------
# for example Circle line polygon polyline rect elipse  

# -----------------------
# <rect> for corner join
# -----------------------
def generate_rect_path(el, offset, line_join):
    x = float(el.get("x", 0))
    y = float(el.get("y", 0))
    width = float(el.get("width", 1))
    height = float(el.get("height", 1))

    rx = float(el.get("rx", 0)) # Range 0.. width/2
    ry = float(el.get("ry", 0)) # Range 0.. /2

    # Clamp rx/ry to half of width/height
    rx = min(rx, width / 2)
    ry = min(ry, height / 2)

    mx = x - offset
    my = y - offset
    mw = x + width + offset
    mh = y + height + offset

    ix = x + offset
    iy = y + offset
    iw = x + width - offset
    ih = y + height - offset

    if line_join == "round":
        if rx > 0 or ry > 0:
            orx = rx + offset
            ory = ry + offset
    
            outer_path = f"""
                M{mx + orx},{my}
                L{mw - orx},{my}
                A{orx},{ory} 0 0 1 {mw},{my + ory}
                L{mw},{mh - ory}
                A{orx},{ory} 0 0 1 {mw - orx},{mh}
                L{mx + orx},{mh}
                A{orx},{ory} 0 0 1 {mx},{mh - ory}
                L{mx},{my + ory}
                A{orx},{ory} 0 0 1 {mx + orx},{my} Z"""

            rrx = max(rx - offset, 0)
            rry = max(ry - offset, 0)

            inner_path = f"""
                M{ix + rrx},{ih}
                L{iw - rrx},{ih}
                A{rrx},{rry} 0 0 0 {iw},{ih - rry}
                L{iw},{iy + rry}
                A{rrx},{rry} 0 0 0 {iw - rrx},{iy}
                L{ix + rrx},{iy}
                A{rrx},{rry} 0 0 0 {ix},{iy + rry}
                L{ix},{ih - rry}
                A{rrx},{rry} 0 0 0 {ix + rrx},{ih} Z"""

        else:
            r = offset
            outer_path = f"""
                M{mx + r},{my}
                L{mw - r},{my}
                A{r},{r} 0 0 1 {mw},{my + r}
                L{mw},{mh - r}
                A{r},{r} 0 0 1 {mw - r},{mh}
                L{mx + r},{mh}
                A{r},{r} 0 0 1 {mx},{mh - r}
                L{mx},{my + r}
                A{r},{r} 0 0 1 {mx + r},{my} Z"""
    
            offset /= 8
            inner_path = f"""M{iw - offset},{iy}
                L{ix + offset},{iy} L{ix},{iy + offset} L{ix},{ih - offset} L{ix + offset},{ih} 
                L{iw - offset},{ih} L{iw},{ih - offset} L{iw},{iy + offset} Z"""


        #print(outer_path + inner_path)
        return outer_path + inner_path

    elif line_join == "bevel":
        # Outer Path (Bevel)
        outer_path = f"""
            M{mx + offset},{my}
            L{mw - offset},{my} L{mw},{my + offset}
            L{mw},{mh - offset} L{mw - offset},{mh}
            L{mx + offset},{mh} L{mx},{mh - offset}
            L{mx},{my + offset} Z"""

        # Inner Path (Bevel)
        inner_offset = offset / 4
        inner_path = f"""
            M{iw - inner_offset},{iy}
            L{ix + inner_offset},{iy} L{ix},{iy + inner_offset}
            L{ix},{ih - inner_offset} L{ix + inner_offset},{ih}
            L{iw - inner_offset},{ih} L{iw},{ih - inner_offset}
            L{iw},{iy + inner_offset} Z"""

        return outer_path + inner_path

    else:
        # Default (Miter)
        return f"""
            M{mx},{my} L{mw},{my} L{mw},{mh} L{mx},{mh} Z
            M{iw},{iy} L{ix},{iy} L{ix},{ih} L{iw},{ih} Z"""

#-----------------------
# <circle>
#-----------------------
def generate_circle_path(el, offset, line_join):
    cx = float(el.get("cx"))
    cy = float(el.get("cy"))
    r = float(el.get("r"))

    if offset == 0:
        return f"""
            M{cx - r - offset},{cy} a{r + offset},{r + offset} 0 1,0 {2 * (r + offset)},0 
            a{r + offset},{r + offset} 0 1,0 -{2 * (r + offset)},0 Z
            """

    return f"""
        M{cx - r - offset},{cy} a{r + offset},{r + offset} 0 1,0 {2 * (r + offset)},0 
        a{r + offset},{r + offset} 0 1,0 -{2 * (r + offset)},0 
        M{cx + r - offset},{cy} a{r - offset},{r - offset} 0 1,1 -{2 * (r - offset)},0 
        a{r - offset},{r - offset} 0 1,1 {2 * (r - offset)},0"""

#-----------------------
# <ellipse>
#-----------------------
def generate_ellipse_path(el, offset, line_join):
    cx = float(el.get("cx", 0))
    cy = float(el.get("cy", 0))
    rx = float(el.get("rx", 0))
    ry = float(el.get("ry", 0))

    if offset == 0:
        return f"""
            M{cx - rx - offset},{cy} a{rx + offset},{ry + offset} 0 1,0 {2 * (rx + offset)},0 
            a{rx + offset},{ry + offset} 0 1,0 -{2 * (rx + offset)},0 Z
            """

    return f"""
        M{cx - rx - offset},{cy} a{rx + offset},{ry + offset} 0 1,0 {2 * (rx + offset)},0 
        a{rx + offset},{ry + offset} 0 1,0 -{2 * (rx + offset)},0 
        M{cx + rx - offset},{cy} a{rx - offset},{ry - offset} 0 1,1 -{2 * (rx - offset)},0 
        a{rx - offset},{ry - offset} 0 1,1 {2 * (rx - offset)},0"""



#----------------------------
# Shape Offset (Main)
#----------------------------
def get_outline_from_shape(orig_elm, tag_name, params):
    global debug_path
    stroke_width = 1.0
    mode    = params.get("mode", "outline") # outline or offset
    fo_mode    = params.get("fo_mode", False) # force offset mode, not for outline
    debug_path = params.get("debug_path", False)

    _, line_join, _, stroke_color, fill_color, stroke_width = extract_common_path_attributes(orig_elm)

    if params['mode']=='offset':
        line_join = params.get("line_join", "miter")
        # stroke_width =  float(params.get("ofs",10.0)) # override
        stroke_width =  float(stroke_width) + float(params.get("ofs",1.0)) # relative offset

    def apply_to_shape(element, shape_func_ref,stroke_width,msg=""):
        if not element:
            return None  # If no element is found
        
        offset = stroke_width*0.5  # All of offset data become a Path-Element
        offset_shape_path = shape_func_ref(element, offset, line_join)
        if msg not in ["rect", "ellipse", "circle"]:
            offset_shape_path = cleaning_path(offset_shape_path)

        if mode == "outline":stroke_width = 0

        path_elm = create_outline_path_elm(offset_shape_path,stroke_color, stroke_color,stroke_width,params)  # Preparation
        if debug:
            print(f"ShapeTagName: {tag_name}")
        return path_elm

    ret_elm = None

    # Processing according to SVG Element tag names
    tag_name = tag_name.lower()
    if tag_name == "rect":
        ret_elm = apply_to_shape(orig_elm, generate_rect_path,stroke_width,"rect")
    elif tag_name == "circle":
        ret_elm = apply_to_shape(orig_elm, generate_circle_path,stroke_width,"circle")
    elif tag_name == "ellipse":
        ret_elm = apply_to_shape(orig_elm, generate_ellipse_path,stroke_width,"ellipse")
    else:
        ret_elm = None
        print(f"Unsupported tagName: {tag_name}")

    return ret_elm



#------------------------------
# <polygon> <polyline> to Path
#------------------------------
def poly_to_path(param, close=True):
    # Start with 'M', then 'L'
    param = re.sub(r'(\d+,\d+)', r'L\1', param).replace('L', 'M', 1)
    # polygon: close=True; polyline : close=False
    param = param + ("Z" if close else "")
    return param

#------------------------------
# <line> to Path
#------------------------------
def line_to_path(line_element,n=1):
    # Get attributes of <line> tag
    a = {'x':line_element.get("x1") , 'y': line_element.get("y1") }
    b = {'x':line_element.get("x2") , 'y': line_element.get("y2") }

    if n <= 0:
        return f"M{a['x']},{a['y']} L{b['x']},{b['y']}"
    
    # subdivided points
    points = []
    for i in range(1, n):
        x = a['x'] + (b['x'] - a['x']) * i / n
        y = a['y'] + (b['y'] - a['y']) * i / n
        points.append(f"L{x},{y}")
    
    d = f"M{a['x']},{a['y']} " + ' '.join(points) + f" L{b['x']},{b['y']}"

    return d


def get_mid_point(a, b):
    if a == b:
        return a
    
    dx = b["x"] - a["x"]
    dy = b["y"] - a["y"]
    
    if dx == 0 and dy == 0:
        return a  # Avoid to zero divide
    
    return {
        "x": a["x"] + dx / 2,
        "y": a["y"] + dy / 2
    }

def is_single_segment_line(svg_path):
    # Regular expression checks whether `M x y` is followed by exactly one `L x y`
    pattern = r"^M[-\d\.]+ [-\d\.]+L[-\d\.]+ [-\d\.]+$"
    return bool(re.match(pattern, svg_path.strip()))



def get_single_segment_line(svg_path,n):
    # Regular expression checks whether `M x y` is followed by exactly one `L x y`
    pattern = r"^M([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)L([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)$"
    match = re.match(pattern, svg_path.strip())
    
    if match:
       return True, [{"x": float(match.group(1)), "y": float(match.group(2))}, {"x":float(match.group(3)),"y": float(match.group(4)) }]
    else:
        return False, []

def single_coord_conv(array):
    a = []
    
    a.append({'x': array[0]['baseX'], 'y': array[0]['baseY']})
    a.append({'x': array[1]['offsetX'], 'y': array[1]['offsetY']})
    
    return a

def subdivide_line_as_dict(a, b, n):
    if n < 0:
        return []
    # angle 
    dx = b['x'] - a['x']
    dy = b['y'] - a['y']
    angle = math.degrees(math.atan2(dy, dx))  # deg
    print("angle?:::"+str(angle))
    points = []
    for i in range(n + 1):  #  
        x = a['x'] + dx * i / n if n != 0 else a['x']
        y = a['y'] + dy * i / n if n != 0 else a['y']
        points.append({'x': x, 'y': y, 'angle': angle})

    return points

Num = Union[int, float, str]
#----------------------------------------
# <circle><ellipse> to Path: Variant
#----------------------------------------
# e.g. (taper affect to a circle and rectangle)
def oval_variant(el,params,is_closed,path_data):

    tag_name  = el['tagName'] # = "path"
    el['d'] = path_data
    el['original'] = True
    # print(f"Oval: {el}")#[x,y,w,h]
    is_closed = True
    return get_outline_from_path(el, tag_name, params, is_closed, path_data)



def generate_v_circle_path(el, offset, line_join, segments=0):
    cx = float(el.get("cx"))
    cy = float(el.get("cy"))
    r = float(el.get("r"))

    if segments == 0:
        # two arc（upper + lower）
        return f"""
            M{cx - r - offset},{cy} a{r + offset},{r + offset} 0 1,0 {2 * (r + offset)},0 
            a{r + offset},{r + offset} 0 1,0 -{2 * (r + offset)},0 Z
            """

    path_parts = []
    total_segments = 4 * (2 ** segments)  # 4, 8, 16, 32...
    angle_step = 2 * math.pi / total_segments
    first = True

    for i in range(total_segments):
        theta1 = i * angle_step
        theta2 = (i + 1) * angle_step
        x1 = cx + (r + offset) * math.cos(theta1)
        y1 = cy + (r + offset) * math.sin(theta1)
        x2 = cx + (r + offset) * math.cos(theta2)
        y2 = cy + (r + offset) * math.sin(theta2)
        if first:
            path_parts.append(f"M{x1:.3f},{y1:.3f}")
            first = False
        large_arc = 0
        path_parts.append(f"A{r + offset},{r + offset} 0 {large_arc},1 {x2:.3f},{y2:.3f}")

    if offset == 0:
        path_parts.append("Z")
    else:
        # internal path
        for i in range(total_segments):
            theta1 = (total_segments - i) * angle_step
            theta2 = (total_segments - i - 1) * angle_step
            x1 = cx + (r - offset) * math.cos(theta1)
            y1 = cy + (r - offset) * math.sin(theta1)
            x2 = cx + (r - offset) * math.cos(theta2)
            y2 = cy + (r - offset) * math.sin(theta2)
            if i == 0:
                path_parts.append(f"M{x1:.3f},{y1:.3f}")
            path_parts.append(f"A{r - offset},{r - offset} 0 0,0 {x2:.3f},{y2:.3f}")

    return "\n".join(path_parts)

 

def generate_v_ellipse_path(el, offset, line_join, segments=0):
    cx = float(el.get("cx", 0))
    cy = float(el.get("cy", 0))
    rx = float(el.get("rx", 0))
    ry = float(el.get("ry", 0))

    if segments == 0:
        return f"""
            M{cx - rx - offset},{cy} a{rx + offset},{ry + offset} 0 1,0 {2 * (rx + offset)},0 
            a{rx + offset},{ry + offset} 0 1,0 -{2 * (rx + offset)},0 Z
        """

    path_parts = []
    total_segments = 4 * (2 ** segments)  # e.g. 4, 8, 16, 32...
    angle_step = 2 * math.pi / total_segments
    first = True

    # outer
    for i in range(total_segments):
        theta1 = i * angle_step
        theta2 = (i + 1) * angle_step
        x1 = cx + (rx + offset) * math.cos(theta1)
        y1 = cy + (ry + offset) * math.sin(theta1)
        x2 = cx + (rx + offset) * math.cos(theta2)
        y2 = cy + (ry + offset) * math.sin(theta2)
        if first:
            path_parts.append(f"M{x1:.3f},{y1:.3f}")
            first = False
        path_parts.append(f"A{rx + offset},{ry + offset} 0 0,1 {x2:.3f},{y2:.3f}")

    if offset == 0:
        path_parts.append("Z")
    else:
        # innner
        for i in range(total_segments):
            theta1 = (total_segments - i) * angle_step
            theta2 = (total_segments - i - 1) * angle_step
            x1 = cx + (rx - offset) * math.cos(theta1)
            y1 = cy + (ry - offset) * math.sin(theta1)
            x2 = cx + (rx - offset) * math.cos(theta2)
            y2 = cy + (ry - offset) * math.sin(theta2)
            if i == 0:
                path_parts.append(f"M{x1:.3f},{y1:.3f}")
            path_parts.append(f"A{rx - offset},{ry - offset} 0 0,0 {x2:.3f},{y2:.3f}")

    return "\n".join(path_parts)


#----------------------------------------
# <rect> to Path: Variant
#----------------------------------------
# e.g. (taper affect to a rectangle)
def rect_variant(el,params,is_closed,path_data):
    x = el.get("x",0)# 0
    y = el.get("y",0)# 0
    h = el.get("height",1)
    w = el.get("width" ,1)
    #print(f"Rect: {el}")#[x,y,w,h]
    tag_name  = el['tagName'] # = "path"
    path_data = el['d'] = rect_to_path(x, y, w, h, division=2)
    is_closed = True
    return get_outline_from_path(el, tag_name, params, is_closed, path_data)


def _to_float(v: Num, *, dpi: float = 96.0) -> float:
    """ to float( px )"""
    if isinstance(v, (int, float)):# Safety Type check 
        return float(v)
    v = str(v).strip().lower()

    # Table (Based on standard 96dpi)
    unit_table = {
        "":    1.0,              # has not unit
        "px":  1.0,
        "in":  dpi,
        "cm":  dpi / 2.54,
        "mm":  dpi / 25.4,
        "pt":  dpi / 72.0,
        "pc":  dpi / 6.0,
    }

    # Separate unit and value
    unit = ""
    while v and (v[-1].isalpha() or v[-1] == "%"):# Is the string only use alphabet?
        unit = v[-1] + unit
        v = v[:-1]

    try:
        num = float(v)
        coeff = unit_table.get(unit, 1.0)  # Unsupport type treat as px
        return num * coeff
    except ValueError:
        raise ValueError(f"Err: Value '{v + unit}' can't convert to px")


def rect_to_path(
    x: Num, y: Num, width: Num, height: Num,
    *, division: int = 0, precision: int = 3
) -> str:
    x, y, w, h = map(_to_float, (x, y, width, height))
    if w <= 0 or h <= 0:
        raise ValueError("Err: width and height must greater than 0 ")
    """
    <rect …/>  to  d="M … Z"

    Parameters
    ----------
    x, y          : Left-top of a coodinates
    width, height : Width and height
    division      : Division of the short edge 
                    0 : No division,just keeps the original 4 corner points 
                    1 : Divide by 2 parts(short edge)（A-M-B）  
                    2 : Divide by 3 parts …
    precision     : The decimal part of floating points for coordinates rounding

    Returns
    -------
    SVG path string (d attribute)
    """

    # Step1: Set 4 point with clockwise
    A = (x, y)
    B = (x + w, y)
    C = (x + w, y + h)
    D = (x, y + h)
    corners: List[Tuple[float, float]] = [A, B, C, D]

    # Set2: standard split, short edge and one segment of itself
    short_len = min(w, h)
    # division==0 : whole segment of short edge
    short_seg_len = short_len / max(1, division + 1)

    def n_segments(edge_len: float, is_short_edge: bool) -> int:
        """What numbers using split the edge"""
        if is_short_edge:
            return max(1, division + 1)        # short edge: division+1 segment
        # long edge is split by par short edge segment
        return max(1, round(edge_len / short_seg_len))

    # Step3 make interpolate points each 4 edges
    edges = [(A, B), (B, C), (C, D), (D, A)]
    path_pts: List[Tuple[float, float]] = []

    for (P, Q) in edges:
        Px, Py, Qx, Qy = *P, *Q
        dx, dy = Qx - Px, Qy - Py
        L = math.hypot(dx, dy)

        short_edge = math.isclose(L, short_len, rel_tol=1e-9, abs_tol=1e-9)
        segs = n_segments(L, short_edge)

        # Convert the segment x segs(contains end points) to segs +1 
        for i in range(segs + 1):
            # Only the 1st edge,use i==0,later avoid dupulication
            if path_pts and i == 0:
                continue
            t = i / segs
            path_pts.append((Px + dx * t, Py + dy * t))

    # Step4 export as d attribute  
    f = lambda v: f"{v:.{precision}f}".rstrip("0").rstrip(".")
    head = f"M {f(path_pts[0][0])},{f(path_pts[0][1])}"
    body = " ".join(f"L {f(x)},{f(y)}" for x, y in path_pts[1:])
    return f"{head} {body} Z"


#-------------------------------
#  Offset processing (+ angle)
#-------------------------------
def offset_path(pData,params, offset, line_join, mitl, taper_mode, order=True):

        # SVG analysis 
    try:
        # epsilon: sampling interval  
        # delta: small offset for tangent calculation
        # 

        # epsilon: this value > 1
        # delta: tangent progression 
        # rdp_epsilon: curve point resolution
        # factor (0-100)
        
        points = []


        flavor = ((params['factor']*0.01)-0.05)          if taper_mode == "none" and line_join == "round" else 0
        flavor = ((params['factor']*0.01)*1.5-0.5)+0.01  if taper_mode == "none" and line_join == "miter" else 0

        if line_join == "round":
            adj = 0.75 if taper_mode in ['rough'] else 0
            epsilon, delta, rdp_epsilon =   1.1, 4, 0.38+flavor+adj
        elif line_join == "bevel":
            epsilon, delta, rdp_epsilon =   3.3, 1, 0.4
        elif line_join == "miter":
            epsilon, delta, rdp_epsilon =   2.0, 2, 1.2+flavor 

 

        # Offset and angle processing:   points = {'x':,'y': ,'rotate': }}
        points = calculate_offset_points(pData,params, offset, epsilon, delta, line_join, mitl, taper_mode)

        if debug:
            print(points)

        if points is None:
            print("Error: calculate_offset_points returned None")
            return []

        # Change order based on line directioƒn
        if not order:
            points = points[::-1]

        if taper_mode == "stamp_top_group" :
            pts = points
        else:
            pts = rdp(points, rdp_epsilon, line_join)

        # More simplify
        if taper_mode in [ "fluffy", "punk" ]:
             pts = rdp(pts, 1.0, line_join)
        
        # Directional effect
        type = ["brush","brush2"]
        brush2_caps = params['cap_a'] in type or params['cap_b'] in type # True/False
        dir_shift = params['taper_mode'] not in ["none", "rough","dynamic_dash","random_dash","round_dot_dash"] and brush2_caps # True/False


        if dir_shift and len(pts) >= 2:
            for i in range(3, len(pts) - 3):  # Processing it only safe range
                p1 = pts[i]
                p2 = pts[i + 2]
                
                flag = (i % 3 == 0)
                shift_amt = 1 if flag else 4
                p1_shifted, p2_shifted = shift_point_along_stroke(p1, p2, flag, shift_amount=shift_amt)
                # Override
                pts[i] = p1_shifted
                pts[i + 2] = p2_shifted
        
                # Option : Copy list
                # shifted_pts.append(p1_shifted)



        return pts

    except Exception as error:
        print("Error processing offset_path:", error)
        print(traceback.format_exc())
        return []




# Extract commands and arguments from SVG path string

def parse_svg_path(d):
    """
    Parse to d attribute of SVG path tag,
    Return a list of tuples, each containing a command and a list of float parameters.
    Supports comma separators and scientific notation.
    """
    # Regular expression that match commands or numbers
    token_re = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?')
    tokens = token_re.findall(d)
    if not tokens:print("Error:not tokens");return []
    
    result = []
    current_cmd = None
    params = []
    for token in tokens:
        if token.isalpha():
            # Store if previous command and parameters exist
            if current_cmd is not None:
                result.append((current_cmd, params))
            current_cmd = token
            params = []
            # Store immediately for 'Z' command since it has no parameters
            if current_cmd.upper() == 'Z':
                result.append((current_cmd, []))
                current_cmd = None
        else:
            try:
                val = float(token)
                params.append(val)
            except Exception as e:
                # Ignore if it can't convert to number
                continue
    if current_cmd is not None:
        result.append((current_cmd, params))
    return result


def arc_center_parameters(x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2):
    """
    This function calculates three values for the 'A' (arc) command:
    (1) The center coordinates (cx, cy) of the ellipse
    (2) theta1 – the start angle
    (3) delta_theta – the angle difference
    Phi represents the rotation of the x-axis (in degrees), and is internally converted to radians
    """
    # Convert to radian
    phi = math.radians(phi)
    
    # Step1: Calculate (x1', y1')
    dx2 = (x1 - x2) / 2.0
    dy2 = (y1 - y2) / 2.0
    x1p = math.cos(phi) * dx2 + math.sin(phi) * dy2
    y1p = -math.sin(phi) * dx2 + math.cos(phi) * dy2

    #  If cordinate (rx, ry) not enough,increase it
    rx = abs(rx)
    ry = abs(ry)
    lambda_val = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
    if lambda_val > 1:
        rx *= math.sqrt(lambda_val)
        ry *= math.sqrt(lambda_val)
    
    # Step2: Calculate center coordinate (cx', cy') 
    factor_numer = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    factor_denom = rx**2 * y1p**2 + ry**2 * x1p**2
    # To prevent numerical errors, adjust so that the value does not become less than 0.
    factor = math.sqrt(max(0, factor_numer / factor_denom))
    if large_arc_flag == sweep_flag:
        factor = -factor
    cxp = factor * (rx * y1p) / ry
    cyp = factor * (-ry * x1p) / rx

    # Step 3: Reset to original coordinate system and calculate the center (cx, cy)
    cx = math.cos(phi) * cxp - math.sin(phi) * cyp + (x1 + x2) / 2.0
    cy = math.sin(phi) * cxp + math.cos(phi) * cyp + (y1 + y2) / 2.0

    def angle(u, v):
        # Calculate the signed angle between two vectors u and v
        dot = u[0]*v[0] + u[1]*v[1]
        mag_u = math.sqrt(u[0]**2 + u[1]**2)
        mag_v = math.sqrt(v[0]**2 + v[1]**2)
        cos_angle = dot / (mag_u * mag_v)
        # Clamp value to [-1, 1] to avoid floating-point errors
        cos_angle = max(min(cos_angle, 1), -1)
        sign = 1 if (u[0]*v[1] - u[1]*v[0]) >= 0 else -1
        return sign * math.acos(cos_angle)
    
    # Step 4: Calculate the starting angle (theta1) and the angle difference (delta_theta)
    ux = (x1p - cxp) / rx
    uy = (y1p - cyp) / ry
    vx = (-x1p - cxp) / rx
    vy = (-y1p - cyp) / ry
    
    theta1 = angle((1, 0), (ux, uy))
    delta_theta = angle((ux, uy), (vx, vy))
    
    if sweep_flag == 0 and delta_theta > 0:
        delta_theta -= 2 * math.pi
    elif sweep_flag == 1 and delta_theta < 0:
        delta_theta += 2 * math.pi

    return cx, cy, rx, ry, phi, theta1, delta_theta

def calculate_arc_length(x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2, num_samples=100):
    """
    This function numerically approximates the length of an elliptical arc segment using split sampling.
    It divides the arc into a number of intermediate points (based on num_samples), 
    and estimates the arc length as the sum of distances between those points.
    """
    cx, cy, rx, ry, phi, theta1, delta_theta = arc_center_parameters(
        x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2
    )
    length = 0.0
    prev_x, prev_y = None, None
    # Sample at regular intervals from theta1 to (theta1 + delta_theta)
    for i in range(num_samples+1):
        t = theta1 + (delta_theta * i / num_samples)
        x = cx + rx * math.cos(phi) * math.cos(t) - ry * math.sin(phi) * math.sin(t)
        y = cy + rx * math.sin(phi) * math.cos(t) + ry * math.cos(phi) * math.sin(t)
        if prev_x is not None:
            length += math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
        prev_x, prev_y = x, y
    return length

def interpolate_arc_point(x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2, ratio):
    """
    Returns a point on the elliptical arc between the start and end points,
    interpolated by a ratio from 0.0 to 1.0.

    """
    cx, cy, rx, ry, phi, theta1, delta_theta = arc_center_parameters(
        x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2
    )
    t = theta1 + (delta_theta * ratio)
    x = cx + rx * math.cos(phi) * math.cos(t) - ry * math.sin(phi) * math.sin(t)
    y = cy + rx * math.sin(phi) * math.cos(t) + ry * math.cos(phi) * math.sin(t)
    return {'x': x, 'y': y}



def calculate_cubic_bezier_length(P0, P1, P2, P3, num_samples=100):
    """
    Calculate the length of a cubic Bézier curve using linear approximation via sampled points.
    """
    length = 0.0
    prev_x, prev_y = P0
    for i in range(1, num_samples + 1):
        t = i / num_samples
        x, y = cubic_bezier_point(P0, P1, P2, P3, t)
        length += math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
        prev_x, prev_y = x, y
    return length

def cubic_bezier_point(P0, P1, P2, P3, t):
    """
    Returns the point on a cubic Bézier curve by interpolating the parameter t (from 0 to 1).
    """
    x = (1 - t) ** 3 * P0[0] + 3 * (1 - t) ** 2 * t * P1[0] + 3 * (1 - t) * t ** 2 * P2[0] + t ** 3 * P3[0]
    y = (1 - t) ** 3 * P0[1] + 3 * (1 - t) ** 2 * t * P1[1] + 3 * (1 - t) * t ** 2 * P2[1] + t ** 3 * P3[1]
    return x, y

def quadratic_bezier_point(P0, P1, P2, t):
    """
    Return the point on a Quadratic Bézier curve by interpolating the parameter t (from 0 to 1)
    """
    x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t ** 2 * P2[0]
    y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t ** 2 * P2[1]
    return x, y

def calculate_quadratic_bezier_length(P0, P1, P2, num_samples=100):
    """
    Calculate the length of Quadratic Bézier curve by linear approximation via sampled points
    """
    length = 0.0
    prev_x, prev_y = P0
    for i in range(1, num_samples + 1):
        t = i / num_samples
        x, y = quadratic_bezier_point(P0, P1, P2, t)
        length += math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
        prev_x, prev_y = x, y
    return length

def calculate_total_length_and_points_tagged(d, divisions=182):
    """
    Returns a dictionary containing the total path length and tag information 
    attached to each subdivided point (including arcs).
    """
    
    #print(f"d:{d}")
    commands = parse_svg_path(d)


    #print(f"commands:{commands}")

    prev_x, prev_y = 0, 0
    start_x, start_y = 0, 0
    total_length = 0
    tagged_points = []

    # These store control points for 'S' and 'T' commands in previous time
    last_cubic_ctrl = None
    last_quadratic_ctrl = None

    for cmd, params in commands:
        if cmd == 'M':  # MoveTo: This command recorded as a starting point of sub-path
            prev_x, prev_y = params[0], params[1]
            start_x, start_y = prev_x, prev_y
            last_cubic_ctrl = None
            last_quadratic_ctrl = None
            # 'M' command not use for draw,so tagged to draw:False
            tagged_points.append({'x': prev_x, 'y': prev_y, 'cmd': 'M', 'draw': False})

        elif cmd in ['L', 'l']:  # LineTo (absolute & relative)
            x, y = params[0], params[1]
            if cmd == 'l':  # Add delta based on current cooridnates if relative command
                x += prev_x
                y += prev_y
        
            segment_length = math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
            for i in range(divisions):
                ratio = (i + 1) / divisions
                point_x = prev_x + ratio * (x - prev_x)
                point_y = prev_y + ratio * (y - prev_y)
                tagged_points.append({
                    'x': point_x,
                    'y': point_y,
                    'cmd': cmd,  # 'L' or 'l'
                    'draw': True
                })
            total_length += segment_length
            prev_x, prev_y = x, y
            last_cubic_ctrl = None
            last_quadratic_ctrl = None
        
        elif cmd in ['H', 'h']:  # Horizontal LineTo
            x = params[0]
            if cmd == 'h':  # Relative
                x += prev_x
        
            segment_length = abs(x - prev_x)
            for i in range(divisions):
                ratio = (i + 1) / divisions
                point_x = prev_x + ratio * (x - prev_x)
                tagged_points.append({
                    'x': point_x,
                    'y': prev_y,
                    'cmd': cmd,  # 'H' or 'h'
                    'draw': True
                })
            total_length += segment_length
            prev_x = x
            last_cubic_ctrl = None
            last_quadratic_ctrl = None
        
        elif cmd in ['V', 'v']:  # Vertical LineTo
            y = params[0]
            if cmd == 'v':  # Relative 
                y += prev_y
        
            segment_length = abs(y - prev_y)
            for i in range(divisions):
                ratio = (i + 1) / divisions
                point_y = prev_y + ratio * (y - prev_y)
                tagged_points.append({
                    'x': prev_x,
                    'y': point_y,
                    'cmd': cmd,  # 'V' or 'v'
                    'draw': True
                })
            total_length += segment_length
            prev_y = y
            last_cubic_ctrl = None
            last_quadratic_ctrl = None
        # Cubic Bézier
        elif cmd in ['C', 'c']:
            j = 0
            while j + 5 < len(params):
                x1, y1, x2, y2, x, y = params[j:j+6]
                # Relative
                if cmd == 'c':
                    x1 += prev_x; y1 += prev_y
                    x2 += prev_x; y2 += prev_y
                    x  += prev_x; y  += prev_y

                # Origin and control points
                P0 = (prev_x, prev_y)
                P1 = (x1, y1)
                P2 = (x2, y2)
                P3 = (x, y)

                # Calculate length,and add division points
                seg_len = calculate_cubic_bezier_length(P0, P1, P2, P3, num_samples=100)
                for i in range(divisions):
                    t = (i + 1) / divisions
                    bx, by = cubic_bezier_point(P0, P1, P2, P3, t)
                    tagged_points.append({
                        'x': bx,
                        'y': by,
                        'cmd': cmd,   # 'C' or 'c'
                        'draw': True
                    })
                total_length += seg_len

                # update
                prev_x, prev_y = x, y
                last_cubic_ctrl    = (x2, y2)
                last_quadratic_ctrl = None

                j += 6
        # Smooth Cubic Bézier 
        elif cmd in ['S', 's']:
            x2, y2, x, y = params
            if cmd == 's':
                x2 += prev_x; y2 += prev_y
                x  += prev_x; y  += prev_y

            P0 = (prev_x, prev_y)
            if last_cubic_ctrl:
                # Reflection of 2ndary control point at previous time
                refl = (2*prev_x - last_cubic_ctrl[0],
                        2*prev_y - last_cubic_ctrl[1])
            else:
                refl = (prev_x, prev_y)

            P1, P2, P3 = refl, (x2, y2), (x, y)
            seg_len = calculate_cubic_bezier_length(P0, P1, P2, P3, num_samples=100)
            for i in range(divisions):
                t = (i + 1) / divisions
                bx, by = cubic_bezier_point(P0, P1, P2, P3, t)
                tagged_points.append({
                    'x': bx,
                    'y': by,
                    'cmd': cmd,  # 'S' or 's'
                    'draw': True
                })
            total_length += seg_len

            prev_x, prev_y     = x, y
            last_cubic_ctrl    = (x2, y2)
            last_quadratic_ctrl = None
        # Quadratic Bézier
        elif cmd in ['Q', 'q']:
            x1, y1, x, y = params
            if cmd == 'q':
                x1 += prev_x; y1 += prev_y
                x  += prev_x; y  += prev_y

            P0 = (prev_x, prev_y)
            P1 = (x1, y1)
            P2 = (x, y)
            seg_len = calculate_quadratic_bezier_length(P0, P1, P2, num_samples=100)
            for i in range(divisions):
                t = (i + 1) / divisions
                bx, by = quadratic_bezier_point(P0, P1, P2, t)
                tagged_points.append({
                    'x': bx,
                    'y': by,
                    'cmd': cmd,  # 'Q' or 'q'
                    'draw': True
                })
            total_length += seg_len

            prev_x, prev_y     = x, y
            last_quadratic_ctrl = (x1, y1)
            last_cubic_ctrl     = None

        # Smooth Quadratic Bézier curve
        elif cmd in ['T', 't']:
            x, y = params
            if cmd == 't':
                x += prev_x; y += prev_y

            P0 = (prev_x, prev_y)
            if last_quadratic_ctrl:
                refl = (2*prev_x - last_quadratic_ctrl[0],
                        2*prev_y - last_quadratic_ctrl[1])
            else:
                refl = (prev_x, prev_y)

            P1, P2 = refl, (x, y)
            seg_len = calculate_quadratic_bezier_length(P0, P1, P2, num_samples=100)
            for i in range(divisions):
                t = (i + 1) / divisions
                bx, by = quadratic_bezier_point(P0, P1, P2, t)
                tagged_points.append({
                    'x': bx,
                    'y': by,
                    'cmd': cmd,  # 'T' or 't'
                    'draw': True
                })
            total_length += seg_len

            prev_x, prev_y     = x, y
            last_quadratic_ctrl = refl
            last_cubic_ctrl     = None

        elif cmd in ['A', 'a']:  # Arc command (absolute and relative)
            rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y = params
            
            if cmd == 'a':  # Relative coordinates
                x += prev_x
                y += prev_y
            
            segment_length = calculate_arc_length(prev_x, prev_y, rx, ry, x_axis_rotation,
                                                int(large_arc_flag), int(sweep_flag), x, y)
            for i in range(divisions):
                ratio = (i + 1) / divisions
                point = interpolate_arc_point(prev_x, prev_y, rx, ry, x_axis_rotation,
                                            int(large_arc_flag), int(sweep_flag), x, y, ratio)
                tagged_points.append({
                    'x': point['x'],
                    'y': point['y'],
                    'cmd': cmd,  # 'A' or 'a' 
                    'draw': True
                })
            total_length += segment_length
            prev_x, prev_y = x, y
            last_cubic_ctrl = None
            last_quadratic_ctrl = None


        elif cmd == 'Z':  # ClosePath: A line segment from end point to start point of a sub-path
            segment_length = math.sqrt((start_x - prev_x) ** 2 + (start_y - prev_y) ** 2)
            total_length += segment_length
            for i in range(divisions):
                ratio = (i + 1) / divisions
                point_x = prev_x + ratio * (start_x - prev_x)
                point_y = prev_y + ratio * (start_y - prev_y)
                # Adjust whether to include the closed line segment (generated by the 'Z' command) 
                # as a drawing target, depending on rendering necessity.
                # If this segment should be excluded, set the 'draw' flag to False.
                tagged_points.append({
                    'x': point_x,
                    'y': point_y,
                    'cmd': 'Z',
                    'draw': True
                })
            prev_x, prev_y = start_x, start_y
            last_cubic_ctrl = None
            last_quadratic_ctrl = None

    return total_length, tagged_points

# ----------------------------
#  Reverse pData
# ----------------------------
def reversed_svg_points(points, close_path=True):
    reversed_points = points[::-1]

    first_draw = None
    last_draw = None
    # get i = index, p = array
    for i, p in enumerate(reversed_points):
        if p['draw']:
            if first_draw is None:
                first_draw = i
            last_draw = i

    # change 1st/last command to M/Z
    if first_draw is not None:
        reversed_points[first_draw]['cmd'] = 'M'
    if close_path and last_draw is not None:
        reversed_points[last_draw]['cmd'] = 'Z'

    return reversed_points


#----------------------------
# All of corner type offset
#----------------------------
def add_final_point(pData, offset, delta):
    length = pData['length']

    # Safe range
    if length <= len(pData['points']):
        final_point = pData['points'][length - 1]
        return final_point
    else:
        # print("Invalid index: data forced to 0th")
        final_point = pData['points'][0]
        return final_point


def shift_point_along_stroke(p1, p2, flag ,shift_amount):
    dx = p2['x'] - p1['x']
    dy = p2['y'] - p1['y']
    length = math.hypot(dx, dy)

    if length == 0:
        return p1.copy(), p2.copy()

    dir_x = dx / length
    dir_y = dy / length

    p1_shifted = p1.copy()
    p2_shifted = p2.copy()

    p1_shifted['x'] += dir_x * (0 if not flag else shift_amount)
    p1_shifted['y'] += dir_y * shift_amount
    p2_shifted['x'] += dir_x * (0 if not flag else shift_amount)
    p2_shifted['y'] += dir_y * shift_amount
    return p1_shifted, p2_shifted



#----------------------------
# Calclate offset points
#----------------------------
def calculate_offset_points(pData,params, offset, epsilon, delta, line_join, mitl, taper_mode):

    #debug mockup
    #pData = {
    #    'length': 800,
    #    'points': [{'x': i, 'y': 0, 'cmd':'L' ,'draw': True} for i in range(0, 800, 10)]
    #}
    #params['factor'] =1.0

    total_length = pData['length']
    points = pData['points']
    factor = params['factor']

    #print(total_length,"___",len(points))

    offset_points = []
    max_offset = offset

    # Create tapered or simple offset path
    offset_points = taper_offset_points(pData, params, offset, epsilon, delta, line_join, mitl, taper_mode)

    # Calculate final offset point
    final_point = add_final_point(pData, offset, delta) # experimental
    offset_points.append(final_point)

    extended_offset_points = []
    i = 0

    # Caluclate the extended offset point, and make corner points
    # THe value i : current point of offset_points
    # STEP 1: Make a offseted-line form pair of neighbor offset_points(p1,p2(i,i+1)) and connect them 
    # STEP 2: Check each curvature of them 
    # STEP 3: Go to STEP 4 if detect it whether sharp peak or right-angle corner,Otherwise to STEP1

    # STEP 4: Find a intersection from both of neighbor offseted-lines (with extend them length)
    # STEP 5: Insert the intersection to between offseted-line (use p3,p4 (i+2,i+3)) 
    # STEP 6: Append them (coordinates) according an order to extended_offsetpoints

    #print(f"No.{i} {offset_points[i]}")
    #if dir_shift:#random.uniform(-2.0, 2.0)
    #    if i > 2 and i + 1 < len(offset_points) - 1:
    #       p1, p2 = shift_point_along_stroke(p1, p2,True, shift_amount=8)

    b2flag = True if params['cap_a'] == "brush2" or params['cap_b'] == "brush2" else False


    for i in range(len(offset_points) - 1):
    # while i < len(offset_points) - 1:
        p1 = offset_points[i]
        p2 = offset_points[i + 1]

        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Detect with 1/5 epsilon granularity, Error if value is 5 / 3?
        if line_join == "bevel" and distance > epsilon * 0.1 and i < len(offset_points) - 3:

            if i + 3 < len(offset_points):
                p3 = offset_points[i + 2]
                p4 = offset_points[i + 3]
                ex = 250  # Extend distance

                if b2flag:
                    shift_amt = 12
                    p3, p2 = shift_point_along_stroke(p3, p2,  True, shift_amount=shift_amt)


                # Calucrate angle difference
                angle1 = math.atan2(p2['y'] - p1['y'], p2['x'] - p1['x']) * (180 / math.pi)
                angle2 = math.atan2(p3['y'] - p2['y'], p3['x'] - p2['x']) * (180 / math.pi)
                angle_difference = abs(angle2 - angle1)
                if angle_difference > 180:
                    angle_difference = 360 - angle_difference
    
                # Handle sharp peaks and right-angle corners
                if 1 < angle_difference < 95:
                    extended_offset_points.extend([p1, p2])
                    i += 4
                    continue
        if line_join == "miter" and distance > epsilon * 0.1 and i < len(offset_points) - 3:


            if i + 3 < len(offset_points):
                p3 = offset_points[i + 2]
                p4 = offset_points[i + 3]
                ex = 250  # Extend distance
               


                # Calucrate angle difference
                angle1 = math.atan2(p2['y'] - p1['y'], p2['x'] - p1['x']) * (180 / math.pi)
                angle2 = math.atan2(p3['y'] - p2['y'], p3['x'] - p2['x']) * (180 / math.pi)
                angle_difference = abs(angle2 - angle1)
                if angle_difference > 180:
                    angle_difference = 360 - angle_difference
    
                # Handle sharp peaks and right-angle corners
                if 1 < angle_difference < 95:
                    intersect = intersect_miter(p1, p2, p3, p4, ex)
    
                    if intersect is not None:
    
                        if debug:# Display curvature and intersection point(s)
                            ang = math.floor(angle_difference * 10) / 10
                            dbg.plot_dot_param2(intersect, ang, "lightgray", 2.0,"2.8em")
    
                        c_top = intersect
                        miter_cut_flag = calculate_miter_limit(p2, p3, c_top, max_offset, mitl)
    
                        if not miter_cut_flag:
                            extended_offset_points.extend([p1, intersect, p4])
                            i += 4
                        else:
                            extended_offset_points.extend([p2, p3])
                            i += 4
                        continue

        # In other cases, just add it
        extended_offset_points.append(p1)
        i += 1
        # While Loop End

    # Append a last point

    extended_offset_points.append(offset_points[-1])
    return extended_offset_points


#--------------------------------------------
# Miter .
#--------------------------------------------
# Find the intersection of offsets in the Miter case.
def intersect_miter(p1, p2, p3, p4, ex , op=False):
    # Extend p1, p2
    dx1 = p2['x'] - p1['x']
    dy1 = p2['y'] - p1['y']
    len1 = math.sqrt(dx1 ** 2 + dy1 ** 2)
    if len1 == 0: len1 = 1
    e1 = {
        'x': p1['x'] - (dx1 / len1) * ex,
        'y': p1['y'] - (dy1 / len1) * ex
    }
    e2 = {
        'x': p2['x'] + (dx1 / len1) * ex,
        'y': p2['y'] + (dy1 / len1) * ex
    }

    # Extend p3, p4
    dx2 = p4['x'] - p3['x']
    dy2 = p4['y'] - p3['y']
    len2 = math.sqrt(dx2 ** 2 + dy2 ** 2)
    if len2 == 0: len2 = 1
    e3 = {
        'x': p3['x'] - (dx2 / len2) * ex,
        'y': p3['y'] - (dy2 / len2) * ex
    }
    e4 = {
        'x': p4['x'] + (dx2 / len2) * ex,
        'y': p4['y'] + (dy2 / len2) * ex
    }

    # Drawing debug lines
    if debug:
        dbg.plot_line( e1, e2, "red")
        dbg.plot_line( e3, e4, "blue")

    # Calclate intersection point (Use a matrix)
    A1 = e2['y'] - e1['y']
    B1 = e1['x'] - e2['x']
    C1 = A1 * e1['x'] + B1 * e1['y']

    A2 = e4['y'] - e3['y']
    B2 = e3['x'] - e4['x']
    C2 = A2 * e3['x'] + B2 * e3['y']

    denominator = A1 * B2 - A2 * B1

    if denominator == 0:
        return p2
        #return {'x': 0, 'y': 0}
        #return None  # If two lines are parallel, no intersection exists.

    if op == False:
        afrac = denominator * 1.7
    else:
        afrac = 1

    x = (B2 * C1 - B1 * C2) / afrac
    y = (A1 * C2 - A2 * C1) / afrac

    # Debug: Visualize of intersection point,dislay them as orrange colord point
    if debug:
        plot_dot(svg_element, {'x': x, 'y': y}, "orange")
        print(f"miter intersect point: {x},{y}")

    return {'x': x, 'y': y}

#----------------------------------------
# Calculate the angle from the path data
#----------------------------------------
def get_point_at_length(points, length):
 

    if length < 0:
        return points[0]  # If negative, return the first point
    elif length >= len(points):
        return points[-1]  # If out of range, return the last point
    else:
        return points[length]  # If index is valid, return it


def get_tangent_at_length(pData, length, total_length, delta):
    points = pData['points']
    n = len(points)
    
    # Calculate the index of the median difference candidate (adjusted for rounding)
    lower = int(round(length - delta))
    upper = int(round(length + delta))
    # Fit within array bounds
    lower = max(0, lower)
    upper = min(n - 1, upper)
    
    # If the indices on both sides are the same, choose the adjacent point if it is an edge
    if lower == upper:
        if lower == 0 and n > 1:
            upper = 1
        elif upper == n - 1 and n > 1:
            lower = n - 2
        else:
            # Retun default direction as fallback
            return {'x': 1, 'y': 0}
    
    p1 = get_point_at_length(points, lower)
    p2 = get_point_at_length(points, upper)
    
    tangent = {'x': p2['x'] - p1['x'], 'y': p2['y'] - p1['y']}
    magnitude = math.sqrt(tangent['x'] ** 2 + tangent['y'] ** 2)
    
    # Fallback for small vectors to prevent division by zero
    if magnitude < 1e-10:
        return {'x': 1, 'y': 0}
    
    return {'x': tangent['x'] / magnitude, 'y': tangent['y'] / magnitude}

#-----------------------------------------------
# miter angle rate 
#-----------------------------------------------
def calculate_miter_limit(P1, P2, miter_top, line_width, miter_limit=10):
    # plotDot(svg_element, miter_top, "blue", 2)  # debug

    line_width = -abs(line_width)

    if line_width > 0:
        print(f"Err: An invalid lineWidth value ({line_width}) was entered")
        return False

    # Calculate the vector:P1 to miter_top
    dir1 = {
        'x': miter_top['x'] - P1['x'],
        'y': miter_top['y'] - P1['y']
    }

    # Calculate the normal vector
    normal = {
        'x': -dir1['y'],
        'y': dir1['x']  # Normal direction
    }
    normal_length = math.sqrt(normal['x'] ** 2 + normal['y'] ** 2)
    if normal_length == 0:normal_length = 0.001
    normalized_normal = {
        'x': normal['x'] / normal_length,
        'y': normal['y'] / normal_length
    }

    # Move P1 in the normal direction by -offset
    xoffset = -line_width  # Move negative direction
    miter_btm = {
        'x': P1['x'] + normalized_normal['x'] * xoffset,
        'y': P1['y'] + normalized_normal['y'] * xoffset
    }

    return miter_btm


#-----------------------------------------------
# Export coordinate list and SVG Path commands
#-----------------------------------------------s
def points_to_path_data(points,tag=""):
    if not points or not isinstance(points, list):  # list type check
        return ""
    d=""
        
    try:
        ds = f"L {points[0]['x']},{points[0]['y']} "
    except Exception as e:
        d = ""
        print(f"Err:pt2path {points} Tag:{tag}")
        return d
        #debug_message(f"Err: {points} Tag:{tag}")
    
    
    for point in points:
        d += f"L {point['x']},{point['y']} "
    return d.strip()

#---------------------------------------------
# Ramer-Douglas-Peucker algorithm (Path simplify)
#---------------------------------------------
def rdp(points, epsilon, line_join):

    points = clean_intersections(points, 0.3 if line_join == 'round' else 0.1) # 6 , 3
    if len(points) < 3:
        return points

    dmax = {'value': 0, 'index': 0}
    end = len(points) - 1

    for i in range(1, end):
        # Draw a perpendicular line from the reference line that connects 
        # the start and end points of the path to each point along the way,
        # and find out how far the point is from the line.
        d = perpendicular_distance(points[i], points[0], points[end])
        if dmax['value'] < d:
            dmax['value'] = d
            dmax['index'] = i

    # If the distance between the points is greater than epsilon, recursively thin out the interval.
    if dmax['value'] > epsilon:
        rec_results1 = rdp(points[:dmax['index'] + 1], epsilon, line_join)
        rec_results2 = rdp(points[dmax['index']:], epsilon, line_join)
        return rec_results1[:-1] + rec_results2
    else:
        return [points[0], points[end]]




#---------------------------------------------
# Clean up points such as straight lines
#---------------------------------------------

def extract_fixed_count_points(points, pData , count):
    path_length = pData['length']
    interval = path_length / (count - 1)
    return extract_evenly_spaced_points(points, interval)


def compute_distances(points):
    distances = [0]
    total = 0
    for i in range(1, len(points)):
        dx = points[i]['x'] - points[i-1]['x']
        dy = points[i]['y'] - points[i-1]['y']
        d = math.hypot(dx, dy)
        total += d
        distances.append(total)
    return distances


def extract_evenly_spaced_points(points, interval):
    distances = compute_distances(points)
    result = [points[0]]
    target_dist = interval
    i = 1

    while i < len(points):
        if distances[i] >= target_dist:
            # linear interpolate
            ratio = (target_dist - distances[i-1]) / (distances[i] - distances[i-1])
            x = points[i-1]['x'] + ratio * (points[i]['x'] - points[i-1]['x'])
            y = points[i-1]['y'] + ratio * (points[i]['y'] - points[i-1]['y'])
            angle = points[i-1]['angle'] + ratio * (points[i]['angle'] - points[i-1]['angle'])
            result.append({'x': x, 'y': y, 'angle': angle})
            target_dist += interval
        else:
            i += 1

    return result

def estimate_angle(points, i):
    if i == 0:
        # get an angle with next point
        dx = points[i+1]['x'] - points[i]['x']
        dy = points[i+1]['y'] - points[i]['y']
    elif i > 0:
        dx = points[i]['x'] - points[i-1]['x']
        dy = points[i]['y'] - points[i-1]['y']
    else:
        return 0.0
    return math.degrees(math.atan2(dy, dx))

#---------------------------------------------
# Clean up points such as straight lines
#---------------------------------------------
def clean_intersections(points, tol=0.3, step=1):
    result = [points[0]]
    count = 0
    for i in range(1, len(points) - 1):
        prev = points[i - 1]
        curr = points[i]
        next_point = points[i + 1]

        angle = math.atan2(next_point['y'] - curr['y'], next_point['x'] - curr['x']) - \
                math.atan2(curr['y'] - prev['y'], curr['x'] - prev['x'])

        if abs(angle) < math.pi / tol:
            count += 1
            if count % step == 0:
                result.append(curr)
        else:
            result.append(curr)
            count = 0  # reset when the angle is big (i.e., turning)

    result.append(points[-1])
    return result


#-------------------------------------------------------------------
# Draw a perpendicular line and find the distance
#-------------------------------------------------------------------
def perpendicular_distance_(point, line_start, line_end):
    area = abs(0.5 * (line_start['x'] * line_end['y'] + line_end['x'] * point['y'] + point['x'] * line_start['y'] -
                      line_end['x'] * line_start['y'] - point['x'] * line_end['y'] - line_start['x'] * point['y']))
    bottom = math.sqrt((line_start['x'] - line_end['x']) ** 2 + (line_start['y'] - line_end['y']) ** 2)
    return (2 * area) / bottom




def perpendicular_distance(point, line_start, line_end):
    area = abs(0.5 * (line_start['x'] * line_end['y'] + line_end['x'] * point['y'] + point['x'] * line_start['y'] -
                      line_end['x'] * line_start['y'] - point['x'] * line_end['y'] - line_start['x'] * point['y']))
    bottom = math.sqrt((line_start['x'] - line_end['x']) ** 2 + (line_start['y'] - line_end['y']) ** 2)
    
    # Check 0 divide
    if bottom == 0:
        return 0
    return (2 * area) / bottom



#-----------------------------------------------
# Line CAP support functions
#-----------------------------------------------
def get_cap_vector(A, B, t, offset, is_curve=False):


    # The case of same coordinate A and B
    if A['x'] == B['x'] and A['y'] == B['y']:

        print(f"Warning: Same coordinates detected on cap vector")
        a_x = A['x'];a_y = A['y']
        b_x = A['x'];b_y = A['y'] - 0.0001
        # Apply a small offset to resolve ambiguity when coordinates are identical.
        return [{'baseX': a_x, 'baseY': a_y, 'offsetX': b_x, 'offsetY': b_y}]
        # return False

    # Linear interpolation (A to B)
    x = A['x'] + t * (B['x'] - A['x'])
    y = A['y'] + t * (B['y'] - A['y'])

    # Calclate directional vector of the line
    dx = B['x'] - A['x']
    dy = B['y'] - A['y']

    # Separate processing depending on whether it is a curve or not
    if not is_curve:
        # Set direction and reference for straight lines
        direction = -1 if t < 0.5 else 1  # Negative direction if t<0.5, positive direction if t>=0.5
        dx = direction * dx
        dy = direction * dy

    # Calculate the length of a line
    length = math.sqrt(dx ** 2 + dy ** 2)

    # Finding a Unit Vector
    unit_x = dx / length
    unit_y = dy / length

    # Offset Reference Point
    base_x = x  # Use the interpolation point as the reference point
    base_y = y

    # Caluclate offet
    offset_x = base_x + unit_x * offset
    offset_y = base_y + unit_y * offset

    # Calclate the line from base_x, base_y to offset_x, offset_y 
    offset_length = math.sqrt(
        (offset_x - base_x) ** 2 + (offset_y - base_y) ** 2
    )

    # Debug
    if debug:
        dbg.plot_line( {'x': base_x, 'y': base_y}, {'x': offset_x, 'y': offset_y}, "green")

    return [{'baseX': base_x, 'baseY': base_y, 'offsetX': offset_x, 'offsetY': offset_y}]


def get_line_vector(A, B, offset, at_start=True, is_curve=False):
    """
    Calculate directional vector from 2 coordinatesA, B (Dictionary:{'x': ..., 'y': ...})
    to particular end point (based at_start=True:A side, False:B side)
    ,and return new points that moved offset distance
    """
    # Error: same coorinate of A and B
    if A['x'] == B['x'] and A['y'] == B['y']:
        raise ValueError("The coordinates A and B must be different coodinate")
    
    if not is_curve:
        # Linear: Using as base point by end point(A or B)
        base_x, base_y = (A['x'], A['y']) if at_start else (B['x'], B['y'])
        
        # At fist calculate direction of A to B, reverse it if nesssesary
        dx = B['x'] - A['x']
        dy = B['y'] - A['y']
        if at_start:
            dx, dy = -dx, -dy
        
        # Normalizing a vector (making it a unit vector)
        mag = math.sqrt(dx**2 + dy**2)
        if math.isclose(mag, 0):
            raise ValueError("Err: Calculated vector magnitude is 0")
        unit_dx = dx / mag
        unit_dy = dy / mag
        
        # Calclate the offset coodinates
        offset_x = base_x + unit_dx * offset
        offset_y = base_y + unit_dy * offset
        
    else:
        # Curve case: Estimate the tangent using numerical differentiation near the endpoints
        
        # The t value near the end point
        t0 = 0.0001 if at_start else 0.9999
        base_x = A['x'] + t0 * (B['x'] - A['x'])
        base_y = A['y'] + t0 * (B['y'] - A['y'])
        
        # Estimating derivatives using small parameter changes
        epsilon = 1e-6
        t1 = t0 + epsilon if at_start else t0 - epsilon
        point1_x = A['x'] + t1 * (B['x'] - A['x'])
        point1_y = A['y'] + t1 * (B['y'] - A['y'])
        
        # Tangent calculation
        dx = point1_x - base_x
        dy = point1_y - base_y
        
        # Vector normalization
        mag = math.sqrt(dx**2 + dy**2)
        if math.isclose(mag, 0):
            raise ValueError("Err:Calculated tangent vector is 0")
        unit_dx = dx / mag
        unit_dy = dy / mag
        
        # Calculate offset coordinates
        offset_x = base_x + unit_dx * offset
        offset_y = base_y + unit_dy * offset

    # Return end point(base) and direction(offset) point
    return [{'baseX': base_x, 'baseY': base_y, 'offsetX': offset_x, 'offsetY': offset_y}]


#-----------------------------------------------
# CAP Directional vector to scaling to particular length
#-----------------------------------------------
def scale_vector_in_direction(A, B, n):
    # Calculate a difference vector of A and B
    diff = {
        'x': B['x'] - A['x'],
        'y': B['y'] - A['y']
    }

    # Caluculate a difference vector length（magnitude）
    magnitude = math.sqrt(diff['x'] ** 2 + diff['y'] ** 2)

    # Normalize the difference vector (to a unit vector)
    if magnitude == 0:
        get_line_vector = 1;magnitude=0.5
        #raise ValueError("Err:Point A and B are same place,so can't define scaling direction")

    unit_vector = {
        'x': diff['x'] / magnitude,
        'y': diff['y'] / magnitude
    }

    # Calculate cooridnate of after scaling
    return {
        'x': A['x'] + n * unit_vector['x'],
        'y': A['y'] + n * unit_vector['y']
    }



#-----------------------------------------------
# Directional vector
#-----------------------------------------------
# Get direcional vector made by two points and move them to their normal direction
def slide_points_perpendicular(pointA, pointB, distance):
    x1 = pointA['x']
    y1 = pointA['y']
    x2 = pointB['x']
    y2 = pointB['y']

    # Calculate normal vector (dy, -dx) against vector (x2 - x1, y2 - y1)
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx ** 2 + dy ** 2)
    if length < 0.1: length = 1.0
    normal_x = dy / length
    normal_y = -dx / length

    # Slide by distance to normal direction
    new_pointA = {
        'baseX': x1 + normal_x * distance,
        'baseY': y1 + normal_y * distance
    }
    new_pointB = {
        'offsetX': x2 + normal_x * distance,
        'offsetY': y2 + normal_y * distance
    }

    # Debug:
    if debug:
        print(new_pointA, new_pointB)

    return [new_pointA, new_pointB]

#-------------------
# Line CAP (main)
#-------------------
def select_coord(a, b, order, key):
    """ Reversed by which dictionary key set at first? """
    return {'x': (b if order else a)[f'{key}X'], 'y': (b if order else a)[f'{key}Y']}


def generate_cap_data(base_dir, offset, cap_type, amp, order=True):

    #     order(True)  : L command , cpp  cap
    # not order(False) : M command , cpp2 cap : 1st part of the path

    command = []
    coords = []
    base_point   = {'x': base_dir['baseX'],   'y': base_dir['baseY']}
    offset_point = {'x': base_dir['offsetX'], 'y': base_dir['offsetY']}

    # print(f"tp:{amp['taper_mode']} order:{order}")


    #Important, Normalized cap order
    od = -1 if not order and amp['taper_mode'] in ["gear", "organic", "sawtooth", "punk", "fluffy", "rough","dynamic_dash","random_dash","round_dot_dash","stamp_top_group" ] else 1
    if amp['taper_mode'] == "linear_a" : offset = offset*-1;order = False;
    if amp['single'] and amp['taper_mode'] in ["linear"]:offset = offset*-1;order = False;
    
    
    #Important, Varibale size cap
    if int(amp['olen']) > 1 and amp['taper_mode'] != "none":
        offset = euler_distance(base_point, amp['ref']) * od


    cap_s = slide_points_perpendicular(base_point, offset_point, offset)
    mcap_s = {'baseX': cap_s[0]['baseX'], 'baseY': cap_s[0]['baseY'],
              'offsetX': cap_s[1]['offsetX'], 'offsetY': cap_s[1]['offsetY']}

    if amp['taper_mode'] != "none" and not amp['single']:
        offset = euler_distance(base_point, amp['ref2']) * od

    cap_e = slide_points_perpendicular(base_point, offset_point, -offset)
    mcap_e = {'baseX': cap_e[0]['baseX'], 'baseY': cap_e[0]['baseY'],
              'offsetX': cap_e[1]['offsetX'], 'offsetY': cap_e[1]['offsetY']}

    cap_start      = select_coord(mcap_s, mcap_e, order, 'base')
    cap_end        = select_coord(mcap_e, mcap_s, order, 'base')  # reverse
    cap_start_exd  = select_coord(mcap_s, mcap_e, order, 'offset')
    cap_end_exd    = select_coord(mcap_e, mcap_s, order, 'offset')
    cap_mid        = offset_point


    if cap_type == 'round':
        # bezier curve magic number for rounded cap
        bezier_factor = 0.552284749
        
        if not order:# False:cpp2

            # Reverse control points order if `order == False` 
            control1 = get_point_between(cap_end, cap_end_exd, bezier_factor)
            control2 = get_point_between(cap_mid, cap_end_exd, bezier_factor)
            control3 = get_point_between(cap_mid, cap_start_exd, bezier_factor)
            control4 = get_point_between(cap_start, cap_start_exd, bezier_factor)

            #extra_control = get_point_between(control3, control4, 0.5)  #
            fan_result = fan(control4, control3, cap_mid, False)  # left 
            fan_smooth_result = fan(control2, control1, cap_end, True) # right

        else:# True cpp1 
            control1 = get_point_between(cap_start, cap_start_exd, bezier_factor)
            control2 = get_point_between(cap_mid, cap_start_exd, bezier_factor)
            control3 = get_point_between(cap_mid, cap_end_exd, bezier_factor)
            control4 = get_point_between(cap_end, cap_end_exd, bezier_factor)

            #extra_control = get_point_between(control1, control2, 0.5)  # 
            
            fan_result = fan(control1, control2, cap_mid, False)
            fan_smooth_result = fan(control3, control4, cap_end, True)



        #print(control1, control2, control3, control4)

        command.extend(fan_result['command'])
        coords.extend(fan_result['coords'])
    
        command.extend(fan_smooth_result['command'])
        coords.extend(fan_smooth_result['coords'])
    

        if not order:# cpp2
            command.insert(0, 'L' )
            coords.insert(0, [cap_start])

            command.append( 'L')
            coords.append( [cap_end])

        else:# cpp
            command.append( 'L');
            coords.append( [cap_end])

    elif cap_type == 'butt':  # 'L',[capStart],

        if not order:# cpp2
            command.insert(0, 'L' )
            #command.insert(1, 'L')
            coords.insert(0, [cap_start])
            #coords.insert(1, [cap_end])
        else:# cpp1
            command.append('L')
            #command.append('L')
            coords.append([cap_start])
            #coords.append([cap_end])

    elif cap_type == 'square':
        if not order:
            command.insert(0, 'L' )
            command.insert(1, 'L')
            command.insert(2, 'L')
            coords.insert(0, [cap_start_exd])
            coords.insert(1, [cap_end_exd])
            coords.insert(2, [cap_end])

        else:
            command.append('L')
            command.append('L')
            command.append('L')
            coords.append([cap_start_exd])
            coords.append([cap_end_exd])
            coords.append([cap_end])

    elif cap_type ==  'ribbon':

        result = scale_vector_in_direction(base_point,offset_point,abs(offset*2)*-1)
        capMidd = {'x': result['x'], 'y': result['y']}
        if not order:
            command.insert(0, 'L' )
            command.insert(1, 'L')
            command.insert(2, 'L')
            coords.insert(0, [cap_start])
            coords.insert(1, [capMidd])
            coords.insert(2, [cap_end])

        else:
            command.append('L')
            command.append('L')
            command.append('L')
            coords.append([cap_start])
            coords.append([capMidd])
            coords.append([cap_end])


    # The case capType is 'arrow'
    elif cap_type == 'arrow':
        capSd = slide_points_perpendicular({'x': base_dir['baseX'], 'y': base_dir['baseY']},{'x': base_dir['offsetX'], 'y': base_dir['offsetY']},offset * 2)
        mcapAS = {'x': capSd[0]['baseX'], 'y': capSd[0]['baseY']}
        
        capEd = slide_points_perpendicular({'x': base_dir['baseX'], 'y': base_dir['baseY']},{'x': base_dir['offsetX'], 'y': base_dir['offsetY']},-offset * 2)
        mcapAE = {'x': capEd[0]['baseX'], 'y': capEd[0]['baseY']}
        
        result = scale_vector_in_direction({'x': base_dir['baseX'], 'y': base_dir['baseY']},{'x': base_dir['offsetX'], 'y': base_dir['offsetY']},abs(offset*2))
        capMidd = {'x': result['x'], 'y': result['y']}
        if not order:
            command = [ 'L' ,'L','L','L','L'] + command  # Right side b, CCW
            coords = [[cap_start],[mcapAS], [capMidd], [mcapAE],[cap_end]] + coords
        else:
            command += ['L','L','L','L','L']# Left side a, CCW
            coords += [[cap_start],[mcapAE], [capMidd], [mcapAS], [cap_end]]


    # The case capType is 'brush'
    elif cap_type in ['brush','brush2','brush3','bell','sigma']:
        capwave = None

        if cap_type=='brush':capwave = generate_wave(cap_start,cap_end,curve_type=cap_type,num_samples=10)
        if cap_type=='bell':capwave = generate_wave(cap_start,cap_end,curve_type=cap_type)
        if cap_type=='sigma':capwave = generate_wave(cap_start,cap_end,curve_type=cap_type,amplitude=8,num_samples=15,invert_side=False)
        if cap_type=='brush2':
            ampl = amp['bb_short'] * 0.08# scaling (7.36%)
            capwave = generate_wave(cap_start,cap_end,curve_type='sigma',wave_count=10,amplitude=ampl,decay=-14.5,variation=20,point_limit=20,num_samples=28,invert_side=False) # num_samples=28
        if cap_type=='brush3':capwave = generate_wave(cap_start,cap_end,curve_type='brush',wave_count=2,amplitude=30,decay=-0.05,variation=10,point_limit=20,num_samples=20,invert_side=False) 

        if capwave==None:print(f"Err:Invailed cap type {cap_type} and Data{capwave}")
        n_capwave = [[p] for p in capwave]
        capwave_length = len(capwave)

        # print(f"CAP Wave:{capwave}")
        if not order:
            cw = ['L'] + ['L'] * (capwave_length - 1)
            command = cw + command  # Right side b, CCW
            coords = n_capwave + coords
        else:
            command += ['L'] * capwave_length # Left side a, CCW
            coords += n_capwave

    # Clamp un-nessesary data
    command.pop();coords.pop();

    pp = {'command': command, 'coords': coords}

    # This part is currently no use but remain,because test for edge-case
    if order and amp['taper_mode'] == "linear_a":
        pp = reverse_cap_data(pp) 

    if not order:
        pp = insert_cap_first(pp, 0, 'M', cap_start)


    return pp

#-------------------
# Rounded CAP
#-------------------
def fan(control1, control2, end_point, use_smooth_curve=False):
    command = []
    coords = []

    if use_smooth_curve:
        command.append('S')
        if debug:
            dbg.plot_point_coord( control2, 'ct2', 'gray', 1, '1')
            dbg.plot_point_coord( control1, 'ct1', 'gray', 1, '1')
            dbg.plot_point_coord( end_point, 'ep1', 'gray', 1, '1')
        coords.append([control2, end_point])
    else:
        command.append('C')
        coords.append([control1, control2, end_point])

    return {'command': command, 'coords': coords}


# ----------------
#  Brush cap
# ----------------
"""
3curve
    wave_count:   int   = 9,# Density
    amplitude:    float = 10,# Vertical
    decay:        float = -0.08,# Decay
    variation:    float = 19,# Wave num and variation
    point_limit:  int   = 18,# Cut off range
    num_samples:  int   = 20,# Thin out
    invert_side:  bool  = False   # True invert upside down

Arch
    wave_count:   int   = 9,# Density
    amplitude:    float = 0,# Vertical
    decay:        float = -0.08,# Decay
    variation:    float = 124,# Wave num and variation
    point_limit:  int   = 18,# Cut off range
    num_samples:  int   = 20,# Thin out
    invert_side:  bool  = False   # True invert upside down
"""
def generate_wave(
    a: Dict[str, float],
    b: Dict[str, float],
    *,
    wave_count:   int   = 9,   # Density（Brush: wave of number）
    amplitude:    float = 10,  # Vertical scale
    decay:        float = -0.08,  # Decay（It enable only brush curve type）
    variation:    float = 19,  # Wave num and variation（It enable only brush curve type）
    point_limit:  int   = 18,  # Cut off range
    num_samples:  int   = 20,  # Thin out
    invert_side:  bool  = False,  # 
    curve_type:   str   = "brush"  # "brush","bell","sigma"
) -> List[Dict[str, float]]:
    """
     a and b are dictionaries with {'x':..., 'y':...} format.
     The first element [0] of the return list is forcibly overwritten with a, and [point_limit-1] with b.
     If invert_side=True, the normal vector is inverted, causing waves to appear on the opposite side.
     The curve_type determines the following types of curves:
         "brush": Original wave (a curve resembling a brush tip with approximately three peaks).
         "bell": A Gaussian-based curve forming a dome that rises only in the center.
         "sigma": A parabolic shape where s ranges from 0 to 1 (0 at both ends, maximum at the center).
                  *In this case, adjustments have been made to characterize only the central part like "{".

    """

    # Auto adjustment if point_limit > num_samples
    point_limit = min(point_limit, num_samples)

    ax, ay = a['x'], a['y']
    bx, by = b['x'], b['y']

    # Step 1: Get length of  vector a,b and unit vector
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L == 0:
        # raise ValueError("Error:Coordinates a and b are same  ")
        Print("Error:Coordinates a and b are same  ")
        return [{'x': a['x'], 'y': a['y']}]

    ux, uy = dx / L, dy / L

    # Step 2: Get Normal vector (initially left-handed normal: pointing upward）
    nx, ny = -uy, ux
    if invert_side:
        nx, ny = -nx, -ny

    # Step 3: Get Wave(or Height) of function h(t)
    def h(t: float) -> float:
        # t ranges from 10 to 390.
        if curve_type == "brush":
            main = math.sin(t / (20 / wave_count) * math.pi)
            env = math.exp(decay * (t - 10))
            jitter = math.sin(t / variation) * 6
            return (main * env * amplitude) + jitter
        elif curve_type == "bell":
            s = (t - 10) / 380.0  # Identify 0 to 1
            sigma_val = 0.15      # Standard deviation (smaller values result in a sharper peak)
            return amplitude * math.exp(-((s - 0.5) ** 2) / (2 * sigma_val ** 2))
        elif curve_type == "sigma":
            #Only the central part 
            # (s between 0.4 and 0.6) is lifted using sine, with both ends linearly interpolated to zero
            s = (t - 10) / 380.0  # s: 0 ～ 1
            if s < 0.4:
                # Linear increase toward both ends
                return amplitude * (s / 0.3)
            elif s > 0.6:
                # Linear decrease toward both ends
                return amplitude * ((1 - s) / 0.6)
            else:
                # Center: Normalize s to a range of 0 to 1 using a sine curve
                s_norm = (s - 0.4) / 0.2
                return amplitude * math.sin(s_norm * math.pi)
        else:
            raise ValueError("Unsupported curve_type: " + curve_type)

    # Step 4: Calculate each sampliing coorinates
    xs, ys = [], []
    for i in range(num_samples):
        s = i / (num_samples - 1)       # 0 to 1
        t = 10 + 380 * s                # t range from 10 to 390
        w = h(t)
        xs.append(ax + ux * (L * s) + nx * w)
        ys.append(ay + uy * (L * s) + ny * w)

    # Step 5: Endpoints are always fixed to a and b
    xs[0], ys[0] = ax, ay
    xs[point_limit - 1], ys[point_limit - 1] = bx, by

    return [{'x': xs[i], 'y': ys[i]} for i in range(point_limit)]


#------------------------
# Get vector on between AB
#------------------------
# Place a control point at t on line AB
def get_point_between(pointA, pointB, t):
    return {
        'x': pointA['x'] + (pointB['x'] - pointA['x']) * t,
        'y': pointA['y'] + (pointB['y'] - pointA['y']) * t
    }

#----------------------------------
# Output SVG path command of CAP
#----------------------------------
def output_cap_path(data):
    if not data['command'] or not data['coords']:
        return ''

    path_string = ''
    # Check the path data has single path or multiple sub-paths
    all_path_data_list = data if isinstance(data, list) else [data]

    for data_item in all_path_data_list:
        command = data_item['command']
        coords = data_item['coords']

        if not command or not coords:
            print('Error: command or coords is undefined')
            return ''  # Exit if error occured

        for index, cmd in enumerate(command):
            coord = coords[index]
            if coord:
                if cmd in ['M', 'L']:
                    path_string += f"{cmd} {coord[0]['x']},{coord[0]['y']}"
                elif cmd == 'C':
                    path_string += f"{cmd} {coord[0]['x']},{coord[0]['y']} {coord[1]['x']},{coord[1]['y']} {coord[2]['x']},{coord[2]['y']}"
                elif cmd in ['S', 'T']:
                    path_string += f"{cmd} {coord[0]['x']},{coord[0]['y']} {coord[1]['x']},{coord[1]['y']}"
                if index < len(command) - 1:
                    path_string += ' '
            else:
                print(f"Error: coord is undefined for command {cmd}")

        # Add space to each path data
        path_string += ' '

    return path_string.strip()  # Remove redundant whitespace from the path string


#-------------------------------
# Generate SVG arc path data 
#-------------------------------
def create_arc_path(P1, P2, rx, ry, large_arc_flag=0, sweep_flag=1):
    return f"M {P1['x']} {P1['y']} A {rx} {ry} 0 {large_arc_flag} {sweep_flag} {P2['x']} {P2['y']}"

#-------------------------
# Add outlined Path data
#-------------------------
def create_outline_path_elm(data, fill_color, stroke_color, stroke_width,params):
    
    if data =="":
        # print("Error:No path data found in attribute 'd'.")
        return None

    if debug_path:
        stroke_color = params['previewcolor'] #'red'
        stroke_width = 1
        fill_color = "none"

    if params['fillview']:
        fill_color = params['previewcolor'] #'red'

    stroke_width = stroke_width or 1
    
    if debug_path == False:
        stroke_width = 0


    elm = initialize_shape_data("path")
    elm['stroke-linejoin'] = "round"

    if params['taper_mode'] in ("round_dot_dash", "dynamic_dash", "random_dash"):
        fct = params['factor']
        oft = abs(float(params['ofs']))
        if fct < 1.0:fct=1
        # print(f":::::{oft} {fct}")# 0-100 
        elm['stroke-dasharray'] = f"0.001, {fct}"
        elm['stroke-linecap'] = "round"# round
        elm['stroke-linejoin'] = "round"# round

        if params['taper_mode'] == "random_dash":
            elm['stroke-dasharray'] = generate_dasharray(fct, oft*1.25, seed=123)
            elm['stroke-linecap'] = "butt"# butt
            elm['stroke-linejoin'] = "miter"# bevel

        if params['taper_mode'] == "dynamic_dash":
            elm['stroke-dasharray'] = f"{oft*0.5+fct*0.35+0.01}, {fct*0.15}"
            elm['stroke-linecap'] = "butt"# butt
            elm['stroke-linejoin'] = "miter"# bevel

        stroke_width = float(stroke_width) + oft

    elm['d'] = data
    elm['fill'] = fill_color
    elm['stroke-miterlimit'] = "4px"
    elm['stroke-width'] = str(stroke_width)+'px'
    elm['stroke'] =  'none' if stroke_width == 0 else stroke_color

    return elm


#-------------------
# random dash
#-------------------

def generate_dasharray(factor: int, ofs: float = 1.0, seed: int = 42, base=5, count=15):
    """
    factor: 0-100 chaos strength
    seed: random seed
    base: basical dash length
    count: dash array elements（it better by even number）
    """
    random.seed(seed)
    # variation = factor / 100  # Rnge 0.0-1.0 
    # variation = 0.3 + 0.7 * (factor / 100)
    variation = (factor / 100) ** 1.5  
    dasharray = []

    for i in range(count):
        # base = abs(variation * base * random)
        delta = base * variation * (random.uniform(-1, 1))
        value = max(0.1, base + delta)  # avoid negative sign
        if i % 2 == 1:value *= ofs*0.34  # Amplify the gaps
        dasharray.append(round(value, 2))

    return ", ".join(map(str, dasharray))


#-------------------------------------------
# Add offsetted path tag (for debug)
#-------------------------------------------
def create_offset_path_elm(data, fill_color='none', stroke_color=None, stroke_width='1'):
    elm = initialize_shape_data("path")
    elm['d'] = data
    elm['fill'] = fill_color
    elm['stroke-width'] = str(stroke_width)
    elm['stroke'] = stroke_color

    return elm

#-------------------
#  for debug
#-------------------
def debug_qtransform(transform: QTransform):
    """Debug function to display each matrix element of QTransform"""
    print(f"m11: {transform.m11()}, m12: {transform.m12()}, m13: {transform.m13()}")
    print(f"m21: {transform.m21()}, m22: {transform.m22()}, m23: {transform.m23()}")
    print(f"m31: {transform.m31()}, m32: {transform.m32()}, m33: {transform.m33()}")

def apply_transform_to_points(transform: QTransform, points: list):
    """ Apply QTransform to the coordinate array
    transform = QTransform(1, 0, 0, 0, 1, 0, 100, 200, 1)
    points = [{"x": 0, "y": 0}, {"x": 50, "y": 50}]
    transformed = apply_transform_to_points(transform, [(p["x"], p["y"]) for p in points])
    print(transformed)  # [{"x": 100, "y": 200}, {"x": 150, "y": 250}]
    
    """
    transformed_points = [transform.map(point[0], point[1]) for point in points]
    return [{"x": p.x(), "y": p.y()} for p in transformed_points]


def qtransform_to_svg_transform(transform: QTransform):
    """Convert QTransform to SVG transform attribute format
    transform = QTransform(1, 0, 0, 1, 100, 200)
    svg_transform = qtransform_to_svg_transform(transform)
    print(svg_transform)  # "matrix(1 0 0 1 100 200)"
    """
    return f"matrix({transform.m11()} {transform.m12()} {transform.m21()} {transform.m22()} {transform.m31()} {transform.m32()})"

#-------------------
# get last point from points array 
#-------------------
def get_last_p(array):
    return array[-1] if array else None

def get_last_s(array):
    return array[-2] if len(array) > 1 else None

#-------------------
# Detect if a path is closed
#-------------------
def is_path_closed(svg_path):
    # Get the SVG path command
    commands = re.findall(r'[a-z][^a-z]*', svg_path, flags=re.IGNORECASE)
    if not commands:
        return False
    last_command = commands[-1].strip()  # Get last command
    return last_command in ['Z', 'z']  # The path closed if 'Z' or 'z' commands



#--------------------------
# Clean up to path data
#--------------------------
def cleaning_path(path_data, decimal_value=3):
    
    path_data = round_path_data(path_data, decimal_value)
    path_data = clean_path_data(path_data)
    path_data = path_data.replace("&#xA;", "").replace(r"\s+", " ").strip()  # Remove line-breaks,and convert spaces
    return path_data

#---------------------------------
# Clean dupulicated points
#---------------------------------
def approximately_equal(a, b, tol=1e-3):
    """
      Convert a and b from strings to floats, 
      and return True if the difference is less than tol
    """
    return abs(float(a) - float(b)) < tol

def coords_equal(pt1, pt2, tol=1e-3):
    """Determine whether two values are equal within a given tolerance."""
    return approximately_equal(pt1[0], pt2[0], tol) and approximately_equal(pt1[1], pt2[1], tol)

def clean_path_data(path_data, tol=1e-3):
    MAX_COORD = 100000
    tokens = re.findall(r'([MLCZS])([^MLCZS]*)', path_data)  # Keep all commands
    new_path = []
    last_point = None

    for command, params in tokens:
        params = params.strip()

        if command == 'M':
            numbers = re.findall(r'[-+]?\d*\.?\d+(?:e[+-]?\d+)?', params)
            if len(numbers) >= 2:
                x, y = float(numbers[0]), float(numbers[1])
                if abs(x) > MAX_COORD or abs(y) > MAX_COORD:
                    print(f"[Warning] Abnormal coordinates in M : ({x}, {y}) are skipped")
                    continue
                last_point = (x, y)
                new_path.append(f"{command}{numbers[0]} {numbers[1]}")
            last_point = None
            continue

        if command == 'L':
            numbers = re.findall(r'[-+]?\d*\.?\d+', params)
            coords = []
            for i in range(0, len(numbers), 2):
                if i + 1 < len(numbers):
                    coords.append((numbers[i], numbers[i+1]))

            cleaned_coords = []
            for xy in coords:

                x = float(xy[0])
                y = float(xy[1])
                if abs(x) > MAX_COORD or abs(y) > MAX_COORD:
                    print(f"[Warning] Abnormal coordinates in L: ({x}, {y}) are skipped")
                    continue

                if last_point is not None and coords_equal(last_point, xy, tol):
                    continue
                cleaned_coords.append(xy)
                last_point = xy

            if cleaned_coords:
                first = cleaned_coords[0]
                out_str = f"{command}{first[0]} {first[1]}"
                for xy in cleaned_coords[1:]:
                    out_str += f" L{xy[0]} {xy[1]}"
                new_path.append(out_str)
            continue
        
        else:
            # Other commands
            new_path.append(f"{command}{params}")

    return "".join(new_path)



#-------------------
# Multiply with string
#-------------------
def multiply_path_data(path_data, multiply=2):
    def multiply_number(match):
        num = float(match.group(0))  # Convert to float
        return str(num * multiply)  # and Multiply the number by a factor
    return re.sub(r"-?\d+(\.\d+)?", multiply_number, path_data)

#-------------------
# Rounded with string
#-------------------
def round_path_data(path_data, decimals=7):
    decimals = min(max(decimals, 0), 7)  # Limit range
    def round_number(match):
        num = float(match.group(0))  # Convert to float
        if num.is_integer():
            return str(int(num))  # integer
        return f"{num:.{decimals}f}"  # Round the decimal part
    return re.sub(r"-?\d+(\.\d+)?", round_number, path_data)

#-------------------
# Shift points
#-------------------
def transform_coordinates(array, shift_x, shift_y, multiply):
    shifted_array = []
    
    for point in array:
        # No shift if x, y = 0
        new_x = (point['x'] + shift_x) * multiply if point['x'] != 0 else point['x']
        new_y = (point['y'] + shift_y) * multiply if point['y'] != 0 else point['y']
        
        shifted_array.append({'x': new_x, 'y': new_y})
    
    return shifted_array

#-------------------
# Boundary check
#-------------------
def remove_pts_outside_rect(pts, rect, shift=0):
    """
    Filters a list of points, retaining only those that lie within a given rectangular area.
    The detection region can be optionally expanded by applying a `shift` offset.
    """
    
    # Expand or shrink rectangle by shift in local coordinates
    x_min = rect['x'] - shift
    y_min = rect['y'] - shift
    x_max = rect['x'] + rect['w'] + shift
    y_max = rect['y'] + rect['h'] + shift

    #print(f"BB  X: {rect['x']} , Y: {rect['y']} , W: {rect['w']} , H: {rect['h']}")
    # Filtering process
    filtered_pts = [p for p in pts if x_min <= p["x"] <= x_max and y_min <= p["y"] <= y_max]
    
    return filtered_pts
#-------------------------------
# Remove self intersection 
#-------------------------------
def euler_distance(p, q):
    """ Calculate eular distance of between two point p and q"""
    return math.sqrt((p["x"] - q["x"]) ** 2 + (p["y"] - q["y"]) ** 2)

def path_length(pts, start_index, end_index):
    """
    Calculate the length along the line from pts[start_index] to pts[end_index]
    Accumulate the distance of each segment between the endpoints
    """
    total = 0.0
    for idx in range(start_index, end_index):
        total += euler_distance(pts[idx], pts[idx + 1])
    return total

def loop_is_closed(points, tol=1e-10):
    """
    If the first and last points are approximately equal, the path is considered closed
    """
    return (abs(points[0]["x"] - points[-1]["x"]) < tol and 
            abs(points[0]["y"] - points[-1]["y"]) < tol)

def segment_intersection(p, p2, q, q2, epsilon=1e-10):
    """
    Find the intersection of line segments p-p2 and q-q2 using a parametric method
    If an intersection is exist and lies on the both line segment,return its coordinates as dictionary {"x": ..., "y": ...},
    Otherwise return None
    """
    dx1 = p2["x"] - p["x"]
    dy1 = p2["y"] - p["y"]
    dx2 = q2["x"] - q["x"]
    dy2 = q2["y"] - q["y"]

    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < epsilon:
        denom= 0.0001
        #return None  # If it is parallel or colinear

    dx = q["x"] - p["x"]
    dy = q["y"] - p["y"]
    t = (dx * dy2 - dy * dx2) / denom
    u = (dx * dy1 - dy * dx1) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        return {"x": p["x"] + t * dx1, "y": p["y"] + t * dy1}
    return None


def remove_self_intersections(points, threshold=3, max_detour_ratio=1.15, epsilon=1e-10):
    """
    Detects self-intersections in a polyline and removes redundant (nearly straight) 
    subpaths by shortcutting through the intersection points.

    Additional conditions for shortcutting:
    - The number of intermediate points between the intersection segments is 
      greater than or equal to `threshold`.
    - The detour ratio (subpath length divided by direct distance between endpoints) 
      is less than or equal to `max_detour_ratio`.

    If both conditions are met, the subpath is replaced with a shortcut line at the 
    intersection, preserving the general shape while reducing noisy path segments.

    Parameters:
        points (List[Dict[str, float]]): A list of coordinates like {"x": value, "y": value}.
        threshold (int): Minimum number of intermediate points to consider for removal.
        max_detour_ratio (float): Maximum allowable ratio of path length to direct distance.
        epsilon (float): Tolerance for numerical computations.

    Returns:
        The simplified list of points.
    """

    max_allowed_ratio = 10.0
    max_removal_count = 20.0

    if len(points) < 3:
        return points[:]

    # Detect opened/closed path (The case of closed path,a duplicated point remove tamporary)
    closed = loop_is_closed(points, tol=epsilon)
    pts = points[:-1] if closed else list(points)
    
    changed = True
    while changed:
        changed = False
        n = len(pts)
        for i in range(n - 1):
            for j in range(i + 2, n - (0 if closed else 1)):
                p = pts[i]
                p2 = pts[i + 1]
                q = pts[j]
                # set index : Use modulo for closed path,and direct access for opened path
                if closed:
                    q2 = pts[(j + 1) % n]
                else:
                    if j + 1 < n:
                        q2 = pts[j + 1]
                    else:
                        continue  # Skip if out of bound 
                
                inter = segment_intersection(p, p2, q, q2, epsilon)
                
                
                if inter is not None:
                    # Snap the intersection to the midpoint of the endpoints.
                    #inter['x'] = (p['x'] + q2['x']) / 2
                    #inter['y'] = (p['y'] + q2['y']) / 2
                
                    removal_count = j - i - 1
                    
                    # Append: Skip if removable targe under than the threshold 
                    if removal_count < threshold or removal_count > max_removal_count:
                        continue
        
                    subpath_length = path_length(pts, i, j + 1)
                    direct_dist = euler_distance(pts[i], pts[(j + 1) % n] if closed else pts[j + 1])
                    ratio = subpath_length / direct_dist if direct_dist > epsilon else 1.0
        
                    # Debug info:
                    #print(f"Intersect: {inter}, remove cnt:{removal_count}, Sub-path len: {subpath_length}, "
                    #    f"line: {direct_dist}, Ratio: {ratio}")
        
                    # Skip if the path is not sufficiently straight (i.e., the detour ratio is too high)
                    if ratio > max_allowed_ratio:
                        continue
        
                    # Apply short-cutting
                    pts = pts[:i + 1] + [inter] + pts[j + 1:]
                    changed = True
                    break  # Re-start loop when change at once
            if changed:
                break

    if closed and not changed:
        # Check: The loop made by 1st and last points
        i, j = n - 2, 0
        p, p2 = pts[i], pts[i + 1]
        q, q2 = pts[j], pts[j + 1]
        inter = segment_intersection(p, p2, q, q2, epsilon)
        if inter is not None:
            removal_count = n - 2  # End to end
            if removal_count >= threshold and removal_count <= max_removal_count:
                subpath_length = path_length(pts, i, j + 1)
                direct_dist = euler_distance(p, q2)
                ratio = subpath_length / direct_dist if direct_dist > epsilon else 1.0
                if ratio <= max_allowed_ratio:
                    # Apply shortcut
                    pts = [inter] + pts[j + 1:i + 1]
                    pts.append(pts[0])  # Close it again

    if closed:
        pts.append(pts[0])


    return pts
#----

def intersect_lp(a, b, c, d, eps=1e-10):

    # Decimal 
    """
    x1, y1 = Decimal(str(a['x'])), Decimal(str(a['y']))
    x2, y2 = Decimal(str(b['x'])), Decimal(str(b['y']))
    x3, y3 = Decimal(str(c['x'])), Decimal(str(c['y']))
    x4, y4 = Decimal(str(d['x'])), Decimal(str(d['y']))
    """
    x1, y1 = a['x'], a['y']
    x2, y2 = b['x'], b['y']
    x3, y3 = c['x'], c['y']
    x4, y4 = d['x'], d['y']
    
    if debug:
        dbg.plot_line( a, b, "red")
        dbg.plot_line( c, d, "blue")

    #print(f"Intersect :::: abcd = {a},{b},{c},{d}")

    # Dirctional vector
    dx1, dy1 = x2 - x1, y2 - y1
    dx2, dy2 = x4 - x3, y4 - y3

    # Denominator for intersection detection
    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < eps:
        denom = 0.001
        #return None  # Considered parallel or coincident with no intersection

    # Find the parameter t
    t = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / denom


    # Intersection coodinates
    ix = x1 + t * dx1
    iy = y1 + t * dy1

    return {'x': float(ix), 'y': float(iy)}



def trim_tail_loop(d1,v):
    # Find the intersected segements form last to first
    for i in range(len(d1)-1, 1, -1):
        a, b = d1[i-1], d1[i]
        c, d = d1[0], d1[1]
        xcp = intersect_lp(a, b, c, d)
        if xcp:
            # delete loop and re connect
            new_d1 = d1[:i-1]+ d1[1:]
            cpp = f"Z M{poi(xcp)} "
            return new_d1, cpp

    # no intersection
    return d1, ''

#----
def remove_tail(points, min_tail_ratio=0.05):
    """
    Removes the tail segment of a path if it is significantly short compared to the entire path.

    The path is treated as a fish-like doodle, consisting of a body and a tail. 
    If the final segment (i.e., the distance between the last two points) is shorter than 
    `min_tail_ratio` of the total path length, the last point is removed as a redundant tail.
    """
    if len(points) < 2:
        return points[:]
        
    total_length = path_length(points, 0, len(points) - 1)
    tail_length = euler_distance(points[-2], points[-1])
    
    # Shorter than `min_tail_ratio` of the total path length
    if tail_length < total_length * min_tail_ratio:
        return points[:-1]
    return points




def fix_tail_intersection(points, epsilon=1e-10):
    """
    Resolves the final self-intersection in a point sequence, typically resembling a "tail fin" shape.

    If the first point (points[0]) is an auxiliary point used for direction initialization,
    the actual shape begins from points[1].

    This function follows these steps:
        1. Computes the intersection between the second segment (points[1] to points[2])
           and the last segment (points[-2] to points[-1]).
        2. If an intersection is found, replaces the final segment with the intersection point,
           removing the tail-end self-intersection.

    If no intersection is found, the original sequence is returned unchanged.

    """
    # Do nothing if the number of points is insufficient
    if len(points) < 3:
        return points[:]

    # 2ndrary segment from points[1] to points[2]
    seg_start = points[1]
    seg_end = points[2]
    
    # Last segment: from points[-2] to points[-1]
    tail_start = points[-2]
    tail_end = points[-1]
    
    inter = segment_intersection(seg_start, seg_end, tail_start, tail_end, epsilon)
    if inter is not None:
        # Replace last point to a intersection
        fixed_points = points[:-1] + [inter]
        return fixed_points
    else:
        return points[:]


#-------------------
# Apply offset : Main 
#-------------------
def apply_offset(original_element,params):

    # MAIN
    tag_name = original_element.get("tagName", 0)

    is_closed = False
    path_data = None

    # Branching logic based on tag type 
    if tag_name in ["circle", "ellipse", "rect"]:
        # is_closed = False
        if params['taper_mode'] == "none":
            return get_outline_from_shape(original_element, tag_name, params)
        if params['taper_mode'] != "none":
            if tag_name == "rect":
                return rect_variant(original_element,params,is_closed,path_data)
            if tag_name == "circle":
                path_data = generate_v_circle_path(original_element, 0 , params['line_join'],0)# offset zero
                return oval_variant(original_element,params,is_closed,path_data)
            if tag_name == "ellipse":
                params['long'] = True if float(original_element['rx']) > 100.0 else False
                params['long'] = True if float(original_element['ry']) > 100.0 else False
                r = 1 if float(original_element['rx']) > 100.0 else 0
                r = 1 if float(original_element['ry']) > 100.0 else 0
                path_data = generate_v_ellipse_path(original_element, 0 , params['line_join'],r)# offset zero params['ofs']
                return oval_variant(original_element,params,is_closed,path_data)
        return get_outline_from_shape(original_element, tag_name, params)

    elif tag_name == "line":
        # Not close the line , Do line join process first than path 
        print("Warining:A single line")
        path_data = line_to_path(original_element)  # line
        is_closed = False

    elif tag_name == "path":
        path_data = original_element.get("d")
        is_closed = is_path_closed(path_data)  # Opend or closed line
        
        if is_single_segment_line(path_data):
            print("Warining:A single path")
            original_element['tagName'] == "line"
            tag_name = "line" # Treat as a straight line segment.
        

    elif tag_name in ["polygon", "polyline"]:
        path_data = original_element.get("points")
        # Polygons are closed shapes; polylines are not.
        is_closed = tag_name == "polygon"
        path_data = poly_to_path(path_data, is_closed)  # closedPath

    else:
        print(f"Err:Unsupported tagName: {tag_name}")

    # Path, polygon, polyline, line
    return get_outline_from_path(original_element, tag_name, params, is_closed, path_data)




#-------------------
# Apply scale multiply
#-------------------
def multiply_coordinates(coordinates, multiplier):

    updated_coordinates = []
    for point in coordinates:

        updated_point = {
            'x': point['x'] * multiplier,
            'y': point['y'] * multiplier
        }
        updated_coordinates.append(updated_point)
    return updated_coordinates
#-------------------
# Get first coordinates 
#-------------------
def get_first_coordinates(d_attribute):
    #  Extract coorinates by RegExp with space or comma separators
    coordinates = re.findall(r"[MmLlCcSsQqTtAaZz]([\d.,\s-]+)", d_attribute)
    if coordinates:
        # Get first coordinates
        first_coord_str = coordinates[0].strip()
        # Split with space or comma
        if ' ' in first_coord_str:
            first_coord_values = first_coord_str.split(' ')
        else:
            first_coord_values = first_coord_str.split(',')
        # Retun x, y by dictionary
        return {'x': float(first_coord_values[0]), 'y': float(first_coord_values[1])}
    return None

#-------------------
# Get last coordinates 
#-------------------
def get_last_coordinates(d_attribute):
    # Extract coorinates by RegExp with space or comma separators
    coordinates = re.findall(r"[MmLlCcSsQqTtAaZz]([\d.,\s-]+)", d_attribute)
    if coordinates:
        # Get last coordinates
        last_coord_str = coordinates[-1].strip()
        # Split with space or comma
        if ' ' in last_coord_str:
            last_coord_values = last_coord_str.split(' ')
        else:
            last_coord_values = last_coord_str.split(',')
        # return x, y by dictionary 
        return {'x': float(last_coord_values[0]), 'y': float(last_coord_values[1])}
    return None


#-------------------
# Extract sub-paths
#-------------------
def split_subpaths(path_data, ofs_flag=False):

    # Extract subpaths starting with "M"
    subpaths = re.findall(r'M[^M]*', path_data)

    if ofs_flag:
        # Keep only even-indexed subpaths (0, 2, 4, ...)
        subpaths = [sp for i, sp in enumerate(subpaths) if i % 2 == 0]

    return subpaths


def is_closed_path(path):
    return path.strip()[-1] == 'Z'  # if "Z" ended,then it is closed path


#-------------------
# Get outline data from path
#-------------------
def keep_longest_path(paths):
    if len(paths) <= 1:
        return paths

    # find longest length
    longest = max(paths, key=lambda p: p['length'])
    
    return [longest]



def get_outline_from_path(orig_elm, tag_name, params, is_closed, path_data):
    global debug_path
    mode    = params.get("mode", "outline") # outline or offset
    fo_mode    = params.get("fo_mode", False) # force offset mode, not for outline
    debug_path = params.get("debug_path", False)

    #line_cap, line_join, mitl,stroke_color,fill_color,stroke_width = extract_common_path_attributes(orig_elm)
    _, _, _,stroke_color,fill_color,stroke_width = extract_common_path_attributes(orig_elm)


    # for offset mode
    if fo_mode == True:
        # stroke_width =  float(params.get("ofs",10.0)) # override (This is experimental)
        stroke_width =  float(stroke_width) + float(params.get("ofs",1.0)) # relative offset
        line_join = params.get("line_join", "miter")


    offset = stroke_width / 2
    fill_color = orig_elm.get("points")
    if fill_color is None:
        fill_color = "black"


    subpaths = split_subpaths(path_data)


    allpData = []
    for subpath in subpaths:
        _is_closed = is_closed_path(subpath)
        total_length, total_points = calculate_total_length_and_points_tagged(subpath, divisions=180)
        
        if params['reverse'] == True and _is_closed == False:
            # Because Error happend closed path with elipse 
            total_points = reversed_svg_points(total_points,_is_closed)

        if params['taper_mode'] in ["dynamic_dash","random_dash","round_dot_dash"]:
            params['dash']=True
        else:
            params['dash']=False

        pData = {
            'length': int(round(total_length)),
            'points': total_points,
            'closed': _is_closed
        }
        #print(f"Subpath length: {int(round(total_length))}")
        allpData.append(pData)
    
    #print(f"{int(round(total_length))}")
    #print(f"{total_points}")

    outline_paths = [] 

    #allpData = allpData[:-1]# remain outside line for debug
    #print(allpData[0]['length'])



    if params.get("single_path", False):
        allpData = keep_longest_path(allpData)# single path


    for sData in allpData:
        gen = generate_outline_path(sData, offset, orig_elm, params, sData['closed'])
        # print(f"gen:{gen}")

        if gen == None:continue
        outline_paths.append(gen)
    
    outline_path = " ".join(outline_paths)  # join as strings
    
    if mode == "outline":stroke_width = 0
    fill_color = stroke_color

    elm = create_outline_path_elm(outline_path, fill_color, stroke_color, stroke_width,params)

    return elm

#-------------------
# Fall-back
#-------------------
def poi(data):
    lx = data['x'];ly = data['y'];
    return f"{lx},{ly}"


def init_path_flg(path_array):
    for a in path_array:
        a["flg"] = True
    return path_array

def set_path_flg(data,num,bool):
    data[num]["flg"]=bool
    return data


def g_segments_intersect(p1, p2, q1, q2):
    """ Check two line segments (p1 p2 and q1 q2) are intersect or not """
    def ccw(a, b, c):
        return (c["y"] - a["y"]) * (b["x"] - a["x"]) > (b["y"] - a["y"]) * (c["x"] - a["x"])

    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))

def is_self_intersecting(path):
    """ Check self intersection acording the list [{x:,y:},...]  """
    n = len(path)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):  # No check neighbor line segment
            if g_segments_intersect(path[i], path[i + 1], path[j], path[j + 1]):
                return True
    return False


#-------------------
# Generate a path
#-------------------
def reverse_cap_data(dic):
    reversed_command = dic['command'][::-1]
    reversed_coords = dic['coords'][::-1]
    return {'command': reversed_command, 'coords': reversed_coords}


def set_cap_cmd(dic,n,cmd):
    dic['command'][n] = str(cmd)
    return dic

def set_cap_coords(dic, n, p):
    if (
        isinstance(p, dict) and 
        "x" in p and "y" in p and 
        isinstance(p["x"], (int, float)) and 
        isinstance(p["y"], (int, float))
    ):
        dic['coords'][n] = p
    else:
        raise ValueError("p must be a dictionary with numeric 'x' and 'y'")
    return dic

def insert_cap_first(dic, n, cmd, point):
    """
    - cmd:  string（'M', 'L', 'C', 'S' etc）
    - point: [{'x': ..., 'y': ...}] single coordinates
    """
    if not isinstance(dic, dict):
        raise ValueError("Invalid dictionary provided")
    if 'command' not in dic or 'coords' not in dic:
        raise KeyError("Missing 'command' or 'coords' keys in dictionary")
    
    dic['command'].insert(n, cmd)
    dic['coords'].insert(n, [point] if isinstance(point, dict) else point)
    return dic

def scale_factor(factor, min_val, max_val):
    """
    factor: 0..100
    min_val: scaled min
    max_val: scaled max
    """
    return (max_val - min_val) * (factor / 100.0) + min_val


# segment
def intp_distance(p1, p2):
    return math.hypot(p2['x'] - p1['x'], p2['y'] - p1['y'])



def generate_outline_path(pData, offset, orig_elm,params, is_closed):
    global total_pts
    # Get directional vectors,and make outline paths 
    # taper:linar_a,linear_b

    taper_mode = params.get("taper_mode", "none") # "none,linear,organic,chain,gear,sawtooth,punk,fluffy,rough"
    line_cap, line_join, mitl,_,_,_ = extract_common_path_attributes(orig_elm)


    fo_mode = params.get("fo_mode", False) # force offset mode, not for outline 
    if fo_mode == True:
        line_join = params.get("line_join", "miter")
        mitl = params.get("mitl", 4.0)
    factor = params.get("factor")
    line_cap_a = params.get("cap_a", "butt") # line_cap_types
    line_cap_b = params.get("cap_b", "butt") # 

    #print(params.get("mode"))
    # In outline mode "offset" is proper
    if params.get("mode") == "outline": 
        line_cap_a = line_cap_b = line_cap

    tagname = orig_elm.get("tagName", "path")

    params['tagname'] = tagname

    # single segment is 2
    short_limit = 2
    is_single_segment = False
    one_segment_coord = []

    is_single_segment,single_segment_coord = get_single_segment_line(orig_elm['d'],0);

    # ====================
    # Create offset paths
    # ====================
    d1=d2=anker=anker2=None
    path_work = True

    # single_coord_conv() will no longer be used.
    if path_work == True and taper_mode != "stamp_top_group":
        # need  array[1:-1] it must remove points generated by M and Z
        # if is_single_segment:pData['points'].pop()
        
        original_path_data = offset_path(pData,params, 0.001, line_join, mitl, taper_mode,True)  # Original (0)
        # bug original_path_data[-1] = pData['points'][-1]

        d1 = offset_path(pData,params, offset, line_join, mitl, taper_mode,True)  # offset 
        d2 = offset_path(pData,params, -offset, line_join, mitl, taper_mode, False)  # offset

        if d1==[]:print("No offset path_d1");return None;# Avoide the Error
        if d2==[]:print("No offset path_d2");return None;# Avoide the Error

    # ===================================
    # stamp mode
    # ===================================
    if taper_mode == "stamp_top_group":# params['stamp_along']['flg']==True:
        #print(f"stamp: {params['stamp_along']['flg']}, {tagname}")
        stamp_main(pData,params, taper_mode, tagname)
        return None

    # print(f"d1{d1} d2{d2}")
    
    if not d1:print("No ofs path_mid");return None;

    anker = d1[0];anker2 = d2[-1];

    if is_single_segment and taper_mode!="organic":# To fix organic style's bug
        d1 = d1[:-1];d2 = d2[1:];
    if debug:
        dbg.plot_dot_param2(d1[0], "ank","pink", 4.0,"1.5em")
        dbg.plot_dot_param2(d2[-1], "ank2","purple", 4.0,"1.5em")
        dbg.plot_dot_param2(d1[-1], "be","purple", 4.0,"1.5em")
        
    if len(original_path_data) > short_limit: d1 = d1[:-1];d2 = d2[1:]
    if tagname in ["circle","ellipse"]      : d1 = d1[:-1];d2 = d2[1:]

    #print(f"D: {original_path_data}  d1{d1}  d2{d2}")

    # ===================================
    # Dot connection mode 
    # ===================================
    if taper_mode == "dot_to_dot":
        dot_to_dot_main(params, d1,d2,taper_mode, orig_elm,total_pts, original_path_data, pData,is_single_segment,single_segment_coord)
        return None;

    # ====================
    #  Original Line mode  and  taper_mode == "round_dot_dash" or  "random_dash"
    # ====================
    # It only apply taper effect to original path(no offset)
    if params['single_path']==True or params['original'] :
        close = "Z" if is_closed == True else ""
        orig_based_path = d1
        ms={'x': orig_based_path[0]['x'],'y':orig_based_path[0]['y'] }
        mg={'x': orig_based_path[-1]['x'],'y':orig_based_path[-1]['y'] }
        orig_based_path[-1]=mg
        cpp=f"M{ms['x']},{ms['y']}";

        orig_based_path = remove_self_intersections(orig_based_path, 1, 1.82)
        all_path = f"{cpp}{points_to_path_data(orig_based_path,'orig_based_path')}{close}"
        return all_path

    if not d1:print("No offset path_s");return None;# Avoide the Error

    is_self_insct = False
    if len(original_path_data) > short_limit:
        is_self_insct = is_self_intersecting(original_path_data[:-1])
    # ====================
    # Debug info
    # ====================
    # debug info for command line output
    #info.append( f"ID:{orig_elm['id']} {tagname},len:{len(original_path_data)}, close?:{is_closed} 1seg:{is_single_segment}, Fst:{pData['points'][0]['cmd']} Lst:{pData['points'][-1]['cmd']} ,  ,  C:{line_cap} J:{line_join}  taper?{taper_mode} \n")

    # get Verbose info
    a = {'x':params['bb']['x'], 'y':params['bb']['x']}
    b = {'x':params['bb']['x'] + params['bb']['w'], 'y':params['bb']['x']+params['bb']['h']}
    center = get_mid_point(a,b)

    # Debug info BB:({a})-({b}),
    inf=f"ShapeInfo:\n\n Coords-Len:{len(original_path_data)},\n Offset:{offset},\n Path-Len{pData['length']} \nSelf Intersect:{is_self_insct}"
    # dbg.plot_dot_param2(center, inf,"black", 4.0,"0.4em")#if debug: 

    """
    bpath = d1 
    #print(f"{bpath}")
    #all_path = cleaning_path(points_to_path_data(bpath))

    all_path = f"{points_to_path_data(d2,'ofd2')} {points_to_path_data(d1,'ofd')} "
    return all_path
    """


    # ====================================
    # Remove self-crossing segments
    # ====================================
    # Remove self-crossing segments in the path (max_detour_ration 180= bug inside line missing )
    # max_detour_ratio = 1.05: Only bends that are nearly straight are removed (sensitive)
    # max_detour_ratio = 3.0: Even slightly detoured paths are removed
    # max_detour_ratio = 9999: Almost all loops remain (hard to remove)
    
    
    max_detour_ratio = 180.0 if taper_mode != "none" else 1.05 # 
    if taper_mode in ["gear","chain","organic","punk","fluffy","stamp_top_group"]:max_detour_ratio = 85.0#85.0
    if taper_mode in ["rough"]:max_detour_ratio = 1.0
    if str(int(mitl))=="999": max_detour_ratio = 85.0
    

    #print(f"d1: {d1}")


    if taper_mode != "gear" and is_self_insct == False:
        # print("Removing short loops")
        d1 = remove_self_intersections(d1, 1, max_detour_ratio) # outside loop
        d2 = remove_self_intersections(d2, 1, max_detour_ratio) #inside loop


    #set coordinates flg (bit slowly)
    # d1=init_path_flg(d1);d2=init_path_flg(d2);

    # Error check
    if not d1:print("No ofs path");return None;



    #print(f"d1: {d1}") # inside rect
    #print(f"d2: {d2}") # outside rect

    #print(f"Orig_path{original_path_data}, len{len(original_path_data)}")

    # ===================================
    # Build line CAPs
    # ===================================
    cpp, cpp2 = "", ""

    # Dislplay all coorinates (It is useful but very slowly)
    #debug_view(d1,"d1",4,"green")
    #debug_view(d2,"d2",-3,"blue")

    # Use for detect short edge
    olen = len(original_path_data)

    if len(original_path_data) > short_limit:
        original_path_data = original_path_data[:-1]

    if is_single_segment:
        a=1 if params.get("reverse", False) else 0
        b=0 if params.get("reverse", False) else 1

        original_path_data[0]['x'] = single_segment_coord[a]['x']
        original_path_data[0]['y'] = single_segment_coord[a]['y']
        original_path_data[1]['x'] = single_segment_coord[b]['x']
        original_path_data[1]['y'] = single_segment_coord[b]['y']

    # === cap1 (line_cap_a : cpp) === 
    base_dir_array = get_cap_vector(original_path_data[0], original_path_data[1], 0.000001, offset)

    # print(f"Bae dir {base_dir_array}")
    base_dir = base_dir_array[0]
    if debug:debug_cap_direction(dase_dir)# display cap normal(debug)

    amp = { # Variable cap
        'taper_mode':taper_mode,'bb_short':params['bb_short'],'dash':params['dash'],'is_closed':is_closed,
        'ref':d2[-1],'ref2':d1[0],'olen':olen,'single':is_single_segment
    }

    cp = generate_cap_data(base_dir, offset, line_cap_a,amp, True) # line_cap
    #if taper_mode == "linear_a" and not is_single_segment:
    #    print(f"mm:{cp}")
    #    cp = reverse_mm_data(cp)

    if debug:
        dbg.plot_dot_param2(cp['coords'][0][0], "0 CAP","line", 6.0,"1em")#
        dbg.plot_dot_param2(cp['coords'][-1][0], "1","red",3.0,"1em")
        dbg.plot_dot_param2(d1[-1], "d1[-1]","blue", 6.0,"1em")
        dbg.plot_dot_param2(d2[0], "d2[0]","purple",3.0,"1em")

    #if taper_mode == "linear_a":print(f"CP:{cp}")
    cpp = output_cap_path(cp)


    # === cap2 (line_cap_b : cpp2) === 
    base_dir_array = get_cap_vector(get_last_s(original_path_data), get_last_p(original_path_data), 0.999999, offset)
    base_dir = base_dir_array[0]
    if debug:debug_cap_direction(dase_dir)# display cap normal(debug)
    
    amp = { # Variable cap
        'taper_mode':taper_mode,'bb_short':params['bb_short'],'dash':params['dash'],'is_closed':is_closed,
        'ref':d2[0],'ref2':d1[-1],'olen':olen,'single':is_single_segment
    }
    cp2 = generate_cap_data(base_dir, -offset, line_cap_b,amp,False) # line_cap

    if debug:
        dbg.plot_dot_param2(cp2['coords'][0][0], "C2[0]","blue", 6.0,"1em")#if debug:
        dbg.plot_dot_param2(cp2['coords'][-1][0], "C2[-1]","blue",3.0,"1em")#if debug:

    cpp2 = output_cap_path(cp2)

    outp=lp=lp2=miter_cut_flag = None
    lastC ="Z"


    # ===================================
    # Closed Path(d2:inside,d1 outside)
    # ===================================
    if is_closed:
        # LastResort:
        if not d2:print("Err:d2 not found");return None;
        #  inside loop(CCW)    outside loop(CCW)
        # M{cpp2}->{d2}->ZM{cpp}->{d1} {lastC:Z}
        #  linecap_b      linecao_a
        # for miter,round,bevel intersect by d2(lastPrim-Second and 0-1) 

        intersect_threshold = 5.0
        if taper_mode in ["rough"]:intersect_threshold = 180.0

        #dbg.plot_dot_param2(d1[-1], "*","blue",2.0,"1em")#if debug:
        #dbg.plot_dot_param2(d2[0], "*","purple",2.0,"1em")#if debug:

        #dbg.plot_dot_param2(anker, "a","green",2.0,"1em")#if debug:
        #dbg.plot_dot_param2(anker2, "a2","orange",2.0,"1em")#if debug:

        # ALL
        if taper_mode != ["linear","linear_a"]:

            cpp2 = f"M{poi(d2[-1])} L{poi(d2[0])} " # inside loop
            cpp = f"Z M{poi(d1[-1])} L{poi(d1[0])} "# outside loop
            # cut two coords in d2(last p and first 0)
            # d2=d2[1:-1]
            # print(f"before d1: {d1}")

            xcp = intersect_lp(d1[-2], d1[-1], d1[1], d1[0])
            if xcp :
                #rcp = get_mid_point(anker,xcp)
                # remove tail and 
                d1 = d1[1:-1]
                cpp = f"Z M{poi(xcp)} "

            #d1, cpp = trim_tail_loop(d1,0)

            if tagname in ["circle","ellipse"]:
                d1 = remove_self_intersections(d1, 1, 2)
                cpp2 = f"M{poi(d2[0])} " # inside loop
                cpp = f"Z M{poi(d1[-1])} "# ioutside loop


        # Edge case
        if taper_mode in ["linear"]:
            
            cpp  = f"Z M{poi(anker)} L{poi(d1[0])}"
            if line_join == "bevel":d1=d1[:-1]
            cpp2 = f"M{poi(anker2)}"
            
            #dbg.plot_dot_param2(d1[0], "L0","black", 2.0,"0.7em")

            all_path = f"{cpp2} {points_to_path_data(d1,'ofd')} {cpp} {points_to_path_data(d2,'ofd2')}Z"
            return cleaning_path(all_path)

        if taper_mode in ["linear_a"]:
            outp = intersect_miter(anker,d1[0],d2[-1],anker,intersect_threshold)
            lp = get_mid_point(anker2,anker)
            cpp2 = f"M{poi(lp)}"
            cpp  = f"Z M{poi(lp)}"

            all_path = f"{cpp2} {points_to_path_data(d1,'ofd')} {cpp} {points_to_path_data(d2,'ofd2')}Z"
            return cleaning_path(all_path)

        if taper_mode in ["gear","punk","fluffy"]:
            d1=d1[:-1]
            cpp2 = f"Z M{poi(d1[0])} "
            cpp = f" L{poi(anker)} "
            #dbg.plot_dot_param2(lp2, "lp2","black", 4.0,"1.5em")
            all_path = f"{cpp2} {points_to_path_data(d1,'ofd')} {cpp}Z"
            return cleaning_path(all_path)

        # An original last point will removed afterwards
        # cut a coord in d1(last p) This point cause glitch(on pallalell case )
        # There are two case  that palallel(circle like) and cross(it has a shapen shape)

        if line_join == "round":# outside loop need Z
            cpp2 = ""+create_arc_path(get_last_p(d2), d2[0], offset, offset, 0, 0)

        if taper_mode in ["organic","chain","rough","stamp_top_group"]:d1=d1[:-1]

        lastC = "Z"

        #print(f"Distance : {eular_distance(anker2,get_last_p(d2))}")

    # ===================================
    # Opend Path 
    # ===================================
    if is_closed==False and taper_mode != "none" :
        #  inside loop(CCW)    outside loop(CCW)
        #  M{cpp2}->{d2}->ZM{cpp}->{ofd1} {lastC:Z}
        #      linecap_b            linecao_a

        # print(f"d1:{d1},,, d2:{d2}")

        if taper_mode in ["linear", "linear_a"] :

            if taper_mode == "linear_a":
                # debug
                if debug:
                    print(f"CP2:hasM:::: {is_move_command(cpp2) }") 
                    print(f"CP1:hasM:::: {is_move_command(cpp) }") 
                
                if is_move_command(cpp2):
                    cpp2=replace_move_to_with_line(cpp2)

                if str(int(mitl))=="999":d1 = d1[:-1]
                # Start point  cap B (cpp2)
                #cpp2 = f"M{poi(d2[0])}"+cpp2
                cpp2 = f"M{poi(d1[-1])}"+cpp2

                # Get and canonicalize a bridge point
                # debug
                if debug:
                    raw_bridge = cp["coords"][-1]
                    bridge_pt = normalize_point(raw_bridge)
                    print("::: raw_bridge  =", raw_bridge)
                    print("::: bridge_pt   =", bridge_pt)
                    print("::: poi(bridge) =", poi(bridge_pt))
            
                # Join  point  cap A (cpp)
                if is_move_command(cpp):
                    cpp=replace_move_to_with_line(cpp)

                lastC = "Z"

            if taper_mode == "linear":
                cpp = f"L{poi(original_path_data[0])}"


        #with open Path

    is_single_segment = False
    if not d1:print("Err:ofs_not found");return None
    """
    if debug:
        dbg.plot_dot_param2(get_last_p(d2), "d2E⇒cp","black", 4.0,"1.5em")
        dbg.plot_dot_param2( d2[0], "cp2⇒d2S","red", 4.0,"1.5em")
        dbg.plot_dot_param2(get_last_p(d1), "d1E⇒Z","black", 4.0,"1.5em")
        dbg.plot_dot_param2( d1[0], "cp⇒d1S","red", 4.0,"1.5em")
    """

    # Join all of the path units
    all_path = f"{cpp2} {points_to_path_data(d2,'d2')} {cpp} {points_to_path_data(d1,'d1')}{lastC}"


    #debug_path_view(0, all_path, 4 , "black")

    """
    print("[DEBUG] cpp2:", cpp2)
    print("[DEBUG] d2  :", points_to_path_data(d2, 'ofd2'))
    print("[DEBUG] cpp :", cpp)
    print("[DEBUG] d1  :", points_to_path_data(d1, 'ofd'))
    print("[DEBUG] all_path:", all_path)
    """
    return cleaning_path(all_path)


# ----------------------------------------
# Support functions for all connection
# ---------------------------------------

def replace_move_to_with_line(path_str):
    """
    The case if SVG path string start with 'M' or 'm' 
    Replace it to 'L' or 'l'
    """
    path_str = path_str.lstrip()  # Remove a white-space at first
    if path_str.startswith("M"):
        return "L" + path_str[1:]
    elif path_str.startswith("m"):
        return "l" + path_str[1:]
    else:
        return path_str

def is_move_command(path_str):
    """
    Check SVG path string start with 'M' 
    e.g.: 'M12 34' -> True, 'L12 34' -> False
    """
    if not path_str:
        return False
    return path_str.strip().startswith('M')

    
def normalize_point(pt):
    # This function doesn't modify to dict 
    if isinstance(pt, dict):
        return pt

    # [x, y] list -> dict
    if isinstance(pt, list) \
       and len(pt) == 2 \
       and all(isinstance(c, (int, float)) for c in pt):
        return {"x": pt[0], "y": pt[1]}

    # Nested list: get the last element 
    if isinstance(pt, list) and pt:
        return normalize_point(pt[-1])

    raise ValueError(f"Unsupported point format: {pt}")


def get_groupshape_bounds(group_shape):
    """
    Return BB and center coordinates of the GroupShape
    Return: (min_x, min_y, max_x, max_y, center_x, center_y)

    bounds = get_groupshape_bounds(group_shape)
    if bounds:
        min_x, min_y, max_x, max_y, cx, cy = bounds

    """
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def collect_bounds(shape):
        nonlocal min_x, min_y, max_x, max_y
        if shape.type() == 'groupshape':
            for child in shape.children():
                collect_bounds(child)
        else:
            inv_transf, invertible = shape.absoluteTransformation().inverted()
            bbox = inv_transf.mapRect(shape.boundingBox())
            min_x = min(min_x, bbox.x())
            min_y = min(min_y, bbox.y())
            max_x = max(max_x, bbox.x() + bbox.width())
            max_y = max(max_y, bbox.y() + bbox.height())

    collect_bounds(group_shape)

    if min_x == float('inf'):
        return None  # No shapes in the group

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    return (min_x, min_y, max_x, max_y, center_x, center_y)

# ------------------------
# optional export(debug)
# ------------------------
def save_svg(svg_element, file_name="result.svg"):
    # Serialize SVG data to strings
    svg_data = ET.tostring(svg_element, encoding="unicode", method="xml")
    
    # Save to file
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(svg_data)

    print(f"SVG file saved as {file_name}")


def debug_message(msg):
    if parent_dialog is not None:
        QMessageBox.information(parent_dialog, "DEBUG", msg)  # Set as parent window
    else:
        print("Warning:Parent window is not selected")
        raise ValueError(msg)

# ------------------------
# dot_to_dot (main) 
# ------------------------
# taper_mode == "dot_to_dot"
def dot_to_dot_main(params,d1,d2,taper_mode, orig_elm,
             total_pts, original_path_data, pData,
             is_single_segment=False,
             single_segment_coord=None):

    if params['original']==True:
        pt = total_pts
    else:
        pt = 1;

    # params['factor'] takes 0 .. 100float(orig_elm['stroke-width']) +
    strokes = float(orig_elm.get("stroke-width", "4"))
    dot_size = round(4 * params['factor'] * 0.01 + params['ofs'] * 0.1, 4)
    if dot_size <= 0:
        dot_size = 0.5
    
    text_size_val =  scale_factor(params['factor'], strokes*0.5, strokes*3)

    if text_size_val <= 0:
        text_size_val = 8
    spacing = text_size_val * 0.5
    text_size = str(text_size_val) + "px"

    #print(f"factor:{params['factor']}  dot:{dot_size} txt:{text_size}")
    #print(f"pt{pt} : total_pts{total_pts}")

    if pt > 0:
        if is_single_segment == True:
            single_segment_coord=single_segment_coord[::-1]
            pt = plot_pts(single_segment_coord,pt,"black",dot_size,text_size,spacing);
            if params['original']==True: total_pts = pt
            return None;

        else:
            ms=[{'x': pData['points'][0]['x'],'y':pData['points'][0]['y'] }]
            mg={'x': pData['points'][-1]['x'],'y':pData['points'][-1]['y'] }# no wrap by[]

        original_path_data[-1]=mg
        e = create_cv_point( ms + original_path_data, deg_threshold=22)
        pt = plot_pts(e,pt,"black",dot_size,text_size,spacing);
        if params['original']==True: total_pts = pt
        
        return None;

# ------------------------
# stamp (path_along)
# ------------------------
def get_extra_stamp_transforms(pData, spacing, rotation_offset,rand_flg,scuff):
    points = pData['points']
    transforms = []

    # calcurate total length
    segments = []
    total_length = 0
    for i in range(len(points) - 1):
        x1, y1 = points[i]['x'], points[i]['y']
        x2, y2 = points[i+1]['x'], points[i+1]['y']
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        segments.append({
            'x1': x1, 'y1': y1,
            'x2': x2, 'y2': y2,
            'dx': dx, 'dy': dy,
            'length': seg_len
        })
        total_length += seg_len

    # caluclate a position of stamp per spacing
    # print(f"Total path length: {total_length} // {spacing}")
    MAX_STAMPS = 75
    
    try:
        num_stamps = int(total_length // spacing)
        if num_stamps > MAX_STAMPS:
            print(f"Stamp count limited from {num_stamps} to {MAX_STAMPS}")
            num_stamps = MAX_STAMPS
    except Exception as e:
        print(f"Error calculating num_stamps: {e} fixed to 1")
        num_stamps = 1


    current_distance = 0
    seg_index = 0

    for i in range(num_stamps + 1):
        target_distance = i * spacing

        # Progress a distance from current segment
        while seg_index < len(segments) and current_distance + segments[seg_index]['length'] < target_distance:
            current_distance += segments[seg_index]['length']
            seg_index += 1

        if seg_index >= len(segments):
            break

        seg = segments[seg_index]
        local_dist = target_distance - current_distance
        t = local_dist / seg['length']
        px = seg['x1'] + seg['dx'] * t
        py = seg['y1'] + seg['dy'] * t
        angle = math.degrees(math.atan2(seg['dy'], seg['dx'])) + rotation_offset

        if rand_flg and scuff != 0:
            angle = round(random.uniform(0, 360), 2) 
            sx = round(random.uniform(-scuff, scuff), 2)
            sy = round(random.uniform(-scuff, scuff), 2)
        else:
            sx = 0
            sy = 0
        transforms.append({
            'x': px+sx,
            'y': py+sy,
            'angle': angle,
            'transform': f'translate({px},{py}) rotate({angle})'
        })

    return transforms




# ------------------------
# stamp (main)
# ------------------------
# taper_mode == "stamp_top_group"
def stamp_main(pData,params,taper_mode, tagname):

    spacing = params['stamp_along']['width'] + (params['stamp_along']['width'] * params['ofs']*0.1)+ params['mitl']
    if spacing < 1 :1.0

    rotation_offset = map_s_scale(params['factor'],0,100,-180,180)

    rand_flg = True if params['original'] else False # Random rotate/scale
    rand_opa = True if params['fillview'] else False # Random opacity

    scuff = params['mitl']
    stamps_pos = get_extra_stamp_transforms(pData, spacing, rotation_offset,rand_flg,scuff)

    pid = str(uuid.uuid4())[:8];# no preview_shapes_ for id
    outer = ' transform="   " ' 
    stmp = params['stamp_along']['original'];
    cen = params['stamp_along']['center'];
    # print(f' spacing : {spacing}')


    if cen == {}:print("Not detect bounding box of the groupshape");return None
    rot=add_angle=ct=0;stmp_shapes=[]

    #scaling
    if params['ofs'] < 0 :
        sc = 0.5 + abs( params['ofs'] )*0.01;
    else:
        sc = 0.5 + abs( params['ofs'] )*0.1;


    if sc <= 0 :sc = 0.5
    if sc >= 10 :sc = 10

    min_scale = 0.1;max_scale = 1.5;total_len = len(stamps_pos)
    

    for pos in stamps_pos:
        # Replace id to pid at first match in stamp
        
        angle = pos.get('angle',0)
        angle = angle + add_angle
        #print(f'Shape::: tag:{tagname}  pos:{pos}')
        subt = f""
        # tf=f' translate({pos["x"]},{pos["y"]}) translate({-cen["x"]},-{cen["y"]})  rotate({angle},{cen["x"]},{cen["y"]}) rotate({rot},0,0)  scale({sc})  '


        if rand_flg == True: sc = round(random.uniform(0.1, 1.5), 2) # random

        if params['single_path']:
            t = ct / (total_len - 1) if total_len > 1 else 0  # normalize（0〜1）
            sc = min_scale + (max_scale - min_scale) * t

        tf=f' {pos["transform"]} scale({sc})  '

        
        stmp = re.sub(r'id="[^"]+"', f'id="{pid+"_ch"+str(ct)}"', stmp, count=1)# id
        stmp = re.sub(r'transform="[^"]+"', f'transform="{tf}"', stmp, count=1)# transform

        # If 'opacity' exists, replace it; otherwise, add it
        if rand_opa==True:
            op = round(random.uniform(0.15, 1.0), 2) 
            if re.search(r'\sopacity="[^"]+"', stmp):
                stmp = re.sub(r'\sopacity="[^"]+"', f' opacity="{op}"', stmp, count=1)
            else:
                stmp = re.sub(r'<g\b', f'<g opacity="{op}"', stmp, count=1)



        #dbg.plot_dot_param2({'x':pos["x"],'y':pos["y"] }, "","blue", 2.0,"1em")
        stmp_shapes.append(stmp)
        ct=ct+1

    s = "\n".join(stmp_shapes); gid=params['preview_id_prefix']+"cpy"+pid
    gtf = params['stamp_along']['abst']
    #print(f'<g id="{gid}" transform="{gtf}">')
    params['stamp_along']['data'].append(f'<g id="{gid}" transform="{gtf}">{s}</g>')# par a shape
    #print(params['stamp_along']['data'][-1])

    return None;


# -----------------------------------------------------------
# Unified management of coefficients (density, spacing, randomness) for each taper mode
# * Density: Adjusts the denseness of the shape, such as the frequency of the waveform and the number of teeth
# * Spacing: Adjusts the spread and amplitude of the wave. The larger the value, the wider it becomes
# * Randomness: Adds noise and sharpness (low is soft, high is sharp)
#
# Below are examples of each mode. For example, in "organic" mode, it is
# (1.0, 0.8, 0.5)
# * 1.0: Density → Smoothness of the entire curve, or the slope of the parabola
# * 0.8: Spacing → Wave spread (narrow/wide)
# * 0.5: Randomness → Random change of shape (modest for soft, strong for punk)
# -----------------------------------------------------------
#         wave nun,wavehight
#          density, spacing, randomness 

def adjust_for_collision(offset_upper, offset_lower, min_gap=0.01):
    """
    A helper function to ensure a minimum gap (min_gap) so that the offsets do not cross above or below.
    
    Parameters:
      offset_upper: float, upside offset value 
      offset_lower: float, downside offset value 
      min_gap     : float, minimum gap for nessesary up to down offset
    
    Returns:
      (offset_upper, offset_lower) : Adjusted tuple data of offset value
    """
    if abs(offset_upper - offset_lower) < min_gap:
        adjustment = (min_gap - abs(offset_upper - offset_lower)) / 2.0
        # Adjusting value increase at upside or decrease at downside
        offset_upper += adjustment
        offset_lower -= adjustment
    return offset_upper, offset_lower


def unified_offset(t, total_length, max_offset,line_join, factor, mode):
    """
    A function to calculate a unified offset value.
    
    The parameter t is normalized by total_length,
    and the correction coefficients for each mode (density, spacing, randomness) and
    the user-adjustable factor are used to return an offset value according to the characteristics of each shape.
    
    Parameters:
        t            : float, current position (distance on the path, ranges from 0 to total_length)
        total_length : float, total path length (used for normalization)
        max_offset   : float, base maximum offset (height)
        factor       : float, user-adjusted factor (controls overall density/scale)
        mode         : str, taper mode. Corresponding values ​​are:
                     "chain", "fluffy", "punk", "gear", "sawtooth",
                     "cycloid", "cycloid2", "organic", "rough", "linear", "linear_a"
    
    Returns:
      offset       : float, Single side offset value (positive applies to top side, negative applies to bottom side)
    """
    if mode == "none": return max_offset

    # Identify t to range from 0 to 1
    normalized_t = t / total_length if total_length != 0 else 0
    f = factor
    # params['factor'] range is 0-100

    #         wave nun,wavehight
    #          density, spacing, randomness 
    mode_coeffs = {
        "chain":     (3.0, 1.0, 0.5),# (1.3, 0.8, 0.5)
        "organic":   (9.4, 1.0, 0.1),# (9.0, 0.9, 0.1)
        "fluffy":    (0.8, 1.6, 0.3),# (0.8, 1.5, 0.3)
        "punk":      (0.6, 0.6, 0.9),# (1.0, 0.6, 0.9)
        "gear":      (1.0, 1.0, 0.7),# (1.0, 1.0, 0.7)
        "sawtooth":  (0.5, 1.0, 0.8),
        "rough":     (0.2, 1.0, 0.8),# (1.0, 1.0, 0.9),
        "linear":    (0.8, 1.0, 0.1),
        "linear_a":  (0.8, 1.0, 0.1),
        "stamp_top_group":(2.0, 1.0, 0.5)# (9.0, 0.9, 0.1)
    }

    # Get adjustment factor to each modes（Default parameter is (1, 1, 1)）
    density, spacing, randomness = mode_coeffs.get(mode, (1.0, 1.0, 1.0))
    
    # Calculate basical angle
    # Based on math.pi, Adjust frequency(or catenary progression)by  density and factor
    base_angle = normalized_t * math.pi * density * factor

    freq = 1.0 if line_join == "miter" else 0.2
    ifreq = 1.0 if line_join == "miter" else 0.02



    # Define offset value to each modes
    if mode in ["chain","organic"]:
        # Taperd and curve on the center
        if mode == "chain":
            pod = 1.2;shift =1.5;
        else:
            pod = 1.4;shift = (0 if max_offset <= 0  else 3)
            if max_offset <= 0:
                offset = max_offset+shift
                return offset

        offset = max_offset * math.sin(base_angle * pod) * spacing 
        offset = offset + shift

    elif mode == "stamp_top_group":
        offset = 0.01

    elif mode in ["fluffy", "punk"]:

        # fluffy / punk: A shape that combines catenary and sharp peak curve
        period = math.pi  # Set to pi for the wave period 
        mod_angle = ((20 if mode == "punk" else 10) * base_angle % period )  # The angle par 10 period: base_angle % period
        u = mod_angle / period  # Normalize from 0 to 1
        x = u - 0.5             # Shifted to be symmetrical around the center
        punk_coef = randomness  # Use randomness as the punk factor
        # A normalization constant (value at x=±0.5) is used to generate catenary-shaped components.
        norm = factor*0.5*math.cosh(punk_coef * 0.5) - 1
        catenary_component = 1 - ((math.cosh(punk_coef * x) - 1) / norm)
        # Sharp peak components near the center
        sharp_component = math.pow(math.sin(math.pi * u), punk_coef)
        weight = punk_coef / (punk_coef + 1)*(5 if mode == "punk" else 1)
        combined = weight * catenary_component + (1 - weight) * sharp_component

        # In "punk" mode,make more sharpen corner to negative direction by shift
        if mode == "punk":
            shift = max_offset * (0.8 + 0.1 * factor * normalized_t)+factor
        else:
            shift = max_offset * 0.04

        offset = max_offset * combined * spacing + shift

    elif mode == "gear":
        # gear: The action resembles a square wave, creating a gear tooth shape.
        # Consider the factor as ranging from 0 to 99, and linearly map the number of teeth from 2 to 100.
        min_teeth = 2;max_teeth = 150
        shift = (-max_offset if max_offset < 0 else 0)
        
        teeth_count = min_teeth + (max_teeth - min_teeth) * (factor / 99.0*1.5)
        frequency = teeth_count * 10 * math.pi  # Frequency according to number of teeth
        # The effect of accelerating the phase by t^2
        scaled_angle = frequency * normalized_t # Frequency (normalized_t ** 2)
        # Change the magnitude when the sin value is positive or negative (square wave-like switching)
        offset = max_offset * (1.5 if math.sin(scaled_angle) >= 0 else 0.5) * spacing
        
        #offset = (offset + factor * 0.5) - shift

        #print(offset)

    elif mode == "sawtooth":
        # sawtooth: Linearly increasing and resetting every cycle
        base_angle = base_angle * 20# ok
        offset = max_offset * ((base_angle % math.pi) / math.pi) * spacing
        offset = offset + factor * 0.1

    elif mode == "rough":
        # Add noise to a basic sine wave to create rough edges
        base = max_offset * (1.2 - 0.01 * math.cos(base_angle*ifreq))
        # Change the multiplier to 0.2 to strengthen the effect of factor
        roughness_scale = 0.1 +factor * freq
        noise = random.uniform(-roughness_scale, roughness_scale) * max_offset * randomness
        offset = base + noise

    elif mode == "linear":
        # linear: Linearly decreasing offset from start point to end point
        
        offset = -max_offset * normalized_t * spacing#+factor
        offset *= smooth_fade(normalized_t,0.599+factor,2*factor,0.95)


    elif mode == "linear_a":
        power = 1.75
        height_scale = 0.15 + factor * 0.4
        width_scale = 0.5
        center = max(0.1, 0.95 + factor * 0.2) + factor*0.5
    
        # Horizontal symmetricalize（same value when t=0.0 and t=1.0)
        t_shifted = abs(normalized_t - center) / center
        t_sym = min(2.0, t_shifted)
    
        # A point of offset path generete（- direction movement ）
        offset = -max_offset * ((2.0 - t_sym) ** power) * height_scale
        offset += 0.1 * width_scale * factor  # A compoment for micro adjustment

    else:
        # No offset unless otherwise specified
        offset = max_offset

    return offset

# ----------------------------------
# Support functions
# ----------------------------------
def smooth_fade(t, edge=0.995, sharpness=100.0, strength=0.5):
    """
    edge : start  , sharpness :e.g.100 obviously change,10 smooth shift 
    """
    x = (t - edge) * sharpness
    s = 1 / (1 + math.exp(-x))
    return 1.0 - s * strength


def taper_offset_points(pData, params, offset, epsilon, delta, line_join, mitl, taper_mode):
    """
    A function that calculates the offset point on one side (e.g. the top side) for a point on a polyline.
    
    The unified function taper_unified_offset is used to calculate the offset value at each point,
    and then it is simply added to the corresponding normal direction. This allows the top and bottom offsets to maintain a state where they do not intersect
    (this can be achieved by simply inverting the positive and negative).
    
    Parameters:
        pData : dict, original path data (contains 'length' and 'points' lists)
        params : dict, parameters passed from GUI, etc. Here includes 'factor'
        offset : float, base maximum offset value (height)
        epsilon : int, step value between samples (for thinning)
        delta : float, auxiliary parameter for tangent calculation (not used here but exists)
        line_join : path connection parameter (use if necessary)
        mitl : additional parameters (use if necessary)
        taper_mode : str, taper mode to use (e.g. "organic", "gear", etc.)
      
    Returns:
      offset_points : list of dicts,The new coordinates of each point after offsetting {'x': float, 'y': float}
    """
    total_length = pData.get('length', 1)
    points = pData.get('points', [])
    
    # Consider the value takes 0 to 100 come from slider GUI element(default:50=1.0)
    raw_slider_value = params.get('factor', 50)
    # Use mapping function,convert raw value to internal factor
    factor = map_slider_to_factor(raw_slider_value,taper_mode)
    
    acc_offset_points = []
    max_offset = offset  # Basical offset value
    
    for i in range(0, len(points), int(epsilon)):

        if i >= len(points):  # Boundary check
            print(f"Index {i} is out of range. Skipping.")
            break


        point = points[i]
        if not point.get('draw', True):
            continue

        # Calculate an angle from path data
        tangent = get_tangent_at_length(pData, i, total_length, delta)
        angle = math.degrees(math.atan2(tangent['y'], tangent['x']))

        # get normal vector 
        normal = {'x': -tangent['y'], 'y': tangent['x']}
        normal_length = math.sqrt(normal['x'] ** 2 + normal['y'] ** 2)
        
        # To avoid zero division to use minimum threshold
        epsilon_threshold = 0.0001
        divisor = normal_length if normal_length >= epsilon_threshold else epsilon_threshold
        unit_normal = {
            'x': normal['x'] / divisor,
            'y': normal['y'] / divisor
        }
        

        # Get t the point lies on the path(assuming index as distance)
        t_value = i
        current_offset = unified_offset(t_value, total_length, max_offset, line_join, factor, taper_mode)

        # Default offset

        # Circle/Ellipse variant fall-back (for make more amplified waves if it a large size object)
        current_offset = current_offset*-1.98 if params.get('long', False) == True else current_offset

        # Set an offset point 
        new_point = {
            'x': point['x'] + current_offset * unit_normal['x'],
            'y': point['y'] + current_offset * unit_normal['y'],
            'angle': angle
        }

        acc_offset_points.append(new_point)
    
    return acc_offset_points

def map_slider_to_factor(slider_value,taper_mode):
    """
    slider_value: from 0 to 100  
    Object : f(0)=0.5, f(50)=1.0, f(100)=2.0 with linear/non-linaer mapping 

    """
    # Quadratic term coefficient, linear term coefficient, initial value
    mode_tune = {
        "gear":     (0.00008, 0.0042, -1.5),# -1.0 - -0.65 - 0.22 
        "rough":     (0.00008, 0.0042,  0 ),# -1.0 - -0.65 - 0 
    }

    # Get the correction coefficient for each mode
    # a=linear , b=quadric , c=constant term
    a,b,c = mode_tune.get(taper_mode, (0.0001, 0.005, 0.5)) # 0.5 - 1.0 -2.0

    return a * slider_value**2 + b * slider_value + c


# ----------------------------------
# ten tunagi(dot to dot)
# ----------------------------------

def calculate_curvature(pts):
    """ Get curvature(angle) of each coordinates ,return dictonary data"""
    if len(pts) < 3:
        print("Err:Too few vertices, at least 3 points are needed to calculate curvature.")
        return []

    curvatures = []
    for i in range(1, len(pts) - 1):
        p1, p2, p3 = pts[i-1], pts[i], pts[i+1]

        # Get coords
        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]
        x3, y3 = p3["x"], p3["y"]

        # Vector caluclate
        v1 = (x1 - x2, y1 - y2)
        v2 = (x3 - x2, y3 - y2)

        dot_product = v1[0] * v2[0] + v1[1] * v2[1]  # Inner product
        magnitude_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
        magnitude_v2 = math.sqrt(v2[0]**2 + v2[1]**2)

        if magnitude_v1 * magnitude_v2 == 0:
            angle = 0
        else:
            cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
            angle = math.degrees(math.acos(max(-1, min(1, cos_theta))))  # Adjust the value to range

        curvatures.append((i, angle))
    
    return curvatures
# ----------------------------------
# Debug plot (part2)
# ----------------------------------
def create_cv_point(original_pts, deg_threshold=22):
    """ Plot a point that has curvature greater than the tolerance."""
    curvatures = calculate_curvature(original_pts)
    if not curvatures:
        return

    high_curvature_pts = [{"x": original_pts[i]["x"], "y": original_pts[i]["y"]} for i, angle in curvatures if angle >= deg_threshold]
    """
    if high_curvature_pts:
        print("High carvature pts are:")
        for pt in high_curvature_pts:
            print(f"p: {pt}")
    else:
        print("Not found high curvature of points")
        return 
    """
    return high_curvature_pts

# Plot 
def plot_pts(coords,num,color="black",dot_size=2,text_size="0.5em",spacing=0):
# Plot points with incremental numbers (for dot_to_dot mode etc)
    if not coords:return num
    for c in coords:
        if dbg:dbg.plot_dot_param2( c , str(num) ,color, dot_size,text_size,spacing);num=num+1
    return num


def plot_pts2(coords,num,name,shift=4,color="black"):
# Plot points with incremental numbers
    if not coords:return num
    for c in coords:
        if dbg:
            # if num < 1 or num > len(coords)-1:
            if 0 <= num:
                dbg.plot_dot_param3( c , name+"["+str(num)+"]" ,color, 3,shift,size="0.8em");
            num=num+1
    return num

def debug_view(path_data,name,shift,color):
    test = True
    # dot connection
    if test:
        pt = 0
        if pt >= 0:
            e = create_cv_point(path_data, deg_threshold=22)
            pt = plot_pts2(e,pt,name,shift,color);


# --------------------
# debug for d attribute
# --------------------
def debug_path_view(cnt, path_data, shift, color):
    if cnt >= 0:
        coords = path_to_array(path_data)
        cnt = plot_pts3(coords, cnt, shift, color)
    return cnt

def plot_pts3(coords, num, shift=4, color="black"):
    if not coords: return num
    for obj in coords:
        cmd = obj["cmd"]
        pt = obj["point"]
        if pt and dbg:
            label = f"{cmd}({num})"
            dbg.plot_dot_param3(pt, label, color, 1.25, shift, size="0.4em")
        num += 1
    return num

def path_to_array(path_data):
    pattern = r'([MLZmlz])([^MLZmlz]*)'
    tokens = re.findall(pattern, path_data)

    result = []
    current_index = 0
    last_m_index = None  # Record the count when M command appeared at last

    for cmd, value in tokens:
        cmd = cmd.upper()
        if cmd == "Z":
            label = f"Z({current_index}→{last_m_index})"
            result.append({
                "cmd": label,
                "point": None
            })
            current_index += 1
        else:
            numbers = list(map(float, re.findall(r'[-+]?[0-9]*\.?[0-9]+', value)))
            for i in range(0, len(numbers), 2):
                point = {"x": numbers[i], "y": numbers[i+1]}
                result.append({
                    "cmd": cmd,
                    "point": point
                })
                if cmd == "M":
                    last_m_index = current_index
                current_index += 1

    return result


# for single test
if __name__ == "__main__":

    re_init(params['preview_id_prefix'])
    process_selected_shapes(params)
    re_z_index(params['preview_id_prefix'],9999)
 