// requires: npm install @mlightcad/libredwg-web   usage: node dwg_read.mjs file.dwg out.json
import { Dwg_File_Type, LibreDwg } from '@mlightcad/libredwg-web';
import fs from 'fs';
const lib = await LibreDwg.create('./node_modules/@mlightcad/libredwg-web/wasm/');
const buf = fs.readFileSync(process.argv[2]);
const dwg = lib.dwg_read_data(buf, Dwg_File_Type.DWG);
const db = lib.convert(dwg);
fs.writeFileSync(process.argv[3], JSON.stringify(db,(k,v)=>typeof v==="bigint"?Number(v):v));
const ents = db.entities || [];
const c = {}; const L = {};
for (const e of ents) { c[e.type]=(c[e.type]||0)+1; L[e.layer]=(L[e.layer]||0)+1; }
console.log('entities', ents.length, c); console.log('layers', L);
console.log('blocks', (db.tables?.BLOCK_RECORD?.entries||[]).length);
