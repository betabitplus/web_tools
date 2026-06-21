"""Text normalization helpers for quoting."""

from __future__ import annotations

import re

import lxml.html  # nosec B410 - HTML parsing required for controlled content
import markdown


def md_to_plaintext(md_text: str) -> str:
    r"""Convert markdown to plaintext via HTML."""
    html = markdown.markdown(md_text)
    if html.strip():
        doc = lxml.html.fromstring(f"<div>{html}</div>")
        return doc.text_content().strip()
    return md_text


def generate_search_variants(text: str) -> list[str]:
    """Generate search variants for fuzzy matching."""
    variants: list[str] = [text]

    def add_variant(value: str) -> None:
        """Add a normalized variant if it is non-empty and unique."""
        value = re.sub(r"\s+", " ", value).strip()
        if value and value not in variants:
            variants.append(value)

    punctuation_map = str.maketrans(
        {
            "’": "'",  # noqa: RUF001
            "‘": "'",  # noqa: RUF001
            "“": '"',
            "”": '"',
            "–": "-",  # noqa: RUF001
            "—": "-",
            "−": "-",  # noqa: RUF001
        }
    )
    add_variant(text.translate(punctuation_map))

    if "'" in text and "’" not in text:  # noqa: RUF001
        add_variant(text.replace("'", "’"))  # noqa: RUF001

    if " - " in text:
        add_variant(text.replace(" - ", " – "))  # noqa: RUF001

    add_variant(re.sub(r"([a-z])([A-Z])", r"\1 \2", text))

    no_space = re.sub(r"(\w)\s+(\d)", r"\1\2", text)
    add_variant(no_space)

    superscripts = str.maketrans(
        {
            "0": "⁰",
            "1": "¹",
            "2": "²",
            "3": "³",
            "4": "⁴",
            "5": "⁵",
            "6": "⁶",
            "7": "⁷",
            "8": "⁸",
            "9": "⁹",
        }
    )
    if "^" in text:
        add_variant(
            re.sub(
                r"\^(\d)",
                lambda m: m.group(1).translate(superscripts),
                text,
            )
        )
        add_variant(re.sub(r"\^(\d)", r" \1", text))

    if re.search(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]", text):
        add_variant(
            re.sub(
                r"([⁰¹²³⁴⁵⁶⁷⁸⁹])",
                lambda m: (
                    " "
                    + str(m.group(1)).translate(
                        str.maketrans(
                            {
                                "⁰": "0",
                                "¹": "1",
                                "²": "2",
                                "³": "3",
                                "⁴": "4",
                                "⁵": "5",
                                "⁶": "6",
                                "⁷": "7",
                                "⁸": "8",
                                "⁹": "9",
                            }
                        )
                    )
                ),
                text,
            )
        )

    if re.search(r"\s[xX]\s", text):
        add_variant(re.sub(r"\s[xX]\s", " × ", text))  # noqa: RUF001

    if "/" in text and re.search(r"[A-Za-z]", text):
        add_variant(re.sub(r"(\d)\s*/\s*(\d)", r"\1 \2", text))

    return variants
