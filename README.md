# OWL Unified 2.0 — Same-domain gateway

A new independent Flask reverse-proxy portal for the two *already deployed* services:
- OWL STORE: https://owldigital.shop (available at `/store/`)
- OWL FINANCE: https://owlfinance.shop (available at `/finance/`)

The original source snapshots are bundled for reference only. Deploy only `portal/` as a new Render Web Service. Do not replace or delete either original service or database. The gateway stores no business data.

## Render Web Service settings

- Root Directory: `portal`
- Runtime: Python
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2`
- Health check: `/health`
- `OWL_STORE_URL=https://owldigital.shop`
- `OWL_FINANCE_URL=https://owlfinance.shop`
- Optionally set `PYTHON_VERSION=3.11.11`

Upload all extracted files to a *new private GitHub repository*. In Render choose New > Web Service, connect that repository, enter the settings above, then deploy. Add the custom domain later under Settings > Custom Domains. No database URL or payment credentials are required in this portal.

## Limitations / security notes

This is a path-prefix HTTP proxy, not an embedded copy of the apps. It rewrites common HTML links, form actions, redirects and cookies, but cannot reliably rewrite arbitrary JavaScript-generated absolute paths, WebSocket connections, service workers, or all CSS/JS API endpoints. Upstream applications may require explicit URL-prefix support and configuration changes for complete same-domain navigation.

Payment providers (including Cashfree), OAuth callbacks, cross-origin authentication, CSRF checks, and webhook URLs must be verified separately. Keep existing payment/webhook URLs intact until end-to-end tests pass. A payment provider's external checkout may necessarily navigate to its own domain.

The gateway intentionally strips upstream CSP and X-Frame-Options headers because it is serving proxied content on a different origin. This may weaken upstream protections. Before production use, audit and apply appropriate CSP, CSRF, origin validation, rate limiting and security headers for both apps. Do not treat this gateway as production-validated until login, logout, form submission, session isolation, asset loading, KYC and payment flows have been tested.

The gateway forwards user requests to the two public production origins, rather than connecting directly to either database. Original websites continue to work independently.


## 2.1 compatibility improvements and limitations

This revision rewrites root-relative JavaScript string URLs and upstream-origin links in HTML, in addition to HTML attributes, Location headers and cookies. It is **not** a guarantee of full application compatibility. External Cashfree hosted checkout pages, provider redirects, CSP, WebSockets, JavaScript-generated absolute URLs, API JSON URLs, cookie SameSite policies and payment callbacks may require changes in the original application services.

Test `/store/` and `/finance/` using browser developer tools, and verify the address bar after login, navigation, API requests and payment returns. If the browser still redirects, capture the Network tab's first 30x response and its `Location` header. The definitive production solution is to make both original Flask apps prefix-aware and redeploy each with its **existing** DATABASE_URL, without database migrations.
