# Research Insights for Sign Language Recognition

**Date Created:** February 2, 2026  
**Purpose:** Compile academic research insights applicable to HandInHand project  
**Note:** All sources properly cited for potential future research paper

---

## 1. SAM-SLR: Skeleton Aware Multi-modal Sign Language Recognition

### Citation

```bibtex
@article{jiang2021skeleton,
  title={Skeleton Aware Multi-modal Sign Language Recognition},
  author={Jiang, Songyao and Sun, Bin and Wang, Lichen and Bai, Yue and Li, Kunpeng and Fu, Yun},
  journal={arXiv preprint arXiv:2103.08833},
  year={2021}
}
```

### Source Details

| Field           | Value                                                                    |
| --------------- | ------------------------------------------------------------------------ |
| **arXiv ID**    | arXiv:2103.08833v5                                                       |
| **Authors**     | Songyao Jiang, Bin Sun, Lichen Wang, Yue Bai, Kunpeng Li, Yun Fu         |
| **Institution** | Northeastern University, Boston MA, USA                                  |
| **Date**        | May 2, 2021                                                              |
| **Code**        | https://github.com/jackyjsy/CVPR21Chal-SLR                               |
| **Achievement** | 1st place, CVPR-21 Challenge on Isolated SLR (both RGB and RGB-D tracks) |

### Legal Status ✅

- **arXiv License:** Non-exclusive license to distribute (arXiv.org perpetual license)
- **Can cite:** Yes, standard academic citation allowed
- **Can use insights:** Yes, for research and implementation
- **Code license:** Check GitHub repo for specific license
- **Commercial use:** Consult code license before commercial deployment

---

### Key Technical Insights

#### 1. Graph Reduction (CRITICAL FINDING)

**Problem:** Full 133-point whole-body skeleton has too many nodes/edges, causing:

- Model noise
- Difficulty learning interactions between distant nodes
- Low accuracy (~63.69% without reduction)

**Solution:** Reduce to **27 nodes**:

- **10 nodes per hand** (reduced from 21)
- **7 nodes for upper body**

**Impact:** Graph reduction is the **single most important optimization**:
| Configuration | Top-1 Accuracy |
|---------------|----------------|
| With Graph Reduction | **95.02%** |
| Without Graph Reduction | 63.69% |
| Difference | **+31.33%** |

**Application to HandInHand:**

- Our current 52 landmarks (21 per hand + upper body) may benefit from reduction
- Consider selecting key joints only (fingertips, wrist, elbow, shoulder)
- Test reduced graph vs. full graph for accuracy comparison

#### 2. Multi-Stream Architecture

SAM-SLR uses **4 parallel streams** of skeleton data:

| Stream           | Data                                                                 | Description                          |
| ---------------- | -------------------------------------------------------------------- | ------------------------------------ |
| **Joint**        | $(x, y, s)$ coordinates                                              | Raw keypoint positions               |
| **Bone**         | Vector between joints                                                | Direction from parent to child joint |
| **Joint Motion** | $v_{i,t}^{JM} = (x_{i,t+1} - x_{i,t}, y_{i,t+1} - y_{i,t}, s_{i,t})$ | Temporal difference of joints        |
| **Bone Motion**  | $v_{i,t}^{BM} = v_{i,t+1}^B - v_{i,t}^B$                             | Temporal difference of bones         |

**Performance by stream:**
| Stream | Top-1 | Top-5 |
|--------|-------|-------|
| Joint | 95.02 | 99.21 |
| Bone | 94.70 | 99.14 |
| Joint Motion | 93.01 | 98.85 |
| Bone Motion | 92.49 | 98.78 |
| **Multi-stream Ensemble** | **95.45** | **99.25** |

**Application to HandInHand:**

- Currently we use joint coordinates only
- Adding **bone vectors** could improve robustness to position variation
- Adding **motion data** captures dynamics better
- Ensemble of streams provides +0.43% improvement

#### 3. SSTCN Keypoint Selection

For the Separable Spatial-Temporal Convolution Network, they use **33 keypoints** from 60 frames:

| Body Part | Landmarks        | Count  |
| --------- | ---------------- | ------ |
| Nose      | 1                | 1      |
| Mouth     | 4                | 4      |
| Shoulders | 2                | 2      |
| Elbows    | 2                | 2      |
| Wrists    | 2                | 2      |
| Hands     | 22 (11 per hand) | 22     |
| **Total** |                  | **33** |

**Application to HandInHand:**

- Our 52-point model is reasonable
- Consider adding facial landmarks (mouth) for signs with mouth morphemes
- Upper body context (shoulders, elbows) is valuable

#### 4. Data Augmentation Techniques

SAM-SLR uses these augmentations for skeleton data:

| Technique       | Description                       |
| --------------- | --------------------------------- |
| Random sampling | Variable frame selection          |
| Mirroring       | Horizontal flip (left-right swap) |
| Rotating        | Small angular rotations           |
| Scaling         | Size variations                   |
| Jittering       | Small random noise on coordinates |
| Shifting        | Translation of entire skeleton    |

