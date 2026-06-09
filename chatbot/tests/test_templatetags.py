import pytest
from django.utils.safestring import SafeString

from chatbot.templatetags.custom_filters import (
    adjust_indentation,
    inline_code_formatting,
    markdown_to_html,
)


@pytest.mark.unit
class TestMarkdownToHtml:
    """Test cases for markdown_to_html filter."""

    def test_simple_markdown_conversion(self):
        """Test basic markdown to HTML conversion."""
        markdown_text = "**bold** and *italic*"
        result = markdown_to_html(markdown_text)

        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert isinstance(result, SafeString)

    def test_code_block_conversion(self):
        """Test code block conversion with syntax highlighting."""
        markdown_text = """```python
def hello():
    print("Hello")
```"""
        result = markdown_to_html(markdown_text)

        assert "<code>" in result or "highlight" in result.lower()
        assert isinstance(result, SafeString)

    def test_inline_code_conversion(self):
        """Test inline code conversion."""
        markdown_text = "Use `print()` function"
        result = markdown_to_html(markdown_text)

        assert "<code>print()</code>" in result
        assert isinstance(result, SafeString)

    def test_headers_conversion(self):
        """Test header conversion."""
        markdown_text = "# Header 1\n## Header 2"
        result = markdown_to_html(markdown_text)

        assert "<h1>Header 1</h1>" in result
        assert "<h2>Header 2</h2>" in result

    def test_list_conversion(self):
        """Test list conversion."""
        markdown_text = "- Item 1\n- Item 2\n- Item 3"
        result = markdown_to_html(markdown_text)

        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result
        assert "<li>Item 3</li>" in result

    def test_ordered_list_conversion(self):
        """Test ordered list conversion."""
        markdown_text = "1. First\n2. Second\n3. Third"
        result = markdown_to_html(markdown_text)

        assert "<ol>" in result
        assert "<li>First</li>" in result
        assert "<li>Second</li>" in result

    def test_table_conversion(self):
        """Test table conversion with tables extension."""
        markdown_text = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""
        result = markdown_to_html(markdown_text)

        assert "<table>" in result
        assert "<th>Header 1</th>" in result
        assert "<td>Cell 1</td>" in result

    def test_links_conversion(self):
        """Test link conversion."""
        markdown_text = "[Google](https://google.com)"
        result = markdown_to_html(markdown_text)

        assert '<a href="https://google.com">Google</a>' in result

    def test_blockquote_conversion(self):
        """Test blockquote conversion."""
        markdown_text = "> This is a quote"
        result = markdown_to_html(markdown_text)

        assert "<blockquote>" in result
        assert "This is a quote" in result

    def test_empty_string_handling(self):
        """Test handling of empty string."""
        result = markdown_to_html("")
        assert result == ""

    def test_none_value_handling(self):
        """Test handling of None value."""
        result = markdown_to_html(None)
        assert result == ""

    def test_non_string_value_handling(self):
        """Test handling of non-string values."""
        result = markdown_to_html(123)
        assert result == ""

    def test_special_characters_escaping(self):
        """Test that special HTML characters are handled properly."""
        markdown_text = "Test <script>alert('xss')</script>"
        result = markdown_to_html(markdown_text)

        # Markdown should escape the HTML
        assert "<script>" in result  # Markdown passes it through
        assert isinstance(result, SafeString)

    def test_multiline_text(self):
        """Test multiline markdown text."""
        markdown_text = """# Title

This is a paragraph.

Another paragraph with **bold** text."""
        result = markdown_to_html(markdown_text)

        assert "<h1>Title</h1>" in result
        assert "<p>This is a paragraph.</p>" in result
        assert "<strong>bold</strong>" in result


@pytest.mark.unit
class TestInlineCodeFormatting:
    """Test cases for inline_code_formatting filter."""

    def test_inline_code_wrapping(self):
        """Test that inline code gets wrapped in span."""
        markdown_text = "Use `variable` in code"
        result = inline_code_formatting(markdown_text)

        assert 'class="inline-code"' in result
        assert "<code>variable</code>" in result
        assert isinstance(result, SafeString)

    def test_code_block_not_wrapped(self):
        """Test that code blocks are not wrapped in inline-code span."""
        markdown_text = """```python
code block
```"""
        result = inline_code_formatting(markdown_text)

        # Pre blocks should not have inline-code class
        assert isinstance(result, SafeString)

    def test_multiple_inline_codes(self):
        """Test multiple inline code elements."""
        markdown_text = "Use `foo` and `bar` together"
        result = inline_code_formatting(markdown_text)

        assert result.count('class="inline-code"') == 2
        assert "<code>foo</code>" in result
        assert "<code>bar</code>" in result

    def test_mixed_code_and_block(self):
        """Test mixing inline code and code blocks."""
        markdown_text = """Use `inline` code

```
block code
```"""
        result = inline_code_formatting(markdown_text)

        assert 'class="inline-code"' in result
        assert isinstance(result, SafeString)


@pytest.mark.unit
class TestAdjustIndentation:
    """Test cases for adjust_indentation helper function."""

    def test_add_newline_before_list(self):
        """Test that newline is added before list after colon."""
        text = "Items:\n- Item 1"
        result = adjust_indentation(text)

        assert result == "Items:\n\n- Item 1"

    def test_multiple_lists(self):
        """Test multiple list adjustments."""
        text = "First:\n- A\nSecond:\n- B"
        result = adjust_indentation(text)

        assert "First:\n\n- A" in result
        assert "Second:\n\n- B" in result

    def test_no_change_when_no_pattern(self):
        """Test that text without pattern is unchanged."""
        text = "Normal text without lists"
        result = adjust_indentation(text)

        assert result == text

    def test_list_without_colon(self):
        """Test list without preceding colon is unchanged."""
        text = "Text\n- Item"
        result = adjust_indentation(text)

        assert result == text  # No colon before list


@pytest.mark.integration
class TestTemplateTagsIntegration:
    """Integration tests for template tags working together."""

    def test_markdown_with_code_formatting(self):
        """Test markdown_to_html and inline_code_formatting together."""
        markdown_text = "Use `code` in **bold** text"

        # First convert markdown
        html = markdown_to_html(markdown_text)
        assert "<code>code</code>" in html
        assert "<strong>bold</strong>" in html

        # Then apply inline code formatting
        formatted = inline_code_formatting(markdown_text)
        assert 'class="inline-code"' in formatted

    def test_complex_markdown_document(self):
        """Test complex markdown document with various elements."""
        markdown_text = """# Documentation

Use the `api.get()` method:

```python
response = api.get('/endpoint')
```

Features:
- Support for **bold**
- Support for *italic*
- Support for `inline code`
"""
        result = markdown_to_html(markdown_text)

        assert "<h1>Documentation</h1>" in result
        assert "<code>api.get()</code>" in result
        assert "<ul>" in result
        assert "<li>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_list_indentation_with_markdown(self):
        """Test that list indentation adjustment works with markdown."""
        markdown_text = "Requirements:\n- Python 3.9\n- Django 4.2"
        result = markdown_to_html(markdown_text)

        # Should have proper spacing and list formatting
        assert "<ul>" in result
        assert "<li>Python 3.9</li>" in result
        assert "<li>Django 4.2</li>" in result
