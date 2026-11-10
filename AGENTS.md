# Naxi AI Studio — Project Instructions

## 1. Project Overview

Project name: Naxi AI Studio
Chinese name: 纳西文化多模态 AI 学习与创作平台

This project is an AI-powered cultural learning and creative platform based on Naxi culture, especially Dongba script, Naxi ancient music, and Naxi Datiao dance.

The platform combines the existing Godot cultural learning game with three independent professional Agent entry points: Dongba handwriting evaluation, music creation and dance video creation.
Streamlit remains the single platform frontend and app.py remains its startup entry. The three Agents share cultural knowledge and infrastructure; do not build a master/orchestrator Agent. Interface contracts and deterministic prototypes must not be presented as implemented Agents.
Milestone 3B implements the first DongbaHandwritingAgent in naxi_agents/dongba_agent.py using one Responses API dual-image request with explicit Mock fallback. Milestone 5 music uses naxi_agents/music_agent.py for one optional model planning request followed by deterministic MIDI/sample rendering. Dance remains an unimplemented contract.

The project is being developed for an Artificial Intelligence Application Competition.

The developer is a beginner in Python and AI engineering. All development decisions must prioritize:
- A working, demonstrable product.
- Clear and maintainable architecture.
- Low development cost and short implementation time.
- Explainable technical decisions.
- Future extensibility.

Do not over-engineer the initial demo.

## 2. Core Product Modules

### Module A: 东巴文 AI 临摹评价 (Target-conditioned Handwriting Evaluation)

Priority: HIGHEST. This is the core demonstration feature.

Main workflow:
1. Select one of the five existing target glyphs from data/glyphs/glyph_catalog.csv. Map character_id to glyph_id at the service boundary; do not change CSV columns.
2. Display the reference glyph and user-provided Chinese meaning. Do not invent pronunciation, stroke order or expert verification.
3. User writes with a mouse on an online canvas or uploads a photograph of paper handwriting.
4. Preprocess both images and compare handwriting against the selected target.
5. Measure shape similarity, proportions, position/direction and regional structure.
6. Provide explainable errors and specific Chinese learning suggestions.
7. Display the reference and submitted handwriting side by side, with measured scores and limitations.

Important requirements:
- This is target-conditioned handwriting evaluation, NOT general OCR or unknown-character identification.
- This module remains the highest development priority. Preserve the existing music and dance architecture.
- Reject clearly incorrect writing; never force a positive assessment. For large differences say:
  “当前书写与目标字差异较大，无法判定为正确临摹，请重新观察示范字。”
- Local prototype similarity scores must be computed from images. The real vision result similarity_score is a model-estimated visual similarity, explicitly uncalibrated and not recognition accuracy. Display and store the two sources separately; do not pass model estimates off as measured scores or human labels.
- Real evaluation uses one non-streaming OpenAI Responses API request with two images and six-field validated JSON output. No tool loop, automatic retries or automatic model replacement.
- Four final statuses are match/close/incorrect/uncertain. Blank, tiny, dark or heavily blurred inputs may be rejected locally with source=quality_check; API/key/model/JSON failures automatically fall back to explicitly labelled Mock with a safe fallback_reason.
- Mock mode is explicitly labelled, uses local measurements and never calls the API. USE_REAL_AI=true enables real-first evaluation; otherwise use Mock only. Retain the page Mock override.
- Without real glyph data, provide a standard data interface and explicit missing-data state. Non-cultural geometric test fixtures must never appear as Dongba teaching characters.
- Support future import from the existing Godot teaching game without modifying that repository.
- Keep local measurement in services/dongba_evaluator.py, image quality in services/handwriting_quality.py, API/result validation in services/dongba_vision.py and orchestration in naxi_agents/dongba_agent.py. Do not put algorithms or keys in pages.
- Reserve training records with character_id, reference_image, user_handwriting_image, similarity_label, structure_errors, evaluation_feedback and data_source. Do not collect player images automatically or treat prototype scores as human labels.
- Do not claim that a general vision model is a specialized Dongba handwriting recognition model.
- Clearly distinguish measured image similarity, model-assisted analysis and sourced cultural interpretation.
- Do not invent Dongba meanings, pronunciations, or historical origins.
- If the result is uncertain, explicitly say so.
- Preserve alternative interpretations when reliable sources disagree.
- Make it possible to replace the local evaluation prototype with a specialized metric-learning model and optional vision assistance in the future.

### Module B: Naxi Ancient Music AI Studio

Main workflow (Milestone 5):
1. Upload MIDI or supported partwise MusicXML/MXL; no free composition mode.
2. Parse real note/tempo/meter/structure events and show limitations; do not fake PDF/image recognition.
3. Choose existing instrument labels, Dongjing/Baisha reference category and melody retention.
4. Query data/music/music_library.sqlite3 and read-only original recordings.
5. Use one optional Responses API planning call (USE_REAL_AI / OPENAI_API_KEY / MUSIC_MODEL), or explicitly labelled local rules; no audio upload.
6. Python tools arrange MIDI and synthesize at most 30 seconds of WAV from limited real samples, excerpts and clearly labelled auxiliary sound.
7. Play and download actual output; show per-source usage and planning provenance.

