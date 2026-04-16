# Spending Tracker — Design

## Summary

A personal spending tracker that ingests credit card and bank statements, classifies transactions via the Claude API, and provides monthly spending visibility through a web UI and CLI. Priorities: accuracy, manual correction capability, minimal data sent externally, and low API costs.

## Interaction Modes

- **Web UI** (Flask + HTMX) — primary interface for browsing, reviewing, correcting, and analyzing transactions
- **CLI** — importing statements, managing accounts and categories, quick status checks
- Both share a common `spending` Python package (repository pattern, SQLAlchemy Core)

---

## Data Model

Six tables in SQLite, managed by Alembic migrations.

### accounts

Represents a bank or credit card account that statements are imported from.

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| name | text, unique | e.g. "Chase Visa" |
| institution | text | e.g. "Chase" |
| account_type | text | checking, savings, credit_card |
| created_at | timestamp | |

### imports

One row per imported file. Tracks provenance and import status.

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| account_id | integer FK → accounts | |
| filename | text | original filename |
| file_hash | text | SHA-256 of file contents; exact re-imports rejected |
| imported_at | timestamp | |
| status | text | staging, confirmed, rejected |

### transactions

Raw imported transactions. Immutable after import — corrections are stored separately.

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| import_id | integer FK → imports | |
| account_id | integer FK → accounts | |
| date | date | transaction date |
| amount | decimal | negative for debits, positive for credits |
| raw_description | text | original description from statement |
| fingerprint | text | hash of (date, amount, description, account, sequence) for dedup |
| created_at | timestamp | |

### merchant_cache

Normalized merchant name → category mappings. Populated by Claude API and manual corrections.

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| merchant_name | text, unique | normalized merchant name |
| category | text | from the fixed category list |
| source | text | api, manual |
| created_at | timestamp | |
| updated_at | timestamp | |

### transaction_corrections

Per-transaction overrides layered on top of raw data. All fields nullable — only set what's being overridden.

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| transaction_id | integer FK → transactions, unique | one correction per transaction |
| category | text, nullable | override classification |
| merchant_name | text, nullable | override merchant name |
| notes | text, nullable | |
| created_at | timestamp | |

### categories

Fixed category list, stored in the database (seeded from config).

| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | auto-increment |
| name | text, unique | e.g. "Groceries" |
| sort_order | integer | display ordering |

---

## Resolution Logic

### Resolved Category

Used by all queries, in priority order:

1. `transaction_corrections.category` for this transaction → use it
2. Look up the resolved merchant name in `merchant_cache` → use its category
3. → "Uncategorized"

### Resolved Merchant Name

1. `transaction_corrections.merchant_name` → use it
2. → normalize `transactions.raw_description` via the normalization pipeline

### Derived Transaction Status

Computed from existing data (not stored):

- **corrected** — has a row in `transaction_corrections`
- **uncategorized** — resolved category is "Uncategorized"
- **categorized** — has a resolved category via merchant cache or correction, and import is confirmed

### Category Validation

`merchant_cache.category` and `transaction_corrections.category` are validated at the application layer against `categories.name`. No FK constraint — keeps schema simple.

---

## Merchant Name Normalization

Raw bank descriptions are cleaned before cache lookup or API classification. The normalization pipeline applies these steps in order:

1. Uppercase
2. Strip known prefixes (SQ *, TST *, PAYPAL *, CKE *, SP *, etc.)
3. Strip trailing reference numbers (digits, transaction IDs, location codes)
4. Strip trailing location info (city/state patterns)
5. Collapse whitespace

Rules live in `configs/normalization.yaml` — new patterns added without code changes.

**Examples:**
- `SQ *COFFEE SHOP 8442 CHICAGO IL` → `COFFEE SHOP`
- `AMZN MKTP US*2K7X9` → `AMZN MKTP`
- `PAYPAL *NETFLIX` → `NETFLIX`

Normalization is intentionally lossy. The original description is always preserved in `transactions.raw_description`. Transaction-level merchant name corrections handle edge cases.

---

## Import & Classification Flow

### CLI Import

```
spending import <files...> [--account "NAME"]
```

Accepts multiple files or directories. Auto-detects format (OFX by extension/magic bytes, CSV by institution config match) and account (from file contents or institution config) where possible.

**Pipeline per file:**

1. Check `file_hash` against `imports` — reject exact re-imports
2. Detect format and parse into normalized transaction records
3. Generate fingerprints; auto-dedup against existing confirmed transactions
4. Flag ambiguous potential duplicates for manual review
5. Insert into `transactions` with a new `imports` row in `staging` status
6. Batch all new unique merchant names (not in `merchant_cache`) → single Claude Haiku API call
7. Store API results in `merchant_cache` with `source=api`
8. Print summary and link to web staging review

### Web Import

The Import tab provides a drag-and-drop zone / file picker accepting multiple files. After file selection, a form assigns each file to an account (auto-detected where possible from OFX metadata, dropdown to override or create). Submit triggers the same shared pipeline as the CLI. Results land in the staging review on the same page.

**Inline account creation:** When a file is selected, the first file is sent to `/import/detect-account`. The server parses OFX metadata and returns a pre-filled "Create Account" form. On a fresh database (no accounts), the form is shown expanded. When accounts exist, a collapsed toggle appears. Account creation hits `POST /accounts` and returns the updated account selector with the new account pre-selected.

### Classification API Call

