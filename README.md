control_prediction_BTP

### Overview
This project demonstrates building, visualizing, and serializing process flowsheets using SFILES (Simplified Flowsheet Input Line Entry System) 2.0. It includes:
- A demonstration script that processes PFD images, builds a mock flowsheet, renders a NetworkX graph, and generates a SFILES 2.0 text string.
- A robust core library to parse SFILES, construct flowsheets as NetworkX graphs, convert graphs back to SFILES (v1/v2), visualize flowsheets (NetworkX and `pyflowsheet`), and map between OntoCape vocabulary and SFILES abbreviations.

The repo helps you rapidly prototype and test SFILES-based representations and visualizations of chemical process flowsheets.

### High-level pipeline
1) PFD image discovery
- Load images from `PFD_Images/`.

2) Flowsheet assembly
- Demo: create a mock flowsheet dictionary (units, streams, optional positions) from the image name.
- Library: alternatively, create a `Flowsheet` from an input SFILES string or a `.graphml` file.

3) Graph construction and visualization
- Build a `networkx.DiGraph` from the flowsheet data.
- Render and save a graph visualization to `output/<image>_graph.png`.
- Optionally render a PFD-style SVG using `pyflowsheet` to `plots/`.

4) SFILES generation
- Convert the flowsheet graph to SFILES v1/v2 via a canonical traversal and edge-tag encoding (heat-integration, column tags, signal edges).
- Save SFILES to `output/<image>_sfiles.txt` and dump a human-readable flowsheet summary to `output/<image>_flowsheet.txt`.

Notes:
- In the demo, image-to-flowsheet is mocked. The core library supports full SFILES parsing and graph generation; implementing CV-based extraction from PFDs is out-of-scope here.

### Repository structure
- `Flowsheet_Class/flowsheet.py`: Main `Flowsheet` class (parsing, graph construction, SFILES conversion, visualization).
- `Flowsheet_Class/nx_to_sfiles.py`: Deterministic NetworkX → SFILES encoder (v1/v2, canonicalization).
- `Flowsheet_Class/OntoCape_SFILES_mapping.py`: OntoCape ↔ SFILES abbreviation mapping.
- `Flowsheet_Class/utils_visualization.py`: Stream/unit tables, NetworkX and `pyflowsheet` visualizations.
- `sfiles_demo.py`: Optional demo runner for image discovery and mock flowsheet conversion.
- `PFD_Images/`, `output/`, `requirements.txt`.

### Flowsheet_Class modules: high-level overview and methodology

#### `flowsheet.py` — Flowsheet model and SFILES I/O
Core responsibilities:
- Maintain the flowsheet state as a `networkx.DiGraph` (`self.state`).
- Parse SFILES strings to tokens and reconstruct a graph (`create_from_sfiles`).
- Convert graphs to SFILES v1/v2 (`convert_to_sfiles`).
- Handle heat-integration (merge/split multi-stream heat exchangers).
- Map between OntoCape terms and SFILES abbreviations (both directions).
- Visualize and tabulate flowsheet information.

Methodology (key methods):
- `SFILES_parser()`: Tokenizes SFILES, recognizing nodes `(unit)`, branches `[ ... ]`, incoming branches `<&| ... &|`, recycles `<#`/`#` (and `%##`), signals `<_##`/`_##`, and edge tags `{...}`.
- `renumber_generalized_SFILES()`: Ensures unique, ordered unit names in the parsed list (e.g., `hex-1/1` for HI streams) before graph construction.
- `create_from_sfiles(sfiles_in, overwrite_nx, merge_HI_nodes)`: Builds `self.state` by scanning tokens, emitting node/edge tuples, propagating and normalizing tag structures for heat integration (`he`), column connectivity (`col`), and signals.
- `convert_to_sfiles(version, remove_hex_tags, canonical)`: Prepares graph (splitting HI nodes as needed), optionally maps to SFILES abbreviations, and calls `nx_to_SFILES` to get a canonical SFILES string and token list.
- `map_SFILES_to_Ontocape()` / `map_Ontocape_to_SFILES()`: Renames nodes using `OntoCape_SFILES_map`, and harmonizes HI nodes by merging/splitting based on tags and edge directions.
- `merge_HI_nodes()` / `split_HI_nodes()`: Deterministic handling of multi-stream heat exchangers into single or sub-nodes using `tags.he` matching.
- `visualize_flowsheet(...)`: Creates tables and plots via NetworkX and optionally PFD-style SVG via `pyflowsheet`.

