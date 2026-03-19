# MVP Milestone

## Problem

Analysts need a first end-to-end product that can generate actionable plans and iteratively improve outputs from human feedback.  
The system currently lacks a unified workflow that (1) orchestrates reasoning into a markdown plan and (2) captures UI comments on HTML for LLM-driven revision.

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
     - Table manipulation
     - Adding constraints or instructions
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
- Implement a Svelte UI that allows users to comment on HTML content.
- Build a Python backend that receives HTML comments and feeds them back into the LLM workflow.
- Use ChatGPT via API as the LLM provider for planning and feedback-driven updates.
- Return updated outputs to the UI after comment ingestion and LLM processing.
- Keep the Build stage explicitly out of MVP scope; include it only as future workflow context.

## Work Breakdown Structure

1. Reasoning orchestration
   1. Define orchestration steps for prompt intake, reasoning execution, and markdown plan output.
   2. Implement markdown plan renderer/formatter in backend flow.
2. Feedback UI
   1. Build Svelte interface for rendering HTML and attaching comment threads/annotations.
   2. Capture and submit comments to backend endpoints.
3. Backend feedback loop
   1. Implement Python API endpoints for comment intake and context persistence.
   2. Rehydrate context and comments into LLM prompts.
4. LLM integration
   1. Integrate ChatGPT API client and request pipeline.
   2. Handle retries, response validation, and error states.
5. End-to-end validation
   1. Verify Plan -> Revise cycle: plan generation -> UI rendering -> comment submission -> revised plan output.
6. Future scope placeholder (non-MVP)
   1. Document Build-stage execution requirements for a later milestone.
