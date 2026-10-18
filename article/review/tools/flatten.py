"""Inline \input{...} of sections, related and tables (recursively) into one file; keep figure inputs."""
import re, sys, pathlib
root = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
def expand(text):
    def rep(m):
        name = m.group(1)
        if name.startswith("figures/"):
            return m.group(0)
        p = root / (name if name.endswith(".tex") else name + ".tex")
        if not p.exists():
            return m.group(0)
        return expand(p.read_text())
    return re.sub(r"\\input\{([^}]+)\}", rep, text)
out.write_text(expand((root / "main.tex").read_text()))
print("wrote", out, len(out.read_text()))
