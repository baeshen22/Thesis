# JMD Visual Design Bible

**Purpose:** one architectural and rendering language for every image of Jeddah Motor District, so the deck shows one district rather than many unrelated pictures.
**Geometry authority:** `FINAL_8-10-2026.dwg`. Every footprint in every render is taken directly from the DWG hatches (see `tools/prep_model.py`). Heights, façades, landscape and context are design-development assumptions.

---

## 1. Architectural language: "Calm frontage, crafted shade"

- Long, low, horizontal buildings that follow the DWG's curved frontage. Each building has a sharp roof line and a deep shading overhang.
- Glass is used only where vehicles are displayed: showroom fronts, the arena concourse and the club gallery. Solid limestone-toned walls are used elsewhere for heat control.
- Champagne-bronze vertical fins and blades are the district's shared detail. They appear on showroom party walls, louvre façades, the arena upper façade and the club upper floors.
- A graphite **brand band** tops every showroom front. It is deliberately left blank in all renders. Brand identity is a tenant decision and is not implied to the municipality.
- No neon, no free-form "futuristic" shells, and no decorative elements without a function (shade, structure, display or wayfinding).

## 2. Massing principles

| Element | DWG footprint | Height (assumed) | Massing rule |
|---|---|---|---|
| Standard showroom | ≈12 × 20 m | 9.0–9.6 m | Single double-height volume |
| Premium showroom | ≈17 × 21–29 m | 10.5–11.1 m | Taller module creates rhythm along the row |
| Flagship / flagship-plus | ≈20 × 22–27 m | 13–14 m | Framed portal or angled canopy; marks the row ends and gateways |
| Lifestyle shop | ≈20 × 20 m | 8.0 m | 4.6 m shopfront plus 5.5 m deep arcade on bronze columns |
| Light-service unit | 21 × 33 m | 9.0 m | Insulated metal shed, roller door, glazed reception |
| Arena | 7 bays ≈12,910 m² within the triangle | 21 m to roof, plus 3.2 m roof zone | Floating roof over the whole triangle, glazed 7.5 m concourse base, fins above |
| Collectors' Club | 30 × 117 m | 15.5 m (3 levels) | Stacked slabs with deep white-metal edges; glazed ground gallery |
| Mosques | 20 × 55 m / 60 × 71 m | 9 m / 12 m, minaret 28 m / 34 m | Restrained limestone volume, bronze lantern |
| Test-drive pavilion | 45 × 79 m | 5.8 m | Glass pavilion under a single flat roof with drop-off canopy |

## 3. Material palette (render values, linear RGB)

| Material | Use | Base colour | Finish |
|---|---|---|---|
| Limestone-tone GRC | Primary walls | 0.70 / 0.64 / 0.54 | Matt (roughness 0.62), subtle variation |
| Warm white aluminium | Roof edges, canopies, columns | 0.70 / 0.69 / 0.66 | Satin |
| Champagne bronze (anodised) | Fins, louvres, portals, columns | 0.40 / 0.30 / 0.19 | Metallic satin |
| Graphite panel | Brand band, plinths, booths | 0.055 / 0.055 / 0.06 | Semi-matt |
| Architectural glass | Showroom fronts, concourse | Clear, low-iron | Thin-wall, low reflectance |
| Solar glass | Back-of-house, upper floors | Neutral grey tint | Thin-wall |
| Standing-seam roof | Arena | 0.42 / 0.41 / 0.38 | Ribbed |
| Polished stone / dark stone | Interiors | Light / near-black | Gloss for display floors |
| Walnut | Club, museum, arena fins | Dark warm | Satin |

## 4. Façade system: showroom kit of parts

These are derived from the five options in S1 p.5. One of them is applied to each unit, and every unit shares the same plinth, roof edge, brand band and bronze corner blades:

1. **Modern minimal:** full-height glass with slim graphite mullions at 2.5 m.
2. **Vertical louvre:** bronze fins at 0.9 m pitch across the glass.
3. **Stone & glass:** a 30% limestone pier with glass.
4. **Contemporary frame:** a protruding stone portal frame. Used for flagships.
5. **Angled canopy:** a roof canopy that rises toward the street. Used for flagships.

## 5. Landscape and public realm

- **Date palms** (*Phoenix dactylifera*) line the frontage road verges and median, the parking-bay edges (about every 26 m), the shop promenade (one per unit) and the plaza perimeters.
- Low native-style shrub beds sit under palms. Planting is olive and grey-green, never lawn-green, except the road median verge.
- **Paving:** warm sand-tone pavers on 3.5 m footways around every building and on plazas.
- **Shade:** shop arcades, hypar shade sails at the launch plaza, the arena roof overhang and the valet canopies.
- Off-road field uses natural dirt tones, with mounds of about 10 m, a dune field, a water crossing, a rock crawl and timber ramps. A red-and-white kerbed loop surrounds it.

## 6. Roads and parking

- **Frontage road** (illustrative cross-section, about 76 m): verge 6, service road 8, separator 4, 4 lanes, median 10 with palms, 4 lanes, separator 4, service road 8, verge 6. Lane markings and street lights every 34 m.
- **South-east road:** 2 × 3 lanes with a 14 m landscaped median (illustrative).
- **Internal:** asphalt drives. Parking is single-row 2.6 × 5.2 m stalls in the DWG's 6 m bays, back-to-back, with 6 m aisles as in the S1 p.4 section.

## 7. Signage strategy

- No brand logos or invented names in any render.
- Brand bands are left blank (graphite).
- All text (labels, numbers, arrows) is added in PowerPoint as editable objects, never baked into images.

## 8. Lighting approach

| Mood | Use | Sun | Notes |
|---|---|---|---|
| **Golden hour** (default) | Hero, frontage, arena, plaza | Azimuth about 288°, elevation 11–20°, warm | Reads form and shade |
| **Day** | Masterplan, off-road | Azimuth 215–250°, elevation 26–55° | Maximum legibility |
| **Dusk / blue hour** | 2 images only (district atmosphere, Collectors' Club) | Elevation about 1.5° | Interiors glow at a realistic level; no neon |
| **Interiors** | Arena, museum, simulator, club | Area and spot lights; daylight through glazing | Warm 3000–3500 K feel |

## 9. Camera and rendering standards

- Path-traced (Blender Cycles 5.2), physically based materials, AgX view transform, denoised.
- Vertical lines kept vertical in eye-level views. Lenses are 20–24 mm for interiors and 26–32 mm for aerials and exteriors.
- Vantage points: drone (12–60 m) for destinations, pedestrian (1.6–2.2 m) only where foreground assets hold up, aerial (170–320 m) for the district.
- One shared post-production grade (`tools/post.py`): mild S-curve, warm highlights / cool shadows, +8% saturation, soft vignette, light sharpening.
- Scale figures and vehicles are kept at least about 7–10 m from the lens, because they are simplified models.
- Surrounding context is generic, low-detail massing that fades with distance. It represents "existing urban fabric" and does not depict actual neighbours.

## 10. Consistency rules (checked in QA)

1. Every view is rendered from the same `jmd.blend`, so the arena, club and showroom row are identical across images.
2. Showroom fronts face the frontage road, and shop fronts face the showroom row.
3. The off-road field always sits between the club and the service zone, and the launch plaza always sits at the arena's south tip.
4. No element is shown that the DWG does not contain, except interiors and the off-site context. The museum and simulator hall appear only as interiors, with "location to be confirmed".
