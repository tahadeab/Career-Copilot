"""Explainable, lightweight chatbot engine for Career Copilot."""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ChatResult:
    response: str
    intent: str
    confidence: float
    sentiment: str


class ChatbotService:
    """A fast, dependency-light intent engine that works offline by default."""

    INTENTS: Dict[str, Dict[str, List[str]]] = {
        "en": {
            "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
            "about": ["who are you", "what can you do", "about you", "your features"],
            "ai_basics": ["what is ai", "what is artificial intelligence", "machine learning", "deep learning"],
            "career": ["cv", "resume", "career", "interview", "job", "portfolio", "skill"],
            "study": ["study", "learn", "course", "exam", "university", "graduation", "project"],
            "thanks": ["thank you", "thanks", "appreciate"],
            "goodbye": ["bye", "goodbye", "see you", "exit"],
        },
        "ar": {
            "greeting": ["مرحبا", "مرحباً", "اهلا", "أهلا", "السلام عليكم"],
            "about": ["من انت", "من أنت", "ماذا تستطيع", "مميزاتك"],
            "ai_basics": ["ما هو الذكاء الاصطناعي", "الذكاء الاصطناعي", "التعلم الآلي", "التعلم العميق"],
            "career": ["السيرة الذاتية", "سي في", "مقابلة", "وظيفة", "مسار مهني", "مهارة", "ملف أعمال"],
            "study": ["دراسة", "تعلم", "دورة", "اختبار", "جامعة", "تخرج", "مشروع"],
            "thanks": ["شكرا", "شكرًا", "ممتن"],
            "goodbye": ["وداعا", "وداعًا", "مع السلامة", "أراك لاحقا"],
        },
    }

    RESPONSES = {
        "en": {
            "greeting": "Hello! I am Career Copilot, an explainable bilingual AI assistant for learning, projects, and career preparation.",
            "about": "I can classify your request, detect language, estimate sentiment, save your conversation, and provide practical guidance for study and career growth.",
            "ai_basics": "Artificial intelligence is the field of building systems that perform tasks associated with human intelligence. Machine learning is a common approach where models learn patterns from data.",
            "career": "For career growth, start with a focused CV, two or three measurable portfolio projects, and structured interview practice. I can help you plan any of these steps.",
            "study": "A strong study plan combines a clear outcome, small weekly milestones, active practice, and a short review loop. Tell me your subject or project goal and I will help you break it down.",
            "thanks": "You are welcome. I am here whenever you need a clear next step.",
            "goodbye": "Goodbye! Keep building, learning, and documenting your progress.",
            "general": "I can help with AI concepts, study planning, graduation projects, CV improvement, interviews, and portfolio strategy. Try asking a focused question.",
        },
        "ar": {
            "greeting": "مرحباً! أنا Career Copilot، مساعد ثنائي اللغة يساعدك في التعلم والمشاريع والاستعداد المهني.",
            "about": "أستطيع تصنيف طلبك، اكتشاف اللغة، تقدير المشاعر، حفظ المحادثة، وتقديم إرشادات عملية للدراسة والتطور المهني.",
            "ai_basics": "الذكاء الاصطناعي هو مجال بناء أنظمة تنفذ مهام مرتبطة بالذكاء البشري. أما التعلم الآلي فهو أسلوب تتعلم فيه النماذج الأنماط من البيانات.",
            "career": "للتطور المهني، ابدأ بسيرة ذاتية مركزة، ومشروعين أو ثلاثة قابلين للعرض مع نتائج قابلة للقياس، ثم تدرب على المقابلات بشكل منظم.",
            "study": "تجمع خطة الدراسة القوية بين نتيجة واضحة، ومراحل أسبوعية صغيرة، وتطبيق عملي، ومراجعة مستمرة. اذكر المادة أو هدف المشروع وسأساعدك في تقسيمه.",
            "thanks": "على الرحب والسعة. أنا هنا لمساعدتك في تحديد الخطوة التالية بوضوح.",
            "goodbye": "إلى اللقاء! استمر في البناء والتعلم وتوثيق تقدمك.",
            "general": "يمكنني مساعدتك في مفاهيم الذكاء الاصطناعي، وخطط الدراسة، ومشاريع التخرج، وتحسين السيرة الذاتية، والمقابلات، وبناء ملف الأعمال.",
        },
    }

    POSITIVE = {"good", "great", "excellent", "love", "helpful", "شكرا", "ممتاز", "رائع", "مفيد"}
    NEGATIVE = {"bad", "difficult", "sad", "angry", "hate", "blocked", "سيئ", "صعب", "حزين", "غاضب", "مشكلة"}

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    def analyze_sentiment(self, message: str) -> str:
        tokens = set(re.findall(r"[\w\u0600-\u06ff]+", self.normalize(message)))
        positive = len(tokens & self.POSITIVE)
        negative = len(tokens & self.NEGATIVE)
        if positive > negative:
            return "positive"
        if negative > positive:
            return "negative"
        return "neutral"

    def classify(self, message: str, language: str) -> Tuple[str, float]:
        normalized = self.normalize(message)
        candidates = self.INTENTS.get(language, self.INTENTS["en"])
        scores = {intent: sum(1 for phrase in phrases if phrase in normalized) for intent, phrases in candidates.items()}
        intent, score = max(scores.items(), key=lambda item: item[1])
        if score == 0:
            return "general", 0.35
        return intent, min(0.98, 0.55 + (score * 0.12))

    def process_message(self, message: str, user_id: str, language: str = "en") -> ChatResult:
        language = language if language in self.RESPONSES else "en"
        intent, confidence = self.classify(message, language)
        return ChatResult(
            response=self.RESPONSES[language][intent],
            intent=intent,
            confidence=confidence,
            sentiment=self.analyze_sentiment(message),
        )

    def get_suggested_questions(self, language: str = "en") -> List[str]:
        return {
            "en": ["What is AI?", "Help me improve my CV", "How should I plan my graduation project?", "What can you do?"],
            "ar": ["ما هو الذكاء الاصطناعي؟", "ساعدني في تحسين سيرتي الذاتية", "كيف أخطط لمشروع تخرجي؟", "ماذا تستطيع أن تفعل؟"],
        }.get(language, self.get_suggested_questions("en"))
