from uuid import UUID

from pydantic import BaseModel


class QuestionAssistant(BaseModel):
    question: str


class ReponseAssistant(BaseModel):
    reponse: str


class AlerteOut(BaseModel):
    niveau: str
    message: str
