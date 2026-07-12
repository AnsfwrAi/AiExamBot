BASE_SCRIPT_PROD_UUID = """
"use strict";
const MIN_SIZE  = 60;
const Z         = 2147483647;
const PAGE_ZOOM = window.visualViewport?.scale || 1;

await import('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
const html2canvas = window.html2canvas;

let isCapturing    = false;
let startPos       = null;
let selectionFrame = null;
let answerPending  = false;
let currentAnswer  = null;

const disableSelection = () => {{
  document.body.style.userSelect       = 'none';
  document.body.style.webkitUserSelect = 'none';
}};
const enableSelection = () => {{
  document.body.style.userSelect       = '';
  document.body.style.webkitUserSelect = '';
}};

const reset = () => {{
  enableSelection();
  isCapturing  = false;
  startPos     = null;
  selectionFrame?.remove();
  selectionFrame = null;
}};
window.resetCapture = reset;

document.addEventListener('mousedown', e => {{
  reset();
  disableSelection();
  isCapturing = true;
  startPos    = [e.clientX + window.scrollX, e.clientY + window.scrollY];

  selectionFrame = document.createElement('div');
  selectionFrame.style = `
    position:fixed;
    left:${{e.clientX}}px; top:${{e.clientY}}px;
    width:0;height:0;
    pointer-events:none; z-index:${{Z}};
  `;
  document.body.append(selectionFrame);
}});

document.addEventListener('mousemove', e => {{
  if (!isCapturing || !selectionFrame) return;

  const [x1, y1] = startPos;
  const x2 = e.clientX + window.scrollX;
  const y2 = e.clientY + window.scrollY;

  const left   = Math.min(x1, x2) - window.scrollX;
  const top    = Math.min(y1, y2) - window.scrollY;
  const width  = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);

  Object.assign(selectionFrame.style, {{
    left:   `${{left}}px`,
    top:    `${{top}}px`,
    width:  `${{width}}px`,
    height: `${{height}}px`
  }});
}});

document.addEventListener('mouseup', async e => {{
  if (!isCapturing || !startPos) return;
  enableSelection();
  isCapturing = false;
  selectionFrame?.remove();

  const [x1, y1] = startPos;
  const x2 = e.clientX + window.scrollX;
  const y2 = e.clientY + window.scrollY;

  let left   = Math.min(x1, x2);
  let top    = Math.min(y1, y2);
  let width  = Math.abs(x2 - x1);
  let height = Math.abs(y2 - y1);

  if (width < MIN_SIZE || height < MIN_SIZE) return reset();

  left   /= PAGE_ZOOM;
  top    /= PAGE_ZOOM;
  width  /= PAGE_ZOOM;
  height /= PAGE_ZOOM;

  document.querySelectorAll('.right').forEach(el => el.classList.remove('right'));

  try {{
    const canvas = await html2canvas(document.body, {{
      x: left,
      y: top,
      width,
      height,
      backgroundColor: '#fff', 
      useCORS: true,
      scale: 1,
      removeContainer: true,
      ignoreElements: el => el?.src?.includes('google.com/recaptcha')
    }});

    const persistentId = '{fingerprint}';

    answerPending = true;
    currentAnswer = null;

    canvas.toBlob(async blob => {{
      if (!blob) return reset();

      const fd = new FormData();
      fd.append('key', '{key}');
      fd.append('fingerprint', persistentId);
      fd.append('image', blob, 'capture.png');

      try {{
        const res = await fetch('{domain}', {{ method: 'POST', body: fd }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const j = await res.json();
        currentAnswer = j?.data?.answer || j?.data || j?.error?.message || '❌ нет ответа';
      }} catch (err) {{
        currentAnswer = '❌ ошибка: ' + err.message;
      }} finally {{
        answerPending = false;
      }}
    }}, 'image/png');
  }} catch (err) {{
    currentAnswer = '❌ capture fail: ' + err.message;
    answerPending = false;
    reset();
  }}
}});

document.addEventListener('dblclick', e => {{
  const text = answerPending ? '🔄 ответ загружается…' : (currentAnswer ?? '❔ нет ответа');

  const bg  = getComputedStyle(document.body).backgroundColor;
  const rgb = bg.match(/\\\\d+/g)?.map(Number) || [255,255,255];
  const lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]) / 255;
  const fg  = lum > 0.5 ? '#000' : '#fff';

  if (window._answerPopup) window._answerPopup.remove();

  const span = document.createElement('span');
  span.textContent = text;
  span.style = `
    position:fixed;
    left:${{e.clientX + 8}}px; top:${{e.clientY + 8}}px;
    z-index:${{Z}};
    font:12px/1 monospace;
    color:${{fg}};
    background:rgba(0,0,0,0.05);
    padding:2px 6px;
    border-radius:4px;
    pointer-events:auto;
    backdrop-filter: blur(1px);
    white-space:pre;
  `;

  window._answerPopup = span;
  document.body.append(span);

  setTimeout(() => {{
    if (window._answerPopup === span) {{
      span.remove();
      window._answerPopup = null;
    }}
  }}, 2200);

}});

document.addEventListener('click', () => {{
  if (window._answerPopup) {{
    window._answerPopup.remove();
    window._answerPopup = null;
  }}
}}, true);

document.addEventListener('keydown', e => e.key === 'Escape' && reset());
"""


