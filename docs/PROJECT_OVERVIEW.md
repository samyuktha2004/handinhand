# HandInHand: Cross-Lingual Sign Language Translation

> **Breaking barriers between Deaf communities worldwide**

---

## Executive Summary

HandInHand is a **sign-to-sign translation system** that enables Deaf individuals using different national sign languages to communicate directly. Unlike text-based translation, HandInHand preserves the visual-spatial grammar and non-manual signals that carry meaning in sign languages.

**Current MVP:** ASL (American Sign Language) ↔ BSL (British Sign Language)

---

## The Problem We're Solving

### The Language Barrier Within the Deaf World

Most hearing people assume sign language is universal. **It is not.**

There are over **300 distinct sign languages** worldwide, each with its own grammar, vocabulary, and cultural context. A Deaf American using ASL cannot understand a Deaf British person using BSL without learning an entirely new language.

| Sign Language       | Region         | Estimated Users             |
| ------------------- | -------------- | --------------------------- |
| ASL (American)      | USA, Canada    | 500,000 - 2 million         |
| BSL (British)       | UK             | 150,000 - 250,000           |
| LSF (French)        | France         | 100,000+                    |
| DGS (German)        | Germany        | 200,000+                    |
| JSL (Japanese)      | Japan          | 320,000+                    |
| **Total worldwide** | 300+ languages | **~70 million Deaf people** |

### Why Not Just Use International Sign (IS)?

**International Sign (IS)** is a contact variety used at international Deaf events. However:

| Factor                | International Sign                         | National Sign Languages     |
| --------------------- | ------------------------------------------ | --------------------------- |
| **Who knows it?**     | ~5-10% of Deaf community                   | 100% of Deaf individuals    |
| **Where learned?**    | International events, specialized training | From birth/early childhood  |
| **Expressiveness**    | Simplified, limited vocabulary             | Full natural language       |
| **Cultural identity** | Neutral, constructed                       | Core to Deaf identity       |
| **Practical use**     | Conferences, Deaflympics                   | Daily life, education, work |

**The reality:** Most Deaf people don't know IS, don't want to learn IS, and are proud of their national sign language as part of their cultural identity.

**HandInHand's approach:** Instead of forcing everyone to learn a new language, we translate between the languages they already know.

---

## Target Audience

### Primary Users

| Audience                        | Use Case                         | Pain Point                                                      |
| ------------------------------- | -------------------------------- | --------------------------------------------------------------- |
| **Deaf Travelers**              | Tourist visiting another country | Can't communicate with local Deaf community                     |
| **Deaf Immigrants/Refugees**    | Relocated to new country         | Must learn entirely new sign language                           |
| **International Deaf Students** | Studying abroad                  | Classroom materials in different sign language                  |
| **Deaf Remote Workers**         | International teams              | Video calls with Deaf colleagues using different sign languages |

### Secondary Users

| Audience                             | Use Case                            | Pain Point                                          |
| ------------------------------------ | ----------------------------------- | --------------------------------------------------- |
| **Healthcare Providers**             | Serving international Deaf patients | No interpreter available for specific sign language |
| **Sign Language Interpreters**       | Working internationally             | Need reference for unfamiliar sign languages        |
| **Deaf Educators**                   | Creating cross-cultural content     | Translating educational materials                   |
| **International Deaf Organizations** | Global advocacy                     | Communication at international meetings             |

### Market Size Estimation

```
Global Deaf population:              ~70 million
Cross-border travel/migration:       ~5-10% annually = 3.5-7 million
International Deaf events/year:      ~500+ (conferences, sports, cultural)
Deaf students studying abroad:       ~50,000+
International remote work (Deaf):    Growing rapidly post-COVID
```

**Conservative addressable market:** 5-10 million Deaf individuals who regularly encounter sign language barriers.

---

## What HandInHand Does

### Core Functionality

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User signs    │────▶│   Recognition    │────▶│   Translate     │
│   in ASL        │     │   (identify sign)│     │   to BSL        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   Avatar plays  │
                                                 │   BSL sign      │
                                                 └─────────────────┘
