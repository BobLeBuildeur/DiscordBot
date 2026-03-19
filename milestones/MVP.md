# MVP Milestone

## Problem

Analysts need a first end-to-end product that can generate actionable plans and iteratively improve outputs from human feedback.  
The plan is expressed in markdown by the orchestration system and converted to HTML in the UI for review and commenting.

This MVP also validates a market gap: business teams need agentic LLM workflows that are usable by average office workers who are not technical, are not interested in code as a deliverable, and do not use developer tools such as Cursor.  
The current gap is the lack of a business-native experience that preserves powerful LLM reasoning while presenting work in familiar document-review patterns (read, comment, revise) instead of coding workflows.

## Core Workflow Model (Plan -> Revise -> Build)

The system follows a Plan -> Revise -> Build workflow for back-office tasks.

1. Plan
   - The user prompts the system to propose a structured plan for completing a task.
   - Example prompts:
     - Analyze sales performance
     - Build a monthly operations report
     - Create a market analysis presentation
   - The system proposes:
     - Steps
     - Required data sources
     - Analysis methods
     - Expected outputs

2. Revise
   - The user reviews and edits the proposed plan before execution.
   - Revision can happen through:
     - Natural language feedback
     - Comments added directly on the HTML representation of the markdown plan (similar to coworker comments in a Word document)
     - Adding constraints or instructions
   - Each comment is captured with:
     - The comment text
     - The location/anchor in the document where the comment was made
   - The backend injects comment text plus document location back into the LLM prompt to refine the plan.
   - This stage ensures:
     - Business context is captured
     - The analytical direction is correct
     - Organizational standards are respected

3. Build *(for context only, outside MVP scope)*
   - Once approved, agents execute the full plan by:
     - Retrieving data
     - Running analysis
     - Producing structured outputs
     - Creating final artifacts (tables, charts, slides)
   - Execution occurs using complete datasets.

## Requirements

- Build a reasoning orchestration workflow for the Plan stage that generates a plan in markdown from a chain-of-thought process.
- Support the Revise stage by allowing users to review and edit the plan before execution.
- Implement a Svelte UI that renders the markdown plan as HTML and supports location-specific comments on that HTML.
- Build a Python backend that receives comments plus document location metadata and feeds both back into the LLM workflow.
- Use ChatGPT via API as the LLM provider for planning and feedback-driven updates.
- Return updated outputs to the UI after comment ingestion and LLM processing.
- Keep the Build stage explicitly out of MVP scope; include it only as future workflow context.

## Work Breakdown Structure

1. Reasoning orchestration
   1. Define orchestration steps for prompt intake, reasoning execution, and markdown plan output.
   2. Implement markdown plan renderer/formatter in backend flow.
2. Feedback UI
   1. Build Svelte interface for rendering markdown-as-HTML and attaching comment threads/annotations at specific locations.
   2. Capture and submit comment text with location anchors to backend endpoints.
3. Backend feedback loop
   1. Implement Python API endpoints for comment intake, location metadata, and context persistence.
   2. Rehydrate the plan plus comments (with location context) into LLM refinement prompts.
4. LLM integration
   1. Integrate ChatGPT API client and request pipeline.
   2. Handle retries, response validation, and error states.
5. End-to-end validation
   1. Verify Plan -> Revise cycle: plan generation -> UI rendering -> comment submission -> revised plan output.
6. Future scope placeholder (non-MVP)
   1. Document Build-stage execution requirements for a later milestone.
