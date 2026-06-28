# check-model-gemini

A command-line utility that retrieves available Gemini models via the Gemini API, probes each model's accessibility, displays published Free Tier rate limits, categorizes models by capability, and presents the results in a readable table.

## Features

- Fetches all models available to your Gemini API key
- Probes model accessibility with a minimal generation request
- Displays published Free Tier rate limits (RPM, TPM, RPD) for each model
- Categorizes models by type (Text-out, Multi-modal generative models, Agents, Live API, Other models)
- Outputs results in a formatted grid table
- Skips non-chat models (embeddings, image generation, video generation, etc.) from accessibility probing — status is shown as `-`

## Prerequisites

- Python 3.10+
- A Gemini API key — get one at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd check-model-gemini
   ```

2. Run the setup script to create a virtual environment and install dependencies:

   ```bash
   bash setup.sh
   ```

   This will:
   - Create a Python virtual environment in `.venv/`
   - Upgrade `pip`
   - Install packages from `requirements.txt`

3. Create a `.env` file in the project root with your API key:

   ```env
   GOOGLE_API_KEY=your-gemini-api-key
   ```

   See `.env.example` for the expected format.

## Usage

```bash
bash run.sh
```

The script will:

1. Fetch all models available to your API key
2. Probe each text-generation model with a minimal request (`"hello"`, 1 token output)
3. Classify each model into a category
4. Look up published rate limits
5. Print the results as a table

## Output

The output is a grid table with the following columns:

| Column        | Description |
|---------------|-------------|
| **Model**     | Full model name (e.g. `models/gemini-2.5-flash`) |
| **Name**      | Human-readable display name from the API |
| **Status**    | Accessibility status — see legend below |
| **Category**  | Model category |
| **RPM (limit)** | Published requests-per-minute limit |
| **TPM (limit)** | Published tokens-per-minute limit |
| **RPD (limit)** | Published requests-per-day limit |

### Status Legend

| Status              | Meaning |
|---------------------|---------|
| ✅ Accessible       | Model responded to a generation request |
| 🔴 Quota Exceeded   | API returned HTTP 429 (rate limit / quota exceeded) |
| 🔴 Forbidden        | API returned HTTP 403 (access denied) |
| ⚠️ Not Found        | API returned HTTP 404 (model not available) |
| ⚠️ Check Failed     | Unexpected error (network timeout, etc.) |
| `SERVER_ERROR_xxx`  | Server-side error with HTTP status code |
| `ERROR_xxx`         | Other client error with HTTP status code |
| `-`                 | Not a text-generation model — not probed |

### Categories

| Category                       | Description |
|--------------------------------|-------------|
| Text-out models                | Standard text-generation models (Gemini, Gemma) |
| Multi-modal generative models  | Imagen, Veo, Lyria, TTS, and other generative models |
| Agents                         | Antigravity, Deep Research (experimental agent models) |
| Live API                       | Models supporting real-time/bidirectional interaction |
| Other models                   | Embeddings, Robotics, Computer Use, AQA |
| Unknown                        | Unrecognized model without supported actions |
| Other                          | Unrecognized model with supported actions |

### Summary Line

At the end, the script prints:

```
Summary: N models Allowed  |  M models Blocked/Error
```

Followed by reference rate-limit information and a reminder that actual remaining quota cannot be queried via the Gemini API.

## Project Structure

```
check-model-gemini/
├── check_model.py          # Main script
├── requirements.txt        # Python dependencies
├── setup.sh                # Virtual environment setup
├── run.sh                  # Convenience runner
├── .env                    # API key (not committed)
├── .env.example            # Example environment file
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Important Notes

### Rate Limits

- The Gemini API enforces rate limits **per minute**, not per day.
- Published limits displayed in the table are **reference values** from [ai.google.dev/pricing](https://ai.google.dev/pricing). They may not reflect your actual tier or regional availability.
- **Actual remaining quota cannot be fetched via the API.** The Gemini API does not return rate-limit headers.
- To check your actual usage, visit:
  - Free Tier / Developer API: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
  - Vertex AI: Google Cloud Console > APIs & Services > Quotas

### Model Probing

- The script checks accessibility by sending a minimal generation request (`"hello"` with `max_output_tokens=1`).
- This **consumes a small amount of quota** (one request per model probed).
- Non-chat models (embeddings, image/video generation, live models, etc.) are detected by their supported actions and **skipped** from probing — their status is shown as `-` and no quota is consumed.
- Model accessibility is probed concurrently using a thread pool (up to 4 parallel requests) to reduce total wall-clock time.
- Each thread has its own API client to avoid `httpx` lock contention.
- This is safe under Free Tier rate limits because the 429 (rate-limited) response acts as a natural backpressure mechanism.

## Limitations

- **Remaining quota cannot be queried** — this is a Gemini API limitation, not a script limitation.
- **Rate limits shown are published estimates**, not real-time per-key limits.
- **Model availability varies by API key tier and region** — some models may return 404 even if documented.
- **Some models may return HTTP 400** (bad request) for a simple text prompt but are still considered "accessible" (e.g., models requiring multimodal input). These are counted as `✅ Accessible`.

## License

This project is provided as-is for personal and educational use.