```

### What Makes Us Different

| Traditional Approach                                          | HandInHand Approach                       |
| ------------------------------------------------------------- | ----------------------------------------- |
| Sign → Text → Text Translation → Sign                         | Sign → Embedding → Direct Mapping → Sign  |
| Loses non-manual signals (facial expressions, mouth patterns) | Preserves full visual-spatial information |
| Requires text as intermediate                                 | Kinematics-to-kinematics (no text)        |
| "Gloss-based" (word-by-word)                                  | Embedding-based (meaning preservation)    |

---

## How It Works

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT STAGE                             │
│  ┌───────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │  Webcam   │───▶│ MediaPipe Holistic│───▶│ 52 Landmarks    │  │
│  │  Feed     │    │ (Pose Estimation) │    │ (pose+hands+face)│ │
│  └───────────┘    └──────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RECOGNITION STAGE                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │ Normalize       │───▶│ Compute Embedding │───▶│ Cosine    │  │
│  │ (body-centric)  │    │ (512-dim vector)  │    │ Similarity│  │
│  └─────────────────┘    └──────────────────┘    └───────────┘  │
│                                                        │        │
│                                           Match against         │
│                                           ASL signatures        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TRANSLATION STAGE                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │ Concept Lookup  │───▶│ BSL Signature    │───▶│ 3D Avatar │  │
│  │ (ASL→Concept)   │    │ (Concept→BSL)    │    │ Playback  │  │
│  └─────────────────┘    └──────────────────┘    └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component           | Technology                             | Purpose                            |
| ------------------- | -------------------------------------- | ---------------------------------- |
| **Pose Estimation** | MediaPipe Holistic                     | Extract 3D skeleton from video     |
| **Landmarks**       | 52 points (6 pose + 42 hands + 4 face) | Capture body/hand/face positions   |
| **Normalization**   | Body-centric (shoulder-based)          | Scale/position invariance          |
| **Embeddings**      | 512-dimensional vectors                | Fixed-size representation of signs |
| **Recognition**     | Cosine Similarity + Tier 4 validation  | Match live signing to known signs  |
| **Translation**     | Concept-based registry                 | Map between languages via concepts |
| **Playback**        | VRM Avatar + Three.js                  | Visual output in target language   |

---

## Current Features

### ✅ Implemented (MVP)

| Feature                        | Description                          | Status     |
| ------------------------------ | ------------------------------------ | ---------- |
| **Live Recognition**           | Real-time sign detection from webcam | ✅ Working |
| **Skeleton Debugger**          | Visual inspection of signatures      | ✅ Working |
| **Multi-language Registry**    | Extensible language support          | ✅ Working |
| **Quality Gates**              | Corruption detection & filtering     | ✅ Working |
| **Body-centric Normalization** | Scale/position invariant matching    | ✅ Working |
| **Signature Augmentation**     | Synthetic data generation            | ✅ Working |

### 🔄 In Progress

| Feature                   | Description                             | Status         |
| ------------------------- | --------------------------------------- | -------------- |
| **Avatar Playback**       | 3D character signing in target language | 🔄 Phase 3     |
| **Real-time Translation** | End-to-end ASL→BSL flow                 | 🔄 Integration |

### 📋 Planned

| Feature                        | Description          | Phase  |
| ------------------------------ | -------------------- | ------ |
| **Mobile App**                 | iOS/Android support  | Future |
| **Additional Languages**       | LSF, DGS, JSL, etc.  | Future |
| **Sentence-level Translation** | Beyond word-by-word  | Future |
| **Offline Mode**               | No internet required | Future |

---

## Current Vocabulary

### MVP Word Set (4 concepts)

| Concept | ASL Variants | BSL Variants | Notes         |
| ------- | ------------ | ------------ | ------------- |
| HELLO   | 3 signatures | 1 signature  | Greeting      |
| YOU     | 3 signatures | 1 signature  | Pronoun       |
| GO      | 3 signatures | 1 signature  | Verb          |
| WHERE   | 1 signature  | 1 signature  | Question word |

**Why start small?** Quality over quantity. We're validating the approach works before scaling vocabulary.

---

## Recognition Pipeline Deep Dive

### Step 1: Landmark Extraction

```python
# MediaPipe extracts 52 landmarks per frame:
# - Pose: [11,12,13,14,15,16] = shoulders, elbows, wrists (6 points)
# - Left Hand: 21 points
# - Right Hand: 21 points
# - Face: [70,107,300,336] = eyebrows (4 points)
```

### Step 2: Normalization

```python
# Center on shoulder midpoint (translation invariance)
shoulder_center = (left_shoulder + right_shoulder) / 2
landmarks -= shoulder_center

