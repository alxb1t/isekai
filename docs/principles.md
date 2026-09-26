# Principles

The general rules this system is built on. Each is the rule, why it holds, and what holds it: a test,
review, or *not yet* — with what will hold it.

## Words

- **Component** — a part of the system with a contract: the caption stage, the run directory, the review
  UI. Not a Vue component: the frontend's own components are pieces of the review UI.
- **Module** — a Python file.
- **Layer** — one directory of the package: `foundation`, `shared`, `boundary`, `pipeline`, `interface`.
- **Sub-system** — a set of components with one boundary of its own, such as evaluation.
- **Refusal** — an expected failure: the work is declined, with what went wrong and what to do next. The
  CLI prints it as `refused: …`. A crash is not a refusal; it is a defect.

## The product

### A person approves every sheet

**A person approves every sheet before it is rendered.** Approving is its own act and writes its own
file; saving a draft never approves it, so a sheet can be left half-edited. Nothing renders from a sheet
no person approved.

- **Why:** the review step is where output quality is decided. A render from an unapproved sheet is a
  different product, not a shortcut.
- **Held by:** `tests/test_review.py::test_a_draft_is_not_treated_as_complete`,
  `tests/test_generate.py::test_a_flow_with_no_approved_sheet_is_refused_naming_the_commands`,
  `tests/test_ui_api.py::test_a_stale_lower_draft_does_not_reopen_an_approved_input`.

## Composition

### A component is a contract

**A component is a facade with a contract: what it takes, what it produces — returned or written — and
how it fails. It has no effect outside that contract.**

It earns its place if something else could use it or replace it; otherwise it is internal to another
component. What it needs from outside — a model, the network, the GPU, randomness — is passed in, so
a test can pass a fake.

**In code, a component is one module, or one package whose `__init__.py` is its front door.** The front
door is the contract: other components import only it, and it assembles the package's own modules.

Everything else in the package is private — only the component's own tests reach inside. One module is
the default; a package earns its place when the contract needs more than one file.

- **Why:** a contract is what lets a part be tested alone and swapped without its callers noticing. A
  component that nothing could use or replace is indirection, not structure. The same rule holds at
  both scales: a front end composes components, and a front door composes its own modules.
- **Held by:** review. The suite passes fakes through those parameters — `FakeReader`,
  `FakeComfyClient`.

### Only a front end composes

**Only a front end composes.** The CLI and the review UI are siblings, and each calls the stage
directly. The CLI builds the components through `wiring.py` and hands them to the review UI when its
`ui` verb starts it; the UI never calls the CLI.

**Composing is all a front end does** — a rule about the work itself, such as how a failure is
classified or what state a sheet is in, belongs to the component that owns that work.

- **Why:** logic in the wiring runs only on the path one front end takes, and nothing else can test it
  or reuse it.
- **Held by:** review.
- **Known break:** `interface/wiring.py`'s `load_vocabulary` classifies a failure — it turns a missing
  vocabulary into a refusal — which is the provisioning component's work.

### The code is layered

**The code is layered, and imports point only down:** `interface → pipeline → boundary → shared →
foundation`. A layer imports from itself and from the layers below it, never from above. Inside a
layer, modules may import each other, but never in a cycle.

Each layer has one role:

- **interface** — the front ends, the CLI and the review UI. They compose, and they serve and build
  themselves.
- **pipeline** — the stages.
- **boundary** — every way to a model, the GPU or the network: Ollama, the ComfyUI transport, the WD14
  session, downloads.
- **shared** — what the stages share: the vocabulary, the field map, image headers.
- **foundation** — the run directory, the flow and the refusal.

A layer's `__init__.py` holds only a docstring: a layer is a folder, not a front door. Evaluation is a
separate sub-system beside the code it measures: it may import isekai, and isekai never imports it.

- **Why:** a layer can be read, tested and changed knowing only what is below it. A cycle means neither
  side can be understood alone.
- **Held by:**
  - `tests/test_layers.py::test_every_import_points_down`
  - `tests/test_layers.py::test_nothing_in_the_package_imports_evaluation`
  - `tests/test_layers.py::test_no_stage_imports_another`
  - `tests/test_layers.py::test_no_import_cycle_inside_a_layer`
  - `tests/test_layers.py::test_a_layer_init_holds_only_a_docstring`
  - `tests/test_layers.py::test_a_subpackage_is_reached_only_through_its_front_door`

