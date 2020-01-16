def render(request, fhtml: str, context: dict) -> str:
    with open(fhtml) as fp:
        html_text = fp.read()
    text_rendered = html_text.format(**context)
    return text_rendered
