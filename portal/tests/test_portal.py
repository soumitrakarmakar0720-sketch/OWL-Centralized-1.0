from app import app, rewrite_url, rewrite_html

def test_home():
    with app.test_client() as c:
        r = c.get('/')
        assert r.status_code == 200
        assert b'/store/' in r.data and b'/finance/' in r.data

def test_health():
    with app.test_client() as c:
        assert c.get('/health').json['status'] == 'ok'

def test_rewrite():
    assert rewrite_url('/login', 'finance') == '/finance/login'
    assert rewrite_url('https://owlfinance.shop/login', 'finance') == '/finance/login'
    assert 'href="/store/static/x.css"' in rewrite_html('<a href="/static/x.css">', 'store')
