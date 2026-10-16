#!/usr/bin/env python3
"""Download EPGShare01 guides and rewrite their channel IDs to match the IPTV provider.

Usage: python3 build_guide.py mapping.json OUT_DIR

Writes OUT_DIR/guide.xml.gz containing only mapped channels, each under the
provider's channel ID (one EPGShare channel can feed several provider IDs).
"""
import copy
import gzip
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://epgshare01.online/epgshare01/"
SOURCES = ["epg_ripper_UK1.xml.gz", "epg_ripper_US2.xml.gz",
           "epg_ripper_US_LOCALS1.xml.gz", "epg_ripper_FANDUEL1.xml.gz",
           "epg_ripper_PEACOCK1.xml.gz"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
MIN_PROGRAMMES = 20000  # refuse to publish a suspiciously empty guide


def fetch(name, tmp):
    path = os.path.join(tmp, name)
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as f:
        shutil.copyfileobj(r, f)
    return path


def main():
    mapping_path, out_dir = sys.argv[1], sys.argv[2]
    mapping = json.load(open(mapping_path))
    targets = {}
    for provider_id, source_id in mapping.items():
        targets.setdefault(source_id, []).append(provider_id)
    # names.json: provider channels with no EPG ID, matched by exact channel name.
    names_path = os.path.join(os.path.dirname(os.path.abspath(mapping_path)), "names.json")
    by_name = json.load(open(names_path)) if os.path.exists(names_path) else {}
    named = set(by_name)
    for provider_name, source_id in by_name.items():
        targets.setdefault(source_id, []).append(provider_name)

    channels, programmes, failed = [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        for name in SOURCES:
            try:
                path = fetch(name, tmp)
                opener = gzip.open if open(path, "rb").read(2) == b"\x1f\x8b" else open
                with opener(path, "rb") as fh:
                    for _, el in ET.iterparse(fh, events=("end",)):
                        if el.tag == "channel":
                            for pid in targets.get(el.get("id"), ()):
                                c = copy.deepcopy(el)
                                c.set("id", pid)
                                if pid in named:
                                    for dn in c.findall("display-name"):
                                        c.remove(dn)
                                    ET.SubElement(c, "display-name").text = pid
                                channels.append(c)
                            el.clear()
                        elif el.tag == "programme":
                            for pid in targets.get(el.get("channel"), ()):
                                p = copy.deepcopy(el)
                                p.set("channel", pid)
                                programmes.append(p)
                            el.clear()
                print(f"{name}: ok")
            except Exception as e:  # one broken source shouldn't sink the rest
                failed.append(name)
                print(f"{name}: FAILED {type(e).__name__}: {e}")

    if len(programmes) < MIN_PROGRAMMES:
        sys.exit(f"only {len(programmes)} programmes - sources look broken, not publishing")

    root = ET.Element("tv", {"generator-info-name": "epg-remap"})
    root.extend(channels)
    root.extend(programmes)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "guide.xml.gz")
    with gzip.open(out, "wb") as f:
        ET.ElementTree(root).write(f, encoding="UTF-8", xml_declaration=True)
    print(f"channels: {len(channels)}  programmes: {len(programmes)}  "
          f"size: {os.path.getsize(out)/1e6:.1f} MB  failed sources: {failed or 'none'}")


if __name__ == "__main__":
    main()
