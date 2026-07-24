# Single-User Learning Compiler

> An exploratory, CLI-first derivative concept inspired by [NSA SkillTree](https://github.com/NationalSecurityAgency/skills-service). It is not affiliated with, endorsed by, or a replacement for the NSA project.

This repository is presently a **design fork**. Its inherited SkillTree source
is retained unchanged while the project is re-scoped from a centralized,
multi-user gamification service into a local tool that compiles a bounded body
of knowledge into an inspectable course for one person.

The source fork relationship is intentional: it preserves provenance and makes
the conceptual inheritance explicit. The original [SkillTree documentation](https://skilltreeplatform.dev/)
and its [Apache License 2.0](LICENSE.txt) remain the relevant upstream
references.

## The thesis

SkillTree's durable insight is its learning model:

```text
training profile → subjects → skills → events / checks → badges / paths
```

For a solitary learner, almost all of the surrounding enterprise machinery is
counterproductive. The port therefore retains the relationship between a
learning unit, evidence of performance, and progress, while changing the model
to:

```text
course → class → lesson → practice → benchmark → local qualification
```

The result should be an offline-first **learning compiler plus a private
evidence ledger**, not a reduced LMS.

## Scope

### Included

- A local command-line workflow for turning a source dossier into a static
  course package.
- Human-authored or AI-proposed course structures that are persisted as
  reviewable Markdown/YAML/JSON artifacts.
- Evidence-linked claims, outcome contracts, prerequisite graphs, lessons,
  practice, benchmarks, review schedules, and local learner state.
- Static Markdown and HTML output, plus a terminal study experience.
- Qualifications that record demonstrable completion within a named local
  course, with evidence and version metadata.

### Explicitly excluded

- Servers, HTTP APIs, accounts, authentication, roles, organisations, tenants,
  and shared databases.
- Administrator dashboards, leaderboards, rankings, peer comparison, corporate
  reporting, notifications, approval queues, and embedded-app event reporting.
- A browser-first authoring interface in the initial release.
- Claims that a local qualification is an employer, regulatory, academic, or
  third-party credential.

## Learning-content pipeline

```text
source dossier
  → evidence cards
  → scope + outcome contract
  → concept / dependency graph
  → class outline
  → atomic lessons
  → practices + benchmarks
  → qualification rules
  → static build + validation
  → learn / retrieve / demonstrate / record
  → revise from failures
```

Every transition produces a durable local artifact. An AI may propose a stage,
but no stage exists only as an unrecoverable chat response.

### 1. Source dossier and evidence cards

Input may be local Markdown or text, extracted PDF text, retrieved web sources
saved with their metadata, or a user-authored brief. Each source has an ID,
provenance, retrieval date, rights/licence note, content hash, and anchors such
as a page, section, or paragraph.

An evidence-backed course must trace assertions in its teaching material to
those anchors. A course created solely from personal notes remains allowed, but
is marked `draft` rather than evidence-backed.

### 2. Outcome contract

Before any lesson is generated, the author specifies:

- learner profile and prerequisites;
- scope, exclusions, and intended time budget;
- three to eight terminal capabilities, each stated as an observable action;
- evidence required for each capability;
- safety, currency, and scheduled review requirements.

This prevents a source book from being flattened into a sequence of summaries
that never asks the learner to do anything with the knowledge.

### 3. Course graph, classes, and lessons

The compiler builds a directed acyclic graph of concepts and prerequisites. A
`class` groups three to seven related lessons around a coherent sub-capability.
A `lesson` is atomic: one objective, explanation, source claims, retrieval
prompt, practice activity, and completion condition.

### 4. Benchmarks before qualifications

Each terminal capability maps to a benchmark. The available modes are:

1. `recall` — closed-book answers or flash prompts;
2. `reason` — explain, compare, diagnose, or calculate;
3. `produce` — create a local artifact against a rubric;
4. `perform` — complete a procedure, optionally with outside verification.

The highest appropriate mode—not a completion counter—determines whether a
qualification can be issued.

### 5. Static build and private learning loop

The canonical course is authored as Markdown/YAML and built to readable
Markdown, printable HTML, and a machine-readable course manifest. Learner
state is stored separately. The CLI presents the next dependency-ready lesson,
runs recall and benchmarks, retains attempts, and schedules later review. No
network listener is required.

## Domain translation from SkillTree

| SkillTree | Learning compiler |
| --- | --- |
| Project | Course: bounded subject to master |
| Subject | Class: coherent domain unit |
| Skill | Lesson: one observable capability |
| Skill event | Local practice/retrieval record |
| Quiz | Benchmark with a pass threshold |
| Badge | Qualification with retained evidence |
| Learning path | Dependency graph and recommended order |
| Points/levels | Optional private momentum indicator, never a credential |

## Canonical course package

```text
courses/roman-survey/
  course.yaml                 # contract, scope, version, source-hash set
  sources/
    dossier.md
    evidence-cards.yaml
  graph.yaml                  # concepts and prerequisite edges
  classes/
    01-origins.yaml
    02-republic.yaml
  lessons/
    origins-01.md
    republic-03-caesar-crosses-the-rubicon.md
  benchmarks/
    diagnose-republic-crisis.yaml
  qualifications/
    roman-foundations.yaml
  rubrics/
    historical-explanation.yaml
  state/                      # private local state; ignored by default
    learner.json
  dist/
    index.md
    index.html
    course.json
  audit/
    generation.json
    validation-report.json
```

`course.yaml` is the stable contract. Markdown is the comfortable editing
surface; YAML/JSON make dependency validation and static rendering
deterministic. Course material may be versioned in Git, while `state/` is
private by default.

## Minimum lesson contract

```yaml
id: republic-03-caesar-crosses-the-rubicon
class: republic
title: Why Caesar's crossing mattered
objective: Explain why the crossing changed the constitutional conflict.
requires: [republic-02-first-triumvirate]
source_claims: [SRC-014#p18, SRC-021#ch7]
teach: lessons/republic-03-caesar-crosses-the-rubicon.md
retrieval:
  - prompt: What legal and political boundary did Caesar cross?
    expected_elements: [Italy, command, civil-war]
practice:
  type: reason
  prompt: Contrast Caesar's act with a normal provincial command transition.
completion:
  type: short_answer
  rubric: rubrics/historical-explanation.yaml
  pass: 0.75
review: [1d, 7d, 30d]
```

The validator must ensure unique IDs, resolvable dependencies, an acyclic
graph, a practice activity for every objective, source anchors for asserted
teaching claims, benchmark coverage of terminal outcomes, and qualification
rules that require more than unchecked completion.

## CLI contract

```bash
# authoring / staticization
learn init roman-survey --from sources/brief.md
learn ingest roman-survey sources/*.md
learn evidence roman-survey
learn outline roman-survey --ai       # writes a proposal; does not publish it
learn compile roman-survey --ai       # emits structured lesson/benchmark drafts
learn validate roman-survey --strict
learn build roman-survey --html --markdown

# learning
learn start roman-survey
learn next
learn lesson republic-03-caesar-crosses-the-rubicon
learn recall due
learn benchmark diagnose-republic-crisis
learn qualify roman-foundations
learn status

# repair
learn audit roman-survey --claims --outcomes --coverage
learn revise roman-survey --from-attempts
```

The `--ai` flag is an adapter boundary, never a hidden dependency. It receives
a versioned input bundle and writes a structured proposal plus generation
provenance: model, prompt-template version, date, and input hashes. The course
can be authored, validated, built, and studied without an AI provider or a
network connection.

## Qualification contract

```yaml
id: roman-foundations
requires:
  lessons_completed: [origins-01, origins-02, republic-01, republic-02, republic-03]
  benchmarks:
    - id: diagnose-republic-crisis
      minimum_score: 0.80
      attempts_within_days: 30
  review_items_passed: 6
issues:
  label: Roman Foundations (local course qualification)
  evidence_file: state/qualifications/roman-foundations.json
```

An issued record contains the course version, source-hash set, benchmark
version, date, outcome, and resulting evidence artifact. Material course
changes can mark an earlier qualification `stale` and prescribe a delta
benchmark. This is intentionally evidence rather than a decorative badge.

## Delivery sequence

1. Implement a local CLI using canonical YAML/Markdown, schema validation, and
   JSON or SQLite learner state.
2. Ship manual authoring, strict validation, terminal study, short-answer
   capture, basic scoring, and static Markdown/HTML build.
3. Add an AI compiler that emits validated proposals instead of opaque prose.
4. Add rubric-assisted evaluation with explicit human override and retained
   attempt artifacts.
5. Add spaced review, diagnostics, and portable import/export only after the
   core contract is stable.

## Status

No application code has been changed in this preliminary fork. This README is
the implementation contract for the first clean-room, single-user version.