Usage patterns:
- From SFILES to graph:
```python
from Flowsheet_Class.flowsheet import Flowsheet
fs = Flowsheet(sfiles_in="(raw)(r)(hex){hot_in}(sep)(prod)")
fs.create_from_sfiles(overwrite_nx=True)
G = fs.state
```
- From graph to SFILES v2 (canonical):
```python
fs.convert_to_sfiles(version="v2", remove_hex_tags=False, canonical=True)
print(fs.sfiles)      # canonical SFILES v2
print(fs.sfiles_list) # tokenized
```
- OntoCape interop:
```python
fs.OntoCapeConform = True
fs.convert_to_sfiles(version="v2")
```
- Visualization:
```python
fig, stream_tbl, unit_tbl = fs.visualize_flowsheet(plot_as_pfd=True, pfd_path="plots/flowsheet")
```

Design notes:
- Graph nodes are named with unit type and an index (e.g., `hex-1`, `r-2`), and HI sub-nodes use `/k` suffixes.
- Edge attribute `tags` aggregates `{"he": [...], "col": [...], "signal": [...]}` for unambiguous v2 placement.
- The parser and builder ensure that removing control/HI decorations still yields a valid canonical SFILES.

#### `nx_to_sfiles.py` — Deterministic NetworkX → SFILES encoding
Core responsibilities:
- Encode a flowsheet `DiGraph` into SFILES v1/v2 strings with deterministic ordering.

Methodology:
- Remove non-material signal edges that are not “next-unit-op” to avoid traversal bias.
- Compute a Morgan-like graph invariant (`calc_graph_invariant`) to rank nodes; break ties by DFS tree structure (`rank_by_dfs_tree`), stream tags, and finally node numbering.
- Single traversal via a virtual source connects all weakly connected subgraphs to produce a single SFILES expression.
- Branches are emitted with `[ ... ]`, independent subgraphs with `n|`, incoming branches with `<&| ... &|`.
- Cycles are encoded with `<# ... #` (or `%##` for two-digit), and signals with `<_##`/`_##`.
- For v2, edge tags are deterministically inserted near targets or at `&` join points based on `special_edges` bookkeeping.
- Generalization step removes unit numbering when required.

Usage:
```python
from Flowsheet_Class.nx_to_sfiles import nx_to_SFILES
sfiles_list, sfiles_str = nx_to_SFILES(fs.state, version="v2", remove_hex_tags=False, canonical=True)
```

#### `OntoCape_SFILES_mapping.py` — Ontology mapping
Core responsibilities:
- Provide a one-to-one dictionary `OntoCape_SFILES_map` mapping OntoCape unit operation names to SFILES abbreviations (`RawMaterial` → `raw`, `HeatExchanger` → `hex`, ...).

Methodology & usage:
- Used by `flowsheet.py` renaming helpers to switch representations before/after conversion.
- Extend cautiously: ensure bijectivity (unique keys/values) to avoid ambiguous renaming.

#### `utils_visualization.py` — Tables and plots
Core responsibilities:
- Stream table (`create_stream_table`) and unit table (`create_unit_table`) using `tabulate`.
- NetworkX plotting (`plot_flowsheet_nx`) with automatic position assignment ensuring readable left-to-right flow.
- PFD-style SVG via `pyflowsheet` (`plot_flowsheet_pyflowsheet`) using unit-specific symbols and port mappings.

Methodology & usage:
- If node positions are absent, `_add_positions` assigns coordinates by exploring successors from feeds, handling branches and avoiding overlaps.
- Column and heat exchanger ports are mapped to appropriate `pyflowsheet` port names (e.g., `VOut/LOut`, `TIn/TOut`).

