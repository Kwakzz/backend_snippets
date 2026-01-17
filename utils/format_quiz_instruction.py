format_quiz_instruction = """
From the quiz provided, generate a list of json bodies like so and return the list:

{
    "text": "What was Grandma's surname?",
    "choices": ["Afram", "Fordwor", "Sarpong"],
    "correct_answer": ["Afram"],
    "question_type": "multiple-choice"
}

question_type is always "multiple-choice".
If you see, a timestamp value assigned to a question, the json will be like so (with a timestamp_seconds key):
{
    "text": "What was Grandma's surname?",
    "choices": ["Afram", "Fordwor", "Sarpong"],
    "correct_answer": ["Afram"],
    "timestamp_seconds": 100,
    "question_type": "multiple-choice"
}

The timestamp is for interactive quizzes where questions are asked at specific points in a video. 

Enclose all choices, and the answer in double quotes, even integers.

The output should not be in markdown. Do not surround the output with triple backticks. Just return the list of JSONs.

If you cannot make sense of the text underneath the 'QUIZ' header, or there's no text underneath it, return "None".

Find below a sample return body I'm expecting:

[
    {
        "text": "What was Grandma's surname?",
        "choices": ["Afram", "Fordwor", "Sarpong"],
        "correct_answer": ["Afram"],
        "question_type": "multiple-choice"
    },

    {
        "text": "What did Grandma have?",
        "choices": ["party", "church service", "picnic"],
        "correct_answer": ["picnic"],
        "question_type": "multiple-choice"
    },

    {
        "text": "How many grandchildren did grandma have?",
        "choices": ["1", "2", "3"],
        "correct_answer": ["2"],
        "question_type": "multiple-choice"
    }
]
"""