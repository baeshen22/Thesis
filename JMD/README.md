# Jeddah Motor District: Municipality Concept Presentation

Concept deck and visualisation package for presenting Jeddah Motor District (JMD) to the Municipality of Jeddah.

## Deliverables

| | Deliverable | Location |
|---|---|---|
| **A** | Final PowerPoint (18 slides, 16:9, editable, presenter notes) | `deck/JMD_Municipality_Concept_Presentation.pptx` (plus a PDF preview) |
| **B** | Render library (new visualisations, 2400 × 1350; masterplan 3000 × 3000) | `renders/` |
| **C** | Visual Design Bible | `docs/02_Visual_Design_Bible.md` |
| **D** | Slide narrative and presenter notes | `docs/03_Slide_Narrative_and_Presenter_Notes.md` |
| **E** | Assumptions and verification register | `docs/04_Assumptions_and_Verification_Register.md` |
| | AI photoreal enhancement kit (depth maps + prompts) | `docs/05_AI_Enhancement_Kit.md`, `renders/depth/` |
| | Source reference matrix (internal, Phase 1) | `docs/01_Source_Reference_Matrix.md` |
| | Reproducible production pipeline | `tools/` |

## How the visualisations were produced

No AI image generator was available in the production environment, and none was used. Instead, every image comes from **one 3D model of the district built from `FINAL_8-10-2026.dwg`**:

1. **DWG to zones.** The DWG (AutoCAD 2018) was read with LibreDWG (WASM). Its 61 hatched zones and 135 labels were classified into showrooms, shops, arena halls, club, off-road, service, parking and so on. See `tools/prep_model.py`.
2. **Ground surfaces.** Asphalt, parking stalls, paving, landscape, off-road dirt and kerbs are painted directly from the DWG polygons. See `tools/make_ground.py`.
3. **3D model.** Buildings are extruded from the exact DWG footprints in Blender 5.2, following the Visual Design Bible. Palms, vehicles and figures are procedural and placed by rule. See `tools/build_scene.py`.
4. **Rendering.** Path-traced in Blender Cycles with physically based materials and an AgX view transform, then a shared studio grade. See `tools/render_view.py`, `tools/views.py`, `tools/post.py`, and `tools/build_interiors.py` for interiors.
5. **Deck.** Built with pptxgenjs as a structured deck: theme, named layouts and sections. All labels, callouts, plan markers, journey arrows and arena-mode diagrams are editable PowerPoint shapes. See `tools/build_deck.js` and `tools/prep_deck_images.py`.

Because every view comes from the same model, the arena, Collectors' Club and showroom row are geometrically identical in every image.

## Limitations (stated plainly)

- These are **conceptual architectural visualisations**, not photographic marketing renders. Vehicles, people and palms are simplified models. Cameras keep them at a distance where they read well.
- Heights, façades, materials, landscape, off-site roads and surrounding context are **illustrative assumptions**. The DWG defines footprints only.
- The **Wall of Fame museum** and **simulator hall** are not on the current drawing. They are shown as interiors only, with "location to be confirmed".
- Arena capacities, parking numbers, site area and the frontage road name are **not stated as facts** in the deck (see register section 3).
- The audio narration (25 s) was transcribed offline. It describes the street-level showroom view in the concept PDF (p.3).

## Rebuilding

```bash
# 1  DWG -> JSON   (node, @mlightcad/libredwg-web)  -> dwg.json, then hatch extraction -> hatches.json
python3 tools/prep_model.py hatches.json model.json
python3 tools/make_ground.py model.json ground_global.jpg -1100 -1000 900 900 0.18
blender-python tools/build_scene.py model.json ground_global.jpg jmd.blend
tools/render_all.sh jmd.blend OUTDIR 2400 1350 64 hero_aerial arrival ...
tools/render_interiors.sh jmd.blend model.json OUTDIR 2400 1350 96 museum simulator ...
python3 tools/prep_deck_images.py OUTDIR PREVIEW SRC deck_img
NODE_PATH=tools/node/node_modules PPTX_SKILL=<pptx skill> node tools/build_deck.js deck_img tools/plan_anchors.json out.pptx
```

This project is separate from AlBalad Development Company (BDC). No BDC material was used.
