# from langchain_ollama import OllamaLLM
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_chroma import Chroma
# from langchain_ollama import OllamaEmbeddings
# from langchain_core.documents import Document
# import logging
# import traceback
# import os

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# class HealthMonitorChatbot:
#     def __init__(self, db_location: str = "./health_monitor_db"):
#         self.db_location = db_location
#         self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
#         self.model = OllamaLLM(model="llama3.2", temperature=0.7, timeout=90)
        
#         # Initialize vector store with health monitoring knowledge
#         self._initialize_vector_store()
#         self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

#     # ---------------------------------------------------------
#     # DOMAIN FILTERING
#     # ---------------------------------------------------------
#     def is_project_related(self, question: str) -> bool:
#         keywords = [
#             # Weekday Mode
#             "posture", "blink", "screen", "fatigue", "drowsy", "slouch", "head", "shoulder",
#             "eye", "neck", "back", "sitting", "work", "office", "monitor",
            
#             # Weekend Mode
#             "yoga", "pose", "asana", "exercise", "stretch", "workout",
            
#             # Health
#             "health", "pain", "discomfort", "strain", "stress", "relief",
            
#             # Sessions & Stats
#             "session", "history", "statistics", "stats", "time", "duration", "blink rate"
#         ]
#         q = question.lower()
#         return any(word in q for word in keywords)

#     # ---------------------------------------------------------
#     # VECTOR STORE SETUP
#     # ---------------------------------------------------------
#     def _initialize_vector_store(self):
#         add_documents = not os.path.exists(self.db_location)
        
#         self.vector_store = Chroma(
#             collection_name="health_monitor_docs",
#             persist_directory=self.db_location,
#             embedding_function=self.embeddings
#         )
        
#         if add_documents:
#             documents = self._create_knowledge_base()
#             self.vector_store.add_documents(documents=documents)
#             logger.info(f"Added {len(documents)} documents to knowledge base")
    
#     def _create_knowledge_base(self):
#         knowledge = [
#             {"content": "Weekday Mode monitors your posture while working. It detects slouching, forward head position, tilted shoulders, and distance from screen. It tracks blink rate to detect screen fatigue and drowsiness. The system provides voice notifications when bad posture is detected for more than 5 seconds.", "category": "weekday_features"},
#             {"content": "Posture detection uses MediaPipe Face Mesh and Pose landmarks. Blink detection uses Eye Aspect Ratio (EAR) threshold of 0.23. Normal blink rate is 15–20 blinks per minute.", "category": "weekday_technical"},
#             {"content": "Weekend Mode supports yoga poses including T-Pose, Warrior II, Tree Pose, Downward Dog, Forward Bend, Chair Pose, and Raised Hands Pose.", "category": "weekend_features"},
#             {"content": "Eye exercises include 20-20-20 rule, palming, eye rolling, focus change, and blinking exercises.", "category": "eye_exercises"},
#             {"content": "Back exercises include cat-cow stretch, seated spinal twist, shoulder blade squeeze, neck stretches, and child's pose.", "category": "back_exercises"},
#         ]
        
#         documents = []
#         for item in knowledge:
#             documents.append(Document(
#                 page_content=item["content"],
#                 metadata={"category": item["category"], "source": "health_monitor"}
#             ))
#         return documents

#     # ---------------------------------------------------------
#     # USER STATISTICS
#     # ---------------------------------------------------------
#     def get_user_statistics(self):
#         try:
#             from .models import WeekdaySession, YogaSession
#             from django.db.models import Sum, Avg
            
#             weekday_sessions = WeekdaySession.objects.all()
#             yoga_sessions = YogaSession.objects.all()
            
#             return {
#                 'weekday': {
#                     'total_sessions': weekday_sessions.count(),
#                     'total_duration': weekday_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
#                     'total_blinks': weekday_sessions.aggregate(Sum('blink_count'))['blink_count__sum'] or 0,
#                     'avg_blinks_per_session': weekday_sessions.aggregate(Avg('blink_count'))['blink_count__avg'] or 0,
#                 },
#                 'yoga': {
#                     'total_sessions': yoga_sessions.count(),
#                     'total_duration': yoga_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
#                 }
#             }
#         except Exception as e:
#             logger.error(f"Stats error: {e}")
#             return None

