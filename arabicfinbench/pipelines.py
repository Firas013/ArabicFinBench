"""ArabicFinBench's own pipeline registrations: VLMs via OpenRouter.

Kept in the overlay rather than added to ``extract_bench``'s pipeline module,
because which models we evaluate and what we ask them for are ArabicFinBench
decisions, not upstream ones.

OpenRouter needs no new provider. The ``qwen3_5`` parse provider already speaks
OpenAI-compatible chat completions with base64 image parts, and takes
``server_url``, ``model`` and ``api_key_env`` from config — which is exactly
OpenRouter's API surface. The one upstream change was making its prompt
settable (see NOTICE); a benchmark that cannot pin the prompt cannot compare
two VLMs on equal terms.

**The prompt is frozen and hashed.** Every VLM receives byte-identical
instructions, and :data:`PROMPT_SHA256` goes into the provenance of every row
produced here, satisfying the no-per-model-tuning rule in ``docs/fairness.md``
guard 9. Editing the text below changes the hash, which is the intended alarm:
results produced under different prompts are not comparable.
"""

from __future__ import annotations

import hashlib

OPENROUTER_BASE = "https://openrouter.ai/api"
OPENROUTER_KEY_ENV = "OPENROUTER_API_KEY"

# Frozen transcription prompt. Authored for Arabic financial statements; every
# rule below exists because its absence produced a specific, observed failure.
# Rules 2-5 in particular defend the properties this benchmark measures:
# digit script, separator form, parenthesised negatives, and the distinction
# between an empty cell and a printed zero.
PARSE_PROMPT = """You are performing OCR on one page of an Arabic financial statement
(Saudi audit filing). Extract EXACTLY what is printed. This is a
transcription task, not an interpretation task.

RULES
1. Transcribe Arabic text in logical reading order (the order it would
   be typed), right-to-left lines read top to bottom.
2. Keep digits in the script printed on the page: Arabic-Indic digits
   (٠١٢٣٤٥٦٧٨٩) stay Arabic-Indic, Latin digits stay Latin. Never
   convert between them.
3. Keep thousands separators and decimal marks exactly as printed
   (e.g. ٣٠,٩٤٥,٥٧٥). Never add, remove, or reformat separators.
4. Numbers in parentheses are negative values: transcribe the
   parentheses, e.g. (٢١,٠٠٠,٠٠٠). Never convert to a minus sign.
5. A dash or empty table cell is transcribed as an empty cell.
   Never write 0 for an empty cell.
6. Do NOT translate anything. Do NOT summarize. Do NOT correct
   spelling, spacing, or numbers you believe are wrong. If a character
   is unreadable, transcribe your best single guess; never omit it.
7. Ignore handwritten signatures, stamps, and marker scribbles: do not
   transcribe them.
8. Note references (e.g. ١٢-٣ or إيضاح ٦) are text cells: transcribe
   them exactly, keeping the hyphen.

OUTPUT
Return the page as HTML. No markdown fences, no commentary, no
explanation.

- Text outside tables: one <p> per printed line, top to bottom.
- Each table on the page: one <table> element, with <tr> per row and
  <td> per cell. Rows top to bottom. Within a row, cells LEFT to RIGHT
  as positioned on the page (spatial order, not reading order). Every
  row in one table must have the same number of cells; use an empty
  <td></td> for empty positions.
- Do not add <thead>, <th>, colspan, rowspan, or CSS. Plain <table>,
  <tr>, <td> only."""

PROMPT_SHA256 = hashlib.sha256(PARSE_PROMPT.encode("utf-8")).hexdigest()

# One model per major family, spanning roughly 10x in price, all with strong
# multilingual coverage. Pipeline names are prefixed ``or_`` so an OpenRouter
# row is never mistaken for a direct-vendor row: the same model served through
# different routes can differ, and the leaderboard should not imply otherwise.
OPENROUTER_VLMS: dict[str, str] = {
    "or_qwen3_7_flash": "qwen/qwen3.7-flash",
    "or_gemini_3_5_flash_lite": "google/gemini-3.5-flash-lite",
    "or_gpt_5_mini": "openai/gpt-5-mini",
    "or_mistral_medium_3_1": "mistralai/mistral-medium-3.1",
    "or_qwen3_8_27b": "qwen/qwen3.8-27b",
    "or_qwen3_5_9b": "qwen/qwen3.5-9b",
}


def register_arabicfinbench_pipelines(register_fn) -> None:  # type: ignore[no-untyped-def]
    """Register the OpenRouter VLM parse pipelines.

    ``temperature=0`` on every one: these are graded as transcribers, and a
    sampled transcription would make the score partly a lottery. Determinism is
    still verified rather than assumed (see
    :mod:`arabicfinbench.determinism`); a model that varies anyway is flagged
    and must report three seeds.
    """
    from extract_bench.schemas.pipeline import PipelineSpec  # type: ignore[import-untyped]
    from extract_bench.schemas.product import ProductType  # type: ignore[import-untyped]

    for pipeline_name, model in OPENROUTER_VLMS.items():
        register_fn(
            PipelineSpec(
                pipeline_name=pipeline_name,
                provider_name="qwen3_5",  # OpenAI-compatible client; see module docstring
                product_type=ProductType.PARSE,
                config={
                    "server_url": OPENROUTER_BASE,
                    "model": model,
                    "api_key_env": OPENROUTER_KEY_ENV,
                    "prompt": PARSE_PROMPT,
                    "temperature": 0,
                    # Test_1 is three pages; without this the provider sends
                    # page 1 only and the model is scored on a third of the
                    # document as though it had seen all of it.
                    "all_pages": True,
                    "dpi": 200,
                    # Raised uniformly after qwen3.5-9b, a reasoning model,
                    # spent the whole 16k budget thinking and returned no
                    # content on at least one page. A ceiling that was never
                    # reached cannot change a result, so this is a no-op for
                    # every model already measured (highest observed reasoning
                    # use was qwen3.7-flash at 4,583 tokens) and is a uniform
                    # setting rather than per-model tuning.
                    "max_tokens": 40000,
                    "timeout": 600,
                },
            )
        )
