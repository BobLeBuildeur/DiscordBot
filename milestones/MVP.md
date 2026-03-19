# MVP Milestone

## Problem

Analysts need a first end-to-end product that can generate actionable plans and iteratively improve outputs from human feedback.  
The system currently lacks a unified workflow that (1) orchestrates reasoning into a markdown plan and (2) captures UI comments on HTML for LLM-driven revision.

## Requirements

- Build a reasoning orchestration workflow that generates a plan in markdown from a chain-of-thought process.
- Implement a Svelte UI that allows users to comment on HTML content.
- Build a Python backend that receives HTML comments and feeds them back into the LLM workflow.
- Use ChatGPT via API as the LLM provider for planning and feedback-driven updates.
- Return updated outputs to the UI after comment ingestion and LLM processing.

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
   1. Verify plan generation -> UI rendering -> comment submission -> revised output cycle.
