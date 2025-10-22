import unicodedata

def normalize_text(s: str) -> str:
    # Replace smart quotes, dashes, etc.
    replacements = {
        "’": "'", "‘": "'", "‛": "'", "‚": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "–": "-", "—": "-", "―": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # Normalize and reduce to ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()

if __name__ == "__main__":
    # Example
    a = "You’re Temporarily Blocked"
    b = "You're Temporarily Blocked"

    if normalize_text(a) == normalize_text(b):
        print("Same")
    else:
        print("Different")
