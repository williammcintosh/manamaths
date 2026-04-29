#!/usr/bin/env python3
"""
Batch update the Mana Maths LO expectations tracker.

Usage:
  python3 update-lo-status.py --set "YR9_T1_LO1=meets_expectation" "YR9_T1_LO2=needs_notes_and_solutions"
  python3 update-lo-status.py --get "YR9_T1_LO1,YR9_T1_LO2,YR9_T1_LO3"
  python3 update-lo-status.py --filter needs_notes_and_solutions
  python3 update-lo-status.py --summary
  python3 update-lo-status.py --sync-from-fs   # Scan filesystem + notes + solutions trackers to auto-detect status
"""

import json, os, sys, datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_PATH = os.path.join(SCRIPT_DIR, '../data/lo-meets-expectations.json')
LO_TRACKER_PATH = os.path.join(SCRIPT_DIR, '../data/lo-tracker.json')
NOTES_TRACKER_PATH = os.path.join(SCRIPT_DIR, '../../../../manamaths-notes/OPERATIONS/data/notes-tracker.json')
MANAMATHS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../..'))
SOLUTIONS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../../../../manamaths-solutions'))

VALID_STATUSES = [
    'meets_expectation',
    'needs_notes',
    'needs_solutions',
    'needs_notes_and_solutions',
    'needs_everything',
    'needs_te_reo',
    'needs_tasks',
]

def load_tracker():
    if os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH) as f:
            return json.load(f)
    return None

def load_lo_tracker():
    with open(LO_TRACKER_PATH) as f:
        return json.load(f)

