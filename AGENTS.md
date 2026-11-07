# Naxi AI Studio — Project Instructions

## 1. Project Overview

Project name: Naxi AI Studio
Chinese name: 纳西文化多模态 AI 学习与创作平台

This project is an AI-powered cultural learning and creative platform based on Naxi culture, especially Dongba script, Naxi ancient music, and Naxi Datiao dance.

The goal is to transform the existing Naxi cultural learning game into an AI-native interactive application.

The project is being developed for an Artificial Intelligence Application Competition.

The developer is a beginner in Python and AI engineering. All development decisions must prioritize:
- A working, demonstrable product.
- Clear and maintainable architecture.
- Low development cost and short implementation time.
- Explainable technical decisions.
- Future extensibility.

Do not over-engineer the initial demo.

## 2. Core Product Modules

### Module A: Dongba Script AI Agent

Priority: HIGHEST. This is the core demonstration feature.

Main workflow:
1. User uploads a handwritten Dongba character image.
2. The system preprocesses the image if necessary.
3. A vision model API analyzes the handwritten character.
4. The system retrieves relevant entries from the Dongba knowledge base.
5. The system compares the recognition result with known character information.
6. The Agent generates an explanation and learning feedback.
7. The interface displays the result, confidence/uncertainty, and references.

Important requirements:
- Do not claim that a general vision model is a specialized Dongba handwriting recognition model.
- Clearly distinguish visual recognition, dictionary matching, and cultural interpretation.
- Do not invent Dongba meanings, pronunciations, or historical origins.
- If the result is uncertain, explicitly say so.
- Preserve alternative interpretations when reliable sources disagree.
- Make it possible to replace the initial vision API with a specialized fine-tuned model in the future.

### Module B: Naxi Ancient Music AI Studio

Main workflow:
1. User selects musical style and mood.
2. User selects available instrument timbres.
3. User adjusts musical parameters such as tempo and duration.
4. The system uses a music-generation API or other suitable generation technology.
5. The user can listen to and save the generated result.

The system should gradually incorporate:
- Dongjing music.
- Baisha Fine Music.
- Traditional instrument timbres.
- Cultural and musical constraints.
- Educational explanations of musical structures.

Important:
- Do not label arbitrary AI-generated music as authentic traditional Naxi music.
- Distinguish AI-inspired compositions from historically documented traditional works.
- Do not invent musical rules or instrument histories.

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
- Python-based web interface.
- Chinese user interface.

Backend:
- Python.
- OpenAI Agents SDK where appropriate.
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

- recognize_dongba_image
- search_dongba_dictionary
- retrieve_cultural_knowledge
- evaluate_recognition_result
- generate_music
- inspect_music_parameters
- generate_dance_video
- search_naxi_costume
- recommend_cultural_attractions

Skills are reusable domain-specific instructions.

Planned skills:

- dongba_recognition
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
│   ├── orchestrator.py
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
│   ├── dongba_recognition.md
│   ├── naxi_music.md
│   └── naxi_datiao.md
│
├── services/
│   ├── vision_service.py
│   ├── music_service.py
│   ├── video_service.py
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

Phase 2: Dongba recognition Agent
- Select a suitable vision API.
- Implement image upload.
- Implement initial recognition.
- Establish a small verified Dongba dictionary.
- Implement retrieval and result evaluation.
- Display sources and uncertainty.

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