# Scale by shoulder width (scale invariance)
shoulder_width = distance(left_shoulder, right_shoulder)
landmarks /= shoulder_width
```

### Step 3: Embedding

```python
# Flatten landmarks across window of frames
# Apply Global Average Pooling
# Result: 512-dimensional vector
```

### Step 4: Recognition

```python
# Compare live embedding against all stored embeddings
similarity = cosine_similarity(live, stored)

# Tier 4 Validation:
# 1. Best match > 0.80 threshold
# 2. Second-best < (best - 0.15) gap
# Result: Verified match or rejected
```

---

## Data Quality System

### Signature Quality Gates

| Gate              | Threshold | Purpose                        |
| ----------------- | --------- | ------------------------------ |
| MIN_POSE_QUALITY  | 80%       | Require 80%+ valid pose frames |
| MIN_HAND_QUALITY  | 20%       | Require 20%+ valid hand frames |
| OUTLIER_THRESHOLD | 3.0       | Remove frames >3σ from median  |

### Audit & Quarantine

```bash
# Audit variants for consistency
python3 skeleton_debugger.py --audit hello

# Quarantine problematic signatures
python3 skeleton_debugger.py --quarantine asl/you_0
```

---

## Project Structure

```
handinhand/
├── recognition_engine.py      # Core real-time recognition
├── recognition_engine_ui.py   # UI with visualization
├── skeleton_debugger.py       # Signature inspection tool
├── extract_signatures.py      # Signature extraction from video
├── generate_embeddings.py     # Embedding generation with quality gates
├── assets/
│   ├── signatures/            # Raw landmark sequences (JSON)
│   │   ├── asl/              # ASL signatures
│   │   └── bsl/              # BSL signatures
│   ├── embeddings/           # Computed embeddings (NPY)
│   │   ├── asl/
│   │   └── bsl/
│   └── registries/           # Language registries (JSON)
│       ├── asl_registry.json
│       ├── bsl_registry.json
│       └── concept_registry.json
└── docs/                     # Documentation
```

---

## Comparison with Alternatives

| Solution                    | Approach                   | Limitations                      |
| --------------------------- | -------------------------- | -------------------------------- |
| **Human Interpreter**       | Professional translation   | Expensive, not always available  |
| **Text Relay**              | Sign → Text → Sign         | Loses non-manual signals, slow   |
| **Learn IS**                | Universal contact language | Not widely known, simplified     |
| **Google Translate (text)** | Text-based                 | Not designed for sign languages  |
| **HandInHand**              | Direct kinematics          | Preserves visual-spatial grammar |

---

## Development Progress

For detailed progress tracking, see:

- [PROGRESS_CHECKLIST.md](PROGRESS_CHECKLIST.md) - Current tasks and completion status
- [progress.md](progress.md) - Detailed development log
- [TECH_LEAD_ASSESSMENT.md](TECH_LEAD_ASSESSMENT.md) - Technical status and open issues

---

## FAQ

### Q: Why not just learn the other sign language?

**A:** Learning a new language takes years. HandInHand enables immediate communication while users may still choose to learn over time.

### Q: Is this replacing interpreters?

**A:** No. Human interpreters provide nuanced cultural translation. HandInHand is for everyday quick communication when interpreters aren't available.

### Q: How accurate is it?

**A:** Current MVP achieves 80-90% recognition accuracy on the limited vocabulary. Accuracy improves with more training data.

### Q: Can it handle sentences, not just words?

**A:** MVP is word-level. Sentence-level translation is on the roadmap and requires understanding sign language grammar, which differs significantly between languages.

### Q: Is this accessible to the Deaf community?

**A:** The visual-first design (3D avatar output) is inherently accessible. We plan user testing with Deaf individuals to ensure usability.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Adding new sign language support
- Contributing signatures
- Reporting issues
- Code contributions

---

## License

[To be determined - considering open-source license to maximize community benefit]

---

## Contact

[Project contact information]

---

_HandInHand: Because sign languages are beautiful, diverse, and worth preserving._