BASE_SCRIPT = """
"use strict";
const MIN_SIZE  = 60;
const Z         = 2147483647;
const PAGE_ZOOM = window.visualViewport?.scale || 1;

await import('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
const html2canvas = window.html2canvas;

let isCapturing    = false;
let startPos       = null;
let selectionFrame = null;
let answerPending  = false;
let currentAnswer  = null;

const disableSelection = () => {{
  document.body.style.userSelect       = 'none';
  document.body.style.webkitUserSelect = 'none';
}};
const enableSelection = () => {{
  document.body.style.userSelect       = '';
  document.body.style.webkitUserSelect = '';
}};

const reset = () => {{
  enableSelection();
  isCapturing  = false;
  startPos     = null;
  selectionFrame?.remove();
  selectionFrame = null;
}};
window.resetCapture = reset;

document.addEventListener('mousedown', e => {{
  reset();
  disableSelection();
  isCapturing = true;
  startPos    = [e.clientX + window.scrollX, e.clientY + window.scrollY];

  selectionFrame = document.createElement('div');
  selectionFrame.style = `
    position:fixed;
    left:${{e.clientX}}px; top:${{e.clientY}}px;
    width:0;height:0;
    pointer-events:none; z-index:${{Z}};
  `;
  document.body.append(selectionFrame);
}});

document.addEventListener('mousemove', e => {{
  if (!isCapturing || !selectionFrame) return;

  const [x1, y1] = startPos;
  const x2 = e.clientX + window.scrollX;
  const y2 = e.clientY + window.scrollY;

  const left   = Math.min(x1, x2) - window.scrollX;
  const top    = Math.min(y1, y2) - window.scrollY;
  const width  = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);

  Object.assign(selectionFrame.style, {{
    left:   `${{left}}px`,
    top:    `${{top}}px`,
    width:  `${{width}}px`,
    height: `${{height}}px`
  }});
}});

document.addEventListener('mouseup', async e => {{
  if (!isCapturing || !startPos) return;
  enableSelection();
  isCapturing = false;
  selectionFrame?.remove();

  const [x1, y1] = startPos;
  const x2 = e.clientX + window.scrollX;
  const y2 = e.clientY + window.scrollY;

  let left   = Math.min(x1, x2);
  let top    = Math.min(y1, y2);
  let width  = Math.abs(x2 - x1);
  let height = Math.abs(y2 - y1);

  if (width < MIN_SIZE || height < MIN_SIZE) return reset();

  left   /= PAGE_ZOOM;
  top    /= PAGE_ZOOM;
  width  /= PAGE_ZOOM;
  height /= PAGE_ZOOM;

  document.querySelectorAll('.right').forEach(el => el.classList.remove('right'));

  try {{
    const canvas = await html2canvas(document.body, {{
      x: left,
      y: top,
      width,
      height,
      backgroundColor: '#fff', 
      useCORS: true,
      scale: 1,
      removeContainer: true,
      ignoreElements: el => el?.src?.includes('google.com/recaptcha')
    }});

    const persistentId = '{fingerprint}';

    answerPending = true;
    currentAnswer = null;

    canvas.toBlob(async blob => {{
      if (!blob) return reset();

      const fd = new FormData();
      fd.append('key', '{key}');
      fd.append('fingerprint', persistentId);
      fd.append('image', blob, 'capture.png');

      try {{
        const res = await fetch('{domain}', {{ method: 'POST', body: fd }});

        let responseData;
        try {{
          responseData = await res.json();
        }} catch (parseError) {{
          throw new Error('Invalid JSON response');
        }}

        if (!res.ok) {{
          if (responseData && !responseData.success && responseData.error) {{
            throw new Error(`${{responseData.error.code}}: ${{responseData.error.message}}`);
          }} else {{
            throw new Error(`HTTP ${{res.status}}`);
          }}
        }}

        if (responseData.success) {{
          currentAnswer = responseData.data?.answer || responseData.data || '❌ нет данных в ответе';
        }} else {{
          const errorMsg = responseData.error?.message || 'Unknown error';
          const errorCode = responseData.error?.code || 'unknown';
          currentAnswer = `❌ ${{errorCode}}: ${{errorMsg}}`;
        }}

      }} catch (err) {{
        currentAnswer = '❌ ошибка: ' + err.message;
      }} finally {{
        answerPending = false;
      }}
    }}, 'image/png');
  }} catch (err) {{
    currentAnswer = '❌ capture fail: ' + err.message;
    answerPending = false;
    reset();
  }}
}});

document.addEventListener('dblclick', e => {{
  const text = answerPending ? '🔄 ответ загружается…' : (currentAnswer ?? '❔ нет ответа');

  const bg  = getComputedStyle(document.body).backgroundColor;
  const rgb = bg.match(/\\\\d+/g)?.map(Number) || [255,255,255];
  const lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]) / 255;
  const fg  = lum > 0.5 ? '#000' : '#fff';

  if (window._answerPopup) window._answerPopup.remove();

  const span = document.createElement('span');
  span.textContent = text;
  span.style = `
    position:fixed;
    left:${{e.clientX + 8}}px; top:${{e.clientY + 8}}px;
    z-index:${{Z}};
    font:12px/1 monospace;
    color:${{fg}};
    background:rgba(0,0,0,0.05);
    padding:2px 6px;
    border-radius:4px;
    pointer-events:auto;
    backdrop-filter: blur(1px);
    white-space:pre;
  `;

  window._answerPopup = span;
  document.body.append(span);

  setTimeout(() => {{
    if (window._answerPopup === span) {{
      span.remove();
      window._answerPopup = null;
    }}
  }}, 2200);

}});

document.addEventListener('click', () => {{
  if (window._answerPopup) {{
    window._answerPopup.remove();
    window._answerPopup = null;
  }}
}}, true);

document.addEventListener('keydown', e => e.key === 'Escape' && reset());
"""

