#!/usr/bin/env python3
"""Render actual STL triangles to a standalone multi-view SVG. No Fusion or packages."""
from array import array
import argparse
import base64
import hashlib
import html
import json
import math
from pathlib import Path
import runpy
import struct
import sys
from types import SimpleNamespace
import zlib

mesh = SimpleNamespace(**runpy.run_path(str(Path(__file__).with_name("meshcheck.py"))))
VERSION = "1.0.0"
VIEWS = {"front": ((0, -1, 0), (0, 0, 1)), "right": ((1, 0, 0), (0, 0, 1)),
         "top": ((0, 0, 1), (0, 1, 0)), "iso": ((3, -4, 2), (0, 0, 1))}


def dot(a, b): return sum(x*y for x, y in zip(a, b))


def unit(v):
    size = math.sqrt(dot(v, v))
    return tuple(x/size for x in v)


def png_bytes(pixels, size):
    def chunk(kind, data):
        return struct.pack(">I", len(data))+kind+data+struct.pack(">I", zlib.crc32(kind+data) & 0xffffffff)
    scan = b"".join(b"\0"+pixels[y*size*3:(y+1)*size*3] for y in range(size))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scan, 6)) + chunk(b"IEND", b""))


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""): digest.update(block)
    return digest.hexdigest()


def bounds_of(path, scale):
    lo, hi, count = [math.inf]*3, [-math.inf]*3, 0
    for tri in mesh.triangles(path):
        if not all(math.isfinite(v*scale) for v in tri): raise ValueError("Non-finite STL coordinate")
        for i, value in enumerate(tri):
            value *= scale
            lo[i % 3], hi[i % 3] = min(lo[i % 3], value), max(hi[i % 3], value)
        count += 1
    if not count or max(hi[i]-lo[i] for i in range(3)) <= 0:
        raise ValueError("No nonzero-size STL geometry")
    return lo, hi, count


