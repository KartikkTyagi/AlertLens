# AlertLens — Live Hackathon Presentation & Demo Script

This script provides an exact, step-by-step walkthrough for demonstrating AlertLens to judges and technical evaluators. Time required: **3 to 4 minutes**.

---

## 🎯 The Pitch in One Sentence
> *"AlertLens replaces the overwhelming SIEM alert flood with prioritized, AI-synthesized incident intelligence — proving an 81% noise reduction while keeping human analysts strictly in the loop."*

---

## 📋 Pre-Demo Checklist
- [x] Docker containers running (`docker compose ps`: `db`, `backend`, `frontend` all `Up`)
- [x] Browser open to `http://localhost:3000`
- [x] Terminal open to project root for the live real-time simulation

---

## 🎙️ Step-by-Step Walkthrough

### Step 1: Login & Access Control
- **Action**: Open `http://localhost:3000`. Show that unauthenticated access redirects to `/login`.
- **Action**: Click the **"Analyst (analyst_demo)"** 1-click button and click **"Sign In"**.
- **Talking Point**:
  > *"First, notice that AlertLens is built with enterprise security in mind. Access is strictly gated behind JWT authentication with role-based access control. As an analyst, I have access to triage and acknowledge incidents, but sensitive administrative functions remain restricted."*

---

### Step 2: The Triage Dashboard & Noise Compression
- **Action**: Arrive on the main dashboard (`/`). Point to the top metric cards and the central dark gradient banner.
- **Talking Point**:
  > *"In a standard SOC, tier-1 analysts face thousands of disconnected logs every shift. Here, AlertLens has taken **2,558 raw SIEM events** and collapsed them into **485 prioritized attack threads** — an **81% reduction in alert noise**.*
  >
  > *Crucially, this isn't arbitrary grouping: we achieved **100% recall** across planted multi-stage attacks and **78.6% precision**, cutting average triage time from 90 seconds down to ~34 seconds per alert."*

---

### Step 3: Deep Dive into Rank #1 Incident & AI Brief
- **Action**: Click on the **Rank #1 Incident** card to open the detail page (`/incidents/{id}`).
- **Talking Point**:
  > *"When an analyst investigates an incident, they don't get a wall of raw JSON. AlertLens leverages a fine-tuned Groq LLM to synthesize a structured 3-part intelligence brief:*
  > 1. ***Attack Synopsis***: *What happened chronologically.*
  > 2. ***Threat Context & Risk***: *Why it matters and which MITRE techniques were observed.*
  > 3. ***Mitigation Playbook***: *Actionable next steps for containment.*
  >
  > *And underneath, complete traceability: every underlying log is preserved, indexed, and inspectable."*

---

### Step 4: Human-in-the-Loop Acknowledgment
- **Action**: Click the teal **"Acknowledge Incident"** button in the header. Watch it transition to `✓ Acknowledged by analyst_demo on <timestamp>`.
- **Talking Point**:
  > *"Notice this core principle: **AI assists, humans decide.** The system suggests severity and synthesizes context, but an accountable human analyst must verify and acknowledge the threat. This state is permanently persisted to PostgreSQL."*

---

### Step 5: Live Real-Time Event Stream (The "Wow" Moment)
- **Action**: Click **"Dashboard"** to return to `/`. Note the pulsing **"Live Socket Active"** green pill.
- **Action**: In your second terminal, run:
  ```bash
  docker compose exec backend python -m ml.live_demo_feed
  ```
- **Action**: Return to the browser and watch the screen. Within 3.5 seconds, a new incident card will appear at the top, pulsing with a bright teal glow ring as the metric counters increment live.
- **Talking Point**:
  > *"Now watch what happens when a live attack occurs. Using PostgreSQL native `LISTEN`/`NOTIFY` and asynchronous WebSockets — with zero client polling — new incidents are pushed instantly. The analyst sees the card slide into position with an animated glow highlight, completely hands-free."*

---

### Step 6: Enterprise Audit Trail (Admin Role Switch)
- **Action**: Click the **Log out** button in the top right.
- **Action**: On `/login`, click the **"Admin (admin_demo)"** quick-fill button and sign in.
- **Action**: Point out the newly revealed **"Audit Trail"** link in the navigation bar. Click it to open `/audit-log`.
- **Talking Point**:
  > *"Now I've switched to the Administrator role. Notice the **Audit Trail** tab appeared. In enterprise environments, compliance demands strict provenance: who inspected which incident, and who signed off on it?*
  >
  > *Here in the audit log, you can see real immutable entries: `viewed_brief` recorded when we inspected Rank #1, and `acknowledged_incident` recorded when our analyst signed off. If a non-admin attempts to access this URL, they receive an HTTP 403 Forbidden."*

---

### Step 7: Closing Summary
- **Talking Point**:
  > *"To summarize: AlertLens solves alert fatigue through a deliberate, defensible architecture:*
  > 1. *Hybrid semantic clustering combining rule-based entity constraints with dense embeddings.*
  > 2. *Multi-factor risk scoring with MITRE ATT&CK alignment.*
  > 3. *Real-time event-driven push via PostgreSQL LISTEN/NOTIFY.*
  > 4. *Human-in-the-loop accountability with a verifiable audit trail.*
  >
  > *Thank you, we're ready for your questions!"*

---

## 🔑 Demo Credentials Reference
| Role | Username | Password | Key Capability to Show |
|---|---|---|---|
| **Analyst** | `analyst_demo` | `demo1234` | Triage, view briefs, acknowledge incident |
| **Admin** | `admin_demo` | `admin1234` | All analyst features + Enterprise Audit Trail |
