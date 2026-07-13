/**
 * seed-lassa-board.js
 *
 * Idempotent seeder for the Lassa Fever — Nigeria Intelligence Board.
 * Upserts the board shell, curated drug candidates, hypotheses, and
 * the LassaAI outbreak forecast as a pinned evidence item.
 *
 * Usage: node scripts/seed-lassa-board.js [--dry-run]
 */
import 'dotenv/config';
import { getSharedPool } from '../src/utils/db.js';
import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DRY_RUN = process.argv.includes('--dry-run');
const log = (...a) => console.log(...a);
const BOARD_SLUG = 'lassa-fever-nigeria';

// ── Evidence items ─────────────────────────────────────────────────────────────
const CURATED_ITEMS = [
  // Tier I — standard of care / strongest antiviral evidence
  {
    object_type: 'drug_candidate',
    object_id: 'ribavirin-lasv',
    evidence_score: 0.82,
    current_state: 'active',
    metadata: {
      drugName: 'Ribavirin',
      mechanism: 'Nucleoside analogue — inhibits LASV L polymerase via lethal mutagenesis and direct polymerase inhibition',
      targets: ['L', 'NP'],
      approvalStatus: 'FDA Orphan Drug Designation',
      tier: 'I',
      indication: 'Lassa fever — WHO/NCDC standard of care',
      note: 'Must be administered within first 6 days of illness. IV route preferred for severe disease. ~9× CFR reduction when given early.',
      trialNct: 'NCT02539832',
      trialStatus: 'COMPLETED',
      keyRef: 'McCormick et al. 1986 N Engl J Med',
    },
  },
  {
    object_type: 'drug_candidate',
    object_id: 'favipiravir-lasv',
    evidence_score: 0.76,
    current_state: 'active',
    metadata: {
      drugName: 'Favipiravir (T-705)',
      mechanism: 'Broad-spectrum RNA polymerase inhibitor — incorporated as faulty nucleoside triphosphate by LASV L polymerase',
      targets: ['L'],
      approvalStatus: 'Investigational (approved in Japan for influenza)',
      tier: 'I',
      indication: 'Lassa fever — superior efficacy vs ribavirin in NHP models; Phase 2 ongoing',
      note: 'Oral bioavailability advantage over IV ribavirin in low-resource settings.',
      trialNct: 'NCT04992026',
      trialStatus: 'RECRUITING',
      animalData: 'Complete protection at 25 mg/kg BID in cynomolgus macaque model',
      keyLimit: 'No completed Phase 2/3 RCT data in human Lassa fever as of 2026.',
    },
  },
  // Tier II — investigational with mechanism support
  {
    object_type: 'drug_candidate',
    object_id: 'molnupiravir-lasv',
    evidence_score: 0.58,
    current_state: 'proposed',
    metadata: {
      drugName: 'Molnupiravir (MK-4482)',
      mechanism: 'Broad-spectrum RNA mutagenesis — NHC-triphosphate drives lethal error accumulation in LASV genome',
      targets: ['L'],
      approvalStatus: 'EUA for SARS-CoV-2; investigational for LASV',
      tier: 'II',
      indication: 'Lassa fever — repurposing from COVID-19 EUA based on pan-arenavirus RNA polymerase inhibition',
      keyLimit: 'No Lassa fever clinical data. Teratogenicity concern limits use in pregnancy (>60% CFR in Lassa fever complicating pregnancy).',
    },
  },
  {
    object_type: 'drug_candidate',
    object_id: 'galidesivir-lasv',
    evidence_score: 0.52,
    current_state: 'proposed',
    metadata: {
      drugName: 'Galidesivir (BCX4430)',
      mechanism: 'Adenosine analogue — inhibits LASV L polymerase; broad-spectrum activity across arenaviruses, filoviruses, flaviviruses',
      targets: ['L'],
      approvalStatus: 'Investigational',
      tier: 'II',
      indication: 'Lassa fever — pan-arenavirus activity demonstrated in vitro and NHP models',
      trialNct: 'NCT03800173',
      trialStatus: 'COMPLETED',
      note: 'Phase 1 safety established (BARDA-funded). No completed efficacy trial for Lassa fever.',
    },
  },
  // Hypotheses — open scientific questions
  {
    object_type: 'hypothesis',
    object_id: 'gpc-lamp1-entry-inhibition',
    evidence_score: 0.74,
    current_state: 'proposed',
    metadata: {
      statement: 'LASV GPC mediates entry via the lysosomal receptor LAMP1. Monoclonal antibodies or small molecules targeting the GPC–LAMP1 interface could neutralise LASV without requiring cross-reactivity across the six LASV lineages — overcoming the key limitation of current GPC-directed approaches.',
      novelty: 0.78,
      plausibility: 0.72,
      type: 'drug_target_hypothesis',
      openQuestion: 'LAMP1 binding is strain-specific for LASV but not for other New World arenaviruses — structural basis of this specificity is not yet fully resolved.',
    },
  },
  {
    object_type: 'hypothesis',
    object_id: 'np-ifn-evasion-druggable',
    evidence_score: 0.68,
    current_state: 'proposed',
    metadata: {
      statement: 'LASV NP suppresses innate immune recognition by degrading dsRNA and blocking RIG-I/MDA5 activation. Small molecules disrupting NP exonuclease activity could restore interferon induction, converting a suppressed immune state to an activated antiviral response.',
      novelty: 0.72,
      plausibility: 0.68,
      type: 'immune_evasion_mechanism',
      openQuestion: 'NP exonuclease active site is structurally characterised — whether selective small-molecule inhibitors can be developed without off-target nuclease effects is unresolved.',
    },
  },
  {
    object_type: 'hypothesis',
    object_id: 'ribavirin-resistance-l-polymerase',
    evidence_score: 0.61,
    current_state: 'proposed',
    metadata: {
      statement: 'Ribavirin resistance in LASV may arise through mutations in the L polymerase that reduce ribavirin triphosphate binding affinity, analogous to resistance mechanisms documented in other RNA viruses (HCV, influenza). Surveillance for L polymerase resistance variants should be incorporated into NCDC genomic monitoring.',
      novelty: 0.65,
      plausibility: 0.70,
      type: 'resistance_mechanism',
      openQuestion: 'No systematic sequencing of LASV from ribavirin treatment failures has been published. Resistance emergence vs. treatment-naive exposure cannot be distinguished from current data.',
    },
  },
];

