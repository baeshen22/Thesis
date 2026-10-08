// JMD municipality concept deck — structured pptxgenjs build (theme, layouts, placeholders, sections).
// usage: node build_deck.js <img_dir> <anchors.json> <out.pptx>
const path = require('path');
const fs = require('fs');
const pptxgen = require(path.join(__dirname, 'node', 'node_modules', 'pptxgenjs'));
const { applyTheme } = require(process.env.PPTX_SKILL + '/scripts/apply_theme.js');

const IMG = process.argv[2], ANCH = JSON.parse(fs.readFileSync(process.argv[3])), OUT = process.argv[4];
const img = (n) => path.join(IMG, n);

const THEME = {
  name: 'JMD Concept',
  headFontFace: 'Arial', bodyFontFace: 'Calibri',
  colors: {
    dk1: '1B1C1E', lt1: 'F4F1EC', dk2: '2B2C2F', lt2: 'D8D1C5',
    accent1: 'B08D57', accent2: '8E8A83', accent3: '6F8A96', accent4: 'C9B48A', accent5: '7A5C3A', accent6: '6E7B5B',
    hlink: 'C9B48A', folHlink: '8E8A83',
  },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';               // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = 'Jeddah Motor District — Concept Presentation';
pres.subject = 'Concept visualisation for the Municipality of Jeddah';
pres.author = 'JMD Project Team';
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, MX = 0.5;

// ------------------------------------------------------------------ layouts (frames)
const footer = [
  { text: { text: 'JEDDAH MOTOR DISTRICT  ·  CONCEPT FOR DISCUSSION', options: { x: MX, y: 7.06, w: 7, h: 0.28, fontSize: 9, color: C.background2, charSpacing: 2, margin: 0 } } },
];
pres.defineSlideMaster({
  title: 'JMD Hero',
  background: { color: HEX.dk1 },
  objects: [],
  slideNumber: { x: 12.45, y: 7.06, w: 0.4, h: 0.28, fontSize: 9, color: HEX.lt2, align: 'right' },
});
pres.defineSlideMaster({
  title: 'JMD Content',
  background: { color: HEX.dk1 },
  objects: [
    ...footer,
    { placeholder: { options: { name: 'kicker', type: 'body', x: MX, y: 0.32, w: 9.5, h: 0.3, fontSize: 11, bold: true, color: C.accent1, charSpacing: 3, margin: 0, valign: 'top', align: 'left' }, text: 'SECTION' } },
    { placeholder: { options: { name: 'title', type: 'title', x: MX, y: 0.6, w: 12.3, h: 0.7, fontSize: 30, color: C.background1, margin: 0, valign: 'top', align: 'left' }, text: 'Slide title' } },
  ],
  slideNumber: { x: 12.45, y: 7.06, w: 0.4, h: 0.28, fontSize: 9, color: HEX.lt2, align: 'right' },
});

// ------------------------------------------------------------------ helpers
let SECTION = '';
function section(t) { pres.addSection({ title: t }); SECTION = t; }
function slide(layout) { return pres.addSlide({ masterName: layout, sectionTitle: SECTION }); }
function T(s, text, o) {
  s.addText(text, Object.assign({ isTextBox: true, margin: 0, fontFace: THEME.bodyFontFace, color: C.background1, fontSize: 14, valign: 'top', paraSpaceAfter: 4 }, o));
}
function heads(s, kicker, title) {
  s.addText(kicker, { placeholder: 'kicker' });
  s.addText(title, { placeholder: 'title' });
}
function pic(s, file, x, y, w, h, name) {
  // all renders are 16:9; 'cover' crops to the frame
  s.addImage({ path: img(file), x, y, w, h, sizing: { type: 'cover', w, h }, altText: name, objectName: name });
}
function tag(s, text, x, y, w, src = false) {
  s.addText(text, { isTextBox: true, x, y, w, h: 0.26, fontSize: 9, margin: [2, 6, 2, 6], color: src ? HEX.dk1 : C.background1,
    fill: { color: src ? HEX.accent4 : HEX.dk1, transparency: src ? 0 : 25 }, charSpacing: 1, objectName: 'image tag', valign: 'middle' });
}
const NEW = 'NEW CONCEPT VISUALISATION · ILLUSTRATIVE';
// 'block' = editable placeholder-style text group: header + body
function block(s, x, y, w, head, body, o = {}) {
  T(s, head.toUpperCase(), { x, y, w, h: 0.28, fontSize: 11, bold: true, color: C.accent1, charSpacing: 2, objectName: 'block head' });
  T(s, body, Object.assign({ x, y: y + 0.32, w, h: o.h || 0.9, fontSize: o.fs || 14, color: C.background1, objectName: 'block body' }, o.opts || {}));
}
function discuss(s, x, y, w, text, h = 0.62) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: HEX.dk2 }, line: { color: HEX.accent5, width: 0.75 }, objectName: 'discussion point frame' });
  T(s, [{ text: 'FOR DISCUSSION  ', options: { bold: true, color: HEX.accent4, fontSize: 10, charSpacing: 2 } }, { text, options: { fontSize: 12, color: HEX.lt1 } }],
    { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h - 0.12, valign: 'middle', objectName: 'discussion point' });
}
function numDot(s, x, y, n, color = HEX.accent1, d = 0.36, fs = 12) {
  s.addShape(pres.shapes.OVAL, { x: x - d / 2, y: y - d / 2, w: d, h: d, fill: { color }, line: { color: HEX.dk1, width: 1 }, objectName: `marker ${n}` });
  s.addText(String(n), { isTextBox: true, x: x - d / 2, y: y - d / 2, w: d, h: d, align: 'center', valign: 'middle', fontSize: fs, bold: true, color: HEX.dk1, margin: 0, objectName: `marker label ${n}` });
}
// plan mapping: anchors are image fractions of the square ortho masterplan
const planXY = (fx, fy, X0, Y0, S) => [X0 + fx * S, Y0 + fy * S];
const m2f = (x, y) => [x / 1000 + 0.5, 0.5 - (y + 5) / 1000];

