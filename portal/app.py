import os
from urllib.parse import urlsplit
from flask import Flask, render_template, redirect, jsonify, abort

app = Flask(__name__)

def public_url(env, fallback):
    value = os.getenv(env, fallback).strip().rstrip('/')
    parts = urlsplit(value)
    if parts.scheme not in ('http','https') or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('','/'):
        raise ValueError(f'{env} must be an absolute http(s) origin, without paths or credentials')
    return value

def destinations():
    return {
        'store': public_url('OWL_STORE_URL','https://owldigital.shop'),
        'finance': public_url('OWL_FINANCE_URL','https://finance.example.com'),
    }

@app.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    resp.headers['X-Frame-Options']='DENY'
    resp.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    return resp

@app.get('/')
def home():
    return render_template('index.html', urls=destinations())

@app.get('/open/<service>')
def open_service(service):
    urls=destinations()
    if service not in urls:abort(404)
    return redirect(urls[service], code=302)

@app.get('/health')
def health():
    return jsonify(status='ok', application='owl-unified-portal')

if __name__=='__main__':
    app.run(port=int(os.getenv('PORT','10000')),host='0.0.0.0')
