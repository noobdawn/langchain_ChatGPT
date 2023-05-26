from fastapi import FastAPI
from pydantic import BaseModel
from local.local_qa import LocalQA
from local.language import *
from configs.model_config import *
import json

local_qa = LocalQA("text2vec", "cpu", 5)
local_qa.build_embeddings()

app = FastAPI()

class Query_Answer(BaseModel):
    kb_name : str
    question : str
    top_k : int = 5
    score_threshold : int = 0


@app.post("/query_answer")
async def query_answer(query_answer: Query_Answer):
    kb_name = query_answer.kb_name
    question = query_answer.question
    top_k = query_answer.top_k
    score_threshold = query_answer.score_threshold
    if kb_name == TEXT_TAB_NEW_KB:
        return {"answer": question }
    possible_questions = local_qa.query_answer_with_score(get_pinyin(kb_name), question, top_k)
    if len(possible_questions) == 0:
        return {"answer": TEXT_ERROR_NO_ANSWER}
    original_questions = []
    answers = []
    for question, score in possible_questions:
        if score_threshold > 0 and score > score_threshold:
            continue
        if question.metadata["original"] not in original_questions:
            original_questions.append(question.metadata["original"])
            answer = "answer:" + question.metadata['answer'] + "  "
            answer += "score: " + str(score) + "\n\n"
            answers.append(answer)
    return {"answer" : answers }