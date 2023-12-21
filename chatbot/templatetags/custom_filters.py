import re
from django import template
from django.utils.html import mark_safe
from bs4 import BeautifulSoup
from markdown import markdown

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


@register.filter(name="markdown_to_html")
def markdown_to_html(markdown_text: str):
    # print(markdown_text)
    # Regex to find code blocks and extract language
    if not isinstance(markdown_text, str):
        return ""
    to_test = """```html
    <pre>
    <code>
    // Your code goes here
    function example() {
        // Your code logic here
    }
    </code>
    </pre>
    ```"""

    markdown_text = re.sub(r"^```(\w+)", r"``` \1", markdown_text)
    result = markdown(markdown_text, extensions=["fenced_code"])

    # Additional formatting can be added here
    return mark_safe(result)
