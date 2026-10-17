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

## Gamification specification and TODO

Gamification is an optional **local practice layer**, not the course's
credentialing system. It exists to make repeated retrieval varied and inviting;
it must not convert study into a score chase or confuse speed with competence.

### Non-negotiable rules

- All game state is private, local, and usable offline. There are no rankings,
  social comparison, variable-reward monetisation, or notifications designed to
  pull a learner back into the app.
- Every mode has a calm, keyboard-first, untimed alternative. Motion, sound,
  countdowns, and colour-only signals are optional, never required to pass.
- Game scores, streaks, and personal bests are session metadata. They cannot
  unlock a qualification or substitute for a benchmark.
- A course author chooses which modes fit each item. The learner can always
  choose a non-game recall session instead.
- Accuracy, delayed recall, and demonstrated application outweigh response
  speed. Timed modes are recognition refreshers, not evidence of mastery.

### Memorisation-item contract

Lessons expose portable items before any game mode consumes them. An item may
represent a term, relationship, ordered step, diagram location, audio prompt,
claim, error pattern, or scenario decision.

```yaml
id: republic-03-rubicon-boundary
lesson: republic-03-caesar-crosses-the-rubicon
kind: fact
prompt: What political and legal boundary did Caesar cross?
answers:
  accepted: ["the Rubicon", "Rubicon river"]
  required_elements: [Italy, command, civil-war]
directions: [prompt_to_answer, answer_to_prompt]
source_claims: [SRC-014#p18]
media: null
tags: [constitutional-crisis, Rome]
```

The compiler produces proposed items from lesson claims; the author validates
the prompt, accepted answers, ambiguity, and source anchors. Items with an
unresolved or subjective answer cannot enter exact-answer game modes.

### Mode catalogue

| ID | Mode | Core mechanic | Appropriate evidence |
| --- | --- | --- | --- |
| `cards` | Recall Cards | Reveal or type a response, then self-grade or compare. | Initial exposure and light review. |
| `ladder` | Mastery Ladder | Move from recognition to cued recall, typed recall, then discrimination; misses return later. | Default memorisation path. |
| `typeback` | Typeback Loop | Enter the answer; missed items must be answered correctly in a later round. | Vocabulary, names, formulas, exact terms. |
| `dictation` | Dictation | Listen to a prompt and type or speak the answer. | Spelling, pronunciation, language learning. |
| `pairs` | Pair Sprint | Pair shuffled prompts and answers; errors apply a time penalty. | Short recognition refreshers only. |
| `label` | Label Map | Identify or place labels on a supplied diagram, image, map, or code structure. | Spatial/visual knowledge. |
| `error-hunt` | Error Hunt | Identify and correct a false claim, faulty step, or bad inference. | Discrimination and conceptual repair. |
| `scenario` | Scenario Branch | Make a decision in a compact case; reveal consequences and next decision. | Procedure and judgement practice. |
| `grid` | Grid Builder | Correct responses earn pieces used to complete a private board. | Optional reward wrapper around recall. |
| `target` | Target Rush | Select the correct response from transient choices; static mode is always available. | Optional high-energy recognition drill. |
| `exam` | Exam Forge | Configurable mixed retrieval session with review of errors. | Benchmark preparation, never qualification itself. |

`grid` and `target` are visual wrappers, not new learning algorithms. They may
reuse the same `cards`, `ladder`, or `pairs` attempt engine and must not change
whether an answer is considered correct.

### Mastery Ladder algorithm

`ladder` is the mandatory first implementation because it turns game activity
into useful retrieval practice:

1. Present a recognition prompt with plausible distractors when appropriate.
2. Require a cued answer: prompt plus partial cue, then a typed or selected
   response.
3. Require uncued recall in the configured direction.
4. Require discrimination: distinguish the item from a nearby misconception,
   confusable term, or counterexample.