// ================================================================== 01 TITLE
section('Introduction');
let s = slide('JMD Hero');
s.background = { path: img('S01_hero.jpg') };
T(s, 'CONCEPT PRESENTATION  ·  MUNICIPALITY OF JEDDAH', { x: 0.7, y: 4.35, w: 8, h: 0.3, fontSize: 12, bold: true, color: C.accent4, charSpacing: 3, objectName: 'kicker' });
s.addText('Jeddah Motor District', { isTextBox: true, x: 0.7, y: 4.7, w: 9, h: 1.0, fontFace: THEME.headFontFace, fontSize: 48, color: C.background1, margin: 0, objectName: 'deck title' });
T(s, 'An integrated automotive destination: retail, experiences, heritage and events in one district', { x: 0.7, y: 5.75, w: 7.6, h: 0.7, fontSize: 18, color: C.background2, objectName: 'subtitle' });
T(s, '[Date]  ·  [Presenter name, organisation]', { x: 0.7, y: 6.6, w: 6, h: 0.3, fontSize: 12, color: C.background2, objectName: 'date and presenter' });
tag(s, NEW, 9.6, 7.05, 3.2);
s.addNotes(`PURPOSE: Open with the whole district in one image before any detail.
TALKING POINTS:
- JMD is proposed as a destination built around automotive culture, not a conventional dealership strip.
- This image shows the full concept layout as drawn in the latest plan (FINAL 8-10-2026): curved showroom frontage, lifestyle boulevard, arena and launch plaza, Collectors' Club, off-road experience, service village.
- Everything shown is at concept stage and for discussion.
SOURCE: Layout = FINAL_8-10-2026.dwg. Render = new illustrative visualisation (heights, materials, landscape and surrounding context are illustrative).`);

// ================================================================== 02 VISION
s = slide('JMD Hero');
s.background = { path: img('S02_vision.jpg') };
T(s, 'THE VISION', { x: 0.7, y: 0.55, w: 6, h: 0.3, fontSize: 12, bold: true, color: C.accent4, charSpacing: 3, objectName: 'kicker' });
s.addText('More than an automotive retail destination', { isTextBox: true, x: 0.7, y: 0.85, w: 9.5, h: 0.8, fontFace: THEME.headFontFace, fontSize: 32, color: C.background1, margin: 0, objectName: 'title' });
const pillars = [
  ['Buy & maintain', 'Brand showrooms, test drives and a dedicated light-service and spare-parts village in one place.'],
  ['Experience & learn', 'Off-road driving, simulators and automotive heritage, open to visitors who are not buying a car.'],
  ['Gather & celebrate', 'A flexible arena, launch plaza and Collectors’ Club for launches, exhibitions and events.'],
];
pillars.forEach(([h, b], i) => block(s, 0.7 + i * 4.1, 5.55, 3.7, h, b, { h: 1.0 }));
tag(s, NEW, 9.6, 0.25, 3.2);
s.addNotes(`PURPOSE: State the central idea in one sentence, then the three things the district does.
TALKING POINTS:
- Commercial core: showrooms, lifestyle retail, service village.
- Public experience: off-road, simulators, heritage museum; people can visit without purchasing.
- Events: arena, launch plaza, club — a reason to return.
SOURCE: Programme from JMD Concept 1 (pp.2–23) and the narration. Image = new illustrative dusk view of the DWG layout.`);

