# An example of user preferences for hyperpersonalization in AI interactions.
# This is also used as a base for rebuilding user preferences.
# Saved in python instead of JSON so we can have comments.
# These comments show examples of potential values, but I recommend not controlling the values too tightly.

default_preferences = {
    "communication_style": {
        "tone": "casual",  # casual | formal | professional | humorous | empathetic
        "response_length": "medium",  # concise | medium | detailed
        "format": "bullets",  # paragraphs | bullets | numbered | tables
        "explanation_depth": "balanced",  # overview | deep_dive | balanced
        "uncertainty_handling": "direct",  # hedge | direct | best_guess
        "examples": "personalized",  # neutral | personalized
    },
    "interaction_dynamics": {
        "proactivity": "suggest_when_relevant",  # reactive | proactive | suggest_when_relevant
        "questions": "direct_answer_first",  # direct_answer_first | guide_with_questions
        "error_handling": "clarify",  # clarify | just_say_dont_know
        "correction_handling": "acknowledge",  # acknowledge | silently_adapt
        "follow_ups": "on_request",  # automatic | on_request
    },
    "content": {
        "topics_of_interest": ["gaming", "coding"],
        "jargon_level": "mixed",  # plain | technical | mixed
        "depth_preference": "intermediate",  # beginner | intermediate | expert
    },
    "practical": {
        "budget_awareness": "cost_conscious",  # cost_conscious | neutral | premium_friendly
        "tools": ["Python", "Neo4j"],  # ecosystems/tools they prefer
        "units": "metric",  # metric | imperial
        "currency": "CAD",  # USD, CAD, etc.
        "date_format": "YYYY-MM-DD",  # DD/MM/YYYY, MM/DD/YYYY, etc.
        "time_format": "24h",  # 12h | 24h
    },
}

preference_definitions = {
    "communication_style": {
        "tone": "The overall mood and style of communication (e.g., casual, formal, professional, humorous, empathetic)",
        "response_length": "Preferred length of responses (e.g., concise, medium, detailed)",
        "format": "How information should be structured (e.g., paragraphs, bullets, numbered lists, tables)",
        "explanation_depth": "Level of detail in explanations (e.g., overview, deep_dive, balanced)",
        "uncertainty_handling": "How to handle uncertain or ambiguous situations (e.g., hedge, direct, best_guess)",
        "examples": "Type of examples to provide (e.g., neutral, personalized)",
    },
    "interaction_dynamics": {
        "proactivity": "How proactive the AI should be in offering suggestions (e.g., reactive, proactive, suggest_when_relevant)",
        "questions": "Approach to answering questions (e.g., direct_answer_first, guide_with_questions)",
        "error_handling": "How to handle errors or misunderstandings (e.g., clarify, just_say_dont_know)",
        "correction_handling": "How to respond when corrected (e.g., acknowledge, silently_adapt)",
        "follow_ups": "When to provide follow-up information (e.g., automatic, on_request)",
    },
    "content": {
        "topics_of_interest": "List of topics the user is particularly interested in",
        "jargon_level": "Preferred level of technical language (e.g., plain, technical, mixed)",
        "depth_preference": "User's expertise level for content depth (e.g., beginner, intermediate, expert)",
    },
    "practical": {
        "budget_awareness": "Consideration for cost in recommendations (e.g., cost_conscious, neutral, premium_friendly)",
        "tools": "List of preferred tools, platforms, or ecosystems",
        "units": "Preferred measurement system (e.g., metric, imperial)",
        "currency": "Preferred currency for financial information (e.g., USD, CAD, EUR)",
        "date_format": "Preferred date format (e.g., YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)",
        "time_format": "Preferred time format (e.g., 12h, 24h)",
    },
}

#### Some personal observations on preferences ####
# Giving the defaults to every user works, but it assumes a lot. Users might not want that.
# Providing the definitions can be helpful, but the AI sometimes populates the preferences with the definitions.
# This can be avoided by not including the definitions in the prompt, although it also seems to work if you are very stern about not including them.
# Leaving the preferences free-form seems to work best, but it's not going to be consistent between users.
