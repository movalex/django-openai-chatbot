import re
from django import template
from django.utils.html import mark_safe
from bs4 import BeautifulSoup
from markdown import markdown
from pprint import pp

register = template.Library()


@register.filter(name="inline_code_formatting")
def inline_code_formatting(value):
    soup = BeautifulSoup(markdown(value), "html.parser")

    # Process `code` elements for inline code
    for code in soup.find_all("code"):
        if not code.find_parent("pre"):
            # This is inline code, not part of a preformatted block
            code.wrap(soup.new_tag("span", **{"class": "inline-code"}))

    # Convert soup back to string and mark as safe
    return mark_safe(str(soup))


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
