(function () {
  // Group every 3 items in .question-list into a .question-row and insert a separator
  // Insert a separator only after every third ROW (i.e. after 9, 18, ... items)
  function groupQuestionLists() {
    const lists = document.querySelectorAll('.question-list');
    lists.forEach(list => {
      // avoid re-running on already-processed lists
      if (list.dataset.separed === '1') return;
      const items = Array.from(list.querySelectorAll('li'));
      if (items.length === 0) return;
      // create a fragment and rebuild the list content with rows + separators
      const frag = document.createDocumentFragment();
      let rowIndex = 0;
      for (let i = 0; i < items.length; i += 3) {
        const row = document.createElement('div');
        row.className = 'question-row';
        // move up to 3 items into the row
        items.slice(i, i + 3).forEach(it => {
          // sanitize obvious wrapping braces in the question text (web-only artefact)
          try {
            let inner = it.innerHTML.trim();
            // unwrap single outer braces
            if (inner.startsWith('{') && inner.endsWith('}')) {
              inner = inner.slice(1, -1).trim();
            }
            // collapse runs of backslashes to a single backslash so MathJax commands render
            // e.g. convert "\\\\times" -> "\\times"
            inner = inner.replace(/\\\\+/g, "\\\\");
            // also remove stray backslashes before punctuation like ':' which were visible
            inner = inner.replace(/\\:/g, ':');
            it.innerHTML = inner;
          } catch (e) {
            // ignore
          }
          // wrap list item in a container to preserve numbering if needed
          const wrapper = document.createElement('div');
          wrapper.className = 'question-cell';
          wrapper.appendChild(it);
          row.appendChild(wrapper);
        });
        frag.appendChild(row);
        rowIndex++;
        // insert separator only after every 3rd row (i.e. when rowIndex % 3 === 0)
        if (rowIndex % 3 === 0 && i + 3 < items.length) {
          const sep = document.createElement('div');
          sep.className = 'row-separator';
          frag.appendChild(sep);
        }
      }
      // replace list's inner content with the new structure
      const container = document.createElement('div');
      container.className = 'question-list-reflow';
      container.appendChild(frag);
      list.parentNode.replaceChild(container, list);
      container.dataset.separed = '1';
      // trigger MathJax re-render if available
      if (window.MathJax && typeof MathJax.typesetPromise === 'function') {
        MathJax.typesetPromise();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', groupQuestionLists);
  } else {
    groupQuestionLists();
  }
})();
