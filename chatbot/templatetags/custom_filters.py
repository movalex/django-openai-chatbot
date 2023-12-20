from django import template
from django.utils.html import format_html, mark_safe

register = template.Library()


@register.filter(name="format_output")
def format_output(value):
    # Splitting the text into lines
    lines = value.split("\n")

    # Variables to keep track of whether we are inside a code block
    in_code_block = False
    formatted_lines = []

    for line in lines:
        if line.strip().startswith("```"):  # Check for code block start/end
            in_code_block = not in_code_block
            if in_code_block:
                formatted_lines.append("<p><pre><code>")
            else:
                formatted_lines.append("</code></pre></p>")
        elif in_code_block:
            formatted_lines.append(mark_safe(line + "\n"))  # Keep code line as is
        else:
            formatted_lines.append(f"<p>{line}</p>")
    concatenated = "".join(formatted_lines)
    return mark_safe(concatenated)