- Send a list of merchant names + the full category list to Claude Haiku
- Only merchant names sent — no amounts, dates, or account info (privacy)
- Prompt asks Claude to return a JSON array of `{merchant_name, category}` pairs
- On API failure or timeout: transactions import as "Uncategorized", corrected in review
- Merchant cache means most future imports hit the API only for new merchants

### Staging Review

Imports land in staging (`import.status = staging`). Not visible in reports until confirmed.

- Import tab shows pending batches, each expandable to its transactions
- Each transaction shows: date, amount, resolved merchant, assigned category, status (new / duplicate-flagged)
- Actions: inline category correction, merchant name correction, dismiss duplicate flags, bulk actions
- "Confirm batch" sets import status to `confirmed`; transactions appear in reports
- "Reject batch" sets import status to `rejected`; transactions are excluded

---

## Deduplication Strategy

Sequence-aware fingerprinting:

- Fingerprint = hash of (date, amount, raw_description, account_id, sequence_number)
- Multiple transactions sharing (date, amount, raw_description) within the same statement get incrementing sequence numbers
- On import, transactions whose fingerprint matches an existing confirmed transaction are auto-skipped
- When fingerprint counts differ between overlapping imports, transactions are flagged for manual review

---

## Manual Corrections

Two levels, stored in the override layer (raw import data is never modified):

### Merchant-Level

Stored in `merchant_cache`. When correcting a transaction's category, user is prompted: "Apply to all transactions from this merchant?" If yes, the merchant cache entry is updated (or created) with `source=manual`. All past and future transactions from that merchant reflect the change.

### Transaction-Level

Stored in `transaction_corrections`. One-off override for a specific transaction's category or merchant name. Takes precedence over the merchant cache for that transaction only.

---

## Web UI

### Navigation

Five tabs, HTMX-swapped content. Tab order: **Monthly** (default) → **Transactions** → **Trends** → **Merchants** → **Import**.

### Monthly Tab (Default)

- Month picker (prev/next arrows + dropdown)
- Category breakdown table: category name, transaction count, month total, trailing 3-month rolling average, above/below-average indicator
- Click a category row → expands to show its transactions inline (HTMX swap)
- Grand total row at bottom

### Transactions Tab

- Sortable table: date, merchant, raw description, category, amount, account, status
- Filter bar: account dropdown, category dropdown, month picker, text search, status filter
- Bulk actions: select rows via checkboxes → re-categorize
- Click a category → inline-edit (prompts for merchant-level correction)
- Click a merchant name → inline-edit (transaction-level correction)

### Trends Tab

- Preset period selector: Quarterly, Year-to-Date, Trailing 12 Months, Annual
- Category table: category name, period total, monthly average, sparkline of monthly values
- Grand total row

### Merchants Tab

- Table: merchant name, assigned category, source (api/manual), transaction count, last seen date
- Inline category editing (merchant-level correction)
- Text search, filter by category or source

### Import Tab

- Drag-and-drop zone / file picker (multiple files)
- Account assignment per file (auto-detect from OFX metadata, with dropdown override and inline create)
- Pending staging batches list, expandable to transaction review
- Per-batch: confirm, reject
- Per-transaction: inline corrections, duplicate flag resolution, bulk actions

---

## CLI Commands

```
spending import <files...> [--account "NAME"]
```
Import statements. Accepts files or directories, auto-detects format and account.

```
spending accounts list
spending accounts add --name "Chase Visa" --institution "Chase" --type credit_card
spending accounts edit <id> --name "..."
spending accounts delete <id>
```
Manage accounts.

```
spending categories list
spending categories add --name "Groceries" --sort-order 5
spending categories edit <id> --name "..."
spending categories delete <id>
```
Manage the category list.

```
spending status
```
Quick summary: current month spending total, top 5 categories, unreviewed transaction count, pending staging batches.

```
spending serve
```
Start the Flask web server.

---

## Input Formats

### OFX/QFX

Parsed with `ofxparse`. Standardized format — one parser handles all institutions. Account info (institution, account type, last 4 digits) extractable from file contents for auto-detection.

### CSV

Per-institution config files in `configs/institutions/`. Each config specifies column mappings (date, amount, description), date format, and optionally the account name. CSV files are matched to an institution config via the `--account` flag or by matching CSV header columns against configs. New institution = new config file, no code change.

### PDF

Out of scope for v1.

---

## Category Taxonomy

A fixed flat list stored in the `categories` table, seeded from `configs/categories.yaml`. Managed via CLI (`spending categories add/edit/delete`) or directly in config. The full list is sent to Claude in the classification prompt, constraining responses to valid categories only.

---

## Time Views & Aggregation

- **Monthly** (primary): category totals for a single month, with trailing 3-month rolling averages for comparison
- **Preset periods**: Quarterly, Year-to-Date, Trailing 12 Months, Annual — each shows category totals, monthly average, and sparklines of monthly values
- Sparklines rendered inline in tables (lightweight library or inline SVGs)

---

## Privacy

Only merchant names are sent to the Claude API. No amounts, dates, account numbers, or personal information. The merchant cache means the vast majority of transactions are classified locally after the first few imports. Raw descriptions stay local in SQLite.

---

## Out of Scope (v1)

- PDF statement parsing
- Multi-currency
- Multi-user / household sharing
- Budgeting / spending targets
- Bank API integrations (Plaid, etc.)
- Local/offline LLM classification (Ollama)
- Custom date range queries (use preset periods)