async function main() {
  const pool = getSharedPool();
  if (!pool) { console.error('No DATABASE_URL — aborting.'); process.exit(1); }

  // 1. Find the board
  const { rows: boardRows } = await pool.query(
    `SELECT board_id, disease_label FROM disease_boards WHERE disease_slug = $1`,
    [BOARD_SLUG]
  );
  if (!boardRows.length) {
    console.error(`Board '${BOARD_SLUG}' not found in DB. Run: node scripts/seed-lassa-board.js after npm run db:seed:disease-boards`);
    process.exit(1);
  }
  const { board_id: boardId, disease_label: label } = boardRows[0];
  log(`Board found: ${boardId} — ${label}`);

  // 2. Load current LassaAI forecast and upsert as a pinned evidence item
  let forecastItem = null;
  try {
    const forecastPath = path.join(__dirname, '../data/lassa/current-forecast.json');
    const raw = JSON.parse(await readFile(forecastPath, 'utf8'));
    // Top 5 states by probability
    const top5 = [...raw.forecasts]
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 5);
    forecastItem = {
      object_type: 'claim',
      object_id: 'lassaai-outbreak-forecast',
      evidence_score: 0.90,
      current_state: 'active',
      metadata: {
        label: 'LassaAI Outbreak Forecast',
        generatedAt: raw.generated_at,
        modelAuroc: 0.880,
        forecastHorizonWeeks: raw.forecast_horizon_weeks,
        asOfYear: raw.forecasts[0]?.as_of_year,
        asOfWeek: raw.forecasts[0]?.as_of_week,
        top5States: top5.map(s => ({ state: s.state, probability: s.probability, risk: s.risk })),
        summary: `Forecast from the LassaAI national outbreak model (XGBoost, out-of-time AUROC 0.880 vs 0.849 naive baseline — a modest ~0.03 gain, dry-season-driven). Elevated national transmission season: November through April.`,
        dataPoints: 313,
        note: 'Retrospective national model (2020–2025); prospective validation not yet started. See gailabai.com/lassa for the live dashboard.',
      },
    };
    log(`Forecast loaded: ${top5.length} states, as of week ${raw.forecasts[0]?.as_of_week}/${raw.forecasts[0]?.as_of_year}`);
  } catch (e) {
    log(`Warning: could not load forecast data — ${e.message}`);
  }

  const allItems = forecastItem ? [forecastItem, ...CURATED_ITEMS] : CURATED_ITEMS;

  // 3. Upsert all evidence items
  log(`\nUpserting ${allItems.length} evidence items (dry-run=${DRY_RUN})...`);
  for (const item of allItems) {
    const decayScore = item.evidence_score * 0.97;
    if (DRY_RUN) {
      log(`  [dry-run] ${item.object_type}/${item.object_id} score=${item.evidence_score}`);
      continue;
    }
    await pool.query(`
      INSERT INTO board_evidence_items
        (board_id, object_type, object_id, current_state, evidence_score, decay_score,
         months_stale, contradicting_evidence_count, metadata)
      VALUES ($1,$2,$3,$4,$5,$6,0,0,$7)
      ON CONFLICT (board_id, object_type, object_id) DO UPDATE SET
        current_state  = EXCLUDED.current_state,
        evidence_score = GREATEST(board_evidence_items.evidence_score, EXCLUDED.evidence_score),
        decay_score    = GREATEST(board_evidence_items.decay_score, EXCLUDED.decay_score),
        metadata       = board_evidence_items.metadata || EXCLUDED.metadata,
        last_refreshed_at = NOW()
    `, [boardId, item.object_type, item.object_id, item.current_state,
        item.evidence_score, decayScore, JSON.stringify(item.metadata)]);
    log(`  upserted ${item.object_type}/${item.object_id}`);
  }

  // 4. Summary
  if (!DRY_RUN) {
    const { rows: evRows } = await pool.query(
      `SELECT COUNT(*) AS cnt FROM board_evidence_items WHERE board_id = $1`,
      [boardId]
    );
    log(`\nBoard '${BOARD_SLUG}' now has ${evRows[0]?.cnt} evidence items`);

    // Verify stats endpoint shape
    const { rows: drugRows } = await pool.query(`
      SELECT metadata->>'drugName' AS drug, evidence_score, metadata->>'tier' AS tier
      FROM board_evidence_items
      WHERE board_id = $1 AND object_type = 'drug_candidate'
      ORDER BY evidence_score DESC
    `, [boardId]);
    log('\nDrug candidates:');
    drugRows.forEach(d => log(`  Tier ${d.tier || '?'} | ${d.drug} | score=${d.evidence_score}`));
  }

  await pool.end();
  log('\nDone.');
}

main().catch(err => { console.error('Fatal:', err.message); process.exit(1); });
