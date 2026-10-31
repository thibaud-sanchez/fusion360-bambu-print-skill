# Fusion 360 & Bambu Studio - Design for 3D Printing

**`fusion-bambu-print`** is an AI assistant skill for designing printable FDM parts in Autodesk Fusion and preparing them in Bambu Studio. It focuses on simple mechanisms, robust assembly, practical build orientations and efficient iterations.

This package contains instructions and focused references. Automation uses the Fusion and Bambu tools already available in your environment; the skill does not install an MCP server or a new application integration.

## What it helps with

- Parametric models designed around print orientation, layer strength, bed contact and support removal.
- Straightforward assemblies, accessible connections and selective use of print-in-place joints.
- Stable part IDs such as `B1` and `A3`, shared across Fusion, exports and assembly guides.
- Print settings suited to a prototype, a working part, a display model or a release prepared for sharing.
- Geometry-based [support selection](references/choose-support-structure.md), including normal, tree and hybrid styles, stability and removal access.
- Smaller iterations: reuse working scripts, test the affected parts and preserve checkpoints without rebuilding every deliverable.
- Clean reconstruction of repeatedly edited parts: preserve functional interfaces and replace accumulated repairs, obsolete tabs and stray ledges with coherent geometry.
- Revision-matched CAD views, exports and assembly instructions when delivering an assembly.

The guiding principle is **KISS — Keep It Simple, Stupid**. Reduce fragile features and delicate handling steps while preserving the mechanism's required function.

## Requirements

| Task | Required capability |
|---|---|
| Use the instructions | An AI assistant that can load skill instructions and their reference files |
| Read or modify native CAD | Autodesk Fusion with an available MCP connection or another supported automation route |
| Run Fusion Python scripts | Access to Fusion's in-process `adsk` API; ordinary external Python is insufficient |
| Apply settings and obtain print estimates | Bambu Studio with usable GUI automation, an installed CLI or an existing compatible tool |

The skill checks available capabilities and actual profiles before using them. When application access is unavailable, it can provide proposed settings or scripts, clearly marked as unverified or unexecuted.

Planning defaults are **Bambu Lab A1 mini, 0.4 mm nozzle and PLA**. Replace them with your project's printer, nozzle, plate and material. Validated machine and filament settings take precedence; AMS availability is never assumed.

## Install locally

Keep `SKILL.md` and `references/` together inside a directory named `fusion-bambu-print`.

1. Download or clone the `fusion360-bambu-print-skill` repository.
2. Locate the directory containing `SKILL.md` and `references/`. Install that directory as `fusion-bambu-print` using your assistant's skill installer, configuration or supported skills directory.
3. Check that the assistant can discover the skill and read its references.
4. Configure access to Fusion and Bambu Studio through tools supported by your environment.

Installation paths, activation syntax and reload behavior depend on the assistant. Use its documentation rather than assuming a common directory or command. If the skill is already installed, update that copy rather than keeping duplicates.

The package supplies workflow instructions; available automation depends on the host and its connected tools. Installing the skill alone does not connect either application.

## Use it

Ask your assistant to use `fusion-bambu-print`, following its supported activation syntax. Include the intended use, size, printer/material, available model files and any physical test feedback.

Examples:

> Use fusion-bambu-print to design a small sliding enclosure in Fusion. Keep assembly simple, identify each part and prepare one mechanical prototype project on one plate if it fits reliably.

> Use fusion-bambu-print to improve this hinge after a printed failure. Reuse the working geometry and validated PLA profile, revise the affected connection and preserve the previous version.

> Cleanly rebuild this part with fusion-bambu-print. Preserve the functional interfaces, reconstruct coherent volumes and remove superseded geometry. Resolve each marked region in the issue image and show matching CAD views.

> Use fusion-bambu-print to prepare this tested assembly in Release mode for sharing. Provide a verified Bambu 3MF and an assembly guide using the same part IDs as Fusion. Do not publish it.

## Print modes

| Mode | Main priority |
|---|---|
| **Prototype** | Fast printable drafts |
| **Prototype --mechanical** | Fast trials that still need to fit, move or transmit force |
| **Functional** | Strength, dimensional accuracy and reliability |
| **Quality** | Appearance and visible surfaces |
| **Release** | Repeatability, approachable assembly and documented print projects for sharing |

During development, the default is one current prototype project, with one plate when practical. Extra modes and delivered variants wait for a request. `Prototype --mechanical` is a workflow label, not a Bambu CLI flag.

See [print configuration](references/choose-print-configuration.md) for initial settings and how to adapt them.

## Outputs and limits

Depending on the request and available tools, outputs can include editable native CAD, exchange files, printable meshes, a Bambu project and an assembly guide. Configuration reports identify applied settings, available slicer estimates, tradeoffs and remaining tests.

The skill distinguishes work that was modeled, exported, sliced or physically tested. Successful slicing and collision checks do not establish snap-fit force, material strength, wear or durability. Physical trials remain necessary for functional interfaces.

Starting a print or uploading a project requires an explicit request. No fixed reduction in tokens, print time or material is promised.

## Package layout

- [SKILL.md](SKILL.md): instructions for the assistant and routing to the relevant references.
- [references/](references/): design, mechanical assembly, Fusion, Bambu settings and iteration guidance.
- `README.md`: installation and usage information for people.

The package is reusable across projects and does not require a particular model or its historical scripts.