// ================================================================== 03 DISTRICT ORGANISATION
section('The District');
s = slide('JMD Content');
heads(s, 'PROJECT COMPONENTS AND DISTRICT ORGANISATION', 'One district, three kinds of place');
const PX0 = 0.5, PY0 = 1.4, PS = 5.45;
pic(s, 'S03_masterplan.jpg', PX0, PY0, PS, PS, 'Masterplan top view');
const legend = [
  ['showrooms', 'Automotive showroom district (52 units)', 'c'], ['shops', 'Lifestyle & retail boulevard', 'c'],
  ['arena', 'Grand automotive arena (7 divisible halls)', 'a'], ['plaza', 'Outdoor launch plaza', 'a'],
  ['club', 'Collectors’ Club', 'a'], ['offroad', 'Off-road experience & test-drive loop', 'a'],
  ['testdrive', 'Test-drive centre & guest parking', 'a'], ['service', 'Light-service & spare-parts village', 'o'],
  ['storage', 'Dealer storage & vehicle preparation', 'o'], ['energy', 'Energy hub', 'o'],
  ['mosque_s', 'Mosques (2)', 'o'], ['management', 'District management', 'o'],
];
const catCol = { c: HEX.accent1, a: HEX.accent4, o: HEX.accent2 };
legend.forEach(([k, label, cat], i) => {
  const [x, y] = planXY(ANCH[k][0], ANCH[k][1], PX0, PY0, PS);
  numDot(s, x, y, i + 1, catCol[cat], 0.3, 10);
});
numDot(s, ...planXY(ANCH['mosque_l'][0], ANCH['mosque_l'][1], PX0, PY0, PS), 11, catCol.o, 0.3, 10);
const LX = 6.35;
[['c', 'COMMERCIAL'], ['a', 'VISITOR ATTRACTIONS & EVENTS'], ['o', 'OPERATIONS & SUPPORT']].forEach(([cat, name], gi) => {
  const items = legend.map((l, i) => [l, i]).filter(([l]) => l[2] === cat);
  const y0 = [1.4, 2.35, 4.32][gi];
  T(s, name, { x: LX, y: y0, w: 6.4, h: 0.28, fontSize: 11, bold: true, color: catCol[cat], charSpacing: 2, objectName: 'legend group' });
  items.forEach(([l, i], j) => {
    numDot(s, LX + 0.15, y0 + 0.47 + j * 0.34, i + 1, catCol[cat], 0.28, 10);
    T(s, l[1], { x: LX + 0.42, y: y0 + 0.335 + j * 0.34, w: 5.9, h: 0.3, fontSize: 14, objectName: 'legend item' });
  });
});
T(s, 'Layout: FINAL 8-10-2026 drawing. Heights, landscape, roads beyond the boundary and surrounding context are illustrative.', { x: LX, y: 6.42, w: 6.4, h: 0.45, fontSize: 10, color: C.background2, objectName: 'plan note' });
tag(s, NEW + ' · NORTH UP', PX0, PY0 + PS - 0.26, 4.4);
s.addNotes(`PURPOSE: Show the complete district and how it is organised before discussing individual buildings.
TALKING POINTS:
- Commercial frontage (1–2): showrooms face the main road; the lifestyle boulevard faces the showrooms.
- Visitor and event core (3–7): arena and launch plaza at the southern tip, Collectors' Club at the hinge, off-road and test-drive in the centre.
- Operations (8–12): service village, dealer storage and vehicle preparation sit at the back, away from the public frontage.
FACTS (measured from FINAL_8-10-2026.dwg, indicative): 52 showroom units (23 standard, 21 premium, 7 flagship, 1 flagship-plus); 29 shop units; 7 arena hall bays ≈12,900 m²; 58 light-service units.
CAUTION: The museum and simulator hall are not located on the current drawing — see slides 11–12.
SOURCE: DWG = confirmed layout; numbering and grouping = new.`);

// ================================================================== 04 URBAN INTEGRATION & ARRIVAL
s = slide('JMD Content');
heads(s, 'URBAN INTEGRATION AND ARRIVAL', 'A clear address on the main road');
pic(s, 'S04_arrival.jpg', 0.5, 1.4, 8.4, 4.725, 'Arrival view from the frontage road');
tag(s, NEW, 0.5, 1.4 + 4.725 - 0.26, 3.2);
block(s, 9.25, 1.45, 3.6, 'Frontage address', 'The showroom row lines the main-road frontage, set behind customer parking and a landscaped verge.', { h: 1.05 });
block(s, 9.25, 2.85, 3.6, 'Access from two sides', 'The front road serves visitors and showrooms. The south-east road serves events and operations.', { h: 1.05 });
block(s, 9.25, 4.25, 3.6, 'Parking at each destination', 'Parking bays are distributed between the rows and next to the arena, test-drive centre and service village.', { h: 1.05 });
discuss(s, 0.5, 6.3, 12.35, 'Access points, junction arrangements and event-day traffic require a traffic impact study and municipal coordination.');
s.addNotes(`PURPOSE: Explain how the district meets the city: road frontage, access, parking.
TALKING POINTS:
- The frontage road is shown with an illustrative cross-section; the narration identifies the frontage as Madinah Road — to be confirmed for the selected site.
- Entry/exit positions, junction design and parking quantities are not yet assessed.
SOURCE: Layout = DWG. Road cross-section, context massing = illustrative assumptions. Road name per narration (S2) and earlier masterplan (S5) — not shown on the DWG.`);

// ================================================================== 05 SHOWROOM BOULEVARD
section('Destinations');
s = slide('JMD Content');
heads(s, 'AUTOMOTIVE SHOWROOM DISTRICT', 'A coordinated frontage of brand showrooms');
pic(s, 'S05_showroom_street.jpg', 0.5, 1.4, 8.9, 5.0, 'Showroom frontage at street level');
tag(s, NEW, 0.5, 6.14, 3.2);
pic(s, 'S05_showroom_blvd.jpg', 9.7, 1.4, 3.15, 1.77, 'Showroom boulevard from above');
block(s, 9.7, 3.4, 3.15, 'One frontage, many brands', '52 showroom units in standard, premium and flagship sizes, joined by one plinth, roof line and shading canopy.', { h: 1.45, fs: 14 });
block(s, 9.7, 5.1, 3.15, 'Customer parking at the door', 'Each showroom faces its own parking bay and the frontage service drive.', { h: 1.0, fs: 14 });
s.addNotes(`PURPOSE: Show the street-level character of the showroom frontage.
TALKING POINTS:
- Unit sizes and arrangement follow the DWG: 23 standard (~240 m²), 21 premium (~350–370 m²), 7 flagship (~390–460 m²), 1 flagship-plus (540 m²).
- Heights 9–14 m and the façade kit are illustrative design development.
- Brand bands are deliberately left blank: no brand commitments are implied.
SOURCE: DWG footprints; design language from JMD Concept 1 pp.3–6 and 31–33; voice notes 1–2 stress the street-level feeling of the boulevard; render new.`);

