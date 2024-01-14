from django.test import TestCase
from chatbot.templatetags.custom_filters import markdown_to_html


class FiltersTest(TestCase):
    INP = """1. **HEADER1**: 

   Example using vanilla JavaScript:
   ```javascript
   some-code {
   };
   ```
2. **HEADER2**"""

    def test_markdown_output(self):
        assert (
            markdown_to_html(self.INP)
            == """<ol>
<li><strong>HEADER1</strong>: </li>
</ol>
<p>Example using vanilla JavaScript:</p>
<pre><code class="language-javascript">   some-code {
   };

</code></pre>
<ol>
<li><strong>HEADER2</strong></li>
</ol>"""
        )