#     def format_statistics_for_context(self, stats):
#         if not stats:
#             return "No session data available yet."

#         return (
#             f"Weekday Sessions: {stats['weekday']['total_sessions']}, "
#             f"Total Screen Time: {round(stats['weekday']['total_duration']/3600,2)} hours, "
#             f"Total Blinks: {stats['weekday']['total_blinks']}. "
#             f"Yoga Sessions: {stats['yoga']['total_sessions']}, "
#             f"Total Yoga Time: {round(stats['yoga']['total_duration']/3600,2)} hours."
#         )

#     # ---------------------------------------------------------
#     # CHAIN SETUP
#     # ---------------------------------------------------------
#     def create_chain(self):
#         template = """
# You are a helpful assistant for the Smart Health Monitor system.

# You ONLY answer questions related to:
# - posture monitoring
# - blink detection
# - eye, back, and neck exercises
# - yoga poses
# - screen fatigue
# - session statistics

# User Stats:
# {user_stats}

# Knowledge:
# {context}

# Question: {question}

# If the question is unrelated, respond politely that you can only help with Smart Health Monitor related topics.
# """
#         prompt = ChatPromptTemplate.from_template(template)
#         return prompt | self.model

#     # ---------------------------------------------------------
#     # MAIN Q&A FUNCTION
#     # ---------------------------------------------------------
#     def answer_question(self, question: str) -> dict:
#         try:
#             # DOMAIN FILTER
#             if not self.is_project_related(question):
#                 return {
#                     "success": True,
#                     "answer": "Interesting question 🙂 But I can only help with topics related to the Smart Health Monitor project like posture monitoring, yoga, exercises, eye strain, and session history.",
#                     "sources": []
#                 }

#             stats = self.get_user_statistics()
#             stats_context = self.format_statistics_for_context(stats)
            
#             docs = self.retriever.invoke(question)
#             knowledge_context = "\n\n".join([doc.page_content for doc in docs])
            
#             chain = self.create_chain()
#             answer = chain.invoke({
#                 "user_stats": stats_context,
#                 "context": knowledge_context,
#                 "question": question
#             })
            
#             return {
#                 "success": True,
#                 "answer": answer,
#                 "sources": [doc.metadata.get("category", "unknown") for doc in docs]
#             }
#         except Exception as e:
#             logger.error(traceback.format_exc())
#             return {
#                 "success": False,
#                 "answer": "System error. Please ensure Ollama is running with llama3.2.",
#                 "sources": []
#             }

