"""One WSGI service hosting both original Flask apps with isolated DBs and sessions."""
import importlib.util
import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, redirect
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT = Path(__file__).resolve().parent

def load_app(name, env_prefix):
    folder = ROOT / name
    required = {'DATABASE_URL': f'{env_prefix}_DATABASE_URL', 'SECRET_KEY': f'{env_prefix}_SECRET_KEY'}
    missing = [source for source in required.values() if not os.environ.get(source)]
    if missing:
        raise RuntimeError(f'Missing required {name} variables: {", ".join(missing)}')
    # Imports happen serially, under each application's original env variable names.
    previous = dict(os.environ)
    try:
        for key in ('DATABASE_URL', 'SECRET_KEY', 'ADMIN_EMAIL', 'ADMIN_USERNAME', 'ADMIN_PASSWORD',
                    'CASHFREE_ENV', 'CASHFREE_CLIENT_ID', 'CASHFREE_CLIENT_SECRET',
                    'CASHFREE_SECRET_KEY', 'CASHFREE_APP_ID', 'PUBLIC_BASE_URL',
                    'KYC_ENCRYPTION_KEY', 'UPLOAD_DIR', 'COOKIE_SECURE', 'UPI_ID', 'UPI_NAME',
                    'LIVE_LENDING_ENABLED', 'MAX_UPLOAD_MB', 'PUBLIC_PHONE_LOOKUP_ENABLED'):
            val = os.environ.get(f'{env_prefix}_{key}')
            if val is not None:
                os.environ[key] = val
            else:
                os.environ.pop(key, None)
        # finance/enterprise.py imports as top-level 'enterprise'. Ensure finance is on sys.path.
        sys.path.insert(0, str(folder))
        spec = importlib.util.spec_from_file_location(f'owl_{name}_app', folder / 'app.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        app = module.app
        app.config['SESSION_COOKIE_NAME'] = f'owl_{name}_session'
        app.config['SESSION_COOKIE_PATH'] = f'/{name}'
        app.config['APPLICATION_ROOT'] = f'/{name}'
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        # Maintain isolated environment reads made inside the original application after import.
        class AppOS:
            path = os.path
            environ = None
            def __init__(self):
                self.environ = dict(os.environ)
            def getenv(self, key, default=None):
                return self.environ.get(key, default)
            def __getattr__(self, key):
                return getattr(os, key)
        module.os = AppOS()
        # enterprise.py is finance-specific and reads process env during requests.
        if name == 'finance' and 'enterprise' in sys.modules:
            sys.modules['enterprise'].os = module.os
        return app
    finally:
        os.environ.clear()
        os.environ.update(previous)
        if sys.path[0] == str(folder):
            sys.path.pop(0)

store = load_app('store', 'STORE')
finance = load_app('finance', 'FINANCE')

landing = Flask(__name__)
landing.secret_key = os.environ.get('PORTAL_SECRET_KEY', os.urandom(32))
@landing.route('/')
def home():
    return render_template_string("""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OWL Unified</title><style>body{margin:0;background:#0c1425;color:#f3f6ff;font-family:system-ui;display:grid;place-items:center;min-height:100vh}main{max-width:850px;padding:32px}h1{font-size:clamp(30px,5vw,52px)}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}a{display:block;padding:32px;border:1px solid #36445e;border-radius:20px;background:#17243c;color:white;text-decoration:none;font-size:24px;font-weight:bold}a:hover{background:#253958}small{display:block;color:#b8c5df;font-size:14px;font-weight:normal;margin-top:12px}</style></head><body><main><h1>🦉 OWL Unified</h1><p>One website. Two independent systems.</p><section><a href="/store/">OWL STORE<small>Billing · Terminal · Cashfree · Customers</small></a><a href="/finance/">OWL FINANCE<small>Loans · KYC · Branches · Staff</small></a></section></main></body></html>""")

# Flask routes remain the original routes. DispatcherMiddleware sets SCRIPT_NAME
# to /store or /finance, so url_for() generates prefixed URLs automatically.
application = ProxyFix(DispatcherMiddleware(landing, {'/store': store, '/finance': finance}), x_for=1, x_proto=1, x_host=1)
app = application
