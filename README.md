# OWL Unified Native 3.0 — single codebase, single Render web service

Both original Flask applications are bundled **as executable code**, not linked or reverse-proxied. The root homepage mounts them at `/store/` and `/finance/` using Werkzeug DispatcherMiddleware. Both use the **same existing external database URLs** as their standalone deployments. Never create new databases or run destructive migrations.

## Render Web Service
- New private GitHub repository: upload the *contents* of this ZIP to repository root.
- Root Directory: **blank**
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`
- Python 3.11.11. Deploy a **new service**; leave existing services running.

## Environment variables
Copy values from each original service, **adding prefixes** to avoid collisions:

Store: `STORE_DATABASE_URL`, `STORE_SECRET_KEY`, `STORE_COOKIE_SECURE=1`, `STORE_ADMIN_USERNAME`, `STORE_ADMIN_PASSWORD`, `STORE_UPI_ID`, `STORE_UPI_NAME`, `STORE_CASHFREE_ENV`, `STORE_CASHFREE_CLIENT_ID`, `STORE_CASHFREE_CLIENT_SECRET`.

Finance: `FINANCE_DATABASE_URL`, `FINANCE_SECRET_KEY`, `FINANCE_ADMIN_EMAIL`, `FINANCE_ADMIN_PASSWORD`, `FINANCE_KYC_ENCRYPTION_KEY`, `FINANCE_CASHFREE_ENV`, `FINANCE_CASHFREE_CLIENT_ID`, `FINANCE_CASHFREE_APP_ID`, `FINANCE_CASHFREE_SECRET_KEY`, `FINANCE_PUBLIC_BASE_URL=https://YOUR-UNIFIED-DOMAIN/finance`, `FINANCE_UPLOAD_DIR`, `FINANCE_LIVE_LENDING_ENABLED`, `FINANCE_PUBLIC_PHONE_LOOKUP_ENABLED`.

Store's `STORE_DATABASE_URL` and Finance's `FINANCE_DATABASE_URL` **must match their original services' DB connection strings**. Keep encryption keys unchanged or existing encrypted KYC data may be unreadable. **Do not paste secret values into chat.**

## Caveats / testing required
- This is a genuine combined Python/Flask deployment, not a gateway. The original code is preserved under `store/` and `finance/`.
- Internal Flask `url_for` links are automatically prefixed. **Hardcoded absolute paths in templates, JS, fetch calls, forms, or redirects may still need subpath fixes.**
- Both source apps perform DB initialization at import time. Confirm schema compatibility and backup databases before deploying; this package has NOT been run against production databases.
- Finance's local upload files will NOT be shared between separate Render services. Use shared object storage or persistent storage strategy for uploaded KYC documents.
- Cashfree webhook endpoints and return URLs require explicit validation; maintain old webhook endpoints until unified routes are tested. If both sites receive the same webhook, confirm idempotency.
- Running two instances against the same DB requires checking any startup bootstrap, background jobs, and schema changes.
- Test all login flows, assets, CRUD, PDFs, payment callbacks, staff/branch and KYC before production.
