#!/usr/bin/env python3
"""Download EPGShare01 UK and rewrite its channel IDs to match the IPTV provider.

Usage: python3 build_guide.py mapping.json OUT_DIR

Writes OUT_DIR/guide.xml.gz containing only mapped channels, each under the
provider's channel ID (one EPGShare channel can feed several provider IDs).
"""
import copy
import gzip
import io
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

SOURCE = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
MIN_PROGRAMMES = 1000  # refuse to publish a suspiciously empty guide


def main():
    mapping_path, out_dir = sys.argv[1], sys.argv[2]
    mapping = json.load(open(mapping_path))
    targets = {}
    for provider_id, source_id in mapping.items():
        targets.setdefault(source_id, []).append(provider_id)

    req = urllib.request.Request(SOURCE, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=300).read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)

    root = ET.Element("tv", {"generator-info-name": "epg-remap"})
    channels, programmes = [], []
    for _, el in ET.iterparse(io.BytesIO(raw), events=("end",)):
        if el.tag == "channel" and el.get("id") in targets:
            for pid in targets[el.get("id")]:
                c = copy.deepcopy(el)
                c.set("id", pid)
                channels.append(c)
            el.clear()
        elif el.tag == "programme":
            if el.get("channel") in targets:
                for pid in targets[el.get("channel")]:
                    p = copy.deepcopy(el)
                    p.set("channel", pid)
                    programmes.append(p)
            el.clear()

    if len(programmes) < MIN_PROGRAMMES:
        sys.exit(f"only {len(programmes)} programmes - source looks broken, not publishing")

    root.extend(channels)
    root.extend(programmes)
    os.makedirs(out_dir, exist_ok=True)
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, encoding="UTF-8", xml_declaration=True)
    with gzip.open(os.path.join(out_dir, "guide.xml.gz"), "wb") as f:
        f.write(buf.getvalue())
    print(f"channels: {len(channels)}  programmes: {len(programmes)}  "
          f"size: {os.path.getsize(os.path.join(out_dir, 'guide.xml.gz'))/1e6:.1f} MB")


if __name__ == "__main__":
    main()
