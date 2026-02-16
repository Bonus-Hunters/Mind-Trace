def get_language_code(language: str) -> str:
    language_mapping = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Arabic": "ar",
        "German": "de",
    }
    return language_mapping.get(language, "en")
