# Documentation Index

## Essential Docs Only

| Doc | Purpose | Audience |
|-----|---------|----------|
| [QUICK_START.md](QUICK_START.md) | Get running in 5 min | Everyone |
| [progress.md](progress.md) | Status & next steps | PM, Dev Lead |
| [EXTRACTION_PIPELINE.md](EXTRACTION_PIPELINE.md) | How to extract signatures | Developer |
| [SIGNATURE_STRATEGY.md](SIGNATURE_STRATEGY.md) | Decision framework for data | Developer |
| [RECOGNITION_ENGINE_DESIGN.md](RECOGNITION_ENGINE_DESIGN.md) | System architecture | Developer |
| [SETUP.md](SETUP.md) | Installation | DevOps |

## For Specific Tasks

### Extracting Reference Videos
1. Read: [EXTRACTION_PIPELINE.md](EXTRACTION_PIPELINE.md)
2. **Key:** Always use `--delete` flag
3. Test: `python3 test_recognition_quality.py`
4. Decide: Use [SIGNATURE_STRATEGY.md](SIGNATURE_STRATEGY.md) framework

### Testing Recognition
```bash
python3 test_recognition_quality.py    # All word metrics
python3 skeleton_debugger.py            # Visual inspection
```

### Running the Engine
```bash
python3 recognition_engine.py           # Live recognition
python3 recognition_engine_ui.py        # UI version
```

---

## Documentation Strategy

**Old approach:** One doc per decision/word  
**New approach:** Systematic, reusable tools + consolidated docs

### What Changed

- ❌ Removed: test_go_impact.py, test_where_impact.py, analyze_go.py (ad-hoc)
- ❌ Removed: GO_ANALYSIS.md, GO_DECISION.md (per-word decision docs)
- ✅ Added: test_recognition_quality.py (unified tool)
- ✅ Added: SIGNATURE_STRATEGY.md (consolidated framework)
- ✅ Updated: EXTRACTION_PIPELINE.md (emphasize --delete, cleanup)

### Principles

1. **One tool per task** - Not multiple one-off scripts
2. **Systematic testing** - Unified metrics, not per-word tests
3. **Reusable patterns** - Documented in strategy doc
4. **Automatic cleanup** - --delete flag in extraction pipeline

---

**Start here:** [QUICK_START.md](QUICK_START.md)  
**Need to extract?** [EXTRACTION_PIPELINE.md](EXTRACTION_PIPELINE.md)  
**Making data decisions?** [SIGNATURE_STRATEGY.md](SIGNATURE_STRATEGY.md)