**Sample length:** 150 frames (repeat video if shorter)

**Normalization:** Coordinates normalized to [-1, 1]

**Application to HandInHand:**

- We already have mirrored signatures ✅
- Add jittering for robustness to tracking noise
- Add scaling for different signer body sizes
- Consider rotation augmentation (±5-10°)

#### 5. Label Smoothing

Instead of hard one-hot labels, they use label smoothing:

$$q'(k|x) = (1 - \epsilon)\delta_{k,y} + \epsilon u(k)$$

Where:

- $\epsilon$ is a hyperparameter (0-1)
- $u()$ is uniform distribution
- $k$ is number of classes

**Benefit:** Reduces overfitting, improves accuracy by ~1%

**Application to HandInHand:**

- Consider label smoothing when training classifiers
- Especially useful with limited training data

#### 6. Ensemble Strategy

Simple weighted average of predictions:

$$q_{RGB} = \alpha_1 q_{skel} + \alpha_2 q_{RGB} + \alpha_3 q_{flow} + \alpha_4 q_{feat}$$

Weights tuned on validation set:

- RGB track: $\alpha = [1, 0.9, 0.4, 0.4]$
- RGB-D track: $\alpha = [1.0, 0.9, 0.4, 0.4, 0.4, 0.1]$

**Application to HandInHand:**

- Skeleton-based methods get highest weight (1.0)
- Multi-modal fusion improves overall accuracy

---

### Results Summary

| Modality                     | Top-1     | Top-5     |
| ---------------------------- | --------- | --------- |
| Baseline RGB                 | 42.58     | -         |
| Baseline RGB-D               | 63.22     | -         |
| **Keypoints (skeleton)**     | **95.45** | **99.25** |
| RGB Frames                   | 94.77     | 99.48     |
| Depth HHA                    | 95.13     | 99.25     |
| Final Ensemble (RGB track)   | **98.42** | -         |
| Final Ensemble (RGB-D track) | **98.53** | -         |

**Key takeaway:** Skeleton-based methods (95.45%) outperform raw RGB (94.77%) and approach depth sensor accuracy, while being much more computationally efficient.

---

### Implementation Recommendations for HandInHand

#### High Priority (Immediate Impact)

1. **Graph Reduction** - Reduce landmarks from 52 to ~25-30 key points
2. **Bone Vectors** - Add bone stream alongside joint coordinates
3. **Data Augmentation** - Add jittering, scaling, small rotations

#### Medium Priority (Future Enhancement)

4. **Motion Streams** - Add temporal difference features
5. **Label Smoothing** - When training ML classifiers
6. **Multi-stream Ensemble** - Combine multiple feature types

#### Lower Priority (Advanced)

7. **GCN Architecture** - If switching from cosine similarity to neural networks
8. **Attention Mechanisms** - STC (Spatial, Temporal, Channel) attention

---

## 2. Additional Research Papers to Review

### Cited by SAM-SLR (Relevant to Our Project)

| Paper  | Topic                       | Citation              |
| ------ | --------------------------- | --------------------- |
| ST-GCN | Skeleton action recognition | Yan et al., AAAI 2018 |
| AS-GCN | Latent joint connections    | Shi et al., 2019      |
| MMPose | Whole-body pose estimation  | OpenMMLab, 2020       |
| HRNet  | Pose keypoints              | Sun et al., CVPR 2019 |

### Papers to Investigate

1. **Spatial-temporal graph convolutional networks for sign language recognition**
   - Cleison et al., ICANN 2019
   - Directly relevant to our skeleton approach

2. **Deep sign: Enabling robust statistical continuous sign language recognition**
   - Koller et al., IJCV 2018
   - Hybrid CNN-HMM approach

3. **Word-level deep sign language recognition from video**
   - Li et al., WACV 2020
   - Dataset comparison methods

---

## Legal Summary

| Resource      | License      | Citation OK | Use Insights     | Commercial           |
| ------------- | ------------ | ----------- | ---------------- | -------------------- |
| SAM-SLR Paper | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| SAM-SLR Code  | GitHub       | ✅ Yes      | ⚠️ Check license | ⚠️ Check license     |
| OpenStax A&P  | CC BY 4.0    | ✅ Yes      | ✅ Yes           | ✅ Yes               |
| Z-Anatomy     | CC BY-SA 4.0 | ✅ Yes      | ✅ Yes           | ✅ Yes (share-alike) |
| Physio-Pedia  | CC BY-SA     | ✅ Yes      | ✅ Yes           | ✅ Yes (share-alike) |

---

## Next Steps

- [ ] Review SAM-SLR GitHub code for implementation details
- [ ] Test graph reduction (52 → 27 nodes) on our signatures
- [ ] Implement bone vector calculation
- [ ] Add jittering augmentation to signature generation
- [ ] Benchmark accuracy before/after optimizations
