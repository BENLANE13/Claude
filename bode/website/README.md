# BODE website

`index.html` is the marketing site. It is a single file with no build step.

- Published preview: https://claude.ai/artifact/8rcrd6uA536sNF8PFQaQFU (private until you share it from the page's Share menu)
- To deploy publicly, wrap it in a normal HTML document (`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">` … `</head><body>` … `</body></html>`) and host it on Netlify, Vercel, or GitHub Pages.
- **Waitlist:** the form currently confirms on screen only. To collect signups, replace the comment `// Production: POST to the waitlist endpoint` in the submit handler with a `fetch()` to Formspree, an Airtable form, or a `/v1/waitlist` endpoint on the BODE Link server.
