import streamlit as st
import time
from agent_1 import agent, SYSTEM_PROMPT
from langgraph.types import Command

st.set_page_config(page_title="Research Assistant", page_icon="📚", layout="centered")

st.title("📚 NotebookLM Mini-Me – עוזר המחקר שלך")
st.write("הזיני נושא מחקר, והסוכן יאסוף עבורך מקורות וקישורים מהאינטרנט.")

# אתחול משתני המצב (Session State)
if "final_report" not in st.session_state:
    st.session_state.final_report = ""
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "topic" not in st.session_state:
    st.session_state.topic = ""

# מזהה שיחה חדש ונקי לגמרי למודל 2.0 החדש
SESSION_CONFIG = {"configurable": {"thread_id": "streamlit_session_v20_final"}}

# תיבת קלט לנושא המחקר
topic_input = st.text_input("מהו הנושא שתרצי לחקור?", value=st.session_state.topic, disabled=st.session_state.awaiting_approval)

if st.button("התחל מחקר", disabled=st.session_state.awaiting_approval or not topic_input):
    st.session_state.topic = topic_input
    st.session_state.awaiting_approval = True
    
    # שלב 1: איסוף המידע
    inputs = {
        "messages": [
            ("system", SYSTEM_PROMPT),
            ("user", f"חפש ואסוף מקורות מידע וקישורים מעודכנים על: {st.session_state.topic}")
        ]
    }
    with st.spinner("⏳ הסוכן אוסף מקורות מידע מהאינטרנט..."):
        for event in agent.stream(inputs, SESSION_CONFIG, stream_mode="values"):
            pass
            
    st.rerun()

# שלב ה-Human in the Loop בממשק הגרפי
if st.session_state.awaiting_approval:
    st.info(f"⏳ הסוכן אסף את המקורות עבור: **{st.session_state.topic}** ועצר לאישור אנושי.")
    st.warning("🛑 [Human-in-the-Loop] האם את מאשרת לסוכן לעבד את המקורות הללו ולהציג את הסיכום הסופי?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ כן, אשר והצג סיכום"):
            with st.spinner("🚀 מפיק את הדוח והסיכום הסופי..."):
                
                time.sleep(1)
                
                # שלב 2: המשך הריצה לסיכום
                final_state = None
                for event in agent.stream(Command(resume="כן"), SESSION_CONFIG, stream_mode="values"):
                    final_state = event
                
                # חילוץ תוכן בצורה נקייה
                if final_state and "messages" in final_state:
                    raw_content = final_state["messages"][-1].content
                    if isinstance(raw_content, list) and len(raw_content) > 0:
                        st.session_state.final_report = raw_content[0].get('text', str(raw_content))
                    else:
                        st.session_state.final_report = str(raw_content)
                else:
                    st.session_state.final_report = "שגיאה: לא ניתן היה לשלוף את הסיכום הסופי."
                
                st.session_state.awaiting_approval = False
                st.rerun()
                
    with col2:
        if st.button("❌ ביטול הריצה"):
            st.session_state.awaiting_approval = False
            st.session_state.topic = ""
            st.session_state.final_report = ""
            st.rerun()

# תצוגת הדו"ח הסופי למשתמש - מיושרת בצורה מושלמת לימין (RTL)
if st.session_state.final_report:
    st.success("🤖 התשובה והסיכום הסופי של עוזר המחקר:")
    
    # עטיפת הדו"ח בתוך בלוק HTML שמאלץ יישור לימין וכיוון עברית תקין
    styled_report = f"""
    <div style="direction: rtl; text-align: right; font-family: sans-serif; line-height: 1.6; font-size: 16px;">
        {st.session_state.final_report.replace('\n', '<br>')}
    </div>
    """
    st.markdown(styled_report, unsafe_allow_html=True)