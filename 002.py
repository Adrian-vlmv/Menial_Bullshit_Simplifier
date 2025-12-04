import re

EXCLUDED_KEYWORDS = r'if|for|while|switch|return|catch|else'  # tu lista real
pattern = re.compile(
    r'(?:^|\n)\s*'
    r'(?:[A-Za-z_][A-Za-z0-9_:<>\s*&]+?\s+)?'
    r'(?!' + EXCLUDED_KEYWORDS + r')'
    r'('
        r'(?:[A-Za-z_][A-Za-z0-9_]*::)?'
        r'(?:'
            r'[A-Za-z_][A-Za-z0-9_:]*'
            r'|'
            r'operator'
            r'\s*'
            r'(?:\(\s*\)|\[\s*\]|==|!=|<=|>=|\+\+|--|<<|>>|->\*|->|new|delete|[+\-*/%<>=&\|\^~])'
        r')'
    r')'
    r'\s*\((.*?)\)'
    r'(?:\s*const)?'
    r'(\s*:[\s\S]*?)?'
    r'\s*\{'
    , re.DOTALL
)

code = """
bool StoredMessage::operator == (const StoredMessage& sMsg) const
{
    // body...
}
"""

m = pattern.search(code)
if m:
    print("Matched name:", repr(m.group(1)))
    print("Params   :", repr(m.group(2)))
else:
    print("No match")
