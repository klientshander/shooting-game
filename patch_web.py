"""Patch Pygbag web build to enforce 16:9 landscape aspect ratio, black letterboxing, and orientation locks."""

import re
from pathlib import Path


def patch_web_index(index_path: str = "build/web/index.html") -> bool:
    target = Path(index_path)
    if not target.exists():
        print(f"Warning: {target} not found. Skipping patch.")
        return False

    content = target.read_text(encoding="utf-8")

    # 1. Ensure landscape meta tags
    meta_tags = (
        '    <meta name="screen-orientation" content="landscape">\n'
        '    <meta name="orientation" content="landscape">\n'
        '    <meta name="theme-color" content="#000000">\n'
    )
    if '<meta name="orientation" content="landscape">' not in content:
        content = content.replace("<head>", f"<head>\n{meta_tags}", 1)

    # 2. Update CSS for canvas.emscripten to strictly enforce 16:9 landscape
    custom_css = """
        /* Enforce fixed 16:9 landscape aspect ratio with centered black letterboxing */
        canvas.emscripten {
            border: 0px none !important;
            background-color: #000000 !important;
            aspect-ratio: 16 / 9 !important;
            width: 100vw !important;
            height: 56.25vw !important;
            max-width: 177.78vh !important;
            max-height: 100vh !important;
            object-fit: contain !important;
            z-index: 5 !important;
            padding: 0 !important;
            margin: auto !important;
            position: absolute !important;
            top: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
        }

        body {
            font-family: arial;
            margin: 0;
            padding: 0;
            background-color: #000000 !important;
            overflow: hidden !important;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100vw;
            height: 100vh;
        }
    """

    # Replace existing canvas.emscripten and body CSS
    content = re.sub(
        r"canvas\.emscripten\s*\{[^}]*\}",
        "",
        content,
    )
    content = re.sub(
        r"body\s*\{[^}]*\}",
        "",
        content,
    )

    # Inject optimized CSS before </style>
    if "</style>" in content:
        content = content.replace("</style>", f"{custom_css}\n    </style>", 1)
    elif "</head>" in content:
        content = content.replace("</head>", f"<style>{custom_css}</style>\n</head>", 1)

    # 3. Ensure background color in custom_site JS is black (#000000) instead of grey (#7f7f7f)
    content = content.replace('"#7f7f7f"', '"#000000"')

    target.write_text(content, encoding="utf-8")
    print(f"Successfully patched {target} for 16:9 landscape aspect ratio.")
    return True


if __name__ == "__main__":
    patch_web_index()
