# Article Study Flow

A small, local AI-assisted reading workflow built through iterative prompting, implementation, and testing in Codex. Import a spreadsheet of article URLs, generate concise study notes, review evidence, and download shareable HTML or Markdown. No Python packages, API keys, or cloud accounts required for the app.

## Quick start

Requires Python 3.10+.

```sh
git clone https://github.com/sydneyhart/article-study-flow.git
cd article-study-flow
python3 app.py
```

Open **http://127.0.0.1:8765**. Click **Load example readings**, then **Generate study notes** for an immediate offline demo. The demo is deterministic sentence extraction, clearly labeled **not AI**.

For actual AI summaries, install [Ollama](https://ollama.com/download), start it, and pull a local model:

```sh
ollama pull llama3.2:3b
ollama serve
```

If the Ollama desktop app is already serving, do not run another server. Enter your installed local model name in the app and uncheck **Offline extractive demo**. Use local model weights, not Ollama cloud models. Hardware, speed, and model quality vary; the model must support structured output. The integration follows the [Ollama chat API](https://docs.ollama.com/api/chat) with a JSON schema and streaming disabled.

## Weekly workflow

1. Make a reading list in Excel or Google Sheets. Export as **CSV UTF-8**.
2. Include a required `url` column. Optional columns: `title`, `text`, `sensitive`.
3. Import the CSV or paste its contents. Blank URLs are ignored; duplicate URLs are processed once. Batches allow 1–25 unique URLs.
4. Provide article text directly, or explicitly enable public HTTPS retrieval. Supplied text takes precedence. HTML page titles are used when the spreadsheet title is empty; otherwise the URL is the fallback label.
5. Generate notes and review each result. One failed reading does not stop the rest. Retry failed rows in another batch after fixing their source or text.
6. Download HTML or Markdown. Share HTML directly, open it in a browser and print to PDF, or upload the HTML to Google Drive and open with Google Docs. There is no automatic cloud upload.

Every summary uses **Title → Main idea → Supporting points → Evidence → Conclusions → Takeaways**, with 1–3 bullets per section and a maximum of 55 words per bullet. Evidence must be an exact source excerpt or `Not reported in supplied text.` Invalid model output is rejected. This verifies excerpt presence, not the truth or relevance of a claim. Check drafts against original sources before citing them.

The model is instructed to treat article contents as untrusted data, use only provided information, distinguish association from causation, and identify absent information. It has no tools or execution permissions. Prompt injection and hallucinations cannot be completely eliminated; human review remains essential.

## Test dataset

`data/readings.csv` contains four original **fictional** mini articles: retrieval practice, urban trees and heat, screen use and sleep, and seminar discussion. They cover quantitative findings, observational limitations, and an article without numerical evidence. The `example.org` URLs are identifiers, not real research links. Embedded text makes tests independent of websites. Regenerate with:

```sh
python3 data/generate_fixture.py
```

For real readings, replace the rows with public article URLs or text you are authorized to process. This app does not bypass paywalls, logins, or robots restrictions. Check the source site's terms before retrieval.

## Privacy and limits

- The app binds only to `127.0.0.1`; it has no analytics, content logs, database, or browser storage. Clear session removes visible content and download links; stopping the app ends server memory. This is not secure erasure from OS memory, downloaded files, or an externally configured model runtime.
- Article text goes only to the fixed local Ollama endpoint, `127.0.0.1:11434`. Configure Ollama to use local inference and review its own logging/retention settings. This app cannot control another program's configuration.
- Public URL retrieval contacts the publisher and DNS resolver, exposing requested URLs and your network address. It is off by default. Mark sensitive rows `yes`, `true`, or `1` and paste their text: those rows are never fetched remotely, even if retrieval is enabled. Keep their titles and URLs free of secrets.
- Downloads stay on your device until you choose to share them. Importing into Google Docs sends them to Google. Check permissions and institutional requirements first. Never commit private readings or exports to this public repository.
- HTTPS retrieval validates certificates, pins a validated public IP, blocks local/private addresses and credentials, and revalidates redirects. Same-origin and Host checks protect the local app against ordinary cross-site requests and DNS rebinding.
- Uploads and retrieved responses are limited to 2 MB. AI input is limited to 40,000 characters and a minimum of 40 words; oversized text is rejected rather than silently truncated. Longer articles need splitting into separate readings. Local model context limits may be smaller: review the model configuration.
- Only static HTML and plain text are supported. For PDF, paywalled, scanned, or JavaScript-only sources, paste authorized article text into the CSV. Page boilerplate can remain after extraction; supply clean text when it affects quality.
- Processing is sequential; a model call can take up to 180 seconds per article. This is a personal local tool, not a multi-user hosted service.

## Testing

```sh
python3 -m unittest discover -s tests -v
```

See [TESTING.md](TESTING.md) for observed results and limitations. GitHub Actions runs the same suite on Python 3.12.

## Vibe-coding process

The natural-language brief was converted into a lightweight browser interface and a Python standard-library backend. Iterations added an offline fixture, schema checks, source-excerpt verification, safe retrieval, and privacy controls. Tests caught an environment network restriction and a macOS Python certificate-bundle issue; the latter was fixed by loading the system CA bundle without disabling verification. The interface was exercised through a browser to confirm the four-reading demo and export controls.

Useful follow-up prompts: “Add PDF text extraction with page citations,” “Add a review checkbox before exports,” or “Add a persistent weekly queue stored only on my device.”