// ================================================================== 06 SHOWROOM IDENTITIES
s = slide('JMD Content');
heads(s, 'INDIVIDUAL SHOWROOM IDENTITIES', 'Brand expression within one district language');
const fac = [['S06a_facade.jpg', 'Vertical louvre + minimal', 'Bronze fins shade the glass; a minimal neighbour sits beside it.'],
  ['S06b_facade.jpg', 'Contemporary frame', 'A protruding stone portal marks a flagship or premium brand.'],
  ['S06c_facade.jpg', 'Stone & glass', 'A solid limestone pier balances a fully glazed display.']];
fac.forEach(([f, h, b], i) => {
  const x = 0.5 + i * 4.17;
  pic(s, f, x, 1.45, 3.95, 2.22, h);
  block(s, x, 3.85, 3.95, h, b, { h: 0.8 });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 5.2, w: 12.35, h: 1.15, rectRadius: 0.06, fill: { color: HEX.dk2 }, line: { color: HEX.dk2 }, objectName: 'shared elements panel' });
T(s, [{ text: 'SHARED BY EVERY SHOWROOM   ', options: { bold: true, color: HEX.accent1, fontSize: 11, charSpacing: 2 } },
  { text: 'common plinth  ·  roof edge and front canopy  ·  bronze corner blades  ·  graphite brand band (left blank for each brand)  ·  limestone-tone side walls', options: { fontSize: 14 } }],
{ x: 0.75, y: 5.3, w: 11.9, h: 0.95, valign: 'middle', objectName: 'shared elements' });
tag(s, NEW + ' · PALMS OMITTED FOR CLARITY', 0.5, 6.5, 5.2);
s.addNotes(`PURPOSE: Answer "will it look uniform?" — brands get identity, the district stays coherent.
TALKING POINTS:
- Voice-note intent: showrooms should have different possible looks rather than identical, typical boxes.
- Five façade options from the concept (louvre, minimal, frame, stone & glass, angled canopy) are applied as a kit of parts.
- Shared plinth, roof line, bronze blades and the blank brand band keep the frontage coherent.
SOURCE: Options = JMD Concept 1 p.5; application = new design development; renders new.`);

// ================================================================== 07 LIFESTYLE BOULEVARD
s = slide('JMD Content');
heads(s, 'COMMERCIAL AND LIFESTYLE BOULEVARD', 'Shaded retail facing the showroom row');
pic(s, 'S07_arcade.jpg', 4.45, 1.4, 8.4, 4.725, 'Lifestyle arcade');
tag(s, NEW, 4.45, 1.4 + 4.725 - 0.26, 3.2);
block(s, 0.5, 1.45, 3.6, 'Behind the showrooms', '29 units for automotive accessories, brand lifestyle and design stores, cafés and food & beverage.', { h: 1.1 });
block(s, 0.5, 2.95, 3.6, 'Continuous shade', 'A 5.5 m deep arcade on slender bronze columns provides shaded walking along the whole row.', { h: 1.1 });
block(s, 0.5, 4.45, 3.6, 'Open to all visitors', 'People can visit without buying a car, which keeps the district active through the day and evening.', { h: 1.1 });
discuss(s, 0.5, 6.3, 12.35, 'Pedestrian crossings between the showroom and retail rows, shade standards and F&B outdoor seating.');
s.addNotes(`PURPOSE: Show the public, pedestrian side of the district.
TALKING POINTS:
- The retail row is drawn as 29 units facing the showroom row across the internal drive.
- Tenant mix is indicative (voice note 2 examples: accessories shops, a brand design store, cafés); arcade and shade are design proposals.
SOURCE: DWG footprints (labelled "commercial shop"); programme from JMD Concept 1 p.13 and earlier masterplan zone 7; render new.`);

// ================================================================== 08 ARENA
s = slide('JMD Content');
heads(s, 'GRAND AUTOMOTIVE ARENA', 'A landmark venue at the district’s southern tip');
pic(s, 'S08_arena.jpg', 0.5, 1.4, 12.35, 5.25, 'Grand arena exterior');
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.75, y: 4.55, w: 4.3, h: 1.85, rectRadius: 0.06, fill: { color: HEX.dk1, transparency: 15 }, line: { color: HEX.dk1 }, objectName: 'facts panel' });
block(s, 0.95, 4.7, 3.95, 'As drawn', '7 divisible hall bays, about 12,900 m², under one roof with a shaded concourse and an entrance on the launch plaza.', { h: 1.2 });
tag(s, NEW, 9.65, 6.39, 3.2);
s.addNotes(`PURPOSE: Introduce the arena as the district's landmark and event anchor.
TALKING POINTS:
- Form follows the triangular site at the southern tip of the DWG; floating roof, glazed concourse, bronze-fin upper façade.
- Hall bays can operate separately or together (see next slide).
- Earlier concept images show different arena forms (glass dome, faceted pavilion); this deck consolidates on the current drawing.
SOURCE: DWG (arena halls ≈12,911 m²; concourse band ≈5,911 m²); render new. Capacities: not yet confirmed.`);

