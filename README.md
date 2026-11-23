# OWL Unified — safe three-service integration

This package contains the two **unchanged source applications** from the supplied ZIPs, plus a **new standalone portal**. It does not combine or migrate databases, create shared authentication, or proxy sensitive customer/payment flows. The original applications continue running on their existing Render services and domains.

## Included
- `portal/`: new responsive Flask portal and deployment manifest
- `original-projects/OWL-STORE-Phase8/`: supplied billing project, source unchanged (Python caches excluded)
- `original-projects/OWL-FINANCE-7.0.1/`: supplied finance project, source unchanged (Python caches excluded)
- `render.yaml`: Render Blueprint for **only** the new portal

## Deploy the portal on Render
1. Extract ZIP and push the contents to a **new private GitHub repository**. Do not replace either existing app repository.
2. In Render choose **New > Blueprint** and connect this new repo. The root `render.yaml` creates **owl-unified-portal only**. (Alternatively, create a Python web service with root directory `portal`, build command `pip install -r requirements.txt`, start command `gunicorn app:app --bind 0.0.0.0:$PORT`.)
3. Set `OWL_STORE_URL` to the actual public root URL of the existing store (default `https://owldigital.shop`). Set `OWL_FINANCE_URL` to the **existing** public root URL of the finance app. Both must be HTTPS origins, no path or trailing query.
4. Deploy. Test `/health`, both buttons, original logins, existing customer routes, and payment webhook deliveries **on the original applications**.
5. Once a domain is purchased, open the new portal service in Render > Settings > Custom Domains. Add the new hostname, then add the DNS record Render specifies at the domain registrar. Do **not** alter DNS for the two existing websites.

## Database & payments
- The portal has **no database** and **no payment credentials**.
- Keep each existing app's `DATABASE_URL`, `SECRET_KEY`, Cashfree keys, KYC encryption key, upload disk, and webhook URLs in its **existing Render service**. Do not copy secrets into the portal.
- Never point both apps to the same database, run one app's migrations against the other database, or repoint Cashfree webhooks to the portal.
- The finance ZIP contains a persistent upload disk configuration; preserve it in the original finance deployment.
- The portal is an **access hub**, not an embedded iframe or single-sign-on system. Each existing app maintains its own sessions. This design avoids breaking authentication, cross-site cookies, payment redirects, and frame restrictions.

## Smoke tests
`cd portal && pip install -r requirements.txt && python -m unittest discover -s tests -v`

## Domain not chosen yet
Use the Render-provided `onrender.com` hostname until a new domain is selected. No new domain purchase is included.
