# Documentation Guidelines

**CORE PRINCIPLE:** No docs unless absolutely necessary. Keep it lean.

---

## When to Create Docs

❌ **NEVER create docs for:**

- Completed tasks (update progress.md instead)
- Implementation details (add comments in code)
- Step-by-step walkthroughs (use code comments)
- Temporary status updates (update progress.md)
- One-off analysis or decisions (update progress.md)
- Code examples (only in SETUP.md if installation-critical)
- Per-feature status (all in progress.md)

✅ **UPDATE existing docs FIRST before creating new ones:**

Before creating a new doc, check:

1. Can this go in **progress.md**? (Status/decisions)
2. Can this go in **QUICK_START.md** or **TESTING.md**? (How to run, commands)
3. Can this go in **SETUP.md**? (Installation)
4. Can this go in **RECOGNITION_ENGINE_DESIGN.md**? (How it works)
5. Can this go in **PROJECT_OVERVIEW.md**? (What we're building)

**If yes to any of above:** Update that file. Don't create new doc.

✅ **CREATE NEW docs ONLY for:**

1. **Major architecture** - New subsystem (>100 lines)
2. **Setup/Installation** - Getting system running (only in SETUP.md)
3. **Roadmap/Strategy** - Long-term direction

---

## Active Documentation (Source of Truth)

**Tier 1 — Updated frequently (project record):**

1. **progress.md** ⭐ - Status & decisions (update daily/weekly)
2. **PRD.md** - Requirements & phase roadmap
3. **PROJECT_OVERVIEW.md** - Plain-language brief for new readers
4. **INDEX.md** - Navigation hub

**Tier 2 — Updated when architecture changes (reference):**

5. **RECOGNITION_ENGINE_DESIGN.md** - How recognition works
6. **SETUP.md** - Installation (code examples OK here only)
7. **QUICK_START.md** - How to run it (commands only, no explanation)
8. **TESTING.md** - All test commands
9. **STACK_UPDATES.md** - Engineering changelog

**Phase-specific (active while the phase is running):**

- **REFERENCE_BODY_SPEC.md** - Phase 3 reference body specification (remove after Phase 3)

---

## All Docs Go Here

**Rule:** Every `.md` file MUST be in `/docs/` folder. Never leave docs in root.

---

## Documentation Location Rules

```
/docs/
├── progress.md                   ← Update frequently
├── PRD.md                        ← Update when requirements change
├── PROJECT_OVERVIEW.md          ← Update at major milestones
├── INDEX.md                     ← Navigation hub
├── RECOGNITION_ENGINE_DESIGN.md ← Reference (update with architecture changes)
├── SETUP.md                     ← Update when dependencies change
├── QUICK_START.md               ← Update when setup changes (commands only)
├── TESTING.md                   ← All test commands
├── STACK_UPDATES.md             ← Engineering changelog
├── REFERENCE_BODY_SPEC.md       ← Phase 3 spec (remove after Phase 3)
└── GUIDELINES.md                ← This file
```

No subfolders. No migration/. No archive/ folder. Flat structure only.

---

## What to Do With Old Docs

1. Delete completed task docs (they're in git history if needed)
2. Move one-time analysis to ARCHIVE.md as reference links
3. If doc is 6+ months old and not referenced → delete it
4. Keep only what users/developers need TODAY

---

## Progress Tracking

**progress.md** replaces all status update docs. Format:

```markdown
# Progress Log

## Today (Jan 23, 2026)

- ✅ Phase 3 complete (4 features)
- 🔧 Organized docs (80% reduction)
- 📊 All tests passing (6/6)

## This Week

- [ ] Multi-language support

## Blockers

None
```

Update daily. That's the single source of truth for status.

---

## Code Comments > Documentation

For implementation details, prefer code comments:

```python
# Use docstrings
def temporal_filter(concept, score):
    """Apply 5-frame confirmation hysteresis.

    Requires 5 consecutive frames above threshold.
    Returns confirmed concept or None.
    """
```

Not a 5-page doc describing this.

---

## Code in Documentation

**RULE: Minimize code in docs. Code rots.**

### ❌ DON'T add code examples to docs UNLESS:

- It's in SETUP.md (installation-critical scripts)
- It's in QUICK_START.md (copy-paste to get started)
- It's reference implementation (mark clearly as reference)

### Why?

- Code changes → docs become wrong
- Developers update code but forget docs
- Then docs mislead future developers

### Solution

Use code comments instead:

```python
# ✅ GOOD: Comment in code
extractor = SignatureExtractor(delete_after=True)  # Auto-cleanup after extraction

# ❌ BAD: Doc with code example that gets stale
# "To extract: extractor = SignatureExtractor(delete_after=True)"
# (6 months later, someone changes the API and docs break)
```

---

## Archival

Old docs go to ARCHIVE.md as links:

```markdown
# Archived Documentation

These docs are historical reference only.

- [Migration Complete Summary](../migration/MIGRATION_COMPLETE.md)
- [Phase 3 Step 1 Details](../phase3/step1.md)
- [UX Enhancement Analysis](../analysis/ux_plan.md)
```

Users know where to find history, but it's not cluttering active docs.

---

## Summary

**Active Docs:** 9 permanent + 1 phase-specific
**Deleted (Feb 2026):** FEATURES.md, CODE_AUDIT.md, TECH_LEAD_ASSESSMENT.md, color_accessibility.md, BODY_MODEL_INSIGHTS.md
**Total:** 10 files in /docs/ (+ 2 in /docs/research_insights/)

This is sustainable and scales.

---

## For Contributors

1. **Before writing a doc:** Ask "Is this in PRD, progress, or QUICK_START?"
2. **If yes:** Update that file instead
3. **If no:** Check with team lead
4. **When done:** Always put in `/docs/` folder

**The default answer is NO.** Assume we don't need it.

---

## File Organization Rules

**IMPORTANT:** Moving files breaks imports. Think carefully before organizing.

### Current Structure (Leave As-Is)

```
/root
├── recognition_engine.py              ← Core engine (keep in root)
├── recognition_engine_ui.py           ← Core UI (keep in root)
├── translation_map.json               ← Core data (keep in root)
├── concept_map.json                   ← Core data (keep in root)
├── requirements.txt                   ← Setup (keep in root)
├── pyproject.toml                     ← Setup (keep in root)
├── activate.sh                        ← Setup (keep in root)
│
├── /docs/                             ← ALL documentation
├── /assets/                           ← Data files (embeddings, videos)
├── /scripts/                          ← Tests & validation
└── /utils/                            ← Helper modules
```

### When to Create New Folders

**RULE: Minimum 3 related files per folder. No single-file folders.**

✓ **DO create folders when:**

- You have 3+ files that belong together
- Files serve a single, clear purpose
- Keeping them in root would clutter

✗ **DON'T create folders when:**

- You only have 1-2 files
- Files are frequently imported from other modules (breaks imports)
- They're core to the system (keep in root)

### If You Create a New Folder

1. **Update all imports** - Every file that `import` or `from` these files
2. **Update all documentation links** - Check docs for file references
3. **Create **init**.py** - If it's a Python package
4. **Update README** - Document the new structure
5. **Test thoroughly** - Run validation suite

**Cost is high. Only do it if structure is really broken.**

### Examples

✗ DON'T do this (too few files):

```
/engine/
  └── recognition_engine.py          ← Only 1 file, breaks imports
```

✓ DO do this (clearly related, 3+ files):

```
/processors/
  ├── generate_embeddings.py
  ├── extract_signatures.py
  ├── extract_wlasl_videos.py
  ├── setup_dataset.py
  └── __init__.py
```

**Current state:** Root is fine. Don't reorganize.