## Invocation

### A failure refuses one input, never the batch

**A failure refuses one input, never the batch, and never silently.** Every failure an operator can
cause is a named refusal; the batch collects them and reports them together at the end.

Nothing is guessed to avoid a refusal — a value that cannot be read or derived refuses its input
rather than defaulting. A traceback is a defect.

**Every failure is recorded in the run, with its kind.** A permanent one is never retried — it would
fail the same way. A transient one is retried up to the stage's budget, and a paid stage is never
retried on its own.

Deleting the record is how an operator tries again: no flag, no decay.

**Every refusal ends with a fix that works** — a command this build has, complete enough to paste, that
succeeds in the state the refusal leaves behind; or the file to delete, by its path in the run.

- **Why:** one bad photograph must not cost the others their session, and on the metered stage that
  costs money. A failure reported mid-batch scrolls away before the batch ends. A default hides the
  failure inside the output. A retry that cannot succeed is waste, and on the paid stage it is spend. A
  fix that parses and does nothing sends the operator in a circle.
- **Held by:** `tests/test_run_directory.py::test_one_photographs_failure_does_not_cost_the_others_their_turn`,
  `tests/test_generate.py::test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session`,
  `tests/test_run_directory.py::test_a_permanent_failure_is_refused_without_attempting_the_work`,
  `tests/test_run_directory.py::test_a_stage_at_its_budget_refuses_naming_the_photograph_and_the_record`,
  `tests/test_run_directory.py::test_a_stage_below_its_budget_is_allowed_to_attempt_again`,
  `tests/test_run_directory.py::test_a_deleted_record_is_never_overwritten`,
  `tests/test_run_directory.py::test_a_record_that_refuses_the_next_run_names_its_deletion`,
  `tests/test_resume.py::test_no_refusal_offers_a_command_this_build_does_not_have`,
  `tests/test_resume.py::test_every_command_a_refusal_prints_is_one_this_build_accepts` — these last
  check that a printed stage command parses and names a run, not that it succeeds.

### Free work first

**Nothing metered starts until all the free work of the batch has succeeded.** Everything a paid call
needs is checked and written locally, for every input, before any endpoint is acquired — so a mistake
costs nothing instead of a boot.

- **Why:** the GPU is the only thing here that costs money, and an error found after acquiring it has
  already been paid for.
- **Held by:** `tests/test_generate.py::test_a_malformed_approved_sheet_is_caught_before_anything_is_rented`,
  `tests/test_generate.py::test_assembly_contacts_no_endpoint_and_writes_an_artifact`.

## Configuration

### Configuration is declared, never computed, and declared once

**Configuration is declared, never computed, and declared once.** A flow's manifest declares everything
that can differ between flows — nodes by role, dials, prompts, models — and the code finds nothing by
searching or guessing.

What cannot differ between flows is a constant in code that says it is not a manifest key. A fact
written twice is written once, or a test holds the two copies equal. **A derived file is such a copy:
a test re-derives it and expects the same bytes.**

- **Why:** a manifest that computes nothing can be checked without running anything, so a broken flow
  fails the test suite instead of a paid boot. Two copies of one fact drift apart silently.
- **Held by:** `tests/test_flow.py::test_no_value_in_a_manifest_is_derived_at_load_time`,
  `tests/test_flow.py::test_a_manifest_missing_a_dial_its_own_roles_read_is_refused_naming_it`,
  `tests/test_flow.py::test_every_dial_a_tracked_flow_declares_is_one_of_its_roles_reads`,
  `tests/test_flow.py::test_every_model_a_flow_declares_carries_the_manifests_digest_for_it`,
  `tests/test_field_map.py::test_the_committed_table_re_derives_without_reading_the_gitignored_runs`.
- **Known breaks:** the sampling options do not say they are not manifest keys. The field map's
  re-derivation skips in CI, which declares the vocabulary absent, and the derivers that fetch from the
  network are never re-run.

### Everything that shapes an output is pinned

**Everything that shapes an output is pinned** — a fetched file by its digest, an authored one by git, a
dependency by its exact version, an image by its digest, a flow by equality with its recorded digest. A
moving tag is not a pin.

