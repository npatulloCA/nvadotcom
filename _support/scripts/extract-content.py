#!/usr/bin/env python3
"""
Extract content from WordPress WXR XML for the static site.
Outputs:
  - pages.json: metadata only (id, title, slug, parentId, path)
  - content/: one HTML file per page (path mirrors URL structure)
  - nav.json: nav tree
Excludes shop, cart, checkout, my-account, and customizer pages.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

# Slugs or slug prefixes to exclude (shop, cart, customizer, etc.)
EXCLUDE_SLUGS = {
    "shop", "cart", "checkout", "checkout-2", "my-account",
    "customizer-combo", "customizer-head-cab", "customizer-bass",
    "customizer-menus", "obfuscated-customizer", "customizer-matchless",
    "customizer-mojo", "customizer-nv-212", "customizer-nv-head",
    "mobile-combo-customizer", "mobile-head-cab-customizer", "mobile-bass-amp-customizer",
    "nv-212-bb-customizer", "new-customizer-menu-switching", "customizer-2",
    "fiddle", "31", "32", "28", "30", "33", "34", "104", "115", "116", "145",
    "146", "147", "164", "167", "169", "170",  # nav menu item placeholders with numeric slugs
}


def strip_shortcodes(html: str) -> str:
    """Remove WordPress shortcodes [bd_...], [bd_separator], etc."""
    if not html or not html.strip():
        return ""
    # Remove [shortcode] and [shortcode ...][/shortcode]
    html = re.sub(r"\[bd_[^\]]*\]", "", html)
    html = re.sub(r"\[/bd_[^\]]*\]", "", html)
    html = re.sub(r"\[bd_[^\]]*\][\s\S]*?\[/bd_[^\]]*\]", "", html)
    html = re.sub(r"\[[a-z_]+[^\]]*\]", "", html)
    html = re.sub(r"\[/[a-z_]+\]", "", html)
    return html


def rewrite_image_urls(html: str, base_url: str = "https://newvintageamps.com") -> str:
    """Rewrite wp-content/uploads URLs to /uploads/ for static assets."""
    if not html:
        return ""
    # Match wp-content/uploads/... or base_url + /wp-content/uploads/...
    pattern = re.compile(
        re.escape(base_url) + r"/wp-content/uploads/([^\s\"'<>]+)",
        re.IGNORECASE
    )
    html = pattern.sub(r"/uploads/\1", html)
    # Also handle protocol-relative or other variants
    html = re.sub(
        r"https?://(?:www\.)?newvintageamps\.com/wp-content/uploads/([^\s\"'<>]+)",
        r"/uploads/\1",
        html,
        flags=re.IGNORECASE
    )
    return html


def get_meta(item, key: str) -> str:
    for meta in item.findall("wp:postmeta", NS):
        k = meta.find("wp:meta_key", NS)
        v = meta.find("wp:meta_value", NS)
        if k is not None and v is not None and k.text == key and v.text:
            return v.text.strip()
    return ""


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))  # project root (script lives in _support/scripts/)
    xml_path = os.path.join(repo_root, "_support", "newvintageamplifiers.WordPress.2026-03-13.xml")
    out_dir = os.path.join(repo_root, "_support", "content-data")
    if len(sys.argv) > 1:
        out_dir = sys.argv[1]

    if not os.path.isfile(xml_path):
        print(f"XML not found: {xml_path}")
        sys.exit(1)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root[0]

    # 1) Collect all published pages
    pages_by_id = {}
    for item in channel.findall("item"):
        pt = item.find("wp:post_type", NS)
        st = item.find("wp:status", NS)
        if pt is None or st is None or pt.text != "page" or st.text != "publish":
            continue
        pid_el = item.find("wp:post_id", NS)
        title_el = item.find("title")
        name_el = item.find("wp:post_name", NS)
        parent_el = item.find("wp:post_parent", NS)
        content_el = item.find("content:encoded", NS)
        if pid_el is None or name_el is None:
            continue
        post_id = pid_el.text
        slug = (name_el.text or "").strip()
        if not slug:
            continue
        if slug in EXCLUDE_SLUGS or any(
            slug.startswith(prefix) for prefix in ("customizer", "mobile-")
        ):
            continue
        title = (title_el.text or "").strip() if title_el is not None else ""
        parent = (parent_el.text or "0") if parent_el is not None else "0"
        content = (content_el.text or "").strip() if content_el is not None else ""
        content = strip_shortcodes(content)
        content = rewrite_image_urls(content)
        pages_by_id[post_id] = {
            "id": post_id,
            "title": title or slug,
            "slug": slug,
            "parentId": parent,
            "content": content,
        }

    # 2) Build path for each page (hierarchical)
    def path_for(page_id: str, seen: set) -> str:
        if page_id in seen or page_id not in pages_by_id:
            return ""
        seen.add(page_id)
        p = pages_by_id[page_id]
        parent_id = p["parentId"]
        if parent_id == "0" or parent_id not in pages_by_id:
            return "/" + p["slug"] + "/"
        parent_path = path_for(parent_id, seen)
        return parent_path.rstrip("/") + "/" + p["slug"] + "/"

    for pid, p in pages_by_id.items():
        p["path"] = path_for(pid, set()).replace("//", "/")
        if p["path"] == "/home/":
            p["path"] = "/"

    # 3) Nav menu: NAV items only, include only pages we have
    id_to_page = {p["id"]: p for p in pages_by_id.values()}
    nav_items = []
    for item in channel.findall("item"):
        pt = item.find("wp:post_type", NS)
        cat = item.find(".//category[@domain='nav_menu'][@nicename='nav']")
        if pt is None or pt.text != "nav_menu_item" or cat is None:
            continue
        menu_id = item.find("wp:post_id", NS)
        order_el = item.find("wp:menu_order", NS)
        parent_el = get_meta(item, "_menu_item_menu_item_parent")
        obj_id = get_meta(item, "_menu_item_object_id")
        if not obj_id or obj_id not in id_to_page:
            continue
        page = id_to_page[obj_id]
        order = int(order_el.text) if order_el is not None and order_el.text else 0
        nav_items.append({
            "menuId": menu_id.text if menu_id is not None else "",
            "order": order,
            "parentMenuId": parent_el or "0",
            "pageId": obj_id,
            "title": page["title"],
            "path": page["path"],
        })

    # Build nav tree: top-level by parentMenuId=0, then children
    def nav_children(parent_menu_id: str):
        kids = [n for n in nav_items if n["parentMenuId"] == parent_menu_id]
        kids.sort(key=lambda x: x["order"])
        return [
            {
                "title": n["title"],
                "path": n["path"],
                "children": nav_children(n["menuId"]),
            }
            for n in kids
        ]

    nav_tree = nav_children("0")

    # 4) Output
    os.makedirs(out_dir, exist_ok=True)
    pages_list = list(pages_by_id.values())
    pages_list.sort(key=lambda x: (x["path"],))

    # pages.json: metadata only (no content), for easy reading and navigation
    meta_list = [
        {"id": p["id"], "title": p["title"], "slug": p["slug"], "parentId": p["parentId"], "path": p["path"]}
        for p in pages_list
    ]
    with open(os.path.join(out_dir, "pages.json"), "w", encoding="utf-8") as f:
        json.dump(meta_list, f, indent=2, ensure_ascii=False)

    # content/: one HTML file per page, path mirrors URL structure
    content_dir = os.path.join(out_dir, "content")
    os.makedirs(content_dir, exist_ok=True)
    for p in pages_list:
        path_slug = p["path"].strip("/") or "index"
        rel = path_slug + ".html"
        file_path = os.path.join(content_dir, rel)
        parent = os.path.dirname(file_path)
        if parent != content_dir:
            os.makedirs(parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(p["content"] or "")

    with open(os.path.join(out_dir, "nav.json"), "w", encoding="utf-8") as f:
        json.dump(nav_tree, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(pages_list)} pages (metadata + content files) and nav tree to {out_dir}/")


if __name__ == "__main__":
    main()
