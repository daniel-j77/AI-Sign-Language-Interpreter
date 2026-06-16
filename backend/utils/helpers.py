def clean_text(text: str) -> str:
    """
    Clean user input text:
    - convert to lowercase
    - remove extra spaces
    """
    if not text:
        return ""

    return text.lower().strip()
