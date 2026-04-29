#!/usr/bin/env bash
# Generate PNG previews for all Mana Maths PDF modules (notes, te reo, tasks, solutions).
# Usage: ./generate-previews.sh [slug]
#   - no args: all LOs with existing PDFs
#   - slug arg: specific LO, e.g. lo-yr9-rounding-to-decimal-points

set -euo pipefail
SITE="/home/debid/.openclaw/workspace/manamaths/SITE"

render_preview() {
    local pdf="$1" outdir="$2" prefix="$3"
    mkdir -p "$outdir"
    local pages
    pages=$(pdftoppm -png -r 72 "$pdf" "$outdir/tmp" 2>&1 | grep -c "Page" || true)
    # pdftoppm outputs tmp-1.png, tmp-2.png etc. 
    # Rename to <prefix>-p001.png, <prefix>-p002.png
    for f in "$outdir"/tmp-*.png; do
        [ -f "$f" ] || continue
        local basename="$(basename "$f")"
        local num="${basename#tmp-}"
        num="${num%.png}"
        printf -v pagenum "%03d" "$num"
        mv "$f" "$outdir/${prefix}-p${pagenum}.png"
        echo "  $outdir/${prefix}-p${pagenum}.png"
    done
}

if [ $# -eq 1 ]; then
    slugs=("$1")
else
    slugs=()
    for f in "$SITE"/notes-pdfs/*.pdf; do
        [ -f "$f" ] || continue
        slug=$(basename "$f" .pdf)
        slugs+=("$slug")
    done
fi

for slug in "${slugs[@]}"; do
    echo "=== $slug ==="
    preview_dir="$SITE/previews/$slug"
    
    # Notes
    pdf="$SITE/notes-pdfs/$slug.pdf"
    [ -f "$pdf" ] && render_preview "$pdf" "$preview_dir" notes
    
    # Te reo
    pdf="$SITE/te-reo-pdfs/$slug.pdf"
    [ -f "$pdf" ] && render_preview "$pdf" "$preview_dir" te-reo
    
    # Tasks (3 levels)
    for level in foundation proficient excellence; do
        pdf="/home/debid/.openclaw/workspace/manamaths/OBJECTIVES/$slug/${level}-questions.pdf"
        [ -f "$pdf" ] && render_preview "$pdf" "$preview_dir" "${level}-tasks"
    done
done
