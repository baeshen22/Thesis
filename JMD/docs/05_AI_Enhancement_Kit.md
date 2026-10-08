# JMD — AI Photoreal Enhancement Kit

**Goal:** add photographic richness to the JMD renders (materials, vehicles, people, vegetation, light) **without changing the architecture**. The renders are geometrically true to `FINAL_8-10-2026.dwg` and consistent with each other. The enhancement must keep it that way.

**Inputs per view** (same name, same pixel size):

| File | Use |
|---|---|
| `renders/<name>.jpg` | Base image for image-to-image, upscaling or editing |
| `renders/depth/depth_<name>.png` | Depth map: near is white, far and sky are dark. Use as the ControlNet / structure reference |

---

## 1. Choose a workflow (best geometry preservation first)

### A. Creative upscaler (Magnific, Krea Enhance, Topaz or similar): **recommended first pass**
- Upload the render. Upscale ×2.
- **Creativity / AI strength: low** (Magnific creativity 1–3, resemblance +2 to +4, HDR 1–3; Krea "AI strength" about 0.2–0.35).
- Paste the style prompt (section 2) plus the view-specific prompt (section 3).
- *Why first:* it adds texture, vehicle detail, foliage and glazing reflections while keeping every edge in place.

### B. Stable Diffusion XL / Flux with ControlNet: **maximum control**
- **img2img:** base render as the init image, **denoising 0.30–0.45** (lower for aerials, higher for interiors).
- **ControlNet 1, depth:** `depth_<name>.png`, weight 0.85–1.0, ending step 0.8.
- **ControlNet 2, canny or lineart:** let the tool pre-process the render itself. Weight 0.5–0.7.
- Use a fixed seed and the same model, sampler, style prompt and LoRA for the **whole set**, so all images match.
- Resolution: work at the native 2400 × 1350 (or tile-upscale).

### C. Instruction-based image editors (current multimodal editors)
- Upload the render and write: *"Make this photorealistic. Keep all buildings, roads, the layout, the camera and the composition exactly as they are. Do not add text or logos."* Then add the view prompt.
- Check the result against the original (section 5). These tools sometimes "redesign" buildings.

### D. Midjourney: **atmosphere only**
- Use the editor's **Retexture** on the uploaded render. It keeps the composition better than an image prompt alone.
- Do **not** rely on an image prompt with `--iw` for these slides. Midjourney reinterprets architecture, which defeats the purpose of DWG-accurate images.

---

## 2. Style prompt (prefix for every image, keep identical across the set)

> Photorealistic architectural visualisation of a contemporary automotive district in Jeddah, Saudi Arabia. Warm limestone-coloured façades, champagne-bronze vertical fins, clear low-iron glass showrooms with cars on display, graphite fascia bands, crisp white aluminium canopies. Mature date palms and drought-tolerant planting, warm sand-coloured paving, clean asphalt with white markings. Natural desert light, accurate shadows, subtle atmospheric haze. Professional architectural photography, realistic scale, natural colour, high detail.

**Negative prompt (all images):**

> text, letters, numbers, logos, brand names, readable signage, watermark, billboard graphics, distorted vehicles, duplicated cars, melted geometry, warped façades, extra floors, changed building shapes, new buildings, neon, cyberpunk, futuristic blob architecture, oversaturated colours, HDR halos, heavy lens flare, snow, rain, European or American city, lush green lawns, deformed people, faces in close-up

---

## 3. View-specific prompts and settings