// ================================================================== 09 ARENA FLEXIBILITY
s = slide('JMD Content');
heads(s, 'GRAND ARENA — FLEXIBLE EVENTS', 'One floor, many configurations');
pic(s, 'S09a_expo.jpg', 0.5, 1.4, 6.05, 3.4, 'Arena exhibition mode');
pic(s, 'S09b_theatre.jpg', 6.8, 1.4, 6.05, 3.4, 'Arena theatre mode');
tag(s, 'EXHIBITION MODE · ILLUSTRATIVE', 0.5, 4.54, 3.0); tag(s, '180° THEATRE MODE · ILLUSTRATIVE', 6.8, 4.54, 3.1);
const modes = ['360° arena', '270° arena', '180° theatre', 'Runway', 'Exhibition', 'E-karting'];
modes.forEach((m, i) => {
  const x = 0.5 + i * 2.07, y = 5.0, w = 1.9, h = 1.15;
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: HEX.dk2 }, line: { color: HEX.dk2 }, objectName: `mode ${m} frame` });
  const fx = x + 0.45, fy = y + 0.25, fw = 1.0, fh = 0.62;
  const seat = { fill: { color: HEX.accent1 }, line: { color: HEX.accent1 } };
  const floor = { fill: { color: '4A4B4F' }, line: { color: '4A4B4F' } };
  const add = (shape, o, nm) => s.addShape(shape, Object.assign({ objectName: `mode ${m} ${nm}` }, o));
  if (i <= 2 || i === 3) add(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ x: fx, y: fy, w: fw, h: fh, rectRadius: 0.08 }, floor), 'floor');
  if (i === 0) { [[fx, fy - 0.17, fw, 0.12], [fx, fy + fh + 0.05, fw, 0.12], [fx - 0.17, fy, 0.12, fh], [fx + fw + 0.05, fy, 0.12, fh]].forEach(([a, b, c, d]) => add(pres.shapes.RECTANGLE, Object.assign({ x: a, y: b, w: c, h: d }, seat), 'seating')); }
  if (i === 1) { [[fx, fy - 0.17, fw, 0.12], [fx - 0.17, fy, 0.12, fh], [fx + fw + 0.05, fy, 0.12, fh]].forEach(([a, b, c, d]) => add(pres.shapes.RECTANGLE, Object.assign({ x: a, y: b, w: c, h: d }, seat), 'seating')); add(pres.shapes.LINE, { x: fx, y: fy + fh + 0.1, w: fw, h: 0, line: { color: HEX.lt2, width: 1, dashType: 'dash' } }, 'open back-of-house'); }
  if (i === 2) { add(pres.shapes.RECTANGLE, { x: fx + 0.15, y: fy + 0.04, w: fw - 0.3, h: 0.1, fill: { color: HEX.lt1 }, line: { color: HEX.lt1 } }, 'stage'); [0, 1, 2].forEach((k) => add(pres.shapes.RECTANGLE, Object.assign({ x: fx + 0.06 + k * 0.32, y: fy + fh - 0.26 + (k === 1 ? 0.05 : 0), w: 0.24, h: 0.2 }, seat), 'seating')); }
  if (i === 3) { add(pres.shapes.RECTANGLE, { x: fx + fw / 2 - 0.07, y: fy + 0.04, w: 0.14, h: fh - 0.08, fill: { color: HEX.lt1 }, line: { color: HEX.lt1 } }, 'runway'); [fx + 0.1, fx + fw / 2 + 0.15].forEach((a) => add(pres.shapes.RECTANGLE, Object.assign({ x: a, y: fy + 0.08, w: 0.25, h: fh - 0.16 }, seat), 'seating')); }
  if (i === 4) { for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) add(pres.shapes.RECTANGLE, Object.assign({ x: fx + 0.05 + c * 0.33, y: fy + 0.06 + r * 0.3, w: 0.24, h: 0.2 }, seat), 'stand'); }
  if (i === 5) { add(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: fy, w: fw, h: fh, rectRadius: 0.2, fill: { color: HEX.dk2 }, line: { color: HEX.accent4, width: 2 } }, 'track'); add(pres.shapes.ROUNDED_RECTANGLE, { x: fx + 0.25, y: fy + 0.2, w: fw - 0.5, h: fh - 0.4, rectRadius: 0.1, fill: { color: HEX.dk2 }, line: { color: HEX.accent4, width: 2 } }, 'track inner'); }
  T(s, m, { x, y: y + h + 0.05, w, h: 0.26, fontSize: 11, bold: true, align: 'center', objectName: `mode ${m} label` });
  T(s, '[capacity TBC]', { x, y: y + h + 0.3, w, h: 0.24, fontSize: 10, align: 'center', color: C.background2, objectName: `mode ${m} capacity` });
});
s.addNotes(`PURPOSE: Demonstrate flexibility — the same hall serves launches, motor shows, conferences and public events.
TALKING POINTS:
- The drawing divides the arena into 7 bays that can be used independently or combined (concept Mode 01–03).
- Six configurations from the concept: 360°, 270°, 180° theatre, runway, exhibition, e-karting.
- Capacities in the earlier concept vary by mode (approx. 4,500–12,000) and are NOT yet confirmed — placeholders left for the team.
SOURCE: Modes = JMD Concept 1 pp.17–23; hall geometry = DWG; interior renders and diagrams new and illustrative.`);

