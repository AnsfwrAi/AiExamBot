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

const generateUUID = () => {{
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  }});
}};

const getPersistentUUID = async () => {{
  const KEY = 'data_refs_key_fp';
  let uuid = null;

  const storageAttempts = [
    () => {{
      try {{
        uuid = localStorage.getItem(KEY);
        if (!uuid) {{
          uuid = generateUUID();
          localStorage.setItem(KEY, uuid);
        }}
        return uuid;
      }} catch (e) {{ return null; }}
    }},

    () => {{
      try {{
        uuid = sessionStorage.getItem(KEY);
        if (!uuid) {{
          uuid = generateUUID();
          sessionStorage.setItem(KEY, uuid);
        }}
        return uuid;
      }} catch (e) {{ return null; }}
    }},

    () => {{
      return new Promise((resolve) => {{
        try {{
          const request = indexedDB.open('DataRefsDB', 1);
          request.onerror = () => resolve(null);
          request.onupgradeneeded = (e) => {{
            const db = e.target.result;
            if (!db.objectStoreNames.contains('refs')) {{
              db.createObjectStore('refs');
            }}
          }};
          request.onsuccess = (e) => {{
            const db = e.target.result;
            const transaction = db.transaction(['refs'], 'readwrite');
            const store = transaction.objectStore('refs');

            const getRequest = store.get(KEY);
            getRequest.onsuccess = () => {{
              if (getRequest.result && getRequest.result.value) {{
                resolve(getRequest.result.value);
              }} else {{
                const newUuid = generateUUID();
                store.put({{ value: newUuid }}, KEY);
                resolve(newUuid);
              }}
            }};
            getRequest.onerror = () => resolve(null);
          }};
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      return new Promise(async (resolve) => {{
        try {{
          const cache = await caches.open('data-refs-cache');
          const response = await cache.match('/refs-data');

          if (response) {{
            const data = await response.text();
            resolve(data);
          }} else {{
            const newUuid = generateUUID();
            await cache.put('/refs-data', new Response(newUuid));
            resolve(newUuid);
          }}
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      return new Promise((resolve) => {{
        try {{
          if (!window.openDatabase) {{
            resolve(null);
            return;
          }}

          const db = openDatabase('DataRefsDB', '1.0', 'Data Refs Storage', 2 * 1024 * 1024);
          db.transaction((tx) => {{
            tx.executeSql('CREATE TABLE IF NOT EXISTS data_refs (id INTEGER PRIMARY KEY, fp_data TEXT)');
            tx.executeSql('SELECT fp_data FROM data_refs WHERE id = 1', [], (tx, results) => {{
              if (results.rows.length > 0) {{
                resolve(results.rows.item(0).fp_data);
              }} else {{
                const newUuid = generateUUID();
                tx.executeSql('INSERT INTO data_refs (id, fp_data) VALUES (1, ?)', [newUuid]);
                resolve(newUuid);
              }}
            }}, () => resolve(null));
          }});
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      try {{
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {{
          const [name, value] = cookie.trim().split('=');
          if (name === KEY) {{
            return decodeURIComponent(value);
          }}
        }}

        const newUuid = generateUUID();
        const expireDate = new Date();
        expireDate.setFullYear(expireDate.getFullYear() + 100);
        document.cookie = `${{KEY}}=${{encodeURIComponent(newUuid)}}; expires=${{expireDate.toUTCString()}}; path=/; SameSite=Lax`;
        return newUuid;
      }} catch (e) {{
        return null;
      }}
    }}
  ];

  for (const attempt of storageAttempts) {{
    try {{
      const result = await attempt();
      if (result) {{
        uuid = result;
        break;
      }}
    }} catch (e) {{
      continue;
    }}
  }}

  return uuid || generateUUID();
}};

const storeUUIDEverywhere = async (uuid) => {{
  const KEY = 'data_refs_key_fp';

  try {{ localStorage.setItem(KEY, uuid); }} catch (e) {{}}

  try {{ sessionStorage.setItem(KEY, uuid); }} catch (e) {{}}

  try {{
    const request = indexedDB.open('DataRefsDB', 1);
    request.onupgradeneeded = (e) => {{
      const db = e.target.result;
      if (!db.objectStoreNames.contains('refs')) {{
        db.createObjectStore('refs');
      }}
    }};
    request.onsuccess = (e) => {{
      const db = e.target.result;
      const transaction = db.transaction(['refs'], 'readwrite');
      const store = transaction.objectStore('refs');
      store.put({{ value: uuid }}, KEY);
    }};
  }} catch (e) {{}}

  try {{
    const cache = await caches.open('data-refs-cache');
    await cache.put('/refs-data', new Response(uuid));
  }} catch (e) {{}}

  try {{
    const expireDate = new Date();
    expireDate.setFullYear(expireDate.getFullYear() + 100);
    document.cookie = `${{KEY}}=${{encodeURIComponent(uuid)}}; expires=${{expireDate.toUTCString()}}; path=/; SameSite=Lax`;
  }} catch (e) {{}}
}};

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

    let persistentId = await getPersistentUUID();

    await storeUUIDEverywhere(persistentId);

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
  const rgb = bg.match(/\\d+/g)?.map(Number) || [255,255,255];
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

const generateUUID = () => {{
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  }});
}};

const getPersistentUUID = async () => {{
  const KEY = 'data_refs_key_fp';
  let uuid = null;

  const storageAttempts = [
    () => {{
      try {{
        uuid = localStorage.getItem(KEY);
        if (!uuid) {{
          uuid = generateUUID();
          localStorage.setItem(KEY, uuid);
        }}
        return uuid;
      }} catch (e) {{ return null; }}
    }},

    () => {{
      try {{
        uuid = sessionStorage.getItem(KEY);
        if (!uuid) {{
          uuid = generateUUID();
          sessionStorage.setItem(KEY, uuid);
        }}
        return uuid;
      }} catch (e) {{ return null; }}
    }},

    () => {{
      return new Promise((resolve) => {{
        try {{
          const request = indexedDB.open('DataRefsDB', 1);
          request.onerror = () => resolve(null);
          request.onupgradeneeded = (e) => {{
            const db = e.target.result;
            if (!db.objectStoreNames.contains('refs')) {{
              db.createObjectStore('refs');
            }}
          }};
          request.onsuccess = (e) => {{
            const db = e.target.result;
            const transaction = db.transaction(['refs'], 'readwrite');
            const store = transaction.objectStore('refs');

            const getRequest = store.get(KEY);
            getRequest.onsuccess = () => {{
              if (getRequest.result && getRequest.result.value) {{
                resolve(getRequest.result.value);
              }} else {{
                const newUuid = generateUUID();
                store.put({{ value: newUuid }}, KEY);
                resolve(newUuid);
              }}
            }};
            getRequest.onerror = () => resolve(null);
          }};
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      return new Promise(async (resolve) => {{
        try {{
          const cache = await caches.open('data-refs-cache');
          const response = await cache.match('/refs-data');

          if (response) {{
            const data = await response.text();
            resolve(data);
          }} else {{
            const newUuid = generateUUID();
            await cache.put('/refs-data', new Response(newUuid));
            resolve(newUuid);
          }}
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      return new Promise((resolve) => {{
        try {{
          if (!window.openDatabase) {{
            resolve(null);
            return;
          }}

          const db = openDatabase('DataRefsDB', '1.0', 'Data Refs Storage', 2 * 1024 * 1024);
          db.transaction((tx) => {{
            tx.executeSql('CREATE TABLE IF NOT EXISTS data_refs (id INTEGER PRIMARY KEY, fp_data TEXT)');
            tx.executeSql('SELECT fp_data FROM data_refs WHERE id = 1', [], (tx, results) => {{
              if (results.rows.length > 0) {{
                resolve(results.rows.item(0).fp_data);
              }} else {{
                const newUuid = generateUUID();
                tx.executeSql('INSERT INTO data_refs (id, fp_data) VALUES (1, ?)', [newUuid]);
                resolve(newUuid);
              }}
            }}, () => resolve(null));
          }});
        }} catch (e) {{
          resolve(null);
        }}
      }});
    }},

    () => {{
      try {{
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {{
          const [name, value] = cookie.trim().split('=');
          if (name === KEY) {{
            return decodeURIComponent(value);
          }}
        }}

        const newUuid = generateUUID();
        const expireDate = new Date();
        expireDate.setFullYear(expireDate.getFullYear() + 100);
        document.cookie = `${{KEY}}=${{encodeURIComponent(newUuid)}}; expires=${{expireDate.toUTCString()}}; path=/; SameSite=Lax`;
        return newUuid;
      }} catch (e) {{
        return null;
      }}
    }}
  ];

  for (const attempt of storageAttempts) {{
    try {{
      const result = await attempt();
      if (result) {{
        uuid = result;
        break;
      }}
    }} catch (e) {{
      continue;
    }}
  }}

  return uuid || generateUUID();
}};

const storeUUIDEverywhere = async (uuid) => {{
  const KEY = 'data_refs_key_fp';

  try {{ localStorage.setItem(KEY, uuid); }} catch (e) {{}}

  try {{ sessionStorage.setItem(KEY, uuid); }} catch (e) {{}}

  try {{
    const request = indexedDB.open('DataRefsDB', 1);
    request.onupgradeneeded = (e) => {{
      const db = e.target.result;
      if (!db.objectStoreNames.contains('refs')) {{
        db.createObjectStore('refs');
      }}
    }};
    request.onsuccess = (e) => {{
      const db = e.target.result;
      const transaction = db.transaction(['refs'], 'readwrite');
      const store = transaction.objectStore('refs');
      store.put({{ value: uuid }}, KEY);
    }};
  }} catch (e) {{}}

  try {{
    const cache = await caches.open('data-refs-cache');
    await cache.put('/refs-data', new Response(uuid));
  }} catch (e) {{}}

  try {{
    const expireDate = new Date();
    expireDate.setFullYear(expireDate.getFullYear() + 100);
    document.cookie = `${{KEY}}=${{encodeURIComponent(uuid)}}; expires=${{expireDate.toUTCString()}}; path=/; SameSite=Lax`;
  }} catch (e) {{}}
}};

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

    let persistentId = await getPersistentUUID();

    await storeUUIDEverywhere(persistentId);

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
  const rgb = bg.match(/\\d+/g)?.map(Number) || [255,255,255];
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