| Render / slide | Add to the prompt | img2img denoise | Notes |
|---|---|---|---|
| `hero_aerial`: slides 1, 17 crop | aerial view, golden hour, long soft shadows, busy highway traffic, low-rise city beyond | 0.30 | Keep the empty sky; titles sit over it |
| `dusk_aerial`: slide 2 | blue-hour aerial, warm interior glow from showroom glazing, street lights on, car light trails | 0.35 | Lights must stay realistic, not neon |
| `vision_aerial`: slide 17 | late-afternoon aerial, warm sun, long shadows across the off-road field | 0.30 | |
| `masterplan`: slides 3, 15 | top-down orthographic site plan render, crisp, neutral daylight | 0.20 | **Keep it nearly untouched.** Callouts are aligned to its pixels |
| `arrival`: slide 4 | elevated view across a multi-lane boulevard to the showroom frontage, flowing traffic | 0.35 | |
| `showroom_street`: slide 5 | eye-level street view, glass showrooms with premium cars inside, people walking, palm shadows on the pavement | 0.40 | Keep brand bands **blank** |
| `showroom_blvd`: slide 5 inset | drone view along the showroom frontage, parked cars, palms | 0.35 | |
| `facade_a/b/c`: slide 6 | frontal façade study of a single car showroom, cars displayed behind glass, polished stone floor | 0.35 | No logos on the dark band |
| `arcade`: slide 7 | shaded retail arcade, shopfront displays of automotive accessories and lifestyle goods, café seating, Saudi families strolling | 0.45 | Keep column rhythm |
| `arena_hero`: slide 8 | landmark events arena with a floating roof, bronze fin façade, crowds arriving across the plaza | 0.35 | Roof outline must not change |
| `int_arena_expo`: slide 9 | international motor-show hall, exhibition stands with premium cars, visitors, polished concrete floor | 0.45 | Stands without readable graphics |
| `int_arena_theatre`: slide 9 | vehicle launch event, stage lighting, car on a turntable, tiered seating | 0.45 | Screen content abstract only |
| `offroad`: slide 10 | off-road driving course, SUVs climbing sand mounds, mud splashing in a water crossing, tyre tracks, dust | 0.45 | Keep the mound and basin positions |
| `int_museum`: slide 11 | automotive heritage museum, classic cars on plinths, warm spot lighting, wall of illuminated milestone panels | 0.45 | Panels blank or abstract (no invented text) |
| `int_simulator`: slide 12 | premium driving-simulator hall, racing seats, triple screens showing driving scenes, dark moody lighting | 0.45 | No brand names on screens or seats |
| `club_ext`: slide 13 | exclusive collectors' club at dusk, warm glowing gallery, supercar at the valet canopy | 0.35 | |
| `int_club_lounge`: slide 13 | luxury members' lounge overlooking a gallery of collectible cars on turntables, walnut and leather | 0.45 | |
| `launch_plaza`: slide 14 | outdoor car-reveal event, covered car on a stage, crowd, white shade sails | 0.40 | |
| `frontage_dusk`: slide 18 | showroom frontage at dusk from the boulevard, glowing glass, arena behind, light trails | 0.35 | |

---

## 4. Rules that must survive enhancement

1. **Geometry is fixed.** Building outlines, number of units, heights, roof lines, road and parking layout, palm positions.
2. **No text and no logos anywhere.** The municipality must not read implied brand commitments. Brand bands stay blank.
3. **Jeddah, not elsewhere:** desert light, date palms, sand tones. People in a natural mix of Saudi and international dress, at small scale.
4. **One look for the whole set:** same model, prompts, seed strategy and grade.
5. **Interiors stay plausible:** no impossible spans or floating objects.

## 5. Accept / reject checklist (for each enhanced image)

- [ ] Overlay the enhanced image on the original at 50% opacity. Edges, rooflines and openings align.
- [ ] Building and unit count unchanged; no added or removed structures.
- [ ] No readable text, logos or pseudo-letters.
- [ ] Vehicles intact: four wheels, correct proportions, no duplicates or merged cars.
- [ ] People natural at small scale; no distorted faces or hands.
- [ ] Glass reads as glass (reflections plus interior), not mirrors or black voids.
- [ ] Colours consistent with the other enhanced images.
- [ ] No dramatic additions: neon, lightning, fireworks, extra lens flares.

Reject and re-run at a lower denoise or creativity if any box fails.

## 6. Putting enhanced images into the deck

- **Quick:** in PowerPoint, right-click the image, choose *Change Picture* then *From a File*. All images are 16:9 at the same size, so framing is preserved.
- **Full rebuild:** save the enhanced files into `deck/img/` under the same `S##_*.jpg` names and run `tools/build_deck.js` (see README).
- Keep the "NEW CONCEPT VISUALISATION · ILLUSTRATIVE" tags. If an image is AI-enhanced, change a tag to "CONCEPT VISUALISATION · AI-ENHANCED · ILLUSTRATIVE".
