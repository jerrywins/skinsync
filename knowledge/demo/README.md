# Demo dataset (FICTIONAL)

Everything in this folder is invented for demonstrations and automated tests:
ingredient names, products, brands, prices, rules, evidence and concern mappings.
It is **not science and not real product data**.

* Files carry `fixture: true`; the real knowledge loader refuses them.
* Loaded only by `python -m skinsync.cli seed-demo` when `SKINSYNC_DEMO_MODE=true`.
* Demo products can only be compared with demo products, and every result made from
  this data is labelled "DEMO — fictional, not scientific" in the API and UI.
* Prod configuration refuses to start with demo mode on.
