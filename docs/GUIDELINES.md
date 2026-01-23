# Documentation Guidelines

**CORE PRINCIPLE:** No docs unless absolutely necessary. Keep it lean.

---

## When to Create Docs

❌ **DON'T create docs for:**

- Completed tasks (update progress.md instead)
- Implementation details (add comments in code)
- Step-by-step walkthroughs (use code comments)
- Temporary status updates (update progress.md)
- Analysis of completed work (not needed)

✅ **CREATE docs ONLY for:**

1. **User-facing features** - How to use the system
2. **Architecture decisions** - Why the system works this way
3. **API specifications** - How external systems integrate
4. **Setup/Installation** - Getting the system running
5. **Roadmap/Strategy** - Long-term direction

---

## Active Documentation (Source of Truth)

These 6 files are THE documentation. Nothing else matters:

1. **PRD.md** - What we're building & why
2. **progress.md** - Current status (updated daily)
3. **QUICK_START.md** - How to run it
4. **SETUP.md** - How to install it
5. **RECOGNITION_ENGINE_DESIGN.md** - How it works
6. **INDEX.md** - Navigation (links to above + archived docs)

---

## All Docs Go Here

**Rule:** Every `.md` file MUST be in `/docs/` folder. Never leave docs in root.

---

## Documentation Location Rules

```
/docs/
├── PRD.md                        ← Update when requirements change
├── progress.md                   ← Update DAILY with status
├── QUICK_START.md               ← Update when setup changes
├── SETUP.md                     ← Update when dependencies change
├── RECOGNITION_ENGINE_DESIGN.md ← Reference (rarely changes)
├── INDEX.md                     ← Navigation hub
├── GUIDELINES.md                ← This file
└── ARCHIVE.md                   ← Links to all historical docs
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

**Active Docs:** 6 files  
**Archived Docs:** 1 reference page (ARCHIVE.md)  
**Total:** ~7 files in /docs/

**Before:** 40+ files spread across folders  
**After:** 7 files, flat structure, clear purpose

This is sustainable and scales.

---

## For Contributors

1. **Before writing a doc:** Ask "Is this in PRD, progress, or QUICK_START?"
2. **If yes:** Update that file instead
3. **If no:** Check with team lead
4. **When done:** Always put in `/docs/` folder

**The default answer is NO.** Assume we don't need it.
