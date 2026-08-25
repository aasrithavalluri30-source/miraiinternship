# Vibe Shelf — Technical Design Document

This document explains *how* Vibe Shelf works internally: how data moves through the system, how it talks to Gemini, and how the codebase is organized into logic modules. For feature descriptions and setup instructions, see [`README.md`](./README.md).

---

## 1. System Overview

Vibe Shelf is a single-file Streamlit app (`app.py`) with three pages sharing one `st.session_state` store:

| Page | Purpose |
|---|---|
| **Matchmaker** | Multimodal input (text / image / audio) → Gemini → 3 verified book recommendations |
| **My Books** | Personal shelf: add, rate, review, and bulk-edit saved books |
| **Book Chat** | Open-ended conversation grounded in your saved shelf |

All three pages read from and write to the same `st.session_state.books` list, so a book added on any page is immediately visible everywhere else — there is one shelf, not three separate data stores.

---

## 2. Data Flow

### 2.1 Matchmaker flow (the core feature)

```
User fills st.form (mood text / genre / tropes / pacing / tone)
        │
        ├── optional: uploads moodboard image → st.file_uploader → raw bytes
        │
        └── optional: records voice note → st.audio_input → raw bytes
                            │
                            ▼
                  transcribe_audio(client, audio_bytes)
                            │
                            ▼
                  visible transcript (shown back to user before sending)
        │
        ▼
On form submit → recommend_books(...)
        │
        ▼
Prompt is assembled as one f-string containing:
  - genre + description
  - custom genre blend (if any)
  - mood text
  - voice transcript (if any)
  - trope list
  - pacing/tone sliders (1–10)
  - three explicit rule blocks (see §3.2)
        │
        ▼
client.models.generate_content(
    model=model_name(),
    contents=[prompt_text, PIL.Image (if uploaded), audio Part (if recorded)],
    config=GenerateContentConfig(temperature=0.2, response_mime_type="application/json")
)
        │
        ▼
extract_json(response.text)      # strips markdown fences, finds the JSON array/object
        │
        ▼
_looks_like_leaked_reasoning()   # filters out any book object containing
        │                          self-correction language ("wait,", "let me verify", etc.)
        ▼
st.session_state.matches = clean list of up to 3 book objects
        │
        ▼
render_result_card() for each match → book-card UI + "Add to My Books" button
        │
        ▼ (on click)
add_book() → appends to st.session_state.books
        │
        ▼
record_session_event() → logged to st.session_state.session_history
```

**Why the transcript is shown back to the user before submission:** it lets the reader correct a bad transcription before it becomes part of the prompt, and it makes the multimodal signal auditable rather than a black box.

### 2.2 My Books flow

```
st.form (title/author) → add_book() → st.session_state.books
        │
        ▼
Two synchronized views of the same data:
  1. Cover-card grid (visual, one card per book, inline rating slider + review box)
  2. st.data_editor table (bulk-edit chapter/rating/review across all books at once)
        │
        ▼
Any edit in either view writes back into the same st.session_state.books list —
there is no separate "draft" state; the UI is a live view over one source of truth.
```

### 2.3 Book Chat flow

```
User types in st.chat_input
        │
        ▼
book_chat_assistant(client, prior_messages, question, assistant_name)
        │
        ├── injects: full list of titles/authors from st.session_state.books
        ├── injects: last 12 messages of conversation history
        └── injects: strict accuracy rules (see §3.3)
        │
        ▼
Single generate_content call → plain text response (not JSON — this page is
conversational, not structured, so free-form text is the correct output shape)
        │
        ▼
Appended to st.session_state.book_chat_messages, rendered as chat bubbles
```

---

## 3. API Integration Strategy

### 3.1 Client initialization and graceful degradation

```python
@st.cache_resource(show_spinner=False)
def get_client():
    if not HAS_GENAI:
        return None
    api_key = next((os.environ.get(name, "") for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if os.environ.get(name, "")), "")
    ...
```

- `HAS_GENAI` is set at import time via a `try/except ImportError`, so the app never crashes on a missing dependency — it just disables AI features and tells the user why (`st.error` / `st.warning` in the sidebar).
-Two environment variable names are checked (GEMINI_API_KEY, GOOGLE_API_KEY) so the app works whether the key was set up via Streamlit Cloud secrets or a more generic Google SDK convention.
- `@st.cache_resource` ensures the client is constructed once per session, not on every rerun — reruns happen constantly in Streamlit (every widget interaction), so this avoids re-authenticating on every keystroke.

### 3.2 Multimodal input, combined into one request

Rather than making separate API calls per input type, all signals are assembled into a single `contents` list passed to one `generate_content` call:

```python
parts = [prompt_text]
if image_bytes: parts.append(PIL.Image.open(...))
if audio_bytes: parts.append(types.Part.from_bytes(data=audio_bytes, mime_type=...))
```

This lets Gemini reason over text, image, and audio context *together* in one pass, rather than trying to merge three independent, disconnected answers after the fact.

### 3.3 Structured, constrained, and self-checked output

Three separate techniques work together to keep Matchmaker's output trustworthy:

1. **JSON-mode enforcement** — `response_mime_type="application/json"` forces the model to return parseable JSON, not prose that has to be regex-scraped.
2. **A three-tier rule hierarchy inside the prompt itself:**
   - *Rule 1 (highest priority):* if the reader names a specific element (vampires, a heist, a specific setting), every returned book **must** contain that element — this overrides "originality."
   - *Rule 2:* among books that already satisfy Rule 1, prefer atmospheric/specific matches over the single most generic bestseller guess.
   - *Rule 3:* no fabrication — real books only, and return fewer than 3 rather than padding with a mismatch.
