import streamlit as st
import time
import requests

API_KEY = "8d91c8d287mshf8beeecb03b1ff5p1e01b1jsndac9e7318adc"

# ========== FUNCTION 1 ==========
def generate_video_from_text(prompt):
    url = "https://runwayml.p.rapidapi.com/generate/text"  # example endpoint
    payload = {
	"text_prompt": prompt,
	"model": "gen3",
	"width": 1344,
	"height": 768,
	"motion": 5,
	"seed": 0,
	"callback_url": "",
	"time": 5
    }
    headers = {
	"x-rapidapi-key": "8d91c8d287mshf8beeecb03b1ff5p1e01b1jsndac9e7318adc",
	"x-rapidapi-host": "runwayml.p.rapidapi.com",
	"Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("uuid")
    else:
        st.error("Failed to initiate video generation.")
        return None

# ========== FUNCTION 2 ==========
def get_video_url(job_id, max_retries=120, delay=3):
    url = "https://runwayml.p.rapidapi.com/status"
    headers = {
        "x-rapidapi-key": API_KEY,  # replace with actual key
        "x-rapidapi-host": "runwayml.p.rapidapi.com"
    }

    for _ in range(max_retries):
        response = requests.get(url, headers=headers, params={"uuid": job_id})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("url"):
                return data["url"]
        time.sleep(delay)

    return None  # if not successful after retries