Important:
- Music labels and directory categories are not verified audio identities or traditional composition rules.
- The current 笛子.mp3 is byte-identical to baisha_01.mp3; never use it as an isolated flute sample.
- Auto pitch candidates support only +/-3 semitones and may contain other sound. Do not claim a complete playable instrument library.
- Ensemble recordings provide acoustic reference only; do not use them as isolated instrument samples.
- Distinguish AI planning, deterministic synthesis and local-rule fallback. Do not call a local rule plan an AI result.
- Do not label the adaptation as authentic traditional Naxi music; culturally validated style analysis remains future work.
- Do not invent musical rules or instrument histories. Do not modify/delete/move original recordings.

### Module C: Naxi Datiao AI Video Studio

Main workflow:
1. User uploads a dance video or reference material.
2. User selects Naxi clothing and visual style.
3. User selects a Lijiang-related background.
4. The system calls a suitable image/video generation API.
5. The user previews the generated result.

Possible future features:
- Motion reference extraction.
- AI video generation.
- Naxi costume replacement.
- Lijiang Ancient Town backgrounds.
- Personalized Datiao videos.

For the initial demo, a working API integration or clearly labelled pre-generated demonstration video is acceptable.

Never pretend that a video was generated when it is only a static sample.

## 3. Technical Architecture

The intended architecture is:

Frontend:
- Streamlit for the initial demo.
- Five pages: home, Godot learning game, Dongba evaluation, music creation and dance video creation; use st.Page and st.navigation.
- Connect existing Godot Web exports by URL (GODOT_WEB_URL) or a read-only local file server. Never modify, copy or move the original game resources as part of this integration.
- Python-based web interface.
- Chinese user interface.

Backend:
- Python.
- OpenAI Agents SDK is not installed in the current environment. Milestone 3B uses the authorized Responses API fallback and a single-request visual workflow. Project implementations live under naxi_agents to avoid the SDK's agents import name; retain old agents/ contracts without using them as runtime implementations.
- Lightweight custom Agent Harness.

AI models:
- GPT or other suitable language models.
- Vision recognition APIs.
- Music generation APIs.
- Video generation APIs.

Knowledge layer:
- RAG (Retrieval-Augmented Generation).
- SQLite for initial structured data.
- JSON for simple dictionaries and configuration.
- A vector retrieval system may be added when justified.

Agent capabilities:
- Task understanding.
- Tool selection.
- Tool execution.
- Context management.
- Knowledge retrieval.
- Result verification.
- Error handling.

The architecture should combine autonomous Agent decisions with deterministic workflows.

Do not force every task to use an LLM.
Use ordinary Python functions for predictable operations, validation, scoring, and data processing.

## 4. Agent Harness Design

The Harness should gradually provide:

1. Task and execution management.
2. Tool registration and invocation.
3. Input and output validation.
4. Permission and API access control.
5. Execution status and error handling.
6. Logging and execution traces.
7. Context and conversation management.
8. Result verification.

The Agents SDK may provide the core Agent execution loop and tool orchestration.

Additional Harness capabilities should be implemented only when needed.

Do not build a complicated custom Agent framework from scratch.

## 5. Tools and Skills

Tools are executable functions that the Agent can call.

Initial planned tools:

- evaluate_dongba_handwriting
- search_dongba_dictionary
- retrieve_cultural_knowledge
- evaluate_handwriting_result
- generate_music
- inspect_music_parameters
- generate_dance_video
- search_naxi_costume
- recommend_cultural_attractions

Skills are reusable domain-specific instructions.

Planned skills:

- dongba_handwriting_evaluation
- dongba_cultural_interpretation
- naxi_music_composition
- naxi_datiao_knowledge
- naxi_cultural_content_review

Do not confuse Skills with model fine-tuning.

## 6. Cultural Knowledge and Data Integrity

The project concerns living cultural heritage.

All cultural knowledge must be handled carefully.

Requirements:

- Prefer authoritative academic publications, cultural institutions, museums, and verified databases.
- Record the source of every important cultural claim.
- Preserve original terminology and alternative interpretations.
- Distinguish established facts from hypotheses.
- Do not invent historical connections between Dongba script and oracle bone script.
- Do not treat visual similarity as proof of historical origin.
- Respect copyright, database access terms, and personal information.
- Do not scrape or reuse restricted databases without permission.

The system should support source-based answers and traceable knowledge retrieval.

## 7. Development Environment

Current environment:

- Operating system: Windows.
- Project directory: D:\Projects\Naxi_AI_Demo
- Python: 3.14.3
- Virtual environment: .venv
- Streamlit: installed and verified.
- VS Code: installed.
- Git: installed and initialized.
- Codex VS Code extension: installed.
- Current Codex extension version: 26.1007.21434.

Always use the project's virtual environment.

Do not modify the user's global Python installation.

Do not modify the original Godot project or other repositories.

## 8. Project Structure

Use the following structure as the target architecture:

Naxi_AI_Demo/
│
├── AGENTS.md
├── .gitignore
├── requirements.txt
├── README.md
├── app.py
│
├── pages/
│   ├── dongba.py
│   ├── music.py
│   └── dance.py
│
├── agents/
│   ├── dongba_agent.py
│   ├── music_agent.py
│   └── dance_agent.py
│
├── tools/
│   ├── dongba_tools.py
│   ├── music_tools.py
│   └── dance_tools.py
│
├── skills/
│   ├── dongba_handwriting_evaluation.md
│   ├── naxi_music.md
│   └── naxi_datiao.md
│
├── services/
│   ├── dongba_evaluator.py
│   ├── dongba_data.py
│   ├── vision_service.py
│   ├── music_service.py
│   ├── dance_service.py
│   └── retrieval_service.py
│
├── database/
│   ├── db.py
│   └── schema.sql
│
├── data/
│   ├── dongba/
│   ├── music/
│   └── dance/
│
├── materials/
│   ├── images/
│   ├── audio/
│   └── video/
│
├── config/
│   └── settings.py
│
└── tests/

This is the intended structure, not a requirement to create every file immediately.

Create files only when their functionality is needed.

## 9. Security

- Never hardcode API keys.
- Store secrets in .env or Streamlit secrets.
- Dongba API settings read project-root .env with python-dotenv; process environment overrides it. DONGBA_VISION_MODEL defaults to gpt-6-luna. Use the official OpenAI endpoint; do not log requests, keys or Base64 images.
- Save optional learning metadata to the per-user NaxiAIStudio/learning.sqlite3 outside the repository. Store source/mock flag, character_id, input method, UTC timestamp, status, score and suggestions; no uploaded image or stroke data is automatically persisted. This is a single-user local demo, not a multi-user account system.
- Canvas submissions retain ordered stroke coordinates in session and allow explicit download. Photographs cannot establish stroke order. Original glyph files are read-only.
- Never commit .env or secrets.toml.
- Provide .env.example with placeholder values only.
- Do not expose API keys in frontend code or logs.
- Validate uploaded files and file sizes.
- Restrict unnecessary filesystem access.
- Do not execute arbitrary commands supplied by users.

## 10. Git and Version Control

Use local Git for version management.

Do not create GitHub branches, pull requests, or remote repositories unless explicitly requested.

Before major modifications:
1. Check git status.
2. Explain the intended changes.
3. Preserve the ability to restore the previous version.

After completing a meaningful milestone, summarize the changes and suggest a Git commit.

Never overwrite existing user files without checking their contents.

## 11. Codex Working Rules

The developer is an AI engineering beginner.

Codex must act as both:
- A software developer.
- A technical mentor.

For every significant development task:

1. Inspect the existing project before editing.
2. Explain the proposed solution briefly.
3. Identify which files will be created or modified.
4. Implement the smallest working version.
5. Run relevant tests.
6. Fix errors before claiming completion.
7. Explain what was implemented and how it works.

Avoid:
- Creating unnecessary files.
- Rewriting working code without a reason.
- Installing excessive dependencies.
- Introducing complex frameworks without justification.
- Making multiple unrelated changes in one task.
- Pretending that an API integration works without testing it.

Prefer complete milestones over excessively fragmented instructions.

When a task can be completed safely as a coherent unit, complete it in one operation.

If an important technical decision is uncertain, explain the alternatives and ask the developer before committing to an irreversible choice.

## 12. Initial Development Priorities

Development should follow this order:

Phase 1: Working application skeleton
- Create the Streamlit homepage.
- Create three functional module pages.
- Establish shared styling and navigation.
- Ensure the application runs locally.

Phase 2: Target-conditioned Dongba handwriting evaluation (current highest priority)
- Establish a reviewed reference-glyph catalog and Godot import contract; do not invent cultural data.
- Implement online mouse drawing and photographed-handwriting upload, preview and preprocessing.
- Implement a local shape/structure comparison prototype with explainable Chinese feedback.
- Test clear mismatches, blanks, missing structure and natural handwriting variation.
- Display computed similarity and prototype limitations, not recognition accuracy.
- Reserve vision API and consent-based training-data interfaces; later explore Siamese Networks or metric learning when real labeled samples are available.
- Add vision-assisted analysis and Agent feedback only after the local workflow works.

Phase 3: Music generation
- Select a suitable music API.
- Implement generation parameters.
- Generate and play audio.

Phase 4: Dance video generation
- Select a suitable video API.
- Implement reference upload and generation parameters.
- Generate or display a clearly labelled demonstration result.

Phase 5: Agent integration
- Connect the tools to the Agents SDK.
- Implement the lightweight Harness.
- Add execution traces and result validation.
- Integrate RAG.

Phase 6: Competition preparation
- Improve interface quality.
- Test all modules.
- Prepare a reliable offline fallback.
- Prepare system architecture diagrams and demonstration materials.

## 13. Important Project Principle

The goal is not to add AI labels to a traditional game.

The goal is to build a real AI-powered cultural learning and creation system.

Every AI capability must have a clear purpose, a real technical implementation, and a demonstrable result.

Prioritize cultural accuracy, technical credibility, user experience, and future extensibility.