5. Mark the item `provisionally_mastered` only after two correct recall events
   in separate rounds. Schedule it for delayed review at 1, 7, and 30 days.
6. A miss returns the item to the previous difficulty stage, stores the error
   category if known, and shows a source-linked correction before the next
   attempt.

The initial schedule is deterministic and local. A later release may add an
adaptive scheduler, but it must remain explainable and export the evidence for
each scheduling decision.

### CLI contract

```bash
# generate and inspect practice material
learn items build roman-survey --from lessons
learn items validate roman-survey --strict
learn items list roman-survey --lesson republic-03

# run private practice sessions
learn play roman-survey --mode ladder --lesson republic-03
learn play roman-survey --mode typeback --tag constitutional-crisis
learn play roman-survey --mode pairs --count 12 --timed
learn play roman-survey --mode error-hunt --class republic
learn play roman-survey --mode label --asset maps/italy.svg
learn review due

# inspect, never publish, performance data
learn practice status roman-survey
learn practice history republic-03-rubicon-boundary
```

All modes write the same append-only attempt record. A renderer may later make
visual modes available in a local browser, but the CLI remains the reference
runtime and must be fully playable without it.

```yaml
item_id: republic-03-rubicon-boundary
mode: ladder
stage: uncued_recall
occurred_at: 2026-07-24T12:00:00Z
result: correct
response: the Rubicon
elapsed_ms: 6800
score_delta: 0
next_review_at: 2026-07-31T12:00:00Z
course_version: 0.1.0
```

The response text is private learner state. It is never committed by default,
sent to a third party, or used to generate a public profile.

### Fast lane: offline study sets

Not every learner needs a course compiler. A **study set** is a deliberately
thin local package for vocabulary, facts, names, formulas, commands, or any
other prompt–answer pairs. It bypasses the full course pipeline: no evidence
cards, classes, lessons, benchmarks, or qualifications are required.

```text
two-column list → local study set → cards / ladder / typeback → private review queue
```

The simplest accepted file is UTF-8 tab-separated text:

```tsv
front	back
Rubicon	The river Caesar crossed into Italy in 49 BCE.
senatus consultum ultimum	The Senate's "final decree" authorising emergency action.
```

CSV with `front` and `back` headers, a two-column Markdown table, and lines in
the form `front :: back` are also accepted. Import must reject malformed rows,
empty fronts or backs, duplicate fronts unless explicitly allowed, and files
with a delimiter that cannot be determined safely.

```bash
# Create a completely local set and begin studying.
learn import roman-terms.tsv --name roman-terms
learn study roman-terms

# Choose a mode or direction; all state remains local.
learn study roman-terms --mode cards
learn study roman-terms --mode ladder --reverse
learn study roman-terms --mode typeback --limit 20
learn review roman-terms --due

# Inspect or move the portable material without exporting learner responses.
learn sets list
learn sets show roman-terms
learn export roman-terms --format tsv --without-state
```

The importer creates this minimal package:

```text
sets/roman-terms/
  set.yaml                    # name, import metadata, default direction
  items.yaml                  # generated prompt–answer items
  state/
    learner.json              # private, ignored by default
```

`items.yaml` uses the same item contract as courses. Each pair becomes a
forward item (`front → back`); `--reverse` creates or enables a separate
reverse item (`back → front`). The import source is recorded as `user-import`
rather than pretending the set has external evidence or curricular authority.

For unstructured notes, an optional AI-assisted command may propose pairs but
never silently writes them:

```bash
learn import notes.md --extract --ai --name biology-midterm
learn items review biology-midterm --accept-all
```

The first command writes a reviewable proposal; the learner must inspect,
accept, edit, or reject the extracted items. The normal two-column import works
with no account, service, AI provider, or network connection.

## Language-learning framework packs

Language learning is a first-class optional framework, not a one-size-fits-all
course template. The engine supplies reusable learning and assessment
machinery; a **language pack** supplies the linguistic facts, media, variants,
and benchmark adaptations for one target language and locale.

