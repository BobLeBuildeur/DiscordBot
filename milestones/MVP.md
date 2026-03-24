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

- **ARO:** **Action:** Register and invoke tools **Result:** outputs flow back into session context **Object:** orchestration runtime and adapters.
- **User Story:** As an **Analyst**, I want agents to **use approved tools in a session** so that **my work is grounded beyond chat**.
- **User Story:** As an **Agent**, I want a **bounded tool surface** so that **I complete tasks predictably**.

**Won’t do (for scoping later plans):** An unbounded marketplace of third-party tools without review; tools that bypass auth or tenant boundaries.

### User management

- **ARO:** **Action:** Verify usernames and passwords **Result:** salted slow-hash checks and issued sessions **Object:** user management service and auth APIs.
- **ARO:** **Action:** Bootstrap master admin **Result:** secure first-admin path on deploy **Object:** bootstrap flow and user service.
- **User Story:** As an **Analyst**, I want to **sign in with my own account** so that **my sessions stay private to me**.
- **User Story:** As an **Admin**, I want to **create and manage users** so that **my team avoids shared credentials**.

**Won’t do:** Full enterprise IdP (SAML/OIDC), fine-grained RBAC, or compliance certifications as mandatory MVP deliverables—those may follow once identity exists.

### Build stage

- **ARO:** **Action:** Execute or dispatch Build work **Result:** observable progress and durable artifacts **Object:** orchestration and worker or job interfaces.
- **User Story:** As an **Analyst**, I want **approved plans to run to execution** so that **I get delivered work from a plan**.

**Won’t do:** Arbitrary code execution on analyst machines without sandboxing and policy; full RPA coverage of every backend system unless explicitly planned.

### Knowledge (Guidelines and SOPs)

- **ARO:** **Action:** CRUD knowledge entities **Result:** auditable agent-readable Guidelines and SOPs **Object:** storage, APIs, and orchestration integration.
- **User Story:** As a **Knowledge Admin**, I want to **publish and update Guidelines and SOPs** so that **org standards stay current for agents and plans**.
- **User Story:** As an **Analyst**, I want **agent outputs to follow documented SOPs** so that **I can use them in strict processes**.

**Won’t do:** A full enterprise CMS; opaque file dumps with no structure for agents to cite or retrieve.

### Non-functional: deployment strategy

- **ARO:** **Action:** Package services, wire config/secrets, and document bring-up **Result:** operators reproduce environments without a dev laptop **Object:** containers, CI/CD, and runbooks.

### Non-functional: design system

- **ARO:** **Action:** Ship tokens, components, and usage docs **Result:** MVP UI stays consistent; new features reuse the library **Object:** frontend packages and contributor docs.

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
