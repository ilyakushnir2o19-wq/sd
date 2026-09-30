# Service Booking Showroom

A sales-first clone of the SGX "24 hours of vibecoding" mechanic.

The goal is not to pitch development. The prospect opens a URL that already
looks like their own branded booking app.

## Demo URLs

- `/showroom/?tenant=graphite`
- `/showroom/?tenant=voltage`

A tenant is one JSON file in `tenants/<slug>.json`. The UI, booking flow and
AI demo are shared.

## Why it is deliberately client-side first

Cold outreach needs a convincing branded demo before the prospect has granted
credentials or access. This preview contains no real bookings, notifications,
payments or customer data. A sold tenant can later be promoted to the Supabase
runtime described in the SGX implementation plan.

## Design rules carried over from the source material

- dark, mobile-first application rather than a landing page;
- one business-specific accent color;
- photography does most of the visual selling;
- dense but calm surfaces with large radii and quiet borders;
- booking path opens in bottom sheets instead of page hops;
- safe-area aware bottom navigation;
- every visible button in the preview does something;
- clear preview language: do not pretend demo booking/AI/push is live.