A flow never changes silently: a variant gets a new identifier and the two are compared, never
migrated; a replaced one is re-pinned with what moved recorded. Where a pin is not yet possible, the
gap is recorded with its trigger, and every artifact it shapes says `pinned: false`.

- **Why:** an unpinned input can change between two runs of the same flow, and then no record can
  explain why their outputs differ.
- **Held by:** `tests/test_flow.py::test_every_model_a_flow_declares_carries_the_manifests_digest_for_it`,
  `tests/test_vocabulary_manifest.py::test_a_label_index_and_a_model_at_two_revisions_fail_the_check`,
  `tests/test_flow.py::test_every_tracked_flow_matches_its_committed_digest`,
  `tests/test_flow.py::test_a_re_pin_leaves_a_record_a_later_reader_can_find`,
  `tests/test_infra.py::test_every_git_clone_in_the_image_is_pinned_to_a_commit`, and the gate's
  first command, which installs the Python dependencies from the lock file.
- **Not yet held** for the local caption model, which is named by an alias whose bytes nothing checks;
  the pod image, run by its moving `latest` tag; the image's base, build tool and system packages; the
  requirement files the image installs without a lock; and the CI actions, pinned only to a major
  version.

### Hold a guarantee by construction, not by a filter

**Hold a guarantee by construction, not by a filter.** Prefer a source whose every output is already
valid — a tagger whose labels are the vocabulary — and a table over a model where the mapping is stable.
Where a model's output still needs narrowing, its answer is stored as it came and a later stage narrows
it: nothing is filtered on the way into storage.

- **Why:** a filter only catches what it anticipates, while a source that cannot produce an invalid
  value never needs one. A raw record is what lets the next source be measured against this one.
- **Held by:** `tests/test_tagging.py::test_every_tag_is_stored_exactly_as_it_came_including_the_unusable`,
  `tests/test_sheet_stage.py::test_the_stage_reads_the_tag_list_and_never_opens_the_caption`.

## State

### The run directory is the only channel between stages, and a run's only state

**A stage never imports or calls another; it reads the files it needs and writes its own.** The run
directory's contract names where every file lives and declares what every file holds, each kind with its
own version — stages depend on that contract, never on each other. What is done and what failed is read
from filenames, never from a status file.

**Every file in it is written whole, numbered, and never changed** — a draft is the one file edited in
place. A stage whose file already exists does nothing unless asked for a new version.

- **Why:** stages can run days apart, be tested alone and resume from disk. A failure in one cannot
  reach into another. A human's correction survives beside the machine's draft, so the two can be
  compared.
- **Held by:**
  - `tests/test_run_directory.py::test_deciding_approval_reads_no_file`
  - `tests/test_run_directory.py::test_a_failed_rename_leaves_neither_the_artifact_nor_its_temporary`
  - `tests/test_review.py::test_an_approved_artifact_is_never_overwritten`
  - `tests/test_resume.py::test_without_the_flag_no_next_version_appears_for_any_stage`
  - `tests/test_layers.py::test_no_stage_imports_another`
  - `tests/test_artifact_bytes.py::test_each_kind_is_written_byte_for_byte`
  - `tests/test_artifact_bytes.py::test_only_the_contract_writes_a_run_file`
  - `tests/test_review.py::test_approving_an_approved_flow_writes_nothing`

### Every artifact records what shaped it

**Every artifact records everything that shaped it** — the models, the prompt, the tables, the dials,
the flow — by digest where one exists, and the version of the file it came from, so any output can be
walked back to its photograph. What is not pinned says so, and nothing unpinned may look pinned.

- **Why:** an output that cannot be traced to its inputs cannot be compared with another or re-run.
- **Held by:** `tests/test_run_directory.py::test_the_link_between_stages_is_the_producer_record`,
  `tests/test_run_directory.py::test_an_unpinnable_producer_says_so_rather_than_claiming_a_pin`,
  `tests/test_run_directory.py::test_a_producer_names_the_upstream_version_it_came_from`,
  `tests/test_generate.py::test_the_provenance_records_the_flow_the_seed_the_version_and_the_graph`.
- **Not yet held** for the sampling options, the tagger's floor, the flow's own digest and the pod
  image. A render records its flow's id but not its digest, so a re-pinned flow is two configurations
  under one name.
