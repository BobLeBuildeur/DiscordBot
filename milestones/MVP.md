# Minimum Viable Product (MVP) Milestone

## Problem

The PoC validated the core conversational loop (problem → clarify → plan → refine) and a business-native experience for Analysts. It deliberately stayed simple: single-node, file-backed persistence, minimal security, no tool execution, no production build pipeline, and no first-class knowledge management.

The MVP must turn that validated experience into something **deployable**, **multi-user**, and **extensible**: agents need concrete **tools** as first-class actions, the product needs **identity and administration**, the **Build** stage moves from placeholder to implemented capability, and organizations need a structured way to own **Guidelines and Standard Operating Procedures (SOPs)** so agent behavior aligns with how the business actually works.

**Outcomes when this milestone is met:**

- Analysts can use the product in a realistic multi-user setting with auditable sign-in and an administrative path to onboard users.
- Agents can select and run approved tools as orchestration actions, not only LLM text generation.
- Approved plans can progress into a **Build** stage that executes or dispatches work according to defined rules (scope to be bounded in implementation plans).
- Knowledge Admins can maintain organizational knowledge (Guidelines, SOPs) that agents and workflows can reference consistently.
- The stack can be **deployed** to serve early external users, and the **UI** follows a documented design system so the experience stays coherent as features grow.

## Requirements

### Tools (agent actions)

- **ARO:** Extend orchestration so that **invoking a registered tool** is one of the actions the agent runtime can take, alongside LLM turns; **results** are fed back into session context; **objects** are the orchestration server (and any tool adapters), with explicit registration and guardrails.
- **User story:** As an **Analyst**, I want agents to use approved tools during a session so that outputs are grounded in actions beyond chat (e.g. retrieval, structured transforms, or integrations we define in scope).
- **User story:** As an **Agent** (system persona), I want a clear, bounded tool surface so that I can complete tasks predictably without ad-hoc side effects.

**Won’t do (for scoping later plans):** An unbounded marketplace of third-party tools without review; tools that bypass auth or tenant boundaries.

### User management

- **ARO:** Provide **username/password authentication** with **salted password hashing** using a recognized slow hash (e.g. bcrypt, Argon2); **results** are secure credential verification and session or token issuance per chosen architecture; **objects** are a dedicated **user management service** and integrated API boundaries.
- **ARO:** Bootstrap a **master admin** account (or equivalent secure bootstrap flow) so that **first deploy** has a controlled path to create admins; **results** are no unsecured default-internet admin; **objects** are deployment docs and the user service.
- **User story:** As an **Analyst**, I want to sign in with my own account so that my projects and sessions are not shared with every other user on the instance.
- **User story:** As a **master admin**, I want to create and manage users so that the organization can adopt the product without shared credentials.

**Won’t do:** Full enterprise IdP (SAML/OIDC), fine-grained RBAC, or compliance certifications as mandatory MVP deliverables—those may follow once identity exists.

### Build stage

- **ARO:** Implement the **Build** stage that the PoC documented as future scope—**executing or dispatching** work from an approved plan per product rules; **results** are observable progress and durable artifacts; **objects** are orchestration and any worker or job interfaces we add.
- **User story:** As an **Analyst**, I want an approved plan to move into execution so that the product closes the loop from planning to delivered work, within defined boundaries.

**Won’t do:** Arbitrary code execution on analyst machines without sandboxing and policy; full RPA coverage of every backend system unless explicitly planned.

### Knowledge (Guidelines and SOPs)

- **ARO:** Introduce **knowledge entities** (e.g. Guidelines, SOPs) with **create/read/update** (and minimal lifecycle as needed); **results** are versioned or auditable content suitable for agent consumption; **objects** are storage, APIs, and orchestration integration points.
- **User story:** As a **Knowledge Admin**, I want to publish and update Guidelines and SOPs so that agents and plans reflect organizational standards.
- **User story:** As an **Analyst**, I want agent suggestions to respect documented SOPs so that outputs are usable in regulated or process-heavy environments.

**Won’t do:** A full enterprise CMS; opaque file dumps with no structure for agents to cite or retrieve.

### Non-functional: deployment strategy

- **ARO:** Define and implement a **deployment strategy** (containers, environments, configuration, secrets handling, and minimal runbooks); **results** are that a qualified operator can deploy an instance for early users; **objects** are repo docs, CI/CD or build artifacts, and infrastructure-as-code or equivalent as chosen.
- **Acceptance:** A new environment can be brought up following documented steps without relying on a developer’s laptop as the runtime.

### Non-functional: design system

- **ARO:** Establish a **design system** (tokens, components, patterns) and **documentation** for how new UI should be built; **results** are consistent layout, typography, and interaction patterns across MVP screens; **objects** are the frontend package(s) and contributor-facing docs.
- **Acceptance:** New features can reuse documented components instead of one-off styles.

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
   1. Specify Build inputs/outputs and how they attach to session and plan artifacts.
   2. Implement execution or job dispatch within safety and observability bounds.
   3. Surface Build status to the client (streaming or polling, aligned with existing patterns).
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
