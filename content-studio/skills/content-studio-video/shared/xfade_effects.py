"""Code-driven two-shot transitions shared by specialist and timeline renderers.

FFmpeg's custom xfade expression sees P descend from 1 (outgoing shot) to 0
(incoming shot). All recipes use both actual clips; none substitutes a point
effect on a continuous master. These are original approximations, not copies
of a third-party motion asset.
"""

from __future__ import annotations


CUSTOM_JOIN_IDS = frozenset({
    "collage", "page-turn", "liquid-streaks", "liquid-drops",
    "fire", "zoom-out", "spin", "heart",
})


def _sample_outgoing(x: str, y: str) -> str:
    """Read the correct Y/U/V plane after custom joins normalize to yuv444p."""
    return (f"if(eq(PLANE,0),a0({x},{y}),"
            f"if(eq(PLANE,1),a1({x},{y}),a2({x},{y})))")


def custom_expression(effect_id: str) -> str:
    """Return a distinct xfade expression with exact outgoing/incoming ends."""
    if effect_id not in CUSTOM_JOIN_IDS:
        raise ValueError(f"No custom transition recipe: {effect_id}")
    progress = "(1-P)"
    if effect_id == "collage":
        # Four panels reveal at staggered times, each with a local sweep.
        panel = "(floor(2*X/W)+2*floor(2*Y/H))"
        local = f"min(1,max(0,({progress}-0.16*{panel})/0.52))"
        body = f"if(lt(mod(X,W/2)/(W/2),{local}),B,A)"
    elif effect_id == "page-turn":
        # A slanted, shaded fold mirrors the outgoing page before exposing B.
        fold = f"(P*W+0.05*W*(Y/H-0.5)*sin(3.14159265*{progress}))"
        width = f"(0.18*W*sin(3.14159265*{progress}))"
        sampled = _sample_outgoing(f"min(W-1,max(0,2*{fold}-X))", "Y")
        body = (f"if(lt(X,{fold}-{width}),A,"
                f"if(lt(X,{fold}),0.7*{sampled}+0.3*B,B))")
    elif effect_id == "liquid-streaks":
        # Two wave frequencies create a moving fluid edge, not a flat wipe.
        edge = (f"({progress}+0.07*sin(20*Y/H+12*{progress})"
                f"+0.035*sin(52*Y/H-7*{progress}))")
        body = f"if(lt(X/W,{edge}),B,A)"
    elif effect_id == "liquid-drops":
        # Three growing, slightly rippled pools reveal the next shot.
        def distance(cx: float, cy: float) -> str:
            return f"sqrt(pow(X/W-{cx},2)+pow(Y/H-{cy},2))"
        nearest = (f"min({distance(.22, .26)},"
                   f"min({distance(.78, .26)},{distance(.5, .72)}))")
        radius = (f"(0.62*pow({progress},1.5)"
                  f"+0.02*sin(40*X/W+27*Y/H+10*{progress}))")
        body = f"if(lt({nearest},{radius}),B,A)"
    elif effect_id == "fire":
        # A warm, irregular rising edge approximates a flame-shaped reveal.
        edge = (f"(P+0.07*sin(17*X/W+11*{progress})"
                f"+0.04*sin(39*X/W-14*{progress}))")
        warm = ("if(eq(PLANE,0),min(235,A+35),"
                "if(eq(PLANE,1),max(16,A-25),min(240,A+55)))")
        body = (f"if(gt(Y/H,{edge}),B,"
                f"if(gt(Y/H,{edge}-0.06),{warm},A))")
    elif effect_id == "zoom-out":
        # The outgoing frame shrinks into the incoming frame; it does not use
        # the built-in zoom-in effect in reverse or a generic dissolve.
        sx = "((X-W/2)/max(P,0.001)+W/2)"
        sy = "((Y-H/2)/max(P,0.001)+H/2)"
        outgoing = _sample_outgoing(sx, sy)
        body = (f"if(between({sx},0,W-1)*between({sy},0,H-1),"
                f"P*{outgoing}+(1-P)*B,B)")
    elif effect_id == "spin":
        # Rotate the outgoing shot by 180 degrees while it recedes.
        angle = f"(3.14159265*{progress})"
        dx, dy = "(X-W/2)", "(Y-H/2)"
        sx = f"(({dx}*cos({angle})+{dy}*sin({angle}))/max(P,0.001)+W/2)"
        sy = f"((0-{dx}*sin({angle})+{dy}*cos({angle}))/max(P,0.001)+H/2)"
        outgoing = _sample_outgoing(sx, sy)
        body = (f"if(between({sx},0,W-1)*between({sy},0,H-1),"
                f"P*{outgoing}+(1-P)*B,B)")
    else:  # heart
        # The classic heart implicit curve grows from the center.
        scale = f"(0.01+3.2*pow({progress},2))"
        x = f"((2*X/W-1)/{scale})"
        y = f"((1-2*Y/H)/{scale})"
        curve = f"(pow({x}*{x}+{y}*{y}-1,3)-{x}*{x}*pow({y},3))"
        body = f"if(lte({curve},0),B,A)"
    # Explicit end guards avoid expression singularities and guarantee clean
    # frame boundaries even when the last sampled P is just above zero.
    return f"if(gte(P,0.999),A,if(lte(P,0.001),B,{body}))"


def xfade_options(effect_id: str, transition: str) -> str:
    """Build the FFmpeg option fragment for native or custom clip joins."""
    if transition != "custom":
        return f"transition={transition}"
    return f"transition=custom:expr='{custom_expression(effect_id)}'"
