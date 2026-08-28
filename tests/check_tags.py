from html.parser import HTMLParser

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag}> at line {self.getpos()[0]}")
            return
        expected, pos = self.stack.pop()
        if expected != tag:
            self.errors.append(f"Mismatched tag: expected </{expected}> (opened at line {pos[0]}), found </{tag}> at line {self.getpos()[0]}")

with open(r"d:\招聘\src\web\templates\index.html", "r", encoding="utf-8") as f:
    content = f.read()

checker = TagChecker()
checker.feed(content)

print(f"Total errors: {len(checker.errors)}")
for err in checker.errors:
    print(err)

if checker.stack:
    print(f"\nUnclosed tags ({len(checker.stack)}):")
    for tag, pos in checker.stack:
        print(f"  <{tag}> opened at line {pos[0]}")