// ================================================================== 10 OFF-ROAD
s = slide('JMD Content');
heads(s, 'OFF-ROAD DRIVING EXPERIENCE', 'Real off-road terrain, inside the city');
pic(s, 'S10_offroad.jpg', 0.5, 1.4, 8.4, 4.725, 'Off-road experience');
tag(s, NEW, 0.5, 1.4 + 4.725 - 0.26, 3.2);
const terr = ['Hill climb and descent', 'Mud and water crossing', 'Dune field', 'Rock crawl', 'Axle-twister ramps', 'Side-slope section', 'Kerbed test-drive loop'];
T(s, 'EXPERIENCE ZONES (AS DRAWN)', { x: 9.25, y: 1.45, w: 3.6, h: 0.28, fontSize: 11, bold: true, color: C.accent1, charSpacing: 2 });
terr.forEach((t, i) => { numDot(s, 9.4, 2.0 + i * 0.47, i + 1, HEX.accent4, 0.28, 10); T(s, t, { x: 9.7, y: 1.87 + i * 0.47, w: 3.2, h: 0.3, fontSize: 14 }); });
T(s, 'Registration pavilion, drop-off, test-car and guest parking sit at the south-east entrance.', { x: 9.25, y: 5.3, w: 3.6, h: 0.8, fontSize: 12, color: C.background2 });
discuss(s, 0.5, 6.3, 12.35, 'Safety separation, dust and noise management, and operating hours next to public areas.');
s.addNotes(`PURPOSE: Explain the off-road experience and where it sits.
TALKING POINTS:
- The drawing defines the off-road zone (≈5.4 ha incl. loop) with 7 obstacle areas inside a test-drive loop.
- Voice-note intent: simulate a real off-road experience within an urban setting — five or six experiences such as mud, water, and driving up and down hills.
- Obstacle types and heights shown are illustrative (mounds ~10 m, mud/water crossing, rocks, ramps, side-slope).
- Earlier masterplan quoted a 2.5 km loop; the current drawing's loop is shorter — length to be confirmed.
SOURCE: DWG zones; JMD Concept 1 p.7 and project voice note 2 for intent; render new.`);

// ================================================================== 11 MUSEUM
s = slide('JMD Content');
heads(s, 'WALL OF FAME — AUTOMOTIVE HERITAGE MUSEUM', 'The stories behind the brands');
pic(s, 'S11_museum.jpg', 0.5, 1.4, 8.4, 4.725, 'Wall of Fame museum interior');
tag(s, NEW, 0.5, 1.4 + 4.725 - 0.26, 3.2);
block(s, 9.25, 1.45, 3.6, 'Heritage, not sales', 'A museum path through the corporate achievements of automotive companies: founders, milestones and collected cars.', { h: 1.2 });
block(s, 9.25, 2.95, 3.6, 'Curated content', 'Milestone panels and display cars are shown blank here. Content is to be curated with the brands.', { h: 1.2 });
block(s, 9.25, 4.45, 3.6, 'Location', '[To be confirmed: it is not located on the current drawing. Options include the arena complex or next to the Collectors’ Club.]', { h: 1.4, fs: 13 });
s.addNotes(`PURPOSE: Introduce the museum as a heritage attraction (explicitly not a showroom).
TALKING POINTS:
- Focus (per voice note 2): a museum of the car companies' achievements as corporations — a visitor path past collected cars, founders and milestones. Explicitly not a showroom or sales space.
- Location and building form are open: the earlier concept shows two different exterior designs and the current drawing does not include the museum.
SOURCE: Intent = JMD Concept 1 pp.8–10 and voice note 2; interior render new and illustrative; location unresolved (register item).`);

// ================================================================== 12 SIMULATOR
s = slide('JMD Content');
heads(s, 'AUTOMOTIVE SIMULATOR HALL', 'Experience driving many different cars');
pic(s, 'S12_simulator.jpg', 4.45, 1.4, 8.4, 4.725, 'Simulator hall interior');
tag(s, NEW, 4.45, 1.4 + 4.725 - 0.26, 3.2);
block(s, 0.5, 1.45, 3.6, 'For every visitor', 'Multiple simulators let visitors experience driving specific cars, from a supercar to an off-roader or a city car.', { h: 1.2 });
block(s, 0.5, 2.95, 3.6, 'Competitive & social', 'Rows of rigs, a feature 360° pod and a lounge support sessions, leagues and corporate events.', { h: 1.2 });
block(s, 0.5, 4.45, 3.6, 'Location', '[To be confirmed: it is not located on the current drawing.]', { h: 1.0 });
s.addNotes(`PURPOSE: Show an all-weather, all-ages attraction.
TALKING POINTS:
- Per voice note 2: multiple simulators, each giving the experience of driving a specific car (examples given ranged from supercars to an off-roader and a city car).
- Screens shown with neutral imagery; brand content would be licensed.
SOURCE: Intent = JMD Concept 1 pp.11–12; render new and illustrative; location unresolved.`);

// ================================================================== 13 COLLECTORS' CLUB
s = slide('JMD Content');
heads(s, 'COLLECTORS’ CLUB', 'A home for rare and classic vehicles');
pic(s, 'S13a_club_ext.jpg', 0.5, 1.4, 6.05, 3.4, 'Collectors club exterior');
pic(s, 'S13b_club_lounge.jpg', 6.8, 1.4, 6.05, 3.4, 'Collectors club lounge');
tag(s, 'EXTERIOR AT DUSK · ILLUSTRATIVE', 0.5, 4.54, 3.0); tag(s, 'GALLERY LOUNGE · ILLUSTRATIVE', 6.8, 4.54, 3.0);
block(s, 0.5, 5.0, 3.9, 'Three levels', 'Glazed display gallery at ground level, members’ lounges above and a shaded roof terrace.', { h: 1.0 });
block(s, 4.72, 5.0, 3.9, 'Store or simply meet', 'Members can store their cars or come to meet in the lounge and café, with valet drop-off.', { h: 1.0 });
block(s, 8.95, 5.0, 3.9, 'At the hinge', 'Sits between the arena and the off-road field, close to events but discreet.', { h: 1.0 });
s.addNotes(`PURPOSE: Present the exclusive club and its place in the district.
TALKING POINTS:
- Footprint as drawn: a 30 x 117 m bar (≈3,500 m²) between the arena and off-road zone.
- Per voice note 2: a club for collectors of luxury and collectible cars — members can store their cars or simply come to spend time (lounge, café).
- Three levels per the earlier concept; storage location (basement) to be confirmed.
SOURCE: DWG footprint; intent from JMD Concept 1 pp.14–15 and earlier masterplan zone 3; renders new.`);

