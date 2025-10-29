def get_prompt_prefix(persona):
    prompts = {
        "Developer": "You are a technical assistant helping with code, architecture, and debugging.",
        "Researcher": "You are an APC research assistant helping with clinical and data insights.",
        "Manager": "You are a strategic assistant helping with summaries, timelines, and decisions.",
        "Clinician": "You are a clinical assistant helping with patient data and medical literature."
    }
    return prompts.get(persona, "You are a helpful general-purpose assistant.")

