# Mana Maths

## Build notes

Worksheet PDF builds use `build_pdfs.py`.

Supported TeX engines:
- `latexmk`
- `pdflatex`
- `tectonic`

On this machine, the intended fallback is the user-local `tectonic` binary at:
- `/home/debid/bin/tectonic`

That path is on PATH for this OpenClaw environment, so fresh chats and cron runs should check for it before claiming TeX is unavailable.

Example:

```bash
python3 build_pdfs.py
```
