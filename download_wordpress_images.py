#!/usr/bin/env python3
"""
Download all images referenced in a WordPress WXR export XML and save them
under wordpress-uploads/ preserving the path structure.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# WordPress WXR namespaces
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

# Base URL to normalize and filter
SITE_BASE = "newvintageamps.com"
OUTPUT_DIR = "wordpress-uploads"


def extract_urls_from_xml(xml_path):
    """Extract all image URLs from WordPress XML (attachments + inline in content)."""
    urls = set()
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root[0]

    for item in channel.findall("item"):
        # 1) Attachment URL (canonical image)
        att_url = item.find("wp:attachment_url", NS)
        if att_url is not None and att_url.text:
            url = att_url.text.strip()
            if SITE_BASE in url and _is_image_url(url):
                urls.add(_normalize_url(url))

        # 2) Content body may contain img src and href to images
        content = item.find("content:encoded", NS)
        if content is not None and content.text:
            text = content.text
            # img src="..." or src='...'
            for m in re.finditer(r'src=["\']([^"\']+)["\']', text):
                u = m.group(1).strip()
                if SITE_BASE in u and _is_image_url(u):
                    urls.add(_normalize_url(u))
            for m in re.finditer(r'href=["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp|svg))["\']', text, re.I):
                u = m.group(1).strip()
                if SITE_BASE in u:
                    urls.add(_normalize_url(u))

    return sorted(urls)


def _is_image_url(url):
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"))


def _normalize_url(url):
    """Use https and strip fragment so duplicate URLs merge."""
    u = url.strip()
    if u.startswith("http://"):
        u = "https://" + u[7:]
    u = u.split("#")[0].split("?")[0]
    return u


def url_to_local_path(url, base_dir):
    """Convert image URL to local path under base_dir, preserving structure."""
    parsed = urlparse(url)
    path = parsed.path
    # Strip leading slash and any wp-content/uploads/ prefix so we get year/month/file
    path = path.lstrip("/")
    if "wp-content/uploads/" in path:
        path = path.split("wp-content/uploads/", 1)[-1]
    elif "uploads/" in path:
        path = path.split("uploads/", 1)[-1]
    # Sanitize: only allow path segments
    path = path.replace("..", "").strip("/")
    if not path:
        # Fallback: use last part of URL
        path = os.path.basename(parsed.path) or "image"
    return os.path.join(base_dir, path)


def download_image(url, local_path, skip_existing=True):
    """Download url to local_path. Returns True on success."""
    if skip_existing and os.path.isfile(local_path):
        return True
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; NVA-Image-Downloader/1.0)"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except (URLError, HTTPError, OSError) as e:
        print(f"  FAIL: {url} -> {e}")
        return False
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(data)
    return True


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(script_dir, "newvintageamplifiers.WordPress.2026-03-13.xml")
    if not os.path.isfile(xml_path):
        print(f"XML not found: {xml_path}")
        sys.exit(1)

    print("Extracting image URLs from WordPress XML...")
    urls = extract_urls_from_xml(xml_path)
    print(f"Found {len(urls)} unique image URL(s).")

    base_dir = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(base_dir, exist_ok=True)
    ok = 0
    for i, url in enumerate(urls, 1):
        local = url_to_local_path(url, base_dir)
        skipped = os.path.isfile(local)
        if skipped:
            print(f"[{i}/{len(urls)}] (exists) {os.path.basename(local)}")
        else:
            print(f"[{i}/{len(urls)}] {os.path.basename(local)}")
        if download_image(url, local):
            ok += 1
    print(f"Done. Downloaded {ok}/{len(urls)} images to {base_dir}/")


if __name__ == "__main__":
    main()