# # Initialize chatbot instance
# chatbot = HealthMonitorChatbot()
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
import logging
import traceback
import os
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthMonitorChatbot:
    def __init__(self, db_location: str = "./health_monitor_db"):
        self.db_location = db_location
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.model = OllamaLLM(model="llama3.2", temperature=0.7, timeout=90)
        
        # Initialize vector store with health monitoring knowledge
        self._initialize_vector_store()
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

    # ---------------------------------------------------------
    # DOMAIN FILTERING
    # ---------------------------------------------------------
    def is_project_related(self, question: str) -> bool:
        keywords = [
            # Weekday Mode
            "posture", "blink", "screen", "fatigue", "drowsy", "slouch", "head", "shoulder",
            "eye", "neck", "back", "sitting", "work", "office", "monitor",
            
            # Weekend Mode
            "yoga", "pose", "asana", "exercise", "stretch", "workout",
            
            # Health
            "health", "pain", "discomfort", "strain", "stress", "relief",
            
            # Sessions & Stats
            "session", "history", "statistics", "stats", "time", "duration", "blink rate",
            "dashboard", "total", "average", "how many", "how much", "show me",
            
            # Questions about data
            "my", "mine", "i", "me", "today", "yesterday", "week", "month"
        ]
        q = question.lower()
        return any(word in q for word in keywords)

    # ---------------------------------------------------------
    # VECTOR STORE SETUP
    # ---------------------------------------------------------
    def _initialize_vector_store(self):
        add_documents = not os.path.exists(self.db_location)
        
        self.vector_store = Chroma(
            collection_name="health_monitor_docs",
            persist_directory=self.db_location,
            embedding_function=self.embeddings
        )
        
        if add_documents:
            documents = self._create_knowledge_base()
            self.vector_store.add_documents(documents=documents)
            logger.info(f"Added {len(documents)} documents to knowledge base")
    
    def _create_knowledge_base(self):
        knowledge = [
            # Weekday Mode Features
            {"content": "Weekday Mode monitors your posture while working. It detects slouching, forward head position, tilted shoulders, and distance from screen. It tracks blink rate to detect screen fatigue and drowsiness. The system provides voice notifications when bad posture is detected for more than 5 seconds.", "category": "weekday_features"},
            
            {"content": "Posture detection uses MediaPipe Face Mesh and Pose landmarks. Blink detection uses Eye Aspect Ratio (EAR) threshold of 0.23. Normal blink rate is 15–20 blinks per minute. A healthy blink rate during computer work should be at least 50-60 blinks per session to prevent dry eyes.", "category": "weekday_technical"},
            
            {"content": "Bad posture indicators include: slouching (shoulder position drops more than 20 pixels below baseline), forward head (nose position more than 20 pixels forward from shoulder baseline), tilted shoulders (shoulder height difference more than 25 pixels), and being too close to the screen (eye distance less than 65% of baseline).", "category": "posture_details"},
            
            # Weekend Mode Features
            {"content": "Weekend Mode supports yoga poses including T-Pose, Warrior II (Virabhadrasana II), Tree Pose (Vrikshasana), Downward Dog (Adho Mukha Svanasana), Forward Bend (Uttanasana), Chair Pose (Utkatasana), and Raised Hands Pose (Urdhva Hastasana).", "category": "weekend_features"},
            
            {"content": "Yoga pose benefits: T-Pose improves breathing and posture; Warrior II builds leg strength; Tree Pose improves balance; Downward Dog stretches hamstrings; Forward Bend relieves stress; Chair Pose strengthens core; Raised Hands energizes the body.", "category": "yoga_benefits"},
            
            # Health Recommendations
            {"content": "Eye exercises include: 20-20-20 rule (every 20 minutes, look 20 feet away for 20 seconds), palming (cover eyes with warm palms), eye rolling, focus change exercises, and conscious blinking exercises.", "category": "eye_exercises"},
            
            {"content": "Back exercises include: cat-cow stretch, seated spinal twist, shoulder blade squeeze, neck stretches, and child's pose. These should be done every 30-60 minutes during work.", "category": "back_exercises"},
            
            {"content": "Recommended screen time breaks: 5-10 minute break every hour, stand and stretch every 30 minutes, eye exercises every 20 minutes. Ideal posture quality is above 80%, meaning you maintain good posture for at least 80% of your session time.", "category": "health_guidelines"},
            
            # Statistics Interpretation
            {"content": "Session statistics help track your health: Total sessions shows consistency, blink rate indicates eye health (50+ per session is good), posture quality above 80% is excellent, 60-80% is good but improvable, below 60% needs attention. Weekly trends show if you're improving.", "category": "stats_interpretation"},
            
            {"content": "Blink rate interpretation: Less than 40 blinks per session indicates severe eye strain. 40-50 blinks shows moderate strain. 50-70 blinks is healthy. Above 70 blinks is excellent. Compare your average to these benchmarks.", "category": "blink_analysis"},
        ]
        
        documents = []
        for item in knowledge:
            documents.append(Document(
                page_content=item["content"],
                metadata={"category": item["category"], "source": "health_monitor"}
            ))
        return documents

    # ---------------------------------------------------------
    # ENHANCED USER STATISTICS
    # ---------------------------------------------------------
    def get_user_statistics(self, detailed=False):
        """Get comprehensive user statistics"""
        try:
            from .models import WeekdaySession, YogaSession
            from django.db.models import Sum, Avg, Count
            from django.utils import timezone
            
            weekday_sessions = WeekdaySession.objects.all()
            yoga_sessions = YogaSession.objects.all()
            
            # Calculate time ranges
            now = timezone.now()
            week_ago = now - timedelta(days=7)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Basic stats
            stats = {
                'weekday': {
                    'total_sessions': weekday_sessions.count(),
                    'total_duration': weekday_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
                    'total_blinks': weekday_sessions.aggregate(Sum('blink_count'))['blink_count__sum'] or 0,
                    'avg_blinks_per_session': weekday_sessions.aggregate(Avg('blink_count'))['blink_count__avg'] or 0,
                    'total_bad_posture': weekday_sessions.aggregate(Sum('bad_posture_time'))['bad_posture_time__sum'] or 0,
                },
                'yoga': {
                    'total_sessions': yoga_sessions.count(),
                    'total_duration': yoga_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
                }
            }
            
            # Calculate posture quality
            if stats['weekday']['total_duration'] > 0:
                posture_quality = ((stats['weekday']['total_duration'] - stats['weekday']['total_bad_posture']) 
                                  / stats['weekday']['total_duration'] * 100)
                stats['weekday']['posture_quality'] = max(0, min(100, posture_quality))
            else:
                stats['weekday']['posture_quality'] = 0
            
            # This week stats
            week_weekday = weekday_sessions.filter(date__gte=week_ago)
            week_yoga = yoga_sessions.filter(date__gte=week_ago)
            
            stats['this_week'] = {
                'weekday_sessions': week_weekday.count(),
                'yoga_sessions': week_yoga.count(),
                'total_sessions': week_weekday.count() + week_yoga.count(),
                'weekday_duration': week_weekday.aggregate(Sum('duration'))['duration__sum'] or 0,
                'yoga_duration': week_yoga.aggregate(Sum('duration'))['duration__sum'] or 0,
            }
            
            # Today stats
            today_weekday = weekday_sessions.filter(date__gte=today_start)
            today_yoga = yoga_sessions.filter(date__gte=today_start)
            
            stats['today'] = {
                'weekday_sessions': today_weekday.count(),
                'yoga_sessions': today_yoga.count(),
                'weekday_duration': today_weekday.aggregate(Sum('duration'))['duration__sum'] or 0,
                'yoga_duration': today_yoga.aggregate(Sum('duration'))['duration__sum'] or 0,
                'blinks': today_weekday.aggregate(Sum('blink_count'))['blink_count__sum'] or 0,
            }
            
            # Recent sessions (last 5)
            if detailed:
                stats['recent_weekday'] = list(weekday_sessions.order_by('-date')[:5].values(
                    'date', 'duration', 'blink_count', 'bad_posture_time'
                ))
                stats['recent_yoga'] = list(yoga_sessions.order_by('-date')[:5].values(
                    'date', 'duration'
                ))
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            logger.error(traceback.format_exc())
            return None

    def format_statistics_for_context(self, stats):
        """Format statistics for LLM context with rich details"""
        if not stats:
            return "No session data available yet. Start your first session to begin tracking!"

        context_parts = []
        
        # Overall summary
        total_sessions = stats['weekday']['total_sessions'] + stats['yoga']['total_sessions']
        total_hours = (stats['weekday']['total_duration'] + stats['yoga']['total_duration']) / 3600
        
        context_parts.append(f"OVERALL STATISTICS:")
        context_parts.append(f"- Total Sessions: {total_sessions}")
        context_parts.append(f"- Total Time: {total_hours:.1f} hours")
        
        # Weekday details
        if stats['weekday']['total_sessions'] > 0:
            weekday_hours = stats['weekday']['total_duration'] / 3600
            avg_session_min = stats['weekday']['total_duration'] / stats['weekday']['total_sessions'] / 60
            
            context_parts.append(f"\nWEEKDAY MODE (Posture Monitoring):")
            context_parts.append(f"- Sessions: {stats['weekday']['total_sessions']}")
            context_parts.append(f"- Total Screen Time: {weekday_hours:.1f} hours")
            context_parts.append(f"- Average Session: {avg_session_min:.0f} minutes")
            context_parts.append(f"- Total Blinks: {stats['weekday']['total_blinks']:.0f}")
            context_parts.append(f"- Average Blinks/Session: {stats['weekday']['avg_blinks_per_session']:.0f}")
            context_parts.append(f"- Posture Quality: {stats['weekday']['posture_quality']:.0f}%")
            context_parts.append(f"- Bad Posture Time: {stats['weekday']['total_bad_posture'] / 3600:.1f} hours total")
        
        # Yoga details
        if stats['yoga']['total_sessions'] > 0:
            yoga_hours = stats['yoga']['total_duration'] / 3600
            avg_yoga_min = stats['yoga']['total_duration'] / stats['yoga']['total_sessions'] / 60
            
            context_parts.append(f"\nYOGA MODE:")
            context_parts.append(f"- Sessions: {stats['yoga']['total_sessions']}")
            context_parts.append(f"- Total Practice Time: {yoga_hours:.1f} hours")
            context_parts.append(f"- Average Session: {avg_yoga_min:.0f} minutes")
        
        # This week
        week_total_hours = (stats['this_week']['weekday_duration'] + stats['this_week']['yoga_duration']) / 3600
        context_parts.append(f"\nTHIS WEEK:")
        context_parts.append(f"- Total Sessions: {stats['this_week']['total_sessions']}")
        context_parts.append(f"- Weekday Sessions: {stats['this_week']['weekday_sessions']}")
        context_parts.append(f"- Yoga Sessions: {stats['this_week']['yoga_sessions']}")
        context_parts.append(f"- Total Time: {week_total_hours:.1f} hours")
        
        # Today
        today_total_hours = (stats['today']['weekday_duration'] + stats['today']['yoga_duration']) / 3600
        context_parts.append(f"\nTODAY:")
        context_parts.append(f"- Weekday Sessions: {stats['today']['weekday_sessions']}")
        context_parts.append(f"- Yoga Sessions: {stats['today']['yoga_sessions']}")
        context_parts.append(f"- Total Time: {today_total_hours:.1f} hours")
        if stats['today']['blinks'] > 0:
            context_parts.append(f"- Blinks: {stats['today']['blinks']:.0f}")
        
        return "\n".join(context_parts)

    # ---------------------------------------------------------
    # CHAIN SETUP
    # ---------------------------------------------------------
    def create_chain(self):
        template = """You are a helpful health assistant for the Smart Health Monitor system.

You ONLY answer questions related to:
- posture monitoring and corrections
- blink detection and eye health
- eye, back, and neck exercises
- yoga poses and benefits
- screen fatigue and wellness
- session statistics and progress tracking

IMPORTANT: When answering questions about statistics, USE THE EXACT NUMBERS from the User Stats section below. Include specific data points like:
- Number of sessions
- Total time in hours
- Blink counts and rates
- Posture quality percentages
- Today's and this week's activities

User's Current Statistics:
{user_stats}

Knowledge Base:
{context}

Question: {question}

Instructions:
1. If the question asks about user's data (like "how many sessions", "my blink rate", "how long", "my statistics"), respond with the SPECIFIC NUMBERS from the User Stats above
2. Include relevant metrics and comparisons to healthy benchmarks
3. Provide actionable insights based on the data
4. If the question is unrelated to health monitoring, politely redirect to relevant topics
5. Be conversational but data-driven when discussing statistics

Answer:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.model

    # ---------------------------------------------------------
    # MAIN Q&A FUNCTION
    # ---------------------------------------------------------
    def answer_question(self, question: str) -> dict:
        try:
            # DOMAIN FILTER
            if not self.is_project_related(question):
                return {
                    "success": True,
                    "answer": "I appreciate your question 🙂 However, I'm specifically designed to help with Smart Health Monitor topics like posture monitoring, yoga practice, eye strain prevention, and tracking your wellness sessions. Is there anything related to your health monitoring that I can help you with?",
                    "sources": []
                }

            # Get detailed statistics
            stats = self.get_user_statistics(detailed=True)
            stats_context = self.format_statistics_for_context(stats)
            
            # Retrieve relevant knowledge
            docs = self.retriever.invoke(question)
            knowledge_context = "\n\n".join([doc.page_content for doc in docs])
            
            # Generate answer
            chain = self.create_chain()
            answer = chain.invoke({
                "user_stats": stats_context,
                "context": knowledge_context,
                "question": question
            })
            
            return {
                "success": True,
                "answer": answer,
                "sources": [doc.metadata.get("category", "unknown") for doc in docs],
                "stats_included": stats is not None
            }
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "answer": "I encountered an error while processing your question. Please ensure Ollama is running with the llama3.2 model (run: ollama run llama3.2). If the issue persists, try restarting the Ollama service.",
                "sources": []
            }

# Initialize chatbot instance
chatbot = HealthMonitorChatbot()