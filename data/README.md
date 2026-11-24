# ECE-009 – Fibre Installation Work-Order Scheduling Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E031.

Input pack for a fibre field-operations scheduler: 6 zones, 10 technicians and 45 work orders requested for 2026-10-10 … 2026-10-14, scheduled by four SCHEDULE commands (12, 13, 14 and 15 October; the 15th is a holiday with everyone on leave).

Pack conventions where the brief is silent: on SCHEDULE|D the candidates are all not-yet-assigned orders with requested_date ≤ D (earlier dates are OVERDUE). Slots are S1 < S2 < S3 < S4 and are always searched from S1 upward. For an adjacent-zone order the travel slot is the slot immediately AFTER the job slots (job then travel), so an adjacent REPAIR needs 2 consecutive free slots and an adjacent NEW_INSTALL needs 3. Lists inside a cell (skills, adjacent zones, leave dates) are separated by `;` and sorted. A NEW_INSTALL with 2 or more bumps is ordered inside the REPAIR group by its requested date, then id.

## Files
| File | What it holds | Rows |
|---|---|---|
| zones.csv | Service zones and their adjacency | 6 |
| technicians.csv | Technicians with home zone, skills and leave dates | 10 |
| work_orders.csv | Work orders to be scheduled | 46 |
| commands.txt | Load commands and four daily SCHEDULE runs | 7 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### zones.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| zone_id | string | Zn | Z1 … Z6 | Primary key |
| zone_name | string | - |  |  |
| adjacent_zones | string | ids joined by ; |  | Symmetric |

### technicians.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| technician_id | string | TECH-nn | TECH-01 … TECH-10 | Primary key; first-fit scans in this order |
| name | string | - |  |  |
| home_zone | string | Zn | must exist |  |
| skills | string | skills joined by ; | ONT_CONFIG, OTDR, ROUTER_CONFIG, SPLICING |  |
| leave_dates | string | dates joined by ; |  | Zero slots on those dates |

### work_orders.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| order_id | string | WO-nnn | unique except one planted duplicate | Tie-breaker |
| order_type | string | - | NEW_INSTALL, REPAIR, ENTERPRISE | 2 / 1 / 3 slots |
| zone_id | string | Zn | must exist |  |
| required_skills | string | skills joined by ; | may include a skill nobody has |  |
| requested_date | date | YYYY-MM-DD | 2026-10-10 … 2026-10-14 |  |
| priority_bumps | integer | count | 0–2 | Starting value; the engine increments on carry-forward |
| customer_name | string | - |  |  |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_ZONES / LOAD_TECHNICIANS / LOAD_WORK_ORDERS | file | Load the named CSV |
| SCHEDULE | YYYY-MM-DD | Assign all pending orders with requested_date ≤ date; print the sheet and the unassigned list; bump leftovers |

`job_slots` is like S1;S2; `travel_slot` is a slot id or NONE. `reason` is NO_SKILL, NO_TECH_IN_RANGE (no technician in home/adjacent zone with the skills), NO_SLOT (eligible technicians exist but none has enough consecutive free slots) or ALL_ON_LEAVE.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Technician with slots S1 and S4 free (not consecutive, cannot take NEW_INSTALL)** — Not reproducible under strict first-fit from S1 (slots always fill from S1 upward), so the nearest real case is planted: on 2026-10-12 TECH-07 takes ENTERPRISE order WO-002 (work_orders.csv line 3, its home zone Z4) in S1–S3, leaving only S4 free, so any NEW_INSTALL (2 consecutive slots) must be refused for TECH-07 that day; WO-001 (line 2) goes to TECH-05 with a travel slot and fills S1–S4. Still write a unit test for the S1+S4 pattern (free slots {S1, S4}, NEW_INSTALL → not placeable).
- **Order needing a skill no technician has (unassigned every day, reason NO_SKILL)** — WO-007 (line 8) needs FIBRE_BLOWING;OTDR and WO-031 (line 32) needs FIBRE_BLOWING;SPLICING — no technician holds FIBRE_BLOWING, so both are unassigned on every SCHEDULE day with reason NO_SKILL (and keep getting bumps).
- **Adjacent-zone REPAIR using the last 2 slots (1 job + 1 travel)** — 2026-10-12: WO-003 (line 4, NEW_INSTALL with 2 bumps → REPAIR priority, requested 2026-10-10, Z1) is the first REPAIR-priority order and takes TECH-01 S1–S2. WO-005 (line 6, REPAIR in Z2, adjacent to TECH-01's home Z1) is next for TECH-01 and needs job + travel = 2 consecutive slots → S3–S4, filling TECH-01 completely.
- **Two orders with the same type and date (tie broken by id)** — WO-005 and WO-006 (lines 6, 7) are both REPAIR, Z2, requested 2026-10-11: WO-005 goes first (lower id) and gets TECH-01; WO-006 is placed on the next eligible technician by id.
- **All technicians on leave on a given day** — Every technician has 2026-10-15 in leave_dates; SCHEDULE|2026-10-15 (commands.txt line 7) must assign nothing, list every pending order with reason ALL_ON_LEAVE and bump each once.

Extra traps (realistic things your validation should catch):

- **Single technician on leave** — TECH-04 is also on leave on 2026-10-13 (zero slots that day only).
- **OVERDUE flag** — WO-003 and WO-004 (lines 4, 5) were requested for 2026-10-10, before the first SCHEDULE day → scheduled but flagged OVERDUE; any order carried past its requested date is likewise OVERDUE.
- **Priority ageing** — A NEW_INSTALL left unassigned on 2026-10-12 and 2026-10-13 reaches 2 bumps and competes in the REPAIR group on 2026-10-14; WO-003 starts there already.
- **Duplicate order id** — work_orders.csv line 47 repeats WO-020 (first at line 21) → reject the second row with an error line.
- **Non-adjacent zone** — Zones form a ring Z1–Z2–Z3–Z4–Z5–Z6–Z1; a technician may only take orders in the home zone or one of its two neighbours, so e.g. TECH-01 (Z1) is skipped for WO-004 in Z5.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### assignments.csv
One row per placed order, ordered by schedule_date, technician_id, first slot.

Columns in order: `schedule_date`, `technician_id`, `order_id`, `order_type`, `zone_id`, `job_slots`, `travel_slot`, `overdue`

### unassigned.csv
One row per pending order not placed that day.

Columns in order: `schedule_date`, `order_id`, `order_type`, `zone_id`, `reason`, `priority_bumps_after`

### errors.csv
Rejected input rows.

Columns in order: `file`, `line_no`, `reason`