```python
from Flowsheet_Class.utils_visualization import plot_flowsheet_nx
fig = plot_flowsheet_nx(fs.state, plot_with_stream_labels=True)
```

### Core library capabilities
The `Flowsheet_Class` package supports:
- Parsing SFILES strings into tokens (`SFILES_parser`) and creating a canonical, numbered representation (`renumber_generalized_SFILES`).
- Building flowsheet graphs from SFILES with correct branch/cycle semantics (`create_from_sfiles`).
- Converting graphs to SFILES v1/v2 (`nx_to_SFILES`) with:
  - Cycle encoding using SMILES-like notation (`<#`, `#`, `%##`).
  - Branch encoding (`[ ... ]`, `<&| ... &|`).
  - Signal edges (`<_#`, `_#`).
  - Heat-integration tags and column connectivity tags placed deterministically.
- Mapping between OntoCape names and SFILES abbreviations; splitting/merging HI heat exchangers.
- Visualizations and tabular summaries of streams and units.

### Installation
1) Python 3.9+ recommended.
2) Create and activate a virtual environment (optional but recommended).
3) Install dependencies:

```bash
pip install -r requirements.txt
```

Optional:
- Install the official SFILES 2.0 package if desired:

```bash
pip install sfiles2
```

### Usage
Run the demo from the project root:

```bash
python sfiles_demo.py
```

You will be prompted to:
- Process all images automatically, or
- Enter interactive mode to process a specific image.

Outputs are written to `output/`:
- `<image>_graph.png`: NetworkX visualization.
- `<image>_sfiles.txt`: SFILES 2.0 string.
- `<image>_flowsheet.txt`: Units and streams summary.

### Programmatic examples
- Build a flowsheet from an existing SFILES string and convert back to canonical SFILES v2:

```python
from Flowsheet_Class.flowsheet import Flowsheet

my_sfiles = "(raw)[(r)](hex){hot_in}(sep)(prod)"
fs = Flowsheet(sfiles_in=my_sfiles)
fs.create_from_sfiles(overwrite_nx=True)
fs.convert_to_sfiles(version="v2", remove_hex_tags=False, canonical=True)
print(fs.sfiles)           # Canonical SFILES v2 string
print(fs.sfiles_list)      # Tokenized list
```

- Visualize a flowsheet graph (NetworkX and PFD-style SVG):

```python
fig, stream_table, unit_table = fs.visualize_flowsheet(
    figure=True,
    plot_with_stream_labels=True,
    table=True,
    plot_as_pfd=True,
    pfd_path="plots/flowsheet"
)
```

### About SFILES 2.0 in this repo
- The conversion algorithm ensures deterministic, canonical SFILES through ranking (Morgan-like invariant) and DFS traversal.
- SFILES v2 augments edges with tags for heat integration and column connectivity, and encodes signal edges distinctly from material recycles.
- The code also supports generating generalized SFILES (without unit numbering) where appropriate.

### Limitations and notes
- The demo’s image-to-flowsheet step is mocked; no computer vision or OCR is performed. Real PFD parsing would require a CV pipeline to detect units, ports, and streams.
- Heat-integration merging for complex topologies can be constrained by NetworkX edge multiplicity limits; the code handles common patterns and warns when merging is not feasible.
- `pyflowsheet` SVG rendering requires a display context when used interactively; headless environments may need adjustments.

### References
- d’Anterroches, L. (2006). Group contribution based process flowsheet synthesis, design and modelling. Ph.D. thesis, Technical University of Denmark.
- Zhang, T., Sahinidis, N. V., & Siirola, J. J. (2019). Pattern recognition in chemical process flowsheets. AIChE Journal, 65(2), 592–603.
- Weininger, D. (1988). SMILES, a chemical language and information system. 1. Introduction to methodology and encoding rules. Journal of Chemical Information and Computer Sciences, 28(1), 31–36.

### Contact
For questions or improvements, open an issue or submit a PR.