BASE_SCRIPT_V2 = """
"use strict";
const MIN_SIZE  = 60;
const Z         = 2147483647;

await import('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
const html2canvas = window.html2canvas;

let isCapturing    = false;
let startPos       = null;
let selectionFrame = null;
let answerPending  = false;
let currentAnswer  = null;

const disableSelection = () => {{
  document.body.style.userSelect       = 'none';
  document.body.style.webkitUserSelect = 'none';
}};
const enableSelection = () => {{
  document.body.style.userSelect       = '';
  document.body.style.webkitUserSelect = '';
}};

const reset = () => {{
  enableSelection();
  isCapturing  = false;
  startPos     = null;
  selectionFrame?.remove();
  selectionFrame = null;
}};
window.resetCapture = reset;

document.addEventListener('mousedown', e => {{
  reset();
  disableSelection();
  isCapturing = true;
  startPos    = [e.clientX, e.clientY];

  selectionFrame = document.createElement('div');
  selectionFrame.style = `
    position:fixed;
    left:${{e.clientX}}px; top:${{e.clientY}}px;
    width:0;height:0;
    pointer-events:none; z-index:${{Z}};
  `;
  document.body.append(selectionFrame);
}});

document.addEventListener('mousemove', e => {{
  if (!isCapturing || !selectionFrame) return;

  const [x1, y1] = startPos;
  const x2 = e.clientX;
  const y2 = e.clientY;

  const left   = Math.min(x1, x2);
  const top    = Math.min(y1, y2);
  const width  = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);

  Object.assign(selectionFrame.style, {{
    left:   `${{left}}px`,
    top:    `${{top}}px`,
    width:  `${{width}}px`,
    height: `${{height}}px`
  }});
}});

document.addEventListener('mouseup', async e => {{
  if (!isCapturing || !startPos) return;
  enableSelection();
  isCapturing = false;
  selectionFrame?.remove();

  const [x1, y1] = startPos;
  const x2 = e.clientX;
  const y2 = e.clientY;

  const left   = Math.min(x1, x2);
  const top    = Math.min(y1, y2);
  const width  = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);

  if (width < MIN_SIZE || height < MIN_SIZE) return reset();

  document.querySelectorAll('.right').forEach(el => el.classList.remove('right'));

  try {{
    // Снимаем ровно то, что видно на экране (текущий viewport), в нативном
    // разрешении экрана (devicePixelRatio) — без пересчётов через scroll/zoom.
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;

    const fullCanvas = await html2canvas(document.documentElement, {{
      backgroundColor: '#fff',
      useCORS: true,
      scale: window.devicePixelRatio || 1,
      x: window.scrollX,
      y: window.scrollY,
      width: vw,
      height: vh,
      windowWidth: vw,
      windowHeight: vh,
      removeContainer: true,
      ignoreElements: el => el?.src?.includes('google.com/recaptcha')
    }});

    // Вырезаем нужный прямоугольник уже из готового снимка через Canvas 2D —
    // детерминированная операция, не зависящая от внутренней логики html2canvas.
    const ratio = fullCanvas.width / vw;

    const canvas = document.createElement('canvas');
    canvas.width  = Math.max(1, Math.round(width  * ratio));
    canvas.height = Math.max(1, Math.round(height * ratio));
    canvas.getContext('2d').drawImage(
      fullCanvas,
      Math.round(left * ratio), Math.round(top * ratio),
      Math.round(width * ratio), Math.round(height * ratio),
      0, 0, canvas.width, canvas.height
    );

    const persistentId = '{fingerprint}';

    answerPending = true;
    currentAnswer = null;

    canvas.toBlob(async blob => {{
      if (!blob) return reset();

      const fd = new FormData();
      fd.append('key', '{key}');
      fd.append('fingerprint', persistentId);
      fd.append('image', blob, 'capture.png');

      try {{
        const res = await fetch('{domain}', {{ method: 'POST', body: fd }});

        let responseData;
        try {{
          responseData = await res.json();
        }} catch (parseError) {{
          throw new Error('Invalid JSON response');
        }}

        if (!res.ok) {{
          if (responseData && !responseData.success && responseData.error) {{
            throw new Error(`${{responseData.error.code}}: ${{responseData.error.message}}`);
          }} else {{
            throw new Error(`HTTP ${{res.status}}`);
          }}
        }}

        if (responseData.success) {{
          currentAnswer = responseData.data?.answer || responseData.data || '❌ нет данных в ответе';
        }} else {{
          const errorMsg = responseData.error?.message || 'Unknown error';
          const errorCode = responseData.error?.code || 'unknown';
          currentAnswer = `❌ ${{errorCode}}: ${{errorMsg}}`;
        }}

      }} catch (err) {{
        currentAnswer = '❌ ошибка: ' + err.message;
      }} finally {{
        answerPending = false;
      }}
    }}, 'image/png');
  }} catch (err) {{
    currentAnswer = '❌ capture fail: ' + err.message;
    answerPending = false;
    reset();
  }}
}});

document.addEventListener('dblclick', e => {{
  const text = answerPending ? '🔄 ответ загружается…' : (currentAnswer ?? '❔ нет ответа');

  const bg  = getComputedStyle(document.body).backgroundColor;
  const rgb = bg.match(/\\\\d+/g)?.map(Number) || [255,255,255];
  const lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]) / 255;
  const fg  = lum > 0.5 ? '#000' : '#fff';

  if (window._answerPopup) window._answerPopup.remove();

  const span = document.createElement('span');
  span.textContent = text;
  span.style = `
    position:fixed;
    left:${{e.clientX + 8}}px; top:${{e.clientY + 8}}px;
    z-index:${{Z}};
    font:12px/1 monospace;
    color:${{fg}};
    background:rgba(0,0,0,0.05);
    padding:2px 6px;
    border-radius:4px;
    pointer-events:auto;
    backdrop-filter: blur(1px);
    white-space:pre;
  `;

  window._answerPopup = span;
  document.body.append(span);

  setTimeout(() => {{
    if (window._answerPopup === span) {{
      span.remove();
      window._answerPopup = null;
    }}
  }}, 2200);

}});

document.addEventListener('click', () => {{
  if (window._answerPopup) {{
    window._answerPopup.remove();
    window._answerPopup = null;
  }}
}}, true);

document.addEventListener('keydown', e => e.key === 'Escape' && reset());
"""
