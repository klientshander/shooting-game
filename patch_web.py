"""Patch Pygbag web build for proper 16:9 landscape aspect ratio, black letterboxing, and sci-fi theme."""

from pathlib import Path


def patch_web_index(index_path: str = "build/web/index.html") -> bool:
    target = Path(index_path)
    if not target.exists():
        print(f"Warning: {target} not found. Skipping patch.")
        return False

    content = target.read_text(encoding="utf-8")

    # 1. Orientation metadata
    if '<meta name="orientation" content="landscape">' not in content:
        content = content.replace(
            "<head>",
            '<head>\n    <meta name="screen-orientation" content="landscape">\n    <meta name="orientation" content="landscape">\n    <meta name="theme-color" content="#000000">',
            1,
        )

    # 2. Set default canvas dimensions to 1280x720 so Pygbag's aspect ratio calculation (canvas.width / canvas.height) is 16:9 immediately
    content = content.replace(
        '<canvas class="emscripten" id="canvas"\nwidth="1px"\nheight="1px"',
        '<canvas class="emscripten" id="canvas"\nwidth="1280px"\nheight="720px"',
    )

    # 3. Set gui_divider to 1 so the canvas doesn't start at half-width
    content = content.replace("gui_divider : 2,", "gui_divider : 1,")

    # 4. Remove width: 100%; height: 100% from canvas.emscripten so Pygbag's window_canvas_adjust sets the correct aspect ratio
    old_canvas_css = """        canvas.emscripten {
            border: 0px none;
            background-color: transparent;
            width: 100%;
            height: 100%;
            z-index: 5;

            padding: 0;
            margin: 0 auto;

            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
        }"""

    new_canvas_css = """        canvas.emscripten {
            border: 0px none;
            background-color: #000000;
            z-index: 5;
            padding: 0;
            margin: auto;
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
        }"""

    if old_canvas_css in content:
        content = content.replace(old_canvas_css, new_canvas_css)
    else:
        # Fallback if whitespace varies
        content = content.replace("background-color: transparent;", "background-color: #000000;")
        content = content.replace("margin: 0 auto;", "margin: auto;")
        content = content.replace("width: 100%;\n            height: 100%;\n", "")

    # 5. Cosmic dark body background
    content = content.replace("background-color:powderblue;", "background-color: #000000; color: #d8dee9;")
    content = content.replace('"#7f7f7f"', '"#000000"')

    # 6. High-contrast sci-fi loading and prompt elements
    old_infobox_css = """        #infobox {
            position: fixed; /* center relative to viewport */
            background: green;
            color: blue;
            font-weight: bold;
            padding: 12px 24px;
 /*           display: none; */
            z-index: 999999;
        }"""

    new_infobox_css = """        #infobox {
            position: fixed;
            background: #101828;
            color: #00e5ff;
            border: 2px solid #00e5ff;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            padding: 14px 28px;
            box-shadow: 0 0 24px rgba(0, 229, 255, 0.45);
            cursor: pointer;
            z-index: 999999;
        }"""

    if old_infobox_css in content:
        content = content.replace(old_infobox_css, new_infobox_css)

    content = content.replace("color: rgb(120, 120, 120);", "color: #00d2ff;")

    target.write_text(content, encoding="utf-8")
    print(f"Successfully patched {target} for 16:9 landscape aspect ratio and cosmic styling.")
    return True


if __name__ == "__main__":
    patch_web_index()
