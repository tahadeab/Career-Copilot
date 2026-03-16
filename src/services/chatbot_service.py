"""
Chatbot Service - Core chatbot logic and response generation
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for processing messages and generating responses."""
    
    def __init__(self):
        self.default_responses = {
            'en': [
                "Hello! How can I help you today?",
                "I'm here to assist you. What would you like to know?",
                "Feel free to ask me anything!",
            ],
            'ar': [
                "مرحباً! كيف يمكنني مساعدتك اليوم؟",
                "أنا هنا لمساعدتك. ماذا تود أن تعرف؟",
                "لا تتردد في سؤالي عن أي شيء!",
            ]
        }
        
        self.knowledge_base = {
            'en': {
                'hello': "Hello! How can I help you?",
                'how are you': "I'm doing well, thank you for asking!",
                'what is ai': "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines.",
                'bye': "Goodbye! Have a great day!",
            },
            'ar': {
                'مرحبا': "مرحباً! كيف يمكنني مساعدتك؟",
                'كيف حالك': "أنا بخير، شكراً لسؤالك!",
                'ما هو الذكاء الاصطناعي': "الذكاء الاصطناعي هو مجال في علوم الحاسوب يهدف إلى إنشاء أنظمة قادرة على تقليد السلوك البشري الذكي.",
                'وداعا': "وداعاً! أتمنى لك يوماً رائعاً!",
            }
        }
    
    def process_message(self, message: str, user_id: str, language: str = 'en') -> str:
        """
        Process a user message and generate a response.
        
        Args:
            message: The user's input message
            user_id: The ID of the user
            language: The language code ('en' or 'ar')
            
        Returns:
            The bot's response
        """
        try:
            # Normalize the message
            normalized_message = message.lower().strip()
            
            # Check knowledge base for matching response
            if language in self.knowledge_base:
                for key, response in self.knowledge_base[language].items():
                    if key in normalized_message:
                        logger.info(f"Found matching response for: {key}")
                        return response
            
            # Return default response if no match found
            import random
            default_responses = self.default_responses.get(language, self.default_responses['en'])
            response = random.choice(default_responses)
            
            logger.info(f"Generated response for user {user_id}: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."
    
    def get_suggested_questions(self, language: str = 'en') -> list:
        """Get suggested questions for the user."""
        suggestions = {
            'en': [
                "What is AI?",
                "How does machine learning work?",
                "Tell me about yourself",
            ],
            'ar': [
                "ما هو الذكاء الاصطناعي؟",
                "كيف يعمل التعلم الآلي؟",
                "أخبرني عن نفسك",
            ]
        }
        return suggestions.get(language, suggestions['en'])
