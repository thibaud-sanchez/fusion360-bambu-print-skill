# Fusion 360 & Bambu Studio - Design for 3D Printing

**`fusion-bambu-print`** is a Codex skill for designing printable FDM parts in Autodesk Fusion and preparing them in Bambu Studio. It focuses on simple mechanisms, robust assembly, practical build orientations and efficient iterations.

This package contains instructions and focused references. Automation uses the Fusion and Bambu tools already available in your environment; the skill does not install an MCP server or a new application integration.

## What it helps with

- Parametric models designed around print orientation, layer strength, bed contact and support removal.
- Straightforward assemblies, accessible connections and selective use of print-in-place joints.
- Stable part IDs such as `B1` and `A3`, shared across Fusion, exports and assembly guides.
- Print settings suited to a prototype, a working part, a display model or a MakerWorld release.
- Smaller iterations: reuse working scripts, test the affected parts and preserve checkpoints without rebuilding every deliverable.
- Revision-matched CAD views, exports and assembly instructions when delivering an assembly.

The guiding principle is **KISS — Keep It Simple, Stupid**. Reduce fragile features and delicate handling steps while preserving the mechanism's required function.

## Requirements

| Task | Required capability |
|---|---|
| Use the instructions | Codex with local skill support |
| Read or modify native CAD | Autodesk Fusion with an available MCP connection or another supported automation route |
| Run Fusion Python scripts | Access to Fusion's in-process `adsk` API; ordinary external Python is insufficient |
| Apply settings and obtain print estimates | Bambu Studio with usable GUI automation, an installed CLI or an existing compatible tool |

The skill checks available capabilities and actual profiles before using them. When application access is unavailable, it can provide proposed settings or scripts, clearly marked as unverified or unexecuted.

Planning defaults are **Bambu Lab A1 mini, 0.4 mm nozzle and PLA**. Replace them with your project's printer, nozzle, plate and material. Validated machine and filament settings take precedence; AMS availability is never assumed.

## Install locally

Keep `SKILL.md` and `references/` together inside a directory named `fusion-bambu-print`.

For the standard repository layout `skills/fusion-bambu-print/`, run the following from the repository root on macOS or Linux to install for your user:

```sh
mkdir -p "$HOME/.agents/skills"
cp -R skills/fusion-bambu-print "$HOME/.agents/skills/"
```

For a project-scoped installation, place the skill directory in `.agents/skills/` inside that project. If the skill is already configured elsewhere, update that copy rather than installing duplicates. Codex detects local skill changes; restart it if the skill does not appear.

See the [official Codex skill documentation](https://developers.openai.com/codex/skills/) for discovery locations and installation details. These commands install only the skill files; configure application access separately.

## Use it

Mention `$fusion-bambu-print` in a Codex prompt, or let Codex select it when the request matches its description. Include the intended use, size, printer/material, available model files and any physical test feedback.

Examples:

> Use $fusion-bambu-print to design a small sliding enclosure in Fusion. Keep assembly simple, identify each part and prepare one mechanical prototype project on one plate if it fits reliably.

> Use $fusion-bambu-print to improve this hinge after a printed failure. Reuse the working geometry and validated PLA profile, revise the affected connection and preserve the previous version.

> Use $fusion-bambu-print to prepare this tested assembly in MakerWorld mode. Provide a verified Bambu 3MF and an assembly guide using the same part IDs as Fusion. Do not publish it.

## Print modes

| Mode | Main priority |
|---|---|
| **Prototype** | Fast printable drafts |
| **Prototype --mechanical** | Fast trials that still need to fit, move or transmit force |
| **Functional** | Strength, dimensional accuracy and reliability |
| **Quality** | Appearance and visible surfaces |
| **MakerWorld** | Repeatability, approachable assembly and documented print projects |

During development, the default is one current prototype project, with one plate when practical. Extra modes and delivered variants wait for a request. `Prototype --mechanical` is a workflow label, not a Bambu CLI flag.

See [print configuration](references/choose-print-configuration.md) for initial settings and how to adapt them.

## Outputs and limits

Depending on the request and available tools, outputs can include editable native CAD, exchange files, printable meshes, a Bambu project and an assembly guide. Configuration reports identify applied settings, available slicer estimates, tradeoffs and remaining tests.

The skill distinguishes work that was modeled, exported, sliced or physically tested. Successful slicing and collision checks do not establish snap-fit force, material strength, wear or durability. Physical trials remain necessary for functional interfaces.

Starting a print or uploading a project requires an explicit request. No fixed reduction in tokens, print time or material is promised.

## Package layout

- [SKILL.md](SKILL.md): instructions for Codex and routing to the relevant references.
- [references/](references/): design, mechanical assembly, Fusion, Bambu settings and iteration guidance.
- `README.md`: installation and usage information for people.

The package is reusable across projects and does not require a particular model or its historical scripts.
