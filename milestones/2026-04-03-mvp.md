# Minimum Viable Product (MVP) Milestone

## Problem

The PoC validated the core conversational loop (problem → clarify → plan → refine) and a business-native experience for Analysts. It deliberately stayed simple: single-node, file-backed persistence, minimal security, no tool execution, no production build pipeline, and no first-class knowledge management.

The MVP must turn that validated experience into something **deployable**, **multi-user**, and **extensible**: agents need concrete **tools** as first-class actions, the product needs **identity and administration**, the **Build** stage moves from placeholder to implemented capability, and organizations need a structured way to own **Guidelines and Standard Operating Procedures (SOPs)** so agent behavior aligns with how the business actually works.

**Outcomes when this milestone is met:**

- Analysts can use the product in a realistic multi-user setting with auditable sign-in and an administrative path to onboard users.
- Agents can select and run approved tools as orchestration actions, not only LLM text generation.
- Approved plans can progress into a **Build** stage where an **LLM uses chain-of-thought reasoning** to execute the plan step by step, refine deliverables with confidence checks, and return a final report to the Analyst.
- Knowledge Admins can maintain organizational knowledge (Guidelines, SOPs) that agents and workflows can reference consistently.
- The stack can be **deployed** to serve early external users, and the **UI** follows a documented design system so the experience stays coherent as features grow.

## Requirements

### Tools (agent actions)

- **ARO:** Register and invoke tools with outputs flowing back into session context for orchestration runtime and adapters.
- **User Story:** As an **Analyst**, I want agents to **use approved tools in a session** so that **my work is grounded beyond chat**.
- **User Story:** As an **Agent**, I want a **bounded tool surface** so that **I complete tasks predictably**.

**Won’t do (for scoping later plans):** An unbounded marketplace of third-party tools without review; tools that bypass auth or tenant boundaries.

### User management

- **ARO:** Verify usernames and passwords with salted slow-hash checks and issued sessions for user management service and auth APIs.
- **ARO:** Bootstrap master admin with a secure first-admin path on deploy for bootstrap flow and user service.
- **User Story:** As an **Analyst**, I want to **sign in with my own account** so that **my sessions stay private to me**.
- **User Story:** As an **Admin**, I want to **create and manage users** so that **my team avoids shared credentials**.

**Won’t do:** Full enterprise IdP (SAML/OIDC), fine-grained RBAC, or compliance certifications as mandatory MVP deliverables—those may follow once identity exists.

### Build stage

Build **executes an approved plan** by driving an **LLM with chain-of-thought reasoning** (explicit intermediate reasoning in the execution path, not a single opaque completion). The runtime keeps **full plan context** in scope for the model for the whole Build.

**Execution model**

1. **Plan context** — The LLM receives the approved plan (and relevant session context, e.g. prior clarifications) as grounding for every Build turn.
2. **Per plan step** — For each step in order:
   1. **Execute the step** — Follow the step instructions and **produce or update a deliverable** (document, structured output, or other artifact type defined in implementation plans).
   2. **Self-critique** — The model proposes **what could make this better** (concrete improvements) together with a **confidence level** that the step’s deliverable is complete enough to proceed.
   3. **Refine** — **Iterate on the deliverable** using that critique and confidence signal (and any prior sub-step outputs for the same plan step, as designed).
   4. **Confidence gate** — If confidence is **below a configurable threshold**, return to (2.1) for that step and refine again; otherwise move on to the next plan step.
3. **Completion** — After **all steps** finish, **report results to the user** (summary, links or copies of deliverables, and any caveats), aligned with streaming or polling patterns used elsewhere in the product.

**Guardrails**

- **Cap iterations:** Per-step refinement loops (and, if applicable, global Build retries) are **limited to a configurable maximum count** so execution cannot spin indefinitely when confidence stays low.
- When max iterations is reached, **surface exhaustion to the user** (no silent stop).

