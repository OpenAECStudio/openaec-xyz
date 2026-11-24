"""Read-only export van alle maatwerk op erp.voorbeeld.nl naar een lokale map (standaard server-export/)."""
import json
import os
import urllib.parse
import urllib.request

TOKEN = os.environ.get('ERPNEXT_API_TOKEN', '<ERPNEXT_API_TOKEN>')
BASE = os.environ.get('ERPNEXT_URL', 'https://erp.voorbeeld.nl')
OUT = os.environ.get("ZNEXT_EXPORT_DIR", "server-export")
os.makedirs(OUT, exist_ok=True)


def get(path, params=None):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(url)
    req.add_header('Authorization', 'token ' + TOKEN)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=120).read().decode('utf-8'))
    except Exception as e:  # noqa: BLE001
        raw = e.read().decode('utf-8', 'replace') if hasattr(e, 'read') else str(e)
        return {'ERROR': raw[:300]}


def lst(doctype, filters=None, fields=('name',)):
    p = {'fields': json.dumps(list(fields)), 'limit_page_length': 0}
    if filters:
        p['filters'] = json.dumps(filters)
    r = get('/api/resource/' + urllib.parse.quote(doctype), p)
    return r.get('data', []) if 'data' in r else ('ERROR', r.get('ERROR'))


def full(doctype, name):
    r = get('/api/resource/' + urllib.parse.quote(doctype) + '/' + urllib.parse.quote(name, safe=''))
    return r.get('data') if 'data' in r else None


SETS = {
    'DocType': ([['custom', '=', 1]], True),
    'Custom Field': (None, False),
    'Property Setter': (None, False),
    'Server Script': (None, True),
    'Client Script': (None, True),
    'Custom DocPerm': (None, False),
    'Report': ([['is_standard', '=', 'No']], True),
    'Number Card': ([['is_standard', '=', 0]], True),
    'Dashboard Chart': ([['is_standard', '=', 0]], True),
    'Dashboard': ([['is_standard', '=', 0]], True),
    'Workspace': (None, True),
    'Role': (None, False),
    'Print Format': ([['standard', '=', 'No']], True),
    'Notification': ([['is_standard', '=', 0]], True),
    'Email Template': (None, True),
    'Workflow': (None, True),
    'Page': ([['standard', '=', 'No']], True),
    'Web Page': (None, False),
    'Web Form': ([['is_standard', '=', 0]], True),
    'Custom HTML Block': (None, True),
    'Letter Head': (None, False),
}

summary = {}
for dt, (flt, need_full) in SETS.items():
    rows = lst(dt, flt, fields=['*'])
    if isinstance(rows, tuple):
        summary[dt] = 'GEEN TOEGANG: ' + str(rows[1])[:80]
        continue
    if need_full:
        docs = []
        for r in rows:
            d = full(dt, r['name'])
            docs.append(d if d else r)
        rows = docs
    json.dump(rows, open(os.path.join(OUT, dt.replace(' ', '_') + '.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, default=str)
    summary[dt] = len(rows)

json.dump(summary, open(os.path.join(OUT, '_summary.json'), 'w'), indent=1)
for k, v in summary.items():
    print(f'  {k:20} {v}')
