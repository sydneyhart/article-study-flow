# Testing results — October 28, 2026

## Passed

- **14/14 automated tests**, Python 3.14.6, macOS. Command: `python3 -m unittest discover -s tests -v`.
- Four fictional readings produced **4 successful summaries, 0 errors** in the browser's offline demo. All five summary sections and article titles appeared; Markdown and HTML download controls were available.
- End-to-end HTTP test submits the full CSV to the app and verifies four results plus both export payloads.
- Live HTTPS retrieval of `https://www.python.org/doc/essays/blurb/`: **2,054 extracted characters**, containing Python. This is a retrieval smoke test, not a model-quality evaluation.
- Tests cover quoted CSV cells, UTF-8 BOM, blank/duplicate URLs, batch limits, missing headers, sensitive-row retrieval prevention, explicit retrieval opt-in, private network blocking, redirect revalidation, exact-evidence rejection, schema and length checks, malformed model JSON, failed-row isolation, HTML escaping, script removal, same-origin protection, and invalid Host rejection.
- Local AI integration tested with a simulated HTTP response, checking the fixed loopback endpoint, schema, non-streaming request, and validated returned summary.

## Debugging performed

The initial HTTP integration check was blocked by the session's network restrictions. After enabling network access it passed. Live HTTPS retrieval exposed the Python installation's missing default CA bundle; loading the system CA bundle fixed retrieval while preserving certificate and hostname validation. The full automated suite was rerun after this change.

## Not verified

- **No live AI inference or semantic model-quality evaluation**: Ollama and model weights were not installed on this machine. The actual AI route is implemented; the offline demo is not a substitute for live AI testing. Install a local model and use the same fixture to review factual accuracy, limitations, and usefulness before relying on it.
- No automated Google Docs upload: HTML and Markdown are the provided downloadable alternatives. Google Docs import instructions are documented; that cloud import was not performed.
- Browser checks confirmed generated results and download controls; downloads are also checked at the export-payload level. PDF printing and Google Docs conversion were not tested.
- Static retrieval was smoke-tested on one public page; extraction quality varies by publisher. No claims of universal article extraction or guaranteed summary accuracy.
