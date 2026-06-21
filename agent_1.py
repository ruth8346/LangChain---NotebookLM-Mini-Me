import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

# טעינת מפתחות סודיים
load_dotenv()

# מעבר למודל 2.0 פלאש - תומך בחיפוש ומספק מכסה חדשה לגמרי
llm_searcher = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0,
    max_retries=6,
    model_kwargs={"tools": [{"google_search": {}}]}
)

# כלי החיפוש עם השהייה קלה למניעת עומס
@tool
def search_the_web(query: str) -> str:
    """Search Google for real-time information, articles, and URLs about the topic."""
    try:
        time.sleep(2)
        response = llm_searcher.invoke(f"Perform a web search and list the top 3 resources and links for: {query}")
        return response.content
    except Exception as e:
        return f"Search failed: {str(e)}"

tools = [search_the_web]

# המודל הראשי של הסוכן - מעבר לגרסה 2.0 פלאש
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0,
    max_retries=6
)

SYSTEM_PROMPT = """You are a research data collection agent, similar to NotebookLM.
Your job is to use the 'search_the_web' tool to gather reliable sources and links about the topic.
The current year is 2026. Always summarize the findings and explicitly print the titles and exact URLs found.
CRITICAL: Always format the links as clickable Markdown links like this: [Title](URL)"""

# הגדרת הזיכרון של הגרף
memory = MemorySaver()

# יצירת הסוכן עם עצירה מובנית מיד אחרי הכלים
agent = create_react_agent(
    llm, 
    tools=tools, 
    checkpointer=memory, 
    interrupt_after=["tools"]
)

def run_research_project(topic: str):
    config = {"configurable": {"thread_id": "notebook_terminal_session_fixed_v20"}}
    print(f"\n📝 הנושא למחקר: {topic}")
    print("⏳ הסוכן אוסף מקורות מידע מהאינטרנט...")
    
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", f"חפש ואסוף מקורות מידע על: {topic}")]}
    
    for event in agent.stream(inputs, config, stream_mode="values"):
        pass
        
    print("\n🛑 [Human-in-the-Loop] הסוכן סיים ועצר לאישור המשתמש.")
    user_approval = input("הקלידי 'כן' כדי לאשר: ")
    
    if user_approval.strip() == "כן":
        print("\n🚀 מפיק דוח סופי...")
        final_state = None
        for event in agent.stream(Command(resume="כן"), config, stream_mode="values"):
            final_state = event
            
        if final_state and "messages" in final_state:
            print("\n🤖 סיכום סופי:")
            print(final_state["messages"][-1].content)