- **ARO:** Run Build with LLM chain-of-thought over approved plan context producing step deliverables and durable artifacts in orchestration and worker or job interfaces.
- **ARO:** Drive per-step refine loop with “what could make this better,” confidence scores, configurable completion threshold, and configurable max iterations for orchestration Build state machine.
- **ARO:** Emit final Build report to the client with outcomes per step after all steps complete for orchestration API and UX.
- **User Story:** As an **Analyst**, I want **approved plans to run to execution** so that **I get delivered work from a plan**.
- **User Story:** As an **Analyst**, I want **Build to show progress and a final summary** so that **I can trust and use the outputs**.

**Won’t do:** Arbitrary unsandboxed code execution on analyst machines; full RPA coverage of every backend system unless explicitly planned.

### Knowledge (Guidelines and SOPs)

- **ARO:** Create model describing knowledge for knowledge-service.
- **ARO:** Expose CRUD for Guidelines and SOPs with auditable agent-readable content through storage, APIs, and orchestration integration.
- **User Story:** As a **Knowledge Admin**, I want to **publish and update Guidelines and SOPs** so that **org standards stay current for agents and plans**.
- **User Story:** As an **Analyst**, I want **agent outputs to follow documented SOPs** so that **I can use them in strict processes**.

**Won’t do:** A full enterprise CMS; opaque file dumps with no structure for agents to cite or retrieve.

### Non-functional: deployment strategy

- **ARO:** Package services, wire config/secrets, and document bring-up so operators reproduce environments without a dev laptop using containers, CI/CD, and runbooks.

### Non-functional: design system

- **ARO:** Ship tokens, components, and usage docs so MVP UI stays consistent and new features reuse the library in frontend packages and contributor docs.

## Work Breakdown Structure

1. **Tools**
   1. Define tool contract (registration, schemas, errors, timeouts).
   2. Integrate tool calls into orchestration state machine and persistence.
   3. Ship at least one reference tool and tests that prove round-trip behavior.
2. **User management service**
   1. Data model for users, credentials (hash + salt), and admin flag or role representation.
   2. APIs for authentication, bootstrap/master admin, and user CRUD for admins.
   3. Integrate protected routes in orchestration and/or API gateway as architecture dictates.
3. **Build stage**
   1. Specify Build inputs (approved plan, session context), deliverable types, and persistence of step artifacts.
   2. Implement LLM-driven per-step execution with chain-of-thought, self-critique (“what could make this better”), confidence scoring, threshold loop, and **configurable max iterations** per step (or per Build).
   3. Implement final user-facing Build report after all steps complete.
   4. Surface Build status to the client (streaming or polling, aligned with existing patterns).
4. **Knowledge**
   1. Model Guidelines and SOPs (metadata, body format, ownership).
   2. Admin and analyst-facing flows for authoring and publishing.
   3. Wire retrieval or injection into agent/orchestration prompts where appropriate.
5. **Deployment**
   1. Container images or equivalent packaging for required services.
   2. Environment configuration and secrets strategy.
   3. Operator documentation for install and upgrade.
6. **Design system**
   1. Token and component baseline aligned with current product UI.
   2. Documentation for usage and extension.
   3. Refactor critical paths to consume shared components (incremental as needed).

## Relationship to the PoC

The PoC milestone in `milestones/PoC.md` remains the baseline for the conversational planning loop. The MVP **extends** that foundation with identity, tools, Build execution, knowledge, and production-minded packaging—without re-litigating the core clarify/plan/refine UX unless discovery shows a necessary adjustment.

## Implementation Notes

- Detailed execution belongs in dated plans under root `plans/` per `.cursor/rules/feature-planning.mdc`; this milestone defines **what** the MVP must achieve, not every file-level change.
- Prefer explicit service boundaries (e.g. user management as its own deployable or logical service) to match monorepo rules in `.cursor/rules/monorepo.mdc`.