// ================================================================== 14 LAUNCH PLAZA
s = slide('JMD Content');
heads(s, 'OUTDOOR EXHIBITION AND LAUNCH PLAZA', 'Where new models meet the public');
pic(s, 'S14_plaza.jpg', 0.5, 1.4, 12.35, 5.25, 'Outdoor launch plaza');
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.55, y: 1.65, w: 4.05, h: 2.2, rectRadius: 0.06, fill: { color: HEX.dk1, transparency: 15 }, line: { color: HEX.dk1 }, objectName: 'text panel' });
block(s, 8.75, 1.8, 3.7, 'Reveal & activate', 'A shaded plaza at the arena entrance for vehicle reveals, temporary exhibitions and brand activations.', { h: 1.3 });
T(s, 'Outdoor function area as drawn: about 2,850 m²', { x: 8.75, y: 3.4, w: 3.7, h: 0.3, fontSize: 11, color: C.background2 });
tag(s, NEW, 0.5, 6.39, 3.2);
s.addNotes(`PURPOSE: Show the public-facing event space.
TALKING POINTS:
- Located at the arena's southern entrance (DWG "outdoor function area").
- Shade sails, reveal stage and planting are illustrative.
- Event-day crowd management to be developed with the municipality.
SOURCE: DWG; intent JMD Concept 1 p.16; render new.`);

// ================================================================== 15 VISITOR JOURNEY
section('How It Works');
s = slide('JMD Content');
heads(s, 'THE INTEGRATED VISITOR EXPERIENCE', 'Three ways to use the district');
const JX0 = 0.5, JY0 = 1.4, JS = 5.45;
pic(s, 'S15_plan_dim.jpg', JX0, JY0, JS, JS, 'Masterplan for visitor journeys');
const journeys = [
  ['Customer journey', HEX.accent1, [[-395, 105], [-330, 112], [-300, 88], [-262, 40], [-190, -55], [-40, -62], [40, 10], [77, 34], [15, 75], [-15, 130], [120, 190], [250, 270]],
    'Arrive on the frontage, compare brands along the showroom row, test-drive on and off road, then use the service village.'],
  ['Family day out', 'E9E4DA', [[-120, 255], [-150, 205], [-182, 185], [-215, 125], [-232, 70], [-160, 0], [-134, -20], [-210, -95], [-297, -224]],
    'Park by the retail row, walk the shaded arcade, visit the club gallery and attractions, finish at the launch plaza.'],
  ['Event night', HEX.accent3, [[-60, -330], [-150, -260], [-250, -230], [-297, -224], [-262, -170], [-226, -116], [-150, -40]],
    'Arrive from the south-east road, gather on the plaza, enter the arena, then continue to the club.'],
];
journeys.forEach(([name, col, pts], ji) => {
  for (let k = 0; k < pts.length - 1; k++) {
    const [ax, ay] = planXY(...m2f(...pts[k]), JX0, JY0, JS), [bx, by] = planXY(...m2f(...pts[k + 1]), JX0, JY0, JS);
    s.addShape(pres.shapes.LINE, { x: Math.min(ax, bx), y: Math.min(ay, by), w: Math.abs(bx - ax) || 0.001, h: Math.abs(by - ay) || 0.001, flipH: bx < ax, flipV: by < ay,
      line: { color: col, width: 3, endArrowType: k === pts.length - 2 ? 'triangle' : undefined }, objectName: `${name} path ${k + 1}` });
  }
  const [sx, sy] = planXY(...m2f(...pts[0]), JX0, JY0, JS);
  numDot(s, sx, sy, ji + 1, col, 0.3, 10);
  const y = 1.5 + ji * 1.55;
  numDot(s, 6.5, y + 0.15, ji + 1, col, 0.32, 11);
  T(s, name.toUpperCase(), { x: 6.8, y, w: 6, h: 0.3, fontSize: 12, bold: true, color: col === 'E9E4DA' ? C.background1 : col, charSpacing: 2 });
  T(s, pts.length && journeys[ji][3], { x: 6.8, y: y + 0.36, w: 6.05, h: 1.0, fontSize: 14 });
});
discuss(s, 6.4, 6.15, 6.45, 'Pedestrian routes, crossings and event-day separation of visitors and service traffic.', 0.75);
tag(s, 'INDICATIVE ROUTES ON THE CONCEPT LAYOUT', JX0, JY0 + JS - 0.26, 3.4);
s.addNotes(`PURPOSE: Show that the components work together as one destination.
TALKING POINTS:
- Three typical visits: customer, family/day visitor, event night.
- Operational traffic (service village, dealer storage, deliveries) stays at the back of the site, away from the public frontage.
- Routes are indicative; detailed movement and access design to follow.
SOURCE: Diagram new; routes drawn on the DWG-based plan.`);

