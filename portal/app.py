"""OWL Unified path-prefix reverse proxy. Does not access either database."""
import os
import re
from urllib.parse import urlsplit, urljoin
import httpx
from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)
ORIGINS = {'store': os.getenv('OWL_STORE_URL', 'https://owldigital.shop').rstrip('/'), 'finance': os.getenv('OWL_FINANCE_URL', 'https://owlfinance.shop').rstrip('/')}
for key, origin in ORIGINS.items():
    p = urlsplit(origin)
    if p.scheme != 'https' or not p.hostname or p.path not in ('', '/') or p.username or p.password or p.query or p.fragment:
        raise RuntimeError(f'Invalid {key} upstream URL')

@app.get('/')
def home():
    return render_template('index.html')

@app.get('/health')
def health():
    return jsonify(status='ok', service='owl-unified-gateway')

def rewrite_url(value, key):
    origin = ORIGINS[key]
    p = urlsplit(value)
    if p.scheme and p.netloc:
        if p.scheme in ('http', 'https') and p.netloc.lower() == urlsplit(origin).netloc.lower():
            return '/' + key + (p.path if p.path.startswith('/') else '/' + p.path) + (('?' + p.query) if p.query else '') + (('#' + p.fragment) if p.fragment else '')
        return value
    if value.startswith('//'):
        return rewrite_url('https:' + value, key)
    if value.startswith('/') and not value.startswith('/' + key + '/'):
        return '/' + key + value
    return value

def rewrite_html(html, key):
    # Handles conventional absolute-root links and form actions. Complex JS-generated URLs may need upstream code changes.
    html = re.sub(r'(?i)(\b(?:href|src|action|poster|data-url)\s*=\s*["\'])([^"\']+)(["\'])', lambda m: m.group(1) + rewrite_url(m.group(2), key) + m.group(3), html)
    html = re.sub(r'(?i)(\burl\(\s*["\']?)(/[^)"\']+)(["\']?\s*\))', lambda m: m.group(1) + rewrite_url(m.group(2), key) + m.group(3), html)
    return html

HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade', 'host', 'content-length', 'accept-encoding'}

@app.route('/<service>/', defaults={'path': ''}, methods=['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'])
@app.route('/<service>/<path:path>', methods=['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'])
def proxy(service, path):
    if service not in ORIGINS:
        return ('Not found', 404)
    origin = ORIGINS[service]
    target = origin + '/' + path
    headers = {k: v for k, v in request.headers if k.lower() not in HOP and k.lower() not in {'cookie', 'origin', 'referer'}}
    headers['X-Forwarded-Host'] = request.host
    headers['X-Forwarded-Prefix'] = '/' + service
    headers['X-Forwarded-Proto'] = request.scheme
    headers['Origin'] = origin if request.headers.get('Origin') else headers.get('Origin', '')
    headers.pop('Origin', None) if not request.headers.get('Origin') else None
    if request.headers.get('Referer'):
        headers['Referer'] = origin + '/' + path
    # Prefix-specific cookie names are passed upstream with their original names.
    cookie_parts = []
    for name, value in request.cookies.items():
        prefix = service + '__'
        if name.startswith(prefix):
            cookie_parts.append(name[len(prefix):] + '=' + value)
    if cookie_parts:
        headers['Cookie'] = '; '.join(cookie_parts)
    try:
        with httpx.Client(timeout=45, follow_redirects=False, trust_env=True) as client:
            upstream = client.request(request.method, target, params=request.query_string.decode('latin1'), content=request.get_data(), headers=headers)
    except httpx.HTTPError:
        return ('Upstream service unavailable', 502)
    content = upstream.content
    ctype = upstream.headers.get('content-type', '')
    if 'text/html' in ctype:
        charset = upstream.encoding or 'utf-8'
        content = rewrite_html(upstream.text, service).encode(charset, errors='replace')
    response = Response(content, status=upstream.status_code)
    excluded = HOP | {'content-encoding', 'content-security-policy', 'x-frame-options', 'set-cookie', 'location', 'content-length'}
    for name, value in upstream.headers.multi_items():
        if name.lower() not in excluded:
            response.headers.add(name, value)
    if upstream.headers.get('location'):
        response.headers['Location'] = rewrite_url(upstream.headers['location'], service)
    for cookie in upstream.headers.get_list('set-cookie'):
        # Prefix cookie names and force their Path to the service path to avoid session collisions.
        match = re.match(r'([^=;\s]+)=', cookie)
        if not match:
            continue
        cookie = service + '__' + cookie
        cookie = re.sub(r'(?i);\s*domain=[^;]*', '', cookie)
        cookie = re.sub(r'(?i);\s*path=[^;]*', '', cookie)
        cookie += '; Path=/' + service + '/'
        response.headers.add('Set-Cookie', cookie)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '10000')))
