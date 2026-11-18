#!/usr/bin/env python3
"""Render reviewed structured social content to editable SVG and delivery PNG/PDF."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
STYLES = Path(__file__).resolve().parents[1] / "catalog" / "styles.json"
COLOR_KEYS = {"background", "surface", "ink", "muted", "accent", "accent2", "line"}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def element(parent, tag: str, **attrs):
    return ET.SubElement(parent, f"{{{SVG}}}{tag}", {key.replace("_", "-"): str(value) for key, value in attrs.items()})


def txt(parent, value, x, y, size, color, weight="normal", font="Arial", anchor="start"):
    node = element(parent, "text", x=x, y=y, fill=color, font_size=size, font_weight=weight,
                   font_family=font, text_anchor=anchor)
    node.text = str(value)
    return node


def lines(value, max_chars):
    words = str(value).split()
    result, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if len(trial) > max_chars and current:
            result.append(current)
            current = word
        else:
            current = trial
    if current:
        result.append(current)
    return result


def wrapped(parent, value, x, y, width, size, color, font, weight="normal", max_lines=4):
    max_chars = max(10, int(width / (size * 0.55)))
    result = lines(value, max_chars)
    if len(result) > max_lines:
        raise ValueError(f"Text exceeds {max_lines} lines at delivery size: {str(value)[:55]}")
    for index, line in enumerate(result):
        txt(parent, line, x, y + index * size * 1.25, size, color, weight, font)
    return y + len(result) * size * 1.25


def validate_content(card: dict):
    if not isinstance(card, dict) or not str(card.get("title", "")).strip():
        raise ValueError("Every card needs a title")
    nodes = card.get("nodes", [])
    if nodes:
        ids = [node.get("id") for node in nodes]
        if any(not re.fullmatch(r"[A-Za-z0-9_-]+", str(node_id or "")) for node_id in ids) or len(set(ids)) != len(ids):
            raise ValueError("Diagram node IDs must be unique and safe")
        if any(not str(node.get("label", "")).strip() for node in nodes):
            raise ValueError("Diagram nodes need labels")
        for node in nodes:
            for axis in ("x", "y"):
                if axis in node and not (isinstance(node[axis], (float, int)) and 0 <= node[axis] <= 1):
                    raise ValueError(f"Node {node['id']} {axis} must be normalized 0..1")
        for edge in card.get("edges", []):
            if edge.get("from") not in ids or edge.get("to") not in ids or edge.get("from") == edge.get("to"):
                raise ValueError(f"Edge references an unknown or identical node: {edge}")
            if not str(edge.get("label", "")).strip():
                raise ValueError("Each diagram edge needs a relationship label")
    elif card.get("edges"):
        raise ValueError("Edges require nodes")
    data = card.get("data", [])
    if data:
        if not str(card.get("unit", "")).strip() or not str(card.get("sourceNote", "")).strip():
            raise ValueError("Charts need unit and sourceNote")
        for item in data:
            if not str(item.get("label", "")).strip() or not isinstance(item.get("value"), (int, float)) or not math.isfinite(item["value"]) or item["value"] < 0:
                raise ValueError("Chart data need labels and finite nonnegative values")
    if card.get("comparison") and len(card["comparison"]) != 2:
        raise ValueError("Comparison cards need exactly two sides")
    if card.get("comparison") and any(not str(side.get("label", "")).strip() for side in card["comparison"]):
        raise ValueError("Comparison sides need labels")


def style_for(style_id: str, theme: dict | None = None):
    catalog = read(STYLES)["styles"]
    style = next((item.copy() for item in catalog if item["id"] == style_id), None)
    if style is None:
        raise ValueError(f"Unknown visual style: {style_id}")
    for key, value in (theme or {}).items():
        if key in COLOR_KEYS:
            if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"Invalid theme color: {key}")
            style[key] = value
        elif key == "font" and isinstance(value, str) and value.strip():
            style[key] = value
        else:
            raise ValueError(f"Unsupported theme key: {key}")
    return style


def backdrop(root, style, width, height, margin):
    treatment = style["treatment"]
    element(root, "rect", x=0, y=0, width=width, height=height, fill=style["background"])
    if treatment == "glass":
        element(root, "circle", cx=width*0.83, cy=height*0.20, r=width*0.31, fill=style["accent2"], opacity="0.8")
        element(root, "circle", cx=width*0.11, cy=height*0.75, r=width*0.38, fill=style["accent"], opacity="0.18")
    elif treatment in {"swiss", "isometric"}:
        step = 75 if treatment == "swiss" else 65
        for x in range(0, width, step):
            element(root, "line", x1=x, y1=0, x2=x, y2=height, stroke=style["line"], stroke_opacity="0.12", stroke_width=1)
        for y in range(0, height, step):
            element(root, "line", x1=0, y1=y, x2=width, y2=y, stroke=style["line"], stroke_opacity="0.12", stroke_width=1)
    if treatment == "brutalist":
        element(root, "rect", x=0, y=0, width=width, height=24, fill=style["ink"])
        element(root, "rect", x=margin, y=margin, width=170, height=20, fill=style["accent2"], stroke=style["ink"], stroke_width=3)
    elif treatment == "handdrawn":
        element(root, "path", d=f"M {margin} {margin} Q {width/2} {margin-11} {width-margin} {margin+5}",
                fill="none", stroke=style["accent"], stroke_width=5)
    elif treatment == "editorial":
        element(root, "line", x1=margin, y1=margin, x2=width-margin, y2=margin, stroke=style["ink"], stroke_width=2)
        element(root, "line", x1=margin, y1=margin+11, x2=width-margin, y2=margin+11, stroke=style["line"], stroke_width=1)
    elif treatment == "bento":
        element(root, "rect", x=margin, y=margin, width=100, height=18, rx=9, fill=style["accent"])
        element(root, "rect", x=margin+112, y=margin, width=48, height=18, rx=9, fill=style["ink"])
    elif treatment == "glow":
        element(root, "line", x1=margin, y1=margin, x2=width-margin, y2=margin,
                stroke=style["accent"], stroke_width=10, opacity="0.12")
        element(root, "line", x1=margin, y1=margin, x2=width-margin, y2=margin,
                stroke=style["accent"], stroke_width=2)
    else:
        element(root, "line", x1=margin, y1=margin, x2=width-margin, y2=margin,
                stroke=style["accent"], stroke_width=4 if treatment == "swiss" else 2)


def panel(root, style, x, y, width, height, accent=False):
    """Draw the same information surface through the selected visual language."""
    treatment = style["treatment"]
    if treatment == "minimal":
        element(root, "rect", x=x, y=y, width=width, height=height, rx=3,
                fill=style["surface"], stroke=style["line"], stroke_width=1)
    elif treatment == "bento":
        element(root, "rect", x=x, y=y, width=width, height=height, rx=34,
                fill=style["accent2"] if accent else style["surface"])
        element(root, "rect", x=x+20, y=y+20, width=62, height=8, rx=4, fill=style["accent"])
        element(root, "circle", cx=x+width-28, cy=y+height-26, r=min(52, height*0.22),
                fill=style["accent"], opacity="0.12")
        element(root, "circle", cx=x+width-28, cy=y+height-26, r=min(30, height*0.13),
                fill=style["accent"], opacity="0.18")
    elif treatment == "glass":
        element(root, "rect", x=x+8, y=y+12, width=width, height=height, rx=30,
                fill=style["background"], opacity="0.20")
        element(root, "rect", x=x, y=y, width=width, height=height, rx=30,
                fill=style["surface"], opacity="0.24", stroke=style["line"], stroke_width=3)
        element(root, "line", x1=x+30, y1=y+7, x2=x+width-30, y2=y+7,
                stroke=style["line"], stroke_width=3, opacity="0.75")
    elif treatment == "neumorphic":
        element(root, "rect", x=x+10, y=y+11, width=width, height=height, rx=30, fill="#b5c3d1", opacity="0.70")
        element(root, "rect", x=x-8, y=y-8, width=width, height=height, rx=30, fill="#ffffff", opacity="0.85")
        element(root, "rect", x=x, y=y, width=width, height=height, rx=30, fill=style["surface"])
    elif treatment == "isometric":
        element(root, "polygon", points=f"{x},{y+18} {x+25},{y} {x+width+25},{y} {x+width},{y+18}",
                fill=style["accent2"], stroke=style["line"], stroke_width=2)
        element(root, "polygon", points=f"{x+width},{y+18} {x+width+25},{y} {x+width+25},{y+height-18} {x+width},{y+height}",
                fill=style["line"])
        element(root, "rect", x=x, y=y+18, width=width, height=height-18, fill=style["surface"],
                stroke=style["line"], stroke_width=2)
    elif treatment == "brutalist":
        element(root, "rect", x=x+13, y=y+13, width=width, height=height, fill=style["ink"])
        element(root, "rect", x=x, y=y, width=width, height=height,
                fill=style["accent2"] if accent else style["surface"], stroke=style["ink"], stroke_width=5)
    elif treatment == "swiss":
        element(root, "rect", x=x, y=y, width=width, height=height,
                fill=style["surface"], stroke=style["ink"], stroke_width=2)
        element(root, "rect", x=x, y=y, width=15, height=height, fill=style["accent"])
    elif treatment == "editorial":
        element(root, "rect", x=x, y=y, width=width, height=height,
                fill=style["surface"], stroke=style["line"], stroke_width=1)
        element(root, "line", x1=x+22, y1=y+22, x2=x+width-22, y2=y+22,
                stroke=style["accent"], stroke_width=2)
    elif treatment == "handdrawn":
        element(root, "path", d=f"M {x+8} {y} Q {x+width/2} {y-9} {x+width} {y+7} L {x+width+3} {y+height-4} Q {x+width/2} {y+height+8} {x-4} {y+height} Z",
                fill=style["surface"], stroke=style["line"], stroke_width=3)
        element(root, "path", d=f"M {x+13} {y+8} Q {x+width/2} {y+2} {x+width-7} {y+12}",
                fill="none", stroke=style["accent"], stroke_width=2)
    elif treatment == "glow":
        element(root, "rect", x=x-6, y=y-6, width=width+12, height=height+12, rx=24,
                fill=style["accent"], opacity="0.10")
        element(root, "rect", x=x, y=y, width=width, height=height, rx=19,
                fill=style["surface"], stroke=style["accent"], stroke_width=2)
    else:
        raise ValueError(f"Unknown visual treatment: {treatment}")


def diagram(root, card, style, region):
    x0, y0, w, h = region
    nodes = card["nodes"]
    columns = min(3, max(1, math.ceil(math.sqrt(len(nodes)))))
    rows = math.ceil(len(nodes) / columns)
    positions, sizes = {}, {}
    node_w = min(320, (w - 40) / columns - 25)
    node_h = min(205, h / rows - 32)
    for index, node in enumerate(nodes):
        col, row = index % columns, index // columns
        cx = x0 + (col + 0.5) * w / columns if "x" not in node else x0 + float(node["x"]) * w
        cy = y0 + (row + 0.5) * h / rows if "y" not in node else y0 + float(node["y"]) * h
        positions[node["id"]] = (cx, cy)
        sizes[node["id"]] = (node_w, node_h)
    if style["treatment"] == "bento" and len(nodes) == 3 and not any("x" in node or "y" in node for node in nodes):
        # A Bento arrangement groups the same three facts into one large and two small tiles.
        slots = [(0.255, 0.50, 0.44, 0.78), (0.755, 0.29, 0.43, 0.35), (0.755, 0.71, 0.43, 0.35)]
        for node, (px, py, pw, ph) in zip(nodes, slots):
            positions[node["id"]] = (x0 + px*w, y0 + py*h)
            sizes[node["id"]] = (pw*w, ph*h)
    for edge in card.get("edges", []):
        ax, ay = positions[edge["from"]]
        bx, by = positions[edge["to"]]
        dx, dy = bx - ax, by - ay
        distance = max(1, math.hypot(dx, dy))
        source_w, source_h = sizes[edge["from"]]
        target_w, target_h = sizes[edge["to"]]
        vx, vy = dx / distance, dy / distance
        # Meet the actual card boundary so directional arrowheads stay visible.
        source_trim = min(source_w / (2*abs(vx)) if abs(vx) > 1e-6 else float("inf"),
                          source_h / (2*abs(vy)) if abs(vy) > 1e-6 else float("inf")) + 5
        target_trim = min(target_w / (2*abs(vx)) if abs(vx) > 1e-6 else float("inf"),
                          target_h / (2*abs(vy)) if abs(vy) > 1e-6 else float("inf")) + 5
        sx, sy = ax + dx / distance * source_trim, ay + dy / distance * source_trim
        ex, ey = bx - dx / distance * target_trim, by - dy / distance * target_trim
        if style["treatment"] == "glow":
            element(root, "line", x1=sx, y1=sy, x2=ex, y2=ey, stroke=style["accent"], stroke_width=12, opacity="0.13")
        element(root, "line", x1=sx, y1=sy, x2=ex, y2=ey, stroke=style["accent"],
                stroke_width=5 if style["treatment"] == "brutalist" else 3,
                stroke_dasharray="9 7" if style["treatment"] == "handdrawn" else "none")
        arrow = [(ex, ey), (ex - 15*vx - 7*vy, ey - 15*vy + 7*vx),
                 (ex - 15*vx + 7*vy, ey - 15*vy - 7*vx)]
        element(root, "polygon", points=" ".join(f"{x},{y}" for x, y in arrow), fill=style["accent"])
        txt(root, edge["label"], (sx + ex) / 2 + 16*vy, (sy + ey) / 2 - 16*vx, 18, style["muted"],
            font=style["font"], anchor="middle")
    for index, node in enumerate(nodes):
        cx, cy = positions[node["id"]]
        this_w, this_h = sizes[node["id"]]
        x, y = cx - this_w / 2, cy - this_h / 2
        panel(root, style, x, y, this_w, this_h, accent=index % 2 == 0)
        symbol = node.get("symbol")
        if symbol:
            if symbol not in {"terminal", "service", "queue", "process", "database", "cloud"}:
                raise ValueError(f"Unknown node symbol: {symbol}")
            icon_y = cy - 35
            if symbol == "database":
                element(root, "rect", x=cx-22, y=icon_y-10, width=44, height=25, fill=style["accent2"], stroke=style["accent"], stroke_width=2)
                element(root, "ellipse", cx=cx, cy=icon_y-10, rx=22, ry=7, fill=style["surface"], stroke=style["accent"], stroke_width=2)
                element(root, "ellipse", cx=cx, cy=icon_y+15, rx=22, ry=7, fill=style["accent2"], stroke=style["accent"], stroke_width=2)
            elif symbol == "queue":
                for offset in (-13, 0, 13):
                    element(root, "rect", x=cx-23, y=icon_y+offset-4, width=46, height=8, rx=3, fill=style["accent"])
            elif symbol == "terminal":
                element(root, "rect", x=cx-26, y=icon_y-17, width=52, height=32, rx=3, fill="none", stroke=style["accent"], stroke_width=3)
                element(root, "line", x1=cx-14, y1=icon_y+22, x2=cx+14, y2=icon_y+22, stroke=style["accent"], stroke_width=3)
            elif symbol == "cloud":
                element(root, "ellipse", cx=cx, cy=icon_y, rx=28, ry=16, fill=style["accent2"], stroke=style["accent"], stroke_width=2)
            elif symbol == "process":
                element(root, "circle", cx=cx, cy=icon_y, r=20, fill=style["accent2"], stroke=style["accent"], stroke_width=3)
                element(root, "circle", cx=cx, cy=icon_y, r=7, fill=style["accent"])
            else:
                element(root, "polygon", points=f"{cx-23},{icon_y} {cx-12},{icon_y-18} {cx+12},{icon_y-18} {cx+23},{icon_y} {cx+12},{icon_y+18} {cx-12},{icon_y+18}", fill=style["accent2"], stroke=style["accent"], stroke_width=2)
        label_lines = lines(node["label"], max(10, int(this_w / 17)))
        if len(label_lines) > 3:
            raise ValueError(f"Node label too long for mobile frame: {node['id']}")
        for index, line in enumerate(label_lines):
            label_y = cy + (14 if symbol else -(len(label_lines)-1)*16 + 8)
            txt(root, line, cx, label_y + index*30, 26, style["ink"], "bold", style["font"], "middle")


def chart(root, card, style, region):
    x0, y0, w, h = region
    data = card["data"]
    maximum = max(item["value"] for item in data) or 1
    bar_h = min(70, h / len(data) * 0.55)
    for index, item in enumerate(data):
        y = y0 + (index + 0.5) * h / len(data)
        txt(root, item["label"], x0, y - 12, 25, style["ink"], "bold", style["font"])
        element(root, "rect", x=x0, y=y, width=w, height=bar_h, rx=7, fill=style["accent2"])
        element(root, "rect", x=x0, y=y, width=max(2, w * item["value"] / maximum), height=bar_h, rx=7, fill=style["accent"])
        txt(root, f"{item['value']:g} {card['unit']}", x0 + w, y - 12, 23, style["muted"], font=style["font"], anchor="end")
    element(root, "line", x1=x0, y1=y0 + h + 12, x2=x0 + w, y2=y0 + h + 12,
            stroke=style["line"], stroke_width=2)


def comparison(root, card, style, region):
    x0, y0, w, h = region
    gap = 25
    cw = (w - gap) / 2
    # Keep short comparisons visually centered while allowing longer lists to grow.
    needed = 180 + max(len(side.get("points", [])) for side in card["comparison"]) * 85
    panel_h = min(h, max(480, needed))
    panel_y = y0 + (h - panel_h) / 2
    for index, side in enumerate(card["comparison"]):
        x = x0 + index * (cw + gap)
        panel(root, style, x, panel_y, cw, panel_h, accent=index == 0)
        element(root, "rect", x=x, y=panel_y, width=cw, height=13, fill=style["accent"] if index == 0 else style["muted"])
        wrapped(root, side["label"], x + 28, panel_y + 65, cw - 56, 34, style["ink"], style["font"], "bold", 2)
        for number, point in enumerate(side.get("points", [])[:6]):
            wrapped(root, f"{number+1}. {point}", x + 28, panel_y + 145 + number * 85, cw - 56, 23, style["ink"], style["font"], max_lines=2)


def list_panel(root, card, style, region):
    x0, y0, w, h = region
    points = card.get("steps") or card.get("points") or ([card["body"]] if card.get("body") else [])
    if not points:
        raise ValueError("A non-diagram card needs steps, points, comparison, data or body")
    if len(points) > 7:
        raise ValueError("Too many points for one mobile frame; use a carousel")
    if card.get("body") and not card.get("steps") and not card.get("points"):
        # A single post thought is a typographic hero, not a numbered list with empty space.
        if style["treatment"] == "minimal":
            element(root, "rect", x=x0+12, y=y0+h*0.24, width=8, height=h*0.42, fill=style["accent"])
            text_x, text_w = x0+62, w-110
        else:
            panel(root, style, x0+18, y0+h*0.13, w-36, h*0.70, accent=True)
            text_x, text_w = x0+70, w-140
        wrapped(root, card["body"], text_x, y0+h*0.43, text_w, 58,
                style["ink"], style["font"], "bold", 4)
        return
    if style["treatment"] == "bento" and len(points) == 3:
        gap = 24
        slots = [(x0+15, y0+25, w-30, h*0.40),
                 (x0+15, y0+h*0.46, (w-54)/2, h*0.40),
                 (x0+39+(w-54)/2, y0+h*0.46, (w-54)/2, h*0.40)]
        for index, (point, (x, y, tw, th)) in enumerate(zip(points, slots)):
            value = point if isinstance(point, str) else point.get("text") or point.get("heading")
            if not str(value or "").strip():
                raise ValueError("Every point needs text")
            panel(root, style, x, y, tw, th, accent=index != 1)
            txt(root, f"0{index+1}", x+35, y+95, 32, style["accent"], "bold", style["font"])
            wrapped(root, value, x+35, y+th*0.62, tw-70, 40 if index == 0 else 32,
                    style["ink"], style["font"], "bold", 3)
        return
    item_h = h / len(points)
    for index, point in enumerate(points):
        value = point if isinstance(point, str) else point.get("text") or point.get("heading")
        if not str(value or "").strip():
            raise ValueError("Every point needs text")
        y = y0 + index * item_h
        panel(root, style, x0+12, y+10, w-24, item_h-25, accent=index % 2 == 0)
        element(root, "circle", cx=x0 + 70, cy=y + item_h/2, r=27, fill=style["accent"])
        txt(root, str(index + 1), x0 + 70, y + item_h/2 + 10, 27,
            style["background"], "bold", style["font"], "middle")
        text_size = min(37, max(22, item_h*0.20))
        max_lines = min(3, max(1, int((item_h-42)/(text_size*1.25))))
        wrapped(root, value, x0 + 125, y + item_h/2 + 12, w - 165, text_size,
                style["ink"], style["font"], "bold", max_lines)


def svg_card(card, style, width, height, margin, slide_number=None):
    validate_content(card)
    root = ET.Element(f"{{{SVG}}}svg", {"width": str(width), "height": str(height),
                                       "viewBox": f"0 0 {width} {height}", "role": "img",
                                       "aria-label": card.get("altText", card["title"])})
    backdrop(root, style, width, height, margin)
    title_bottom = wrapped(root, card["title"], margin, margin + 105, width - 2 * margin,
                           58 if height > 1100 else 49, style["ink"], style["font"], "bold", 3)
    if card.get("subtitle"):
        title_bottom = wrapped(root, card["subtitle"], margin, title_bottom + 18, width - 2 * margin,
                               27, style["muted"], style["font"], max_lines=2)
    footer_y = height - margin - 35
    region = (margin, title_bottom + 40, width - 2 * margin, footer_y - title_bottom - 75)
    if region[3] < 250:
        raise ValueError("Title leaves insufficient visual space")
    if card.get("nodes"):
        diagram(root, card, style, region)
    elif card.get("data"):
        chart(root, card, style, region)
    elif card.get("comparison"):
        comparison(root, card, style, region)
    else:
        list_panel(root, card, style, region)
    element(root, "line", x1=margin, y1=footer_y, x2=width-margin, y2=footer_y,
            stroke=style["line"], stroke_width=2)
    if card.get("sourceNote"):
        source_label = "SOURCE" if card.get("sourceUrl") else "NOTE"
        wrapped(root, f"{source_label}  {card['sourceNote']}", margin, footer_y + 32, width - 2*margin - 100,
                17, style["muted"], style["font"], max_lines=1)
    if slide_number:
        txt(root, f"{slide_number:02d}", width-margin, footer_y + 32, 22, style["accent"], "bold", style["font"], "end")
    return ET.tostring(root, encoding="unicode")


def render(input_path: Path, output: Path, style_id: str, theme_path: Path | None = None,
           width=1080, height=1350, margin=81):
    """Render one reviewed card without requiring a social presets plan."""
    card = read(input_path)
    validate_content(card)
    if any(claim.get("type") == "fact" and not claim.get("sourceUrl") for claim in card.get("claims", [])):
        raise ValueError("Resolve factual sources before rendering")
    if any(asset.get("rights") not in {"owned", "licensed", "permission", "original"}
           for asset in card.get("assets", [])):
        raise ValueError("Resolve asset rights before rendering")
    if not 480 <= width <= 4096 or not 480 <= height <= 4096 or not 40 <= margin < min(width, height)//4:
        raise ValueError("Invalid canvas or safe margin")
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError("Install content-studio-image/requirements.txt for PNG rendering") from exc
    style = style_for(style_id, read(theme_path) if theme_path else None)
    output.mkdir(parents=True, exist_ok=True)
    svg = output / "image.svg"
    png = output / "image.png"
    svg.write_text(svg_card(card, style, width, height, margin), encoding="utf-8")
    # Render these exact SVG bytes so the editable source matches the reviewed raster.
    cairosvg.svg2png(bytestring=svg.read_bytes(), write_to=str(png), output_width=width, output_height=height)
    manifest = {"schemaVersion": 1, "inputSha256": digest(input_path), "style": style_id,
                "width": width, "height": height, "requiresHumanReview": True,
                "files": [{"path": file.name, "sha256": digest(file), "bytes": file.stat().st_size}
                          for file in (svg, png)]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "review.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Image review</title>'
        '<style>body{font:18px Arial;background:#e9e9e9;padding:24px}img{max-width:100%;width:540px}</style>'
        f'<h1>{html.escape(card["title"])}</h1><p>Inspect at mobile size before use.</p><img src="image.png">',
        encoding="utf-8")
    return manifest


def sample_theme(reference: Path, output: Path):
    from PIL import Image
    # Palette extraction is a starting point; typography and semantic color use still need human review.
    with Image.open(reference) as source:
        image = source.convert("RGB").resize((160, 160))
        colors = sorted(image.getcolors(160 * 160) or [], reverse=True)
    if len(colors) < 2:
        raise ValueError("Reference needs at least two colors")
    background = colors[0][1]
    accent = next((rgb for _, rgb in colors[1:] if sum(abs(rgb[i] - background[i]) for i in range(3)) > 180), colors[1][1])
    value = {"background": "#%02x%02x%02x" % background, "accent": "#%02x%02x%02x" % accent}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render_cmd = sub.add_parser("render")
    render_cmd.add_argument("--input", type=Path, required=True)
    render_cmd.add_argument("--style", required=True)
    render_cmd.add_argument("--output", type=Path, required=True)
    render_cmd.add_argument("--theme", type=Path)
    render_cmd.add_argument("--width", type=int, default=1080)
    render_cmd.add_argument("--height", type=int, default=1350)
    render_cmd.add_argument("--margin", type=int, default=81)
    sample = sub.add_parser("sample-theme")
    sample.add_argument("--reference", type=Path, required=True)
    sample.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.input, args.output, args.style, args.theme, args.width, args.height, args.margin) if args.command == "render" else sample_theme(args.reference, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