3. **Self-check instruction + a second-pass code filter** — the prompt asks the model to silently verify each book against the reader's stated elements before answering. As a backstop (models don't always follow "silent" instructions perfectly), `_looks_like_leaked_reasoning()` scans every returned field for tell-tale self-correction phrases (`"wait,"`, `"let me verify"`, `"actually,"`, etc.) and drops any book object that contains them — so even if the model's internal verification leaks into the output, it never reaches the UI.

`temperature=0.2` is deliberately low for this call — this is a constraint-following, factual-retrieval task, not a creative one, so the model is kept close to its most confident answer rather than encouraged to explore.

### 3.4 Spoiler-safety in Book Chat's cousin feature, and factual guardrails in Book Chat

Book Chat's prompt includes an explicit accuracy contract: verify character/book identities silently before answering, never merge details from similarly-named books, and say *"I'm not certain enough to state that as fact"* rather than inventing a plausible-sounding answer. This is a prompt-level guardrail (not code-enforced like §3.3), appropriate here since Book Chat's output is conversational prose, not parseable structured data.

### 3.5 Error handling

Every AI-calling function is wrapped in `try/except` at the call site (in the page-render functions, not inside the helper functions themselves) so a failed or slow API call surfaces as an `st.error()` message with the actual exception text, rather than crashing the whole app with a traceback.

---

## 4. Logic Modules

| Function | Responsibility |
|---|---|
| `get_client()` | Lazily constructs and caches the Gemini client; returns `None` if unavailable |
| `extract_json(text)` | Strips markdown code fences and locates the JSON payload even if the model wraps it in extra text |
| `safe_hex_color(value, fallback)` | Validates any user-supplied color against a strict 6-digit hex regex before it's allowed into raw CSS — prevents malformed or malicious input from breaking page styling |
| `apply_mood_background(color, ...)` | Injects a validated color as a CSS radial-gradient tint over the page background |
| `mood_color_control(label, state_key, default)` | Renders the preset/custom color picker UI and keeps its value synced in `st.session_state` |
| `_looks_like_leaked_reasoning(value)` | Recursively scans a book object's fields for self-correction language; used to filter Matchmaker results |
| `transcribe_audio(client, audio_bytes, audio_type)` | Sends a recorded voice note to Gemini and returns the plain-text transcript |
| `recommend_books(...)` | Builds the constrained prompt, sends the multimodal request, parses and filters the response — the core of Matchmaker |
| `story_assistant(...)` | (Story Desk feature) Answers questions about a saved book without crossing the reader's current chapter |
| `book_chat_assistant(...)` | Builds context (saved shelf + recent transcript) and sends a single conversational turn to Gemini |
| `add_book()` / `remove_book()` | Mutate `st.session_state.books`, handling duplicate-title updates and keeping `active_book_index` valid after a removal |
| `record_session_event()` | Appends a capped (last 30) activity log entry to `st.session_state.session_history` |
| `render_result_card()`, `render_matchmaker()`, `render_my_books()`, `render_book_chat()`, `render_sidebar()` | Page/component rendering — pure UI, no business logic |

---

## 5. State Management Design

Everything lives in `st.session_state`, initialized once near the bottom of the file with a block of `if "key" not in st.session_state:` checks. Key design choices:

- **One shelf, not per-page copies.** `books` is a single list referenced by all three pages — avoids the "which copy is the source of truth" bug class entirely.
- **Widget/state key separation for Matchmaker.** Form widgets use private keys (`_match_genre`, `_match_mood`, etc.) that get synced into durable state keys (`match_genre`, `match_mood`) via `sync_matchmaker_state()`. This is needed because Streamlit form widget values reset on certain navigation events; the durable copies survive page switches.
- **`st.fragment` with a fallback.** `render_session_history_fragment()` uses `st.fragment` when available (isolates reruns to just that panel for a snappier feel) and silently falls back to a plain function call on older Streamlit versions via `_fragment_decorator = st.fragment if hasattr(st, "fragment") else (lambda f: f)`.
- **Callback-based clearing, not manual rerun logic.** The "Clear session history" button uses `on_click=_clear_session_history_callback` rather than checking the button's return value and calling `st.rerun()` manually — callbacks run *before* the rerun Streamlit already triggers on a button click, which is more reliable across Streamlit versions than hand-rolled rerun timing.

---

## 6. Security Considerations

- **CSS injection prevention:** any user-controlled value that ends up inside a `<style>` block (mood colors) is validated with `safe_hex_color()` against `#[0-9a-fA-F]{6}` before use — an invalid or malicious string silently falls back to a safe default instead of being injected raw.
- **HTML escaping:** all user-supplied text rendered inside custom HTML (book titles, authors, reviews, chat messages) is passed through `html.escape()` before interpolation, preventing HTML/script injection into the rendered page.
- **No API key exposure:** the key is read from environment variables only, never rendered, logged, or echoed back in any UI element.

---

## 7. Known Limitations / Future Extensions

- Book data is session-only (no database) — closing the browser tab loses the shelf. A persistence layer (SQLite, or the same key-value storage pattern used elsewhere in this project set) would be the natural next step.
- `recommend_books()` currently returns exactly 3 matches by design; a "show more" pagination flow would require a second, differently-prompted call rather than just slicing a longer list, since the model is only asked for 3.
- Story Desk (`story_assistant`) exists in the codebase but is not currently wired into the sidebar navigation — it's reachable only via direct function call, not through the UI.
