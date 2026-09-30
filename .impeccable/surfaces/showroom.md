# Showroom — visual direction contract

## Product truth

This surface is not a marketing landing page. It is a believable mobile booking
application that is pre-branded for one real auto service/detailing business
before outreach.

The first cold-contact impression should be: "this is already my app", not
"someone generated a concept for me".

Primary flow:
1. See the business identity and current booking state.
2. Choose a real service.
3. Choose date/time.
4. Confirm contact/car details.
5. Understand what the client receives.
6. Optionally inspect the owner-facing experience.

## Direction

- App-first, not website-in-a-phone.
- Utility-led with strong photography where the business actually has strong photos.
- Dark is allowed, but avoid default AI "premium dark": no neon glow language,
  gratuitous glass, ambient blobs, or acid accents everywhere.
- Brand styling must come from the prospect's actual identity when possible.
- Use fewer containers. Prefer lists, dividers, whitespace, typography and image
  composition over stacks of rounded cards.
- Radius is contextual, not a global personality. Do not round every surface.
- Typography should have character appropriate to automotive/service contexts;
  do not default to Inter everywhere merely because it is available.
- Icons should feel product-specific and consistent, not like an untouched
  generic developer icon pack.
- Motion should communicate state/continuity, not decorate.

## AI-slop blacklist

Do not introduce:
- nested cards or "card for every thought";
- floating AI sparkle button as a default visual trope;
- purple/blue or acid-on-black gradients just to signal technology;
- glow, glassmorphism, grain, bento, pills, badges, or stats without product need;
- giant landing-page headline occupying the useful first viewport;
- fake dashboards, fake metrics, fake social proof, or fake urgency;
- excessive micro-labels/uppercase tracking;
- identical 20–30px radii everywhere;
- generic copy such as "seamless", "smart", "next-gen", "premium experience";
- decorative UI that competes with booking.

## Quality gate

Before a showroom build is approved:
1. Run an Impeccable critique/audit/polish pass.
2. Run the gpt-taste/redesign rules against the rendered mobile screenshot.
3. Compare against at least one real automotive/service app reference or a
   deliberately generated image-first reference.
4. Ask: could this exact screen be sent to ten unrelated businesses by only
   swapping the logo and accent color? If yes, personalization is insufficient.
5. Ask: does the first viewport look like a functioning app or a portfolio hero?
   If it looks like a portfolio hero, redesign it.
6. Browser-render at a normal phone viewport and inspect the screenshot manually.
