# fxpower 📈

**fxpower** is a Python CLI tool designed for investors and savers who want to track currency "buy opportunities" based on historical context. It generates a modern, interactive single-page HTML report ranking major currencies against your chosen base currency (PLN, USD, EUR, or GBP).

---

## Key Features

* ✅ **Efficient Data Handling:** One command to update a local Parquet cache (approx. 5 years of history).
* ✅ **Insightful Analytics:** Generates reports using Plotly with explainable metrics (Z-score, Percentiles).
* ✅ **Multi-Currency Support:** Seamlessly switch between base currencies.
* ✅ **Portfolio Ready:** Clean, modular code with a full CI/CD suite (Linting, Testing).

> [!IMPORTANT]
> **This tool is NOT a forecast.** It does not predict future prices. It provides historical context to help you understand if a currency is currently "expensive" or "cheap" relative to the last 5 years.

---

## How It Works

The tool evaluates "buy opportunities" by analyzing four core dimensions:

| Metric | Description |
| :--- | :--- |
| **Value vs History** | Uses **Percentiles** and **Z-scores** to show where the current rate sits in a 5-year window. |
| **Trend** | Measures **Momentum** and distance from the **SMA200** (200-day Simple Moving Average). |
| **Risk** | Calculates **90-day annualized volatility** to assess price stability. |
| **Overall Score** | A weighted blend of the above to rank the best "buy" entries. |

### Rate Convention
All rates follow the "Base per Quote" logic:
> **Rate = [BASE] for 1 [QUOTE]**
> *Example: Base=PLN, Quote=USD → Rate is how many PLN you pay for 1 USD.*

---

## Quickstart

### 1. Installation
The project uses an editable installation for development:

```bash
# Create and activate environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Fetch Data
Update your local Parquet cache with the latest rates:
```bash
fxpower fetch
```
*Default cache location: `data/cache.parquet`*

### 3. Generate Report
Generate an interactive HTML report for your base currency:
```bash
fxpower report --base PLN
```
*Your report will be saved in: `reports/fxpower_PLN.html`*

---

## Development & CI

This project is built with maintenance and scalability in mind.

* **Linting:** `make lint` (Ensures PEP8 compliance)
* **Testing:** `make test` (Unit tests for cross-rate logic and data integrity)
* **CI/CD:** Automated via GitHub Actions on every push.

### Data Source
Rates are fetched from the [Frankfurter API](https://www.frankfurter.app/) (EUR-based). Cross-rates (e.g., USD/PLN) are derived algebraically and validated via internal sanity checks to ensure 100% accuracy against direct pairs.

---

## Security & Privacy

* **No Secrets:** This project does not require API keys or handle sensitive user data.
* **Local Processing:** All HTML reports are generated locally on your machine.
* **Public Data:** Network calls are strictly limited to fetching public FX rates.

---

## License
Distributed under the **MIT License**. See `LICENSE` for more information.
