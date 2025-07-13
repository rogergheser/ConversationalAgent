# 📚 BookMe — A Conversational Agent for Apartment Rentals

**BookMe** is a conversational agent designed to help rental agencies automate the booking process for multiple apartments. Built using **Llama 3**, this system reduces operator workload by taking initiative in conversations with guests looking to book an apartment for leisure stays in **Verona**.

---

## 🚀 Features

- **Task-Oriented Dialogue** — Focused purely on booking apartments.
- **Modular Pipeline**:
  - **PreNLU (Chunker)**: Splits user input into multiple intents.
  - **NLU**: Recognizes intents & fills slots.
  - **Dialogue Manager (DM)**: Controls flow and next best actions.
  - **NLG**: Generates polite, clear, engaging responses.
- **Multi-Intent Handling** — Processes multiple requests in one turn.
- **Error Recovery** — Manages incomplete or incoherent input.
- **Fallback & Human Handoff** — Transfers to an operator for out-of-scope requests.
- **Apartment Manager** — Handles listings and info display (demo phase).

---

## 📂 Project Structure
```bash
ConversationalAgent/
├── chat.py                # Entry point for the agent
├── config.yaml            # Main configuration
├── components/            # Core pipeline modules
│   ├── __init__.py
│   ├── apartmentManager.py
│   ├── apartmentTracker.py
│   ├── DM.py
│   ├── NLG.py
│   ├── NLU.py
│   ├── service.py
│   ├── stateTracker.py
│   └── validate.py
│
├── data/                  # Data & test data
│   ├── apartments/
│   ├── apartments.csv
│   ├── images/
│   └── test/
│
├── data_generation/       # Synthetic data generation
│   ├── __init__.py
│   ├── generate.py
│   ├── templates_dm.py
│   └── templates_nlu.py
│
├── prompts/               # LLM prompts
│   ├── apartment_manager/
│   └── gpt_prompts/
│
├── utils/                 # Utility functions
├── eval.py                # Evaluation script
├── README.md              # Project README
├── requirements.txt       # Python requirements
└── HMD_Gheser.pdf         # Project report
```

---

## ⚙️ How It Works

1. **PreNLU:** Segments user input by intent.
2. **NLU:** Extracts structured meaning (intents & slots).
3. **DM:** Decides actions based on extracted data & context.
4. **NLG:** Generates natural language replies from system actions.
5. **Conversation History:** Maintains context across turns.

---

## 🗂️ Supported Intents

- `book_apartment` — Book an apartment.
- `list_apartments` — See what’s available.
- `see_apartments` — View specific apartment(s).
- `contact_operator` — Speak to a human.
- `give_feedback` — Leave feedback.
- `fallback` — Catch-all for out-of-scope input.

---

## ✅ Evaluation Summary

| Component | F1 | Precision | Accuracy | Recall | Cohen’s Kappa |
|-----------|-----|-----------|----------|--------|----------------|
| **NLU — Intents** | 0.97 | 0.97 | 0.97 | 0.97 | 0.96 |
| **NLU — Slots** | 0.94 | 0.94 | 0.94 | 0.94 | 0.93 |
| **DM — Actions** | 0.82 | 0.84 | 0.80 | 0.80 | 0.77 |
| **DM — Arguments** | 0.94 | 0.94 | 0.95 | 0.95 | 0.93 |

**User tests** confirmed the agent’s clarity, politeness, and engagement.

---

## 📌 Limitations & Future Work

- The DM needs further tuning for edge cases.
- The NLG may drift when given too much conversation history.
- Planned improvements:
  - Better context prompts.
  - Richer apartment details.
  - Q&A features.
  - Stricter slot validation.

---

## ▶️ Run the Agent

Create your env by following the requirements and then run
```bash
python chat.py
```