The framework measures what a learner can do across reception, production,
interaction, and mediation—rather than treating language ability as a count of
memorised words. This follows the same action-oriented distinction used by the
[CEFR](https://www.coe.int/en/web/portfolio/the-common-european-framework-of-reference-for-languages-learning-teaching-assessment-cefr-),
whose descriptors define reception, production, interaction, and mediation as
separate activities. CEFR alignment is optional: the tool may report a local
profile without claiming a formal CEFR level.

### Separation of responsibilities

| Reusable language framework | Language and locale pack |
| --- | --- |
| Course graph, review scheduler, game modes, rubrics, recordings, attempt ledger, static build | Writing system, sound/sign system, vocabulary, grammar, examples, audio/video, varieties, cultural notes, benchmark tasks |
| Capability axes and completion evaluator | Which axes apply, target outcomes, pass criteria, accepted variants, source and media provenance |
| Generic item types: cards, dictation, minimal pairs, cloze, dialogue turns, labels, scenarios | Actual items, distractors, transliterations, glosses, translations, recordings, images, and context |

The framework must never invent a default dialect. A target is identified by a
BCP 47-style language–script–region tag where relevant (for example,
`es-419`, `pt-BR`, `sr-Cyrl-RS`), plus a pack-defined name. Script and regional
variation are explicit because a language can have multiple customary scripts
or materially different regional forms. Unicode CLDR treats language, script,
and region as distinct locale dimensions. [Unicode locale guidance](https://cldr.unicode.org/translation/translation-guide-general/default-content)

### Capability axes

Every language profile selects the axes it can credibly assess; none are
silently assumed. Spoken, signed, written, and primarily oral languages can
therefore share a framework without being forced into the same lesson type.

| Axis | Evidence examples |
| --- | --- |
| `reception` | Understand an unfamiliar spoken, signed, audio-visual, or written input; identify gist and necessary details. |
| `production` | Speak, sign, or write an intelligible message for a stated purpose and audience. |
| `interaction` | Sustain a turn-taking exchange, repair a misunderstanding, ask follow-up questions, and respond appropriately. |
| `mediation` | Summarise, paraphrase, translate, or help two parties understand a text or concept. |
| `form` | Use the selected writing system, phonology/handshape, orthography, morphology, and syntax required by the profile. |
| `lexis` | Retrieve and select useful words, fixed expressions, collocations, and domain vocabulary in context. |
| `sociopragmatics` | Select a register, politeness strategy, convention, and cultural reference suitable for the situation. |

`form` is configured per modality: a signed-language pack may select signing
features rather than phonology; an unwritten-language pack may omit literacy;
a multi-script pack may make a particular script an explicit target instead of
assuming transliteration is competence.

### Pack shape

```text
language-packs/es-419/
  pack.yaml                   # target, variants, modalities, licences, version
  profiles/
    foundation.yaml
    everyday-interaction.yaml
  writing/
    orthography.yaml
    keyboard-layouts.yaml
  sound/
    phoneme-inventory.yaml
    minimal-pairs.yaml
  lexicon/
    core.yaml
    domains/food.yaml
  grammar/
    patterns.yaml
    constructions.yaml
  pragmatics/
    registers.yaml
    interaction-repairs.yaml
  media/
    manifest.yaml             # local audio/video/image hashes and rights
  benchmarks/
    foundation.yaml
  sources/
    provenance.yaml
```

`pack.yaml` declares the primary locale, supported alternatives, scripts,
modalities, transliteration policy, default input method, and a review date.
All language claims and media retain source, rights, speaker/performer consent
where applicable, and content hashes. A pack cannot claim audio or dialect
coverage it does not actually provide.

### Reusable progression profiles

Profiles are named by function, not by an unsupported claim of fluency. A pack
may map a profile to a CEFR level only when it ships an explicit descriptor
crosswalk and language-specific benchmark tasks.

| Profile | Purpose | Typical included axes |
| --- | --- | --- |
| `orientation` | Establish sound/sign, script, input, survival vocabulary, and basic classroom directions. | Form, lexis, selected reception/production. |
| `foundation` | Exchange predictable personal information and manage rehearsed everyday micro-tasks. | Reception, production, interaction, form, lexis. |
| `everyday-interaction` | Handle routine transactions, plans, directions, needs, and short personal narratives with repair. | All core axes except mediation if the pack omits it. |
| `independent-use` | Understand and produce connected discourse in familiar domains; handle variation and unplanned interaction. | All selected axes, including sociopragmatics. |
| `domain-use` | Function in a declared domain such as travel, family, workplace, theology, medicine, or literature. | Pack-selected axes plus domain lexis and tasks. |

Profiles are composable. A learner can complete `foundation` plus
`domain-use:travel` without the system implying broad independent proficiency.

### Language-specific benchmark contract

Each profile has a benchmark matrix. Completion means meeting every required
row with held-out content, not completing a fixed number of cards.

```yaml
id: es-419-foundation
profile: foundation
target: es-419
framework_version: 0.1.0
axes:
  reception:
    required: true
    task: understand-short-unfamiliar-audio
    pass: {gist: 0.80, required_details: 0.70}
  production:
    required: true
    task: record-a-60-second-self-introduction
    rubric: rubrics/foundation-production.yaml
    pass: 0.75
  interaction:
    required: true
    task: branching-everyday-dialogue
    requirements: [ask_follow_up, respond_to_repair, appropriate_register]
  form:
    required: true
    task: write-short-message
    requirements: [target_orthography, intelligible_word_order]
  lexis:
    required: true
    task: delayed-contextual-retrieval
    pass: {sample_size: 40, accuracy: 0.80, delayed_days: 7}
  sociopragmatics:
    required: true
    task: choose-register-for-three-contexts
    pass: 0.80
qualification:
  label: "Spanish (Latin America) — Foundation (local profile)"
```

The benchmark author chooses appropriate tasks for the language. An exact
spelling test is not a valid universal proxy for speech, signing, or
interaction; a multiple-choice grammar score is not a sufficient proxy for
production. Automated or AI-assisted evaluation may provide feedback and a
provisional score, but interaction, pragmatic appropriateness, and open-ended
production require a retained recording/text plus a transparent rubric and
learner or human review before a qualification is issued.

### Framework-specific learning pipeline

```text
select target locale + variant
  → install/author a language pack
  → select functional profile(s)
  → validate coverage and media rights
  → generate courses, study sets, and modality-appropriate games
  → practise with delayed retrieval and comprehensible input
  → perform held-out benchmark tasks per capability axis
  → issue local profile qualification with retained evidence
```

```bash
# Select a local pack and create a learning plan.
learn languages list
learn language install ./language-packs/es-419
learn language validate es-419 --strict
learn language plan es-419 --profile foundation

# Study generated or hand-authored material by modality.
learn language study es-419 --track reception
learn language study es-419 --track form --script Latn
learn language practise es-419 --mode dialogue-repair

# Evaluate a named local profile.
learn language benchmark es-419 foundation
learn language qualify es-419 foundation
```

### Language framework TODO

- [ ] Define language-pack, variant, modality, transliteration, media-rights,
  and benchmark-matrix schemas.
- [ ] Implement pack validation: valid target tag, declared scripts and input
  methods, complete source/media provenance, resolved profile references, and
  no benchmark axis without a task and rubric.
- [ ] Ship a language-neutral framework pack with item types for lexical
  retrieval, cloze, dictation, minimal pairs, script practice, dialogue turns,
  and scenario-based repair.
- [ ] Build profile planning so a learner chooses a locale and functional
  outcome rather than an unbounded “learn this language” goal.
- [ ] Implement audio/video recording and local evidence retention; make all
  recording opt-in and provide text-only alternatives where possible.
- [ ] Implement held-out benchmark selection and qualification evaluation that
  ignores raw game points and uses only declared axis evidence.
- [ ] Add an optional CEFR crosswalk format; prohibit display of a CEFR label
  unless every mapped descriptor and benchmark is present in the pack.
- [ ] Create one reference pack only after a qualified language specialist has
  reviewed its variation policy, prompts, benchmarks, and rights metadata.

## Corpus-ingestion implementation sketch

The first ingestion implementation should be a **generic corpus compiler**.
Gray’s Anatomy is only the first proof-of-work fixture because it exercises
hard cases—scanned pages, columns, figures, captions, historical terminology,
and dense cross-references. No production schema or command should contain
anatomy-specific assumptions.

### Stable interfaces

```text
SourceAdapter
  ingest(input) -> SourceManifest + immutable source artifacts

Page/UnitExtractor
  extract(source artifact) -> EvidenceUnit[]

StructureResolver
  resolve(EvidenceUnit[]) -> StructureNode[] + source edges

EdgeProposer
  propose(verified structure window) -> CandidateEdge[]

LessonCompiler
  compile(approved edges + bounded evidence) -> LessonProposal

BenchmarkCompiler
  compile(approved lesson + profile) -> BenchmarkProposal

ReleaseValidator
  validate(corpus, lessons, benchmarks) -> blocking report
```

Adapters are responsible for source shape; the later stages consume the same
canonical evidence interface. Initial adapters should cover paginated PDFs,
plain text/Markdown, and timestamped transcripts. Future adapters can cover
HTML, slide decks, scanned images, and structured language packs.

### Canonical evidence model

```text
Corpus
  └─ SourceDocument (edition/version/hash/rights)
      └─ EvidenceUnit (page, section, timestamp, or note block)
          ├─ EvidenceSpan (exact text, coordinates, confidence)
          ├─ MediaReference (image/audio/video + hash)
          └─ StructureNode (chapter, heading, figure, procedure, clause, ...)
```

Interpretation is kept separate from evidence:

```text
Concept ──GraphEdge──> Concept
   │                    │
   └── EvidenceSpan[]   └── EvidenceSpan[]
```

An edge can be `contains`, `precedes`, `requires`, `contrasts`, `part_of`,
`cross_references`, `illustrates`, or `theme_of`. Every proposed edge carries
source spans, generator metadata, confidence, and `proposed|reviewed|rejected`
status. An AI may propose edges; it may not silently promote them to reviewed
facts.

### Phased proof of work

1. **Acquire and fingerprint:** accept one selected edition, save the original
   file, record rights/provenance, and compute hashes.
2. **Extract without loss:** render each page/unit, run OCR or transcript
   extraction independently, and preserve raw output, normalized output,
   confidence, coordinates, and page/unit identity.
3. **Verify structure:** reconcile page count, table of contents, section
   boundaries, figures, captions, and missing/duplicate units. Block synthesis
   when structural checks fail.
4. **Persist corpus:** load documents, units, spans, structures, media, and
   review events into a local SQLite database; retain the original artifacts
   beside the database.
5. **Propose edges:** send only bounded, verified chapter/section windows to an
   AI edge pass. Store candidate themes, prerequisites, concepts, and
   cross-references with citations.
6. **Review graph:** provide a text/CLI review that accepts, edits, or rejects
   candidates. No lesson compilation runs against unreviewed edges by default.
7. **Compile lessons:** generate lesson proposals from approved edges and
   bounded evidence windows. Require page/unit citations for every claim.
8. **Compile and audit benchmarks:** create retrieval, explanation,
   discrimination, and application tasks; run source-fidelity, coverage, and
   citation audits before static release.

### Proof-of-work commands

```bash
learn corpus init gray-anatomy-1918 --source ./source.pdf
learn corpus fingerprint gray-anatomy-1918
learn corpus extract gray-anatomy-1918 --ocr --pages independently
learn corpus verify-structure gray-anatomy-1918 --strict
learn corpus load gray-anatomy-1918 --db corpus.sqlite
learn corpus edges gray-anatomy-1918 --chapters 1-3 --ai --proposal-only
learn corpus review-edges gray-anatomy-1918
learn corpus lessons gray-anatomy-1918 --from-reviewed-edges
learn corpus audit gray-anatomy-1918 --claims --citations --coverage
```

The Gray’s Anatomy run is successful only if the same interfaces can later
accept a manual, legal text, transcript, language pack, or ordinary Markdown
corpus without changing the evidence or graph schema. At this stage the
deliverable is a verified corpus plus lesson proposals—not a claim that the
entire book has been pedagogically or medically modernised.

### Implementation TODO

- [ ] Implement the study-set importer for TSV, headered CSV, Markdown tables,
  and `front :: back` text, with clear row-level error reporting.
- [ ] Create a study-set package from a valid import and initialise a private,
  ignored learner-state file only after the first study session.
- [ ] Implement `learn study`, reverse direction, due-only review, and
  state-free TSV export before adding any visual game mode.
- [ ] Add proposal-only AI extraction for unstructured notes; require explicit
  review before items enter a set.
- [ ] Define `memorisation_item`, accepted-answer, distractor, media, and
  scenario schemas; require item IDs and source anchors.
- [ ] Build the local append-only attempt ledger and deterministic due-review
  scheduler.
- [ ] Implement `cards`, `ladder`, and `typeback` in the terminal, including
  skip, reveal, correction, and retry flows.
- [ ] Implement strict validation for duplicate items, missing lesson/source
  links, unusable exact-answer items, and unsafe/circular scenario graphs.
- [ ] Implement `pairs` and `error-hunt` as wrappers over the same item and
  attempt contracts; test that their scoring cannot affect qualifications.
- [ ] Add local personal-best, streak, and session-summary views, each with an
  option to disable gamification display entirely.
- [ ] Add `label`, `scenario`, `grid`, and `target` only after a local visual
  renderer exists; retain static and keyboard-accessible variants.
- [ ] Add `exam` as a separately versioned preparation mode, then connect only
  validated performance benchmarks to qualifications.

### Acceptance checks

- A fully offline terminal session can complete a ladder round, record an
  attempt, surface the correction for a miss, and show the next due review.
- A learner can disable timers, motion, sound, scores, and streaks without
  losing access to any course material or qualification.
- A qualification evaluator ignores all game-specific fields and evaluates only
  its declared lesson, review, and benchmark evidence.
- Deleting a private state directory removes progress but never alters authored
  course content or source evidence.

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

Milestone 1 is implemented as a standalone Python 3.12 CLI in
[`skilltree-cli/`](skilltree-cli/) (see its README and `SPEC-m1.md`): YAML skill
trees, typed-recall study, FSRS scheduling, successive relearning, BKT, and
mastery-gated unlocks over an append-only SQLite event log. The inherited
SkillTree Groovy/Vue code is retained unchanged as a historical snapshot; the CLI
does not use or depend on it.

## Provenance

This repository is a fork of
[NationalSecurityAgency/skills-service](https://github.com/NationalSecurityAgency/skills-service).
The inherited code is based on upstream commit
[`821e83b`](https://github.com/NationalSecurityAgency/skills-service/commit/821e83bee884b36a94737c840a1474f8bf5fa5ea)
(2026-07-24, "Merge pull request #3973"), the merge-base with upstream `master`.
That commit is a `4.6.0-SNAPSHOT` development build: 221 commits after the 4.5.2
release and 14 commits before the 4.6.0 tag. Upstream changes are intentionally
not synced, since the CLI shares no code with skills-service.
