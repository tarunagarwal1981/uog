import streamlit as st
import openai
from datetime import datetime
import pytz
import json

# Set page config
st.set_page_config(layout="wide", page_title="Maritime Reporting Chatbot")

# Set up OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define report types and their sequences
REPORT_TYPES = [
    "Arrival", "Departure", "Begin of sea passage", "End of sea passage",
    "Noon (Position) - Sea passage", "Drifting", "Anchor Arrival / FWE",
    "Noon Port / Anchor", "Anchor/STS Departure / SBE", "Berth Arrival / FWE",
    "Berth Departure / SBE", "Begin fuel change over", "End fuel change over",
    "Entering special area", "Leaving special area", "Begin offhire", "End offhire",
    "Begin canal passage", "End canal passage", "Begin Anchoring/Drifting",
    "End Anchoring/Drifting", "Noon (Position) - Port", "Noon (Position) - River",
    "Noon (Position) - Stoppage", "ETA update", "Change destination (Deviation)",
    "Begin of deviation", "End of deviation", "Other event"
]

FOLLOW_UP_REPORTS = {
    "Arrival": ["Departure", "Noon (Position) - Port", "Begin fuel change over", "End fuel change over", "Bunkering", "Off hire"],
    "Departure": ["Begin of sea passage", "Noon (Position) - Port", "ArrivalSTS", "DepartureSTS", "Begin canal passage", "End canal passage", "Begin Anchoring/Drifting", "End Anchoring/Drifting", "Noon (Position) - River", "Noon (Position) - Stoppage", "Begin fuel change over", "End fuel change over", "Entering special area", "Leaving special area"],
    "Begin of sea passage": ["Noon (Position) - Sea passage", "End of sea passage", "Begin fuel change over", "End fuel change over", "Entering special area", "Leaving special area"],
    "End of sea passage": ["Anchor Arrival / FWE", "Berth Arrival / FWE", "Begin Anchoring/Drifting"],
    "Noon (Position) - Sea passage": ["Noon (Position) - Sea passage", "End of sea passage", "Begin fuel change over", "End fuel change over", "Entering special area", "Leaving special area"],
    "Drifting": ["End Anchoring/Drifting", "Begin of sea passage"],
    "Anchor Arrival / FWE": ["Noon Port / Anchor", "Anchor/STS Departure / SBE", "Begin fuel change over", "End fuel change over"],
    "Noon Port / Anchor": ["Noon Port / Anchor", "Anchor/STS Departure / SBE", "Begin fuel change over", "End fuel change over"],
    "Anchor/STS Departure / SBE": ["Begin of sea passage", "Berth Arrival / FWE"],
    "Berth Arrival / FWE": ["Noon (Position) - Port", "Berth Departure / SBE", "Begin fuel change over", "End fuel change over"],
    "Berth Departure / SBE": ["Begin of sea passage", "Anchor Arrival / FWE"]
}

REQUIRED_FOLLOW_UPS = {
    "Begin fuel change over": "End fuel change over",
    "Entering special area": "Leaving special area",
    "Begin offhire": "End offhire",
    "Begin canal passage": "End canal passage",
    "Begin Anchoring/Drifting": "End Anchoring/Drifting",
    "Begin of deviation": "End of deviation"
}

# Prepare the training data as a string
TRAINING_DATA = f"""
You are an AI assistant for a maritime reporting system. Your role is to guide users through creating various types of maritime reports, ensuring they follow the correct sequence and rules.

Report Types: {json.dumps(REPORT_TYPES)}
Follow-up Reports: {json.dumps(FOLLOW_UP_REPORTS)}
Required Follow-ups: {json.dumps(REQUIRED_FOLLOW_UPS)}

Rules:
1. Check if there are any pending reports before allowing new report creation.
2. Validate the sequence of reports based on the FOLLOW_UP_REPORTS dictionary.
3. Noon reports can only be created between 11:00 and 13:00 LT.
4. When a valid report type is requested, inform the user that the report can be initiated.
5. Provide guidance on which reports can be created based on the last report.
6. If an invalid report sequence is requested, inform the user and suggest valid options.

Always maintain a professional and helpful tone. If you're unsure about something, it's okay to say so and offer to provide the information you do have.
"""

def get_ai_response(user_input, last_report):
    current_time = datetime.now(pytz.utc).strftime("%H:%M:%S")
    
    messages = [
        {"role": "system", "content": TRAINING_DATA},
        {"role": "system", "content": f"The current UTC time is {current_time}. The last report submitted was: {last_report}"},
        {"role": "user", "content": user_input}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].message['content'].strip()

def main():
    st.title("Maritime Reporting Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_report" not in st.session_state:
        st.session_state.last_report = REPORT_TYPES[0]

    last_report = st.selectbox("Select last report (for testing)", REPORT_TYPES, key="last_report")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How can I assist you with your maritime reporting?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = get_ai_response(prompt, last_report)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.experimental_rerun()

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()
