from sqlalchemy.orm import Session
from asag_engine.learning_plans.generator import LearningPlanGenerator  # reuse ollama logic
from .context_retriever import CopilotContextRetriever
from .prompt_builder import build_prompt
from .schemas import CopilotResponse
from asag_engine.resource_intelligence.service import ResourceIntelligenceService

class ClassroomCopilotService:

    def __init__(self):
        self.resource_service = ResourceIntelligenceService()
        self.retriever = CopilotContextRetriever(self.resource_service)

    def generate(self, db: Session, request):
        context = self.retriever.retrieve(
            db=db,
            topic=request.topic,
            top_k=request.top_k_context
        )

        prompt = build_prompt(request, context)

        content = LearningPlanGenerator.ask_ollama(prompt)

        return CopilotResponse(
            generated_content=content,
            citations=context["faiss"]["citations"]
        )