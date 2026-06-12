import re

from django import template
from django.utils.safestring import mark_safe
from markdown import markdown

register = template.Library()


def adjust_indentation(text: str):
    # add newline before a list
    text = re.sub(r":\n-", r":\n\n-", text, flags=re.MULTILINE)
    return text


@register.filter(name="markdown_to_html")
def markdown_to_html(markdown_text: str):
    # Regex to find code blocks and extract language
    if not isinstance(markdown_text, str):
        return ""
    adjusted_text = adjust_indentation(markdown_text)
    result = markdown(adjusted_text, tab_length=3, extensions=["pymdownx.superfences", "tables"])
    return mark_safe(result)
