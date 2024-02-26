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


def add_new_line_to_lists(text: str):
    pattern = r"(?<!\n)\n(\d+\.\s)"
    # Insert newline before list items
    processed_text = re.sub(pattern, "\n\n\\1", text)
    return processed_text


def adjust_indentation_for_markdown(text: str):
    # unindent code blocks
    text = re.sub(r" *```(\w*)", r"\n```\1", text, flags=re.MULTILINE)
    text = add_new_line_to_lists(text)
    return text


@register.filter(name="markdown_to_html")
def markdown_to_html(markdown_text: str):
    # Regex to find code blocks and extract language
    if not isinstance(markdown_text, str):
        return ""
    adjusted_text = adjust_indentation_for_markdown(markdown_text)
    result = markdown(adjusted_text, extensions=["fenced_code"])
    return mark_safe(result)
