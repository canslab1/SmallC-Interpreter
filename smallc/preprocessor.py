"""Simple preprocessor for #define constant expansion."""

import re


class Preprocessor:
    def __init__(self, source: str):
        self.source = source
        self.macros: dict[str, str] = {}

    def process(self) -> str:
        lines = self.source.split('\n')
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#define'):
                parts = stripped.split(None, 2)
                if len(parts) >= 2:
                    name = parts[1]
                    value = parts[2] if len(parts) > 2 else ""
                    self.macros[name] = value
                out.append('')  # preserve line numbering
            else:
                out.append(line)
        result = '\n'.join(out)
        for name in sorted(self.macros, key=len, reverse=True):
            result = re.sub(r'\b' + re.escape(name) + r'\b', self.macros[name], result)
        return result