def save_tracker(data):
    os.makedirs(os.path.dirname(TRACKER_PATH), exist_ok=True)
    with open(TRACKER_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {TRACKER_PATH}")

def build_from_lo_tracker():
    """Build a fresh expectations tracker from the main LO tracker + filesystem scan."""
    lo_data = load_lo_tracker()
    
    notes_data = None
    if os.path.exists(NOTES_TRACKER_PATH):
        with open(NOTES_TRACKER_PATH) as f:
            notes_data = json.load(f)
    
    los = {}
    for lo in lo_data['learningObjectives']:
        oid = lo['objectiveId']
        slug = lo['slug']
        title = lo.get('canonicalDisplayTitle', lo.get('canonicalTitle', ''))
        topic = lo.get('canonicalTopicId', '')
        
        # Check filesystem state
        obj_dir = os.path.join(MANAMATHS_ROOT, 'OBJECTIVES', slug)
        te_reo_pdf = os.path.join(MANAMATHS_ROOT, 'SITE', 'te-reo-pdfs', f'{slug}.pdf')
        notes_pdf = os.path.join(MANAMATHS_ROOT, 'SITE', 'notes-pdfs', f'{slug}.pdf')
        sol_dir = os.path.join(MANAMATHS_ROOT, 'SITE', 'solutions-pdfs', slug)
        
        has_tasks = all(
            os.path.exists(os.path.join(obj_dir, f'{f}-questions.pdf'))
            for f in ['foundation', 'proficient', 'excellence']
        ) if os.path.isdir(obj_dir) else False
        
        has_te_reo = os.path.exists(te_reo_pdf)
        has_notes = os.path.exists(notes_pdf)
        has_solutions = all(
            os.path.exists(os.path.join(sol_dir, f'{f}-answers.pdf'))
            for f in ['foundation', 'proficient', 'excellence']
        ) if os.path.isdir(sol_dir) else False
        
        # Determine status
        if has_tasks and has_te_reo and has_notes and has_solutions:
            status = 'meets_expectation'
        elif has_tasks and has_te_reo and has_notes:
            status = 'needs_solutions'
        elif has_tasks and has_te_reo:
            status = 'needs_notes_and_solutions'
        elif has_tasks and not has_te_reo:
            status = 'needs_te_reo'
        elif not has_tasks:
            status = 'needs_tasks'
        else:
            status = 'needs_everything'
        
        los[oid] = {
            'objectiveId': oid,
            'canonicalTopicId': topic,
            'status': status,
            'slug': slug,
            'displayTitle': title,
            'lastUpdated': datetime.date.today().isoformat(),
        }
    
    # Build summary
    counts = {s: 0 for s in VALID_STATUSES}
    for lo in los.values():
        s = lo['status']
        counts[s] = counts.get(s, 0) + 1
    
    result = {
        'schema': 'manamaths/meets-expectations.v1',
        'generatedAt': datetime.date.today().isoformat(),
        'summary': {
            'total': len(los),
            'meetsExpectation': counts.get('meets_expectation', 0),
            'needsNotes': counts.get('needs_notes', 0),
            'needsSolutions': counts.get('needs_solutions', 0),
            'needsNotesAndSolutions': counts.get('needs_notes_and_solutions', 0),
            'needsEverything': counts.get('needs_everything', 0),
            'needsTeReo': counts.get('needs_te_reo', 0),
            'needsTasks': counts.get('needs_tasks', 0),
        },
        'learningObjectives': sorted(los.values(), key=lambda x: x['objectiveId']),
    }
    
    return result

def set_status(status_updates):
    """Update status for up to 5 LOs."""
    if len(status_updates) > 5:
        print("Error: maximum 5 updates at a time")
        return False
    
    data = load_tracker()
    if not data:
        data = build_from_lo_tracker()
    
    updates = {}
    for entry in status_updates:
        if '=' not in entry:
            print(f"Error: malformed '{entry}'. Use OID=status format.")
            return False
        oid, status = entry.split('=', 1)
        if status not in VALID_STATUSES:
            print(f"Error: invalid status '{status}'. Valid: {', '.join(VALID_STATUSES)}")
            return False
        updates[oid] = status
    
    updated = 0
    found_ids = {lo['objectiveId'] for lo in data['learningObjectives']}
    for oid, status in updates.items():
        if oid not in found_ids:
            print(f"Warning: {oid} not found in tracker. Skipping.")
            continue
        for lo in data['learningObjectives']:
            if lo['objectiveId'] == oid:
                lo['status'] = status
                lo['lastUpdated'] = datetime.date.today().isoformat()
                updated += 1
                print(f"  ✓ {oid} → {status}")
                break
    
    # Rebuild summary
    counts = {s: 0 for s in VALID_STATUSES}
    for lo in data['learningObjectives']:
        s = lo['status']
        counts[s] = counts.get(s, 0) + 1
    data['summary'] = {
        'total': len(data['learningObjectives']),
        'meetsExpectation': counts.get('meets_expectation', 0),
        'needsNotes': counts.get('needs_notes', 0),
        'needsSolutions': counts.get('needs_solutions', 0),
        'needsNotesAndSolutions': counts.get('needs_notes_and_solutions', 0),
        'needsEverything': counts.get('needs_everything', 0),
        'needsTeReo': counts.get('needs_te_reo', 0),
        'needsTasks': counts.get('needs_tasks', 0),
    }
    data['generatedAt'] = datetime.date.today().isoformat()
    
    save_tracker(data)
    print(f"\nUpdated {updated}/{len(status_updates)} objectives.")
    print_summary(data['summary'])
    return True

def get_status(oids_str):
    """Display status for one or more comma-separated OIDs."""
    oids = [o.strip() for o in oids_str.split(',')]
    data = load_tracker()
    if not data:
        data = build_from_lo_tracker()
    
    lookup = {lo['objectiveId']: lo for lo in data['learningObjectives']}
    for oid in oids:
        lo = lookup.get(oid)
        if lo:
            print(f"  {oid}: {lo['status']} — {lo['displayTitle']} (slug: {lo['slug']})")
        else:
            print(f"  {oid}: NOT FOUND")

def filter_status(status):
    """List all LOs with a given status."""
    data = load_tracker()
    if not data:
        data = build_from_lo_tracker()
    
    matches = [lo for lo in data['learningObjectives'] if lo['status'] == status]
    print(f"LOs with status '{status}': {len(matches)}")
    for lo in matches:
        print(f"  {lo['objectiveId']} — {lo['displayTitle']}")

def print_summary(summary):
    print(f"  Total: {summary['total']}")
    print(f"  Meets expectation: {summary['meetsExpectation']}")
    print(f"  Needs notes: {summary['needsNotes']}")
    print(f"  Needs solutions: {summary['needsSolutions']}")
    print(f"  Needs notes + solutions: {summary['needsNotesAndSolutions']}")
    print(f"  Needs everything: {summary['needsEverything']}")
    print(f"  Needs te reo: {summary['needsTeReo']}")
    print(f"  Needs tasks: {summary['needsTasks']}")

def next_batch(count=5, status_filter='needs_notes_and_solutions'):
    """Print the next N LOs needing work in a format ready for a sub-agent task."""
    data = load_tracker()
    if not data:
        data = build_from_lo_tracker()
    
    matches = [lo for lo in data['learningObjectives'] if lo['status'] == status_filter]
    batch = matches[:count]
    
    if not batch:
        print(f"No LOs with status '{status_filter}'")
        return
    
    print(f"Next {len(batch)} LOs (status: {status_filter}):\n")
    for lo in batch:
        print(f"  {lo['objectiveId']}: {lo['displayTitle']} (slug: {lo['slug']})")
    
    print(f"\n--- Build task for these {len(batch)} LOs ---\n")
    print("Create notes + solutions for the following LOs:")
    for lo in batch:
        print(f"- **{lo['objectiveId']}** — {lo['displayTitle']} — slug: `{lo['slug']}`")
    
    print("""
For each LO:
1. Create notes in `manamaths-notes/OBJECTIVES/<slug>/main.tex` (copy T1 LO1's pattern)
2. Create solutions in `manamaths-solutions/OBJECTIVES/<slug>/` (copy from task questions)
3. Build PDFs with `tectonic`
4. Copy PDFs to `manamaths/SITE/notes-pdfs/` and `manamaths/SITE/solutions-pdfs/`
5. Generate previews: `bash manamaths/OPERATIONS/scripts/generate-previews.sh <slug>`
6. Regenerate site page: `python3 manamaths/OPERATIONS/scripts/generate_web_html.py --slug <slug>`
7. Update trackers and push

Reference: manamaths/REFERENCE_LO.md
""")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == '--set':
        if len(sys.argv) < 3:
            print("Usage: --set OID=status [OID=status ...]")
            sys.exit(1)
        set_status(sys.argv[2:])
    elif cmd == '--get':
        if len(sys.argv) < 3:
            print("Usage: --get OID[,OID,...]")
            sys.exit(1)
        get_status(sys.argv[2])
    elif cmd == '--filter':
        if len(sys.argv) < 3:
            print("Usage: --filter status")
            sys.exit(1)
        filter_status(sys.argv[2])
    elif cmd == '--summary':
        data = load_tracker()
        if not data:
            data = build_from_lo_tracker()
        print_summary(data['summary'])
    elif cmd == '--sync-from-fs':
        data = build_from_lo_tracker()
        save_tracker(data)
        print_summary(data['summary'])
    elif cmd == '--next-batch':
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        status_filter = sys.argv[3] if len(sys.argv) > 3 else 'needs_notes_and_solutions'
        next_batch(count, status_filter)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
