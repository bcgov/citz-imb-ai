from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "./gemma-2b-search-classifier"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

questions = [
    "What is the process for filing a complaint against a government agency in Canada?",
    "What is the significance of the British Columbia Tartan recorded on January 8, 1969?",
    "Which acts or regulations in British Columbia are related to the rights of tenants?",
    "How many times is the word 'interprovincial' mentioned in the British Columbia laws?",
]

for question in questions:
    print(question)
    input_text = f"""
      Your job is to identify which type of search is required to gather the appropriate context to answer the attached question.
      The search options are as follows:
              semantic: questions that require a vector similarity search to find relevant information
              explicit: questions that a neo4j cypher query can provide context for
              global: questions that require a broader understanding of the legal domain and may involve multiple documents or sections

      You can choose one or more of these options to answer the question, but try to avoid performing searching that would not be applicable to the question.
      Do not form any other sentences. Only respond with a list of valid search options.

      Here are some examples of questions and their search type:
      - "How much notice does a tenant have to give before terminating a tenancy?" (semantic) This question requires a vector search to find relevant information about tenancy laws.
      - "Do I need to wear a seatbelt in BC?" (semantic) This question requires a vector search to find relevant information about seatbelt laws.
      - "How many subsections are in this act?" (explicit) A cypher query could return the number of unique subsections.
      - "Give me a summary of the Motor Vehicle Act." (explicit) A cypher query would return the entire act for summarization.
      - "Which acts contain information about the rights of tenants in BC?" (global) This question requires a broader understanding of the legal domain and may involve multiple documents or sections.

      What search type(s) would you use to answer the following question?

      The question:
      "{question}"

      Your answer:
    """

    input_ids = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**input_ids, max_length=1000)
    # Only decode the new tokens (skip the input)
    response = tokenizer.decode(
        outputs[0][len(input_ids["input_ids"][0]) :], skip_special_tokens=True
    )
    print(response.strip())
    print("---")