// ================================================================== 16 SITE OPPORTUNITIES
s = slide('JMD Content');
heads(s, 'SITE OPPORTUNITIES AND DEVELOPMENT CONTEXT', 'Location options under consideration');
s.addImage({ path: img('S16_locations.jpg'), x: 0.5, y: 1.4, w: 6.05, h: 3.4, sizing: { type: 'cover', w: 6.05, h: 3.4 }, objectName: 'source location overview' });
s.addImage({ path: img('S16_options.jpg'), x: 6.8, y: 1.4, w: 6.05, h: 3.4, sizing: { type: 'cover', w: 6.05, h: 3.4 }, objectName: 'source site options' });
tag(s, 'SOURCE MATERIAL · JMD CONCEPT 1, P.24', 0.5, 4.54, 3.3, true);
tag(s, 'SOURCE MATERIAL · JMD CONCEPT 1, P.25 · OPTIONS 1–3', 6.8, 4.54, 4.2, true);
block(s, 0.5, 5.0, 3.9, 'Options, not decisions', 'Three candidate locations were identified in the concept material. No site has been selected or approved.', { h: 1.1 });
block(s, 4.72, 5.0, 3.9, 'Adaptable concept', 'The district concept (components and relationships) can be adapted to the selected site.', { h: 1.1 });
block(s, 8.95, 5.0, 3.9, 'Next step', '[Confirm the preferred site, its boundary and area, then re-fit the layout.]', { h: 1.1 });
s.addNotes(`PURPOSE: Separate the district concept from location-specific proposals.
TALKING POINTS:
- Three location options appear in the concept material; none is approved.
- The current drawing (FINAL 8-10-2026) is a location-specific layout; the site it relates to and its boundary are to be confirmed.
- Site areas quoted in earlier material differ (≈170,000–180,000 m²) from the current drawing's boundary (≈41 ha) — to be reconciled.
SOURCE: Images reproduced from JMD Concept 1 pp.24–25 (satellite imagery as supplied).`);

// ================================================================== 17 OVERALL VISION + COORDINATION
section('Conclusion');
s = slide('JMD Hero');
s.background = { path: img('S17_vision.jpg') };
T(s, 'OVERALL DEVELOPMENT VISION', { x: 0.7, y: 0.55, w: 7, h: 0.3, fontSize: 12, bold: true, color: C.accent4, charSpacing: 3, objectName: 'kicker' });
s.addText('A distinctive automotive destination for Jeddah', { isTextBox: true, x: 0.7, y: 0.85, w: 7.4, h: 1.3, fontFace: THEME.headFontFace, fontSize: 32, color: C.background1, margin: 0, objectName: 'title' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.55, y: 0.5, w: 4.3, h: 6.3, rectRadius: 0.06, fill: { color: HEX.dk1, transparency: 12 }, line: { color: HEX.dk1 }, objectName: 'coordination panel' });
T(s, 'MATTERS FOR MUNICIPAL COORDINATION', { x: 8.8, y: 0.75, w: 3.9, h: 0.5, fontSize: 11, bold: true, color: C.accent1, charSpacing: 2 });
const coord = ['Site selection, boundary and land use', 'Access points and traffic impact', 'Parking provision and event-day management', 'Public realm, shade and pedestrian safety', 'Utilities and infrastructure interfaces', 'Off-road dust, noise and safety', 'Programme phasing'];
coord.forEach((c, i) => { numDot(s, 9.0, 1.55 + i * 0.66, i + 1, HEX.accent1, 0.28, 10); T(s, c, { x: 9.3, y: 1.42 + i * 0.66, w: 3.4, h: 0.6, fontSize: 14 }); });
T(s, 'Discussion topics, not completed assessments.', { x: 8.8, y: 6.2, w: 3.9, h: 0.4, fontSize: 11, color: C.background2 });
tag(s, NEW, 0.7, 7.05, 3.2);
s.addNotes(`PURPOSE: Bring the district back together and name what needs coordination next.
TALKING POINTS:
- One coherent district: commercial frontage, public attractions, events, operations at the back.
- The listed topics are proposed discussion items — no technical assessments have been completed and no approvals are implied.
SOURCE: Render new (DWG layout); coordination list new.`);

// ================================================================== 18 CLOSING
s = slide('JMD Hero');
s.background = { path: img('S18_closing.jpg') };
s.addText('Thank you', { isTextBox: true, x: 0.7, y: 4.9, w: 8, h: 0.9, fontFace: THEME.headFontFace, fontSize: 44, color: C.background1, margin: 0, objectName: 'closing title' });
T(s, 'Discussion  ·  [Contact name, email, phone]', { x: 0.7, y: 5.85, w: 8, h: 0.4, fontSize: 18, color: C.background2, objectName: 'contact' });
tag(s, NEW + ' · SHOWROOM FRONTAGE WITH ARENA BEYOND', 0.7, 7.05, 6.4);
s.addNotes(`PURPOSE: Close and invite discussion.
TALKING POINTS: Summarise the three roles (buy & maintain, experience & learn, gather & celebrate) and propose next steps: site confirmation, traffic and parking study, programme confirmation (museum, simulator, arena capacity).
SOURCE: Render new; this street-level view corresponds to the view described in the project narration (showrooms on the main road with the arena and club behind).`);

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log('wrote', OUT); });