def render(path, view, lo, hi, *, size=320, scale=1.):
    eye, suggested_up = VIEWS[view]
    eye = unit(eye); right = unit(mesh.cross(suggested_up, eye)); up = mesh.cross(eye, right)
    center = tuple((lo[i]+hi[i])/2 for i in range(3))
    corners = [(x-center[0], y-center[1], z-center[2]) for x in (lo[0], hi[0])
               for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    umin, umax = min(dot(c, right) for c in corners), max(dot(c, right) for c in corners)
    vmin, vmax = min(dot(c, up) for c in corners), max(dot(c, up) for c in corners)
    factor = (size-32)/max(umax-umin, vmax-vmin, 1e-12)
    ucenter, vcenter = (umin+umax)/2, (vmin+vmax)/2
    image = bytearray((246, 248, 251)) * (size*size)
    depth = array("d", [-math.inf]) * (size*size)
    light = unit((-.3, -.5, .8))
    rendered = 0
    for tri in mesh.triangles(path):
        pts = [tuple(tri[k+i]*scale-center[i] for i in range(3)) for k in (0, 3, 6)]
        projected = [(size/2+(dot(p, right)-ucenter)*factor,
                      size/2-(dot(p, up)-vcenter)*factor, dot(p, eye)) for p in pts]
        a, b, c = projected
        area = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if abs(area) <= 1e-12: continue
        if area < 0: b, c = c, b; area = -area
        xmin, xmax = max(0, math.floor(min(a[0], b[0], c[0]))), min(size-1, math.ceil(max(a[0], b[0], c[0])))
        ymin, ymax = max(0, math.floor(min(a[1], b[1], c[1]))), min(size-1, math.ceil(max(a[1], b[1], c[1])))
        normal = mesh.cross(tuple(pts[1][i]-pts[0][i] for i in range(3)), tuple(pts[2][i]-pts[0][i] for i in range(3)))
        if dot(normal, normal) <= 1e-24: continue
        normal = unit(normal)
        # Two-sided display lets a broken/inverted STL remain inspectable.
        if dot(normal, eye) < 0: normal = tuple(-v for v in normal)
        brightness = .35+.65*max(0., dot(normal, light))
        color = bytes(round(v*brightness) for v in (105, 169, 215))
        for y in range(ymin, ymax+1):
            yy = y+.5
            for x in range(xmin, xmax+1):
                xx = x+.5
                wa = ((c[0]-b[0])*(yy-b[1])-(c[1]-b[1])*(xx-b[0]))/area
                wb = ((a[0]-c[0])*(yy-c[1])-(a[1]-c[1])*(xx-c[0]))/area
                wc = 1-wa-wb
                if min(wa, wb, wc) < -1e-9: continue
                z = wa*a[2]+wb*b[2]+wc*c[2]
                index = y*size+x
                if z > depth[index]:
                    depth[index] = z
                    image[index*3:index*3+3] = color
        rendered += 1
    return png_bytes(image, size), rendered


def preview(source, output, *, views=("front", "right", "top", "iso"), size=320, scale=1.):
    source, output = Path(source), Path(output)
    if output.suffix.lower() != ".svg" or output.resolve() == source.resolve():
        raise ValueError("Output must be a distinct .svg file")
    if not 64 <= size <= 1024 or not math.isfinite(scale) or scale <= 0:
        raise ValueError("Panel size must be 64..1024 pixels and scale positive/finite")
    if not views or len(views) > 4 or len(set(views)) != len(views) or any(v not in VIEWS for v in views):
        raise ValueError("Choose up to four distinct views: front right top iso")
    digest = file_hash(source)
    lo, hi, count = bounds_of(source, scale)
    dimensions = [hi[i]-lo[i] for i in range(3)]
    cols = min(2, len(views)); rows = math.ceil(len(views)/cols)
    panel_h, width, height = size+34, cols*size, 98+rows*(size+34)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<title>{html.escape(source.name)} — actual STL triangles</title>',
           f'<text x="12" y="23" font-family="sans-serif" font-size="16">{html.escape(source.name[:max(8, width//9)])}</text>',
           f'<text x="12" y="45" font-family="sans-serif" font-size="12">'+
           ' × '.join(f'{v:.3f}' for v in dimensions)+' mm</text>',
           f'<text x="12" y="63" font-family="sans-serif" font-size="11">{count:,} triangles · actual STL geometry</text>']
    for index, view in enumerate(views):
        pixels, _ = render(source, view, lo, hi, size=size, scale=scale)
        data = base64.b64encode(pixels).decode("ascii")
        x, y = (index % cols)*size, 74+(index//cols)*panel_h
        svg += [f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="data:image/png;base64,{data}"/>',
                f'<text x="{x+12}" y="{y+size+22}" font-family="sans-serif" font-size="14">{view.upper()}</text>']
    svg += [f'<text x="12" y="{height-8}" font-family="sans-serif" font-size="10">Preview only; verify topology and clearances.</text>', '</svg>']
    if file_hash(source) != digest: raise RuntimeError("Source changed during preview; result was not saved")
    output.write_text("\n".join(svg), encoding="utf-8")
    return {"tool": "stl_preview", "version": VERSION, "status": "pass", "source": str(source),
            "sha256": digest, "output": str(output), "dimensions_mm": dimensions, "triangles": count,
            "views": list(views), "panel_size_px": size, "coordinate_scale_to_mm": scale,
            "limits": "Actual triangles with depth-buffer occlusion; no decimation. Original XYZ orientation is preserved. Uniform diagnostic color, no materials/supports or perspective. Finite pixel resolution can hide small features. Not a topology, clearance, first-layer or mechanical validation."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--views", nargs="+", choices=VIEWS, default=list(VIEWS))
    p.add_argument("--size", type=int, default=320, help="Pixels per square panel, 64..1024")
    p.add_argument("--scale", type=float, default=1., help="Source-coordinate to mm multiplier")
    p.add_argument("--report", type=Path)
    args = p.parse_args(argv)
    try:
        if args.report and args.report.resolve() in {args.source.resolve(), args.output.resolve()}:
            raise ValueError("Report path must differ from source and SVG")
        report = preview(args.source, args.output, views=args.views, size=args.size, scale=args.scale)
        if args.report: args.report.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    except (OSError, ValueError, OverflowError, struct.error, RuntimeError) as exc:
        print(json.dumps({"tool": "stl_preview", "status": "incomplete", "error": str(exc)})); return 2
    print(json.dumps(report)); return 0


if __name__ == "__main__":
    sys.exit(main())
