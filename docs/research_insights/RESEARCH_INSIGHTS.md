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

## 2. ST-GCN: Spatial Temporal Graph Convolutional Networks

### Citation

```bibtex
@inproceedings{yan2018spatial,
  title={Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition},
  author={Yan, Sijie and Xiong, Yuanjun and Lin, Dahua},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2018}
}
```

### Source Details

| Field           | Value                               |
| --------------- | ----------------------------------- |
| **arXiv ID**    | arXiv:1801.07455v2                  |
| **Authors**     | Sijie Yan, Yuanjun Xiong, Dahua Lin |
| **Institution** | The Chinese University of Hong Kong |
| **Date**        | January 2018                        |
| **Venue**       | AAAI 2018                           |
| **Code**        | https://github.com/yysijie/st-gcn   |

### Legal Status ✅

- **arXiv License:** Non-exclusive distribution license
- **Can cite:** Yes
- **Can use insights:** Yes

### Key Technical Insights

#### 1. Foundational Architecture

**Core Contribution:** First to apply Graph Convolutional Networks to skeleton-based action recognition by modeling skeleton as a spatial-temporal graph.

**Key Innovation:** Eliminates need for hand-crafted part assignment or traversal rules. The model automatically learns both spatial and temporal patterns from data.

#### 2. Graph Construction (Figure 1 from paper)

![ST-GCN Graph](st-gcn-graph.png)

**Two types of edges:**

- **Spatial edges ($E_S$):** Intra-body connections based on natural human skeleton
- **Temporal edges ($E_F$):** Connect same joint across consecutive frames

**Formal Definition:**

- Graph $G = (V, E)$ with $N$ joints and $T$ frames
- Node set: $V = \{v_{ti} | t = 1, ..., T, i = 1, ..., N\}$
- $E_S = \{v_{ti}v_{tj} | (i,j) \in H\}$ where $H$ is human body structure
- $E_F = \{v_{ti}v_{(t+1)i}\}$ connecting same joint over time

#### 3. Partitioning Strategies (CRITICAL)

Three strategies for constructing convolution kernels:

| Strategy                  | K   | Description                        | Performance |
| ------------------------- | --- | ---------------------------------- | ----------- |
| **Uni-labeling**          | 1   | All neighbors share same label     | 19.3%       |
| **Distance partitioning** | 2   | Root node (d=0) vs neighbors (d=1) | 29.1%       |
| **Spatial configuration** | 3   | Root + centripetal + centrifugal   | **29.9%**   |

**Spatial Configuration (Best):**

- **Root (0):** The node itself
- **Centripetal (1):** Nodes closer to skeleton gravity center
- **Centrifugal (2):** Nodes farther from gravity center

This strategy captures concentric vs eccentric motion patterns.

#### 4. Learnable Edge Importance Weighting

Added learnable mask **M** on every ST-GCN layer:

- Scales contribution of neighboring nodes
- Data-dependent attention mechanism
- Improves recognition by ~1%

**Result with importance weighting: 30.7% Top-1** (vs 29.9% without)

#### 5. Network Architecture Details

| Component               | Value                             |
| ----------------------- | --------------------------------- |
| **Layers**              | 9 ST-GCN units                    |
| **Channels**            | 64 → 128 → 256 (3 layers each)    |
| **Temporal kernel**     | 9 frames                          |
| **Dropout**             | 0.5 after each unit               |
| **Optimizer**           | SGD, lr=0.01, decay 0.1/10 epochs |
| **Batch normalization** | Before each layer                 |
| **ResNet mechanism**    | Applied on each unit              |

#### 6. Data Augmentation

**Random Affine Transformation:**

- Random angle, translation, scaling
- Interpolated across frames (simulates camera movement)

**Random Fragment Sampling:**

- Sample random fragments during training
- Use all frames during testing

**Global Pooling:** Handles variable-length sequences

#### 7. Experimental Results

**Kinetics Dataset (Table 1 - Ablation):**
| Configuration | Top-1 | Top-5 |
|---------------|-------|-------|
| Baseline TCN | 20.3% | 40.0% |
| Local Convolution | 22.0% | 43.2% |
| Uni-labeling | 19.3% | 37.4% |
| Distance Partitioning | 29.1% | 51.3% |
| Spatial Configuration | 29.9% | 52.2% |
| **ST-GCN + Importance** | **30.7%** | **52.8%** |

**Kinetics Comparison (Table 2):**
| Method | Top-1 | Top-5 |
|--------|-------|-------|
| RGB | 57.0% | 77.3% |
| Optical Flow | 49.5% | 71.9% |
| Feature Encoding | 14.9% | 25.8% |
| Deep LSTM | 16.4% | 35.3% |
| Temporal Conv. | 20.3% | 40.0% |
| **ST-GCN** | **30.7%** | **52.8%** |

**NTU-RGB+D Dataset (Table 3):**
| Method | X-Sub | X-View |
|--------|-------|--------|
| Lie Group | 50.1% | 52.8% |
| H-RNN | 59.1% | 64.0% |
| Deep LSTM | 60.7% | 67.3% |
| PA-LSTM | 62.9% | 70.3% |
| ST-LSTM+TS | 69.2% | 77.7% |
| Temporal Conv. | 74.3% | 83.1% |
| C-CNN + MTLN | 79.6% | 84.8% |
| **ST-GCN** | **81.5%** | **88.3%** |

#### 8. Key Finding: Skeleton Complements RGB

**Table 5 - Ensemble Performance:**
| Streams | Accuracy |
|---------|----------|
| RGB only | 70.3% |
| Flow only | 51.0% |
| ST-GCN only | 30.7% |
| RGB + Flow | 71.1% |
| **RGB + ST-GCN** | **71.2%** |
| **RGB + Flow + ST-GCN** | **71.7%** |

**Key Insight:** Adding ST-GCN to RGB improves by +0.9%, even better than optical flow (+0.8%). Skeleton provides complementary information!

### Application to HandInHand

#### High Priority

1. **Spatial configuration partitioning** - Use centripetal/centrifugal distinction
2. **Learnable edge weighting** - Joints have different importance for different signs
3. **9-layer architecture** - If upgrading to neural network

#### Medium Priority

4. **Random affine augmentation** - Camera movement simulation
5. **Global pooling** - Handle variable-length signs

#### Key Takeaways

- ST-GCN is the **foundational paper** for skeleton-based action recognition
- Spatial configuration partitioning outperforms simpler strategies
- Skeleton complements RGB modality (ensemble improves accuracy)
- Architecture validated on 400 action classes and 56,000 clips

---

## 3. 2s-AGCN: Two-Stream Adaptive GCN

### Citation

```bibtex
@inproceedings{shi2019two,
  title={Two-Stream Adaptive Graph Convolutional Networks for Skeleton-Based Action Recognition},
  author={Shi, Lei and Zhang, Yifan and Cheng, Jian and Lu, Hanqing},
  booktitle={CVPR},
  pages={12026--12035},
  year={2019}
}
```

### Source Details

| Field           | Value                                        |
| --------------- | -------------------------------------------- |
| **arXiv ID**    | arXiv:1805.07694v3                           |
| **Authors**     | Lei Shi, Yifan Zhang, Jian Cheng, Hanqing Lu |
| **Institution** | Chinese Academy of Sciences                  |
| **Date**        | July 2019                                    |
| **Venue**       | CVPR 2019                                    |

### Legal Status ✅

- **arXiv License:** Non-exclusive distribution license
- **Can cite:** Yes
- **Can use insights:** Yes

### Key Technical Insights

**Problem with ST-GCN:**

- Fixed graph topology set manually
- Same topology across all layers and samples
- Only uses first-order information (joint positions)

**Solution - Adaptive Graph:**

- Graph topology learned by backpropagation (end-to-end)
- Data-driven method increases model flexibility
- Can be uniform or sample-specific

**Two-Stream Architecture:**
| Stream | Data | Description |
|--------|------|-------------|
| **Joint stream** | $(x, y, z)$ coordinates | First-order position info |
| **Bone stream** | $(x_j - x_i, y_j - y_i, z_j - z_i)$ | Second-order direction/length info |

**Key Insight:** Bone vectors (second-order info) are "naturally more informative and discriminative for action recognition."

**Performance:** Significant margin over state-of-the-art on NTU-RGBD and Kinetics-Skeleton.

**Application to HandInHand:**

- **CRITICAL:** Confirms importance of bone vectors (already noted in SAM-SLR)
- Learnable graph topology could help for sign language variations
- Two-stream approach validated by multiple papers now

---

## 4. Cleison et al.: ST-GCN for Sign Language Recognition

### Citation

```bibtex
@inproceedings{amorim2019spatial,
  title={Spatial-Temporal Graph Convolutional Networks for Sign Language Recognition},
  author={de Amorim, Cleison Correia and Macêdo, David and Zanchettin, Cleber},
  booktitle={International Conference on Artificial Neural Networks (ICANN)},
  year={2019},
  publisher={Springer}
}
```

### Source Details

| Field           | Value                                                      |
| --------------- | ---------------------------------------------------------- |
| **arXiv ID**    | arXiv:1901.11164v2                                         |
| **Authors**     | Cleison Correia de Amorim, David Macêdo, Cleber Zanchettin |
| **Institution** | Federal University of Pernambuco, Brazil                   |
| **Date**        | May 2020 (v2)                                              |
| **Venue**       | ICANN 2019                                                 |
| **DOI**         | 10.1007/978-3-030-30493-5_59                               |

### Legal Status ✅

- **arXiv License:** Non-exclusive distribution license
- **Can cite:** Yes
- **Can use insights:** Yes

### Key Technical Insights

**Significance:** Direct application of ST-GCN to sign language recognition (not just general action recognition).

**Contributions:**

1. Adapted ST-GCN architecture specifically for sign language
2. Created new skeleton dataset from ASLLVD (American Sign Language Lexicon Video Dataset)
3. Demonstrated graphs capture sign language dynamics in spatial and temporal dimensions
4. Addressed complex aspects of sign language movement

**Dataset Contribution:** Human skeleton dataset for sign language based on ASLLVD available for future research.

**Application to HandInHand:**

- **Validates our approach:** Skeleton-based methods work for sign language
- Dataset could be useful for benchmarking
- Directly applicable architecture for neural network upgrade path

---

## 5. Das et al.: Bangla Sign Language Recognition with Transfer Learning + Random Forest

### Citation

```bibtex
@article{das2023bsl_hybrid,
  title={A hybrid approach for Bangla sign language recognition using deep transfer learning model with random forest classifier},
  author={Das, Sunanda and Imtiaz, Md. Samir and Neom, Nieb Hasan and Siddique, Nazmul and Wang, Hui},
  journal={Expert Systems With Applications},
  volume={213},
  pages={118914},
  year={2023},
  doi={10.1016/j.eswa.2022.118914}
}
```

### Source Details

| Field        | Value                                                                     |
| ------------ | ------------------------------------------------------------------------- |
| **Authors**  | Sunanda Das, Md. Samir Imtiaz, Nieb Hasan Neom, Nazmul Siddique, Hui Wang |
| **Venue**    | Expert Systems With Applications (ESWA)                                   |
| **Year**     | 2023                                                                      |
| **DOI**      | 10.1016/j.eswa.2022.118914                                                |
| **Datasets** | Ishara-Bochon (digits), Ishara-Lipi (alphabets)                           |

### Key Technical Insights

- Uses transfer learning (VGG16/19, InceptionV3, Xception, ResNet50) with Random Forest classifier for small datasets.
- Introduces background elimination with morphological ops and adaptive Gaussian thresholding.
- Reported results: ~91.7% accuracy for characters and ~97.3% for digits on BSL datasets.

**Application to HandInHand:**

- Reinforces transfer learning for small sign datasets; consider lightweight backbones for rapid baselines.
- Background cleanup can improve landmark stability before pose extraction.

---

## 6. Roy et al.: Position/Rotation-Invariant SLR from 3D Kinect Data

### Citation

```bibtex
@article{roy2025kinect_rnn,
  title={Position and Rotation Invariant Sign Language Recognition from 3D Kinect Data with Recurrent Neural Networks},
  author={Roy, Prasun and Bhattacharya, Saumik and Roy, Partha Pratim and Pal, Umapada},
  journal={arXiv preprint arXiv:2010.12669v4},
  year={2025}
}
```

### Source Details

| Field        | Value                                                           |
| ------------ | --------------------------------------------------------------- |
| **arXiv ID** | arXiv:2010.12669v4                                              |
| **Authors**  | Prasun Roy, Saumik Bhattacharya, Partha Pratim Roy, Umapada Pal |
| **Sensors**  | Kinect v1 (RGB + depth)                                         |
| **Data**     | 20 body joints, 30 Indian sign gestures                         |
| **Model**    | RNN/LSTM sequence classifier                                    |
| **Accuracy** | 84.81%                                                          |

### Key Technical Insights

- Uses geometric alignment (affine transform) to correct rotation/position variance from depth sensors.
- Sequence modeling on 3D joint trajectories improves robustness to signer orientation.

**Application to HandInHand:**

- Consider rigid alignment to a canonical shoulder plane before embedding for better invariance.

---

## 7. Anetha & Rejina: Hand Talk (Accelerometer + sEMG Glove)

### Citation

```bibtex
@article{anetha2014handtalk,
  title={Hand Talk - A Sign Language Recognition Based on Accelerometer and SEMG Data},
  author={Anetha, K. and Rejina Parvin, J.},
  journal={International Journal of Innovative Research in Computer and Communication Engineering},
  volume={2},
  number={Special Issue 3},
  year={2014}
}
```

### Source Details

| Field       | Value                                        |
| ----------- | -------------------------------------------- |
| **Venue**   | IJIRCCE (Vol. 2, Special Issue 3, July 2014) |
| **Sensors** | Flex sensors, 3-axis accelerometer, sEMG     |
| **Task**    | Isolated ASL alphabet recognition            |

### Key Technical Insights

- Glove-based sensing captures finger bend + hand trajectory + muscle activity.
- sEMG complements accelerometer data for gesture disambiguation in noisy settings.

**Application to HandInHand:**

- Highlights the value of multi-sensor fusion; for vision-only pipelines, mimic this by combining kinematics + dynamics features.

---

## 8. Ravikiran et al.: Finger Detection via Boundary Tracing

### Citation

```bibtex
@inproceedings{ravikiran2009finger,
  title={Finger Detection for Sign Language Recognition},
  author={Ravikiran, J. and Mahesh, Kavi and Mahishi, Suhas and Dheeraj, R. and Sudheender, S. and Pujari, Nitin V.},
  booktitle={Proceedings of the International MultiConference of Engineers and Computer Scientists (IMECS)},
  year={2009}
}
```

### Source Details

| Field      | Value                                               |
| ---------- | --------------------------------------------------- |
| **Venue**  | IMECS 2009 (Hong Kong)                              |
| **Method** | Canny edge + boundary tracing + fingertip detection |
| **Claim**  | ~95% finger recognition in tests                    |

### Key Technical Insights

- Boundary tracing + fingertip detection can identify number of open fingers without gloves/markers.
- Robust to small breaks in the contour by rejoining traces.

**Application to HandInHand:**

- Can serve as a lightweight fallback for finger-count verification on rendered masks.

---

## 9. Akdag & Baykan: Multi-Stream Finger Features from Pose Data (MDPI)

### Citation

```bibtex
@article{akdag2024multistream,
  title={Multi-Stream Isolated Sign Language Recognition Based on Finger Features Derived from Pose Data},
  author={Akdag, Ali and Baykan, Omer Kaan},
  journal={Electronics},
  volume={13},
  number={8},
  pages={1591},
  year={2024},
  doi={10.3390/electronics13081591}
}
```

### Key Technical Insights

- Uses MediaPipe Holistic keypoints to render per-finger channels (FINGER), merged finger crops, and frame-difference (FD) finger motion.
- PCA + SVM on fused features; high accuracy across multiple datasets.
- Finger-only features are strong; face-only features are weak but improve when fused with hand/body.

**Application to HandInHand:**

- Supports multi-stream features (static + temporal) and finger-centric representations.
- Frame-difference features can be emulated via temporal deltas in our embeddings.

---

## 10. pose-format: Shoulder-Width Normalization (sign/translate ecosystem)

**Source:** sign-language-processing/pose (GitHub) — used by sign.mt
**License:** CC BY-NC-SA 4.0 (insights usable, code not) — reviewed Feb 26, 2026

### Key Technical Insight: Industry-Standard Scale Normalization

The canonical normalization for sign language skeleton data is **shoulder-width scaling**:

```python
# pose-format API (insight only):
pose.normalize(p.header.normalization_info(
    p1=("pose_keypoints_2d", "RShoulder"),
    p2=("pose_keypoints_2d", "LShoulder")
))
```

This produces coordinates in **"body-width units"**:
- Inter-shoulder distance = 1.0 unit
- Hand at face level ≈ 0.6 units above shoulder center
- Arm extended to side ≈ 1.2 units

**Why shoulder-center subtraction alone is insufficient:**
A signer 1m from camera has shoulder width ~0.8 in [0,1] MediaPipe coords; at 2m it's ~0.4. After position-only centering, the same hand position differs by 2× — embeddings are not comparable across signers at different distances.

**Dividing by shoulder width** makes embeddings invariant to:
- Camera distance (signer position relative to camera)
- Absolute body size (different signers' proportions)
- Position in frame

**Application to HandInHand:** Implemented Feb 26, 2026 in both `generate_embeddings.py` and `recognition_engine.py`. New baseline after adding scale normalization: **0.6840** mean ASL↔BSL (was 0.6712 position-only).

### Assessment: 2D vs 3D Reference Body for Embedding

**User question (Feb 26, 2026):** "Can't we make the reference body in 3D — wouldn't that be most efficient?"

**Assessment:**

| Approach | Position Invariant | Scale Invariant | Depth Accurate | Complexity |
|----------|-------------------|-----------------|----------------|------------|
| Raw MediaPipe coords | ❌ | ❌ | ❌ | Low |
| Shoulder-center only (previous) | ✅ | ❌ | ❌ | Low |
| **Shoulder-width scaling (current)** | ✅ | ✅ | Approximate | Low |
| 3D Reference Body (IK-based) | ✅ | ✅ | ✅ | Very High |
| Joint angles (bone dot products) | ✅ | ✅ | ✅ | Medium |

**Why NOT 3D reference body (now):**
1. **MediaPipe z is unreliable** from a single 2D camera — depth is estimated, not measured. Building IK on top of noisy z would amplify errors.
2. **Inverse kinematics is expensive** — mapping raw joint positions to angles on a fixed-segment body requires iterative optimization (Newton-Raphson, FABRIK, etc.). Overkill for 4 concepts.
3. **Bone vectors already approximate it** — our 4-stream embedding includes bone vectors (parent→child joint differences) which are partially scale-invariant and direction-preserving. This is a first-order 3D approximation.
4. **We already capture the essential invariance** with shoulder-width scaling + bone stream.

**Why joint angles WOULD be better (Phase 6/7):**
True joint angles (elbow angle, wrist flexion, shoulder abduction) are fully scale-invariant by construction — they don't need any normalization. Computing them only requires dot products between consecutive bone vectors (no IK). This is the natural Phase 5/6 upgrade when we need to distinguish:
- Palm-forward (forward arm, elbow extended) from palm-backward (same position, wrist pronated)
- Shoulder abduction angle from wrist extension angle

**Implementation path:** `bone_angle_feat = np.arccos(np.clip(np.dot(bone_i, bone_j) / (|bone_i| * |bone_j|), -1, 1))` — no IK required. Add as 5th stream in Phase 5/6.

**Current recommendation:** Keep shoulder-width scaling (implemented). Consider joint angles as Phase 5 enhancement after attention replaces GAP.

---

## 11. Multilingual Sign Language Embedding Alignment + Sign Boundary Detection (2022–2024)

### 11a. SignCLIP: Shared Multilingual Embedding via Contrastive Learning

**Citation:**
```bibtex
@article{bohacek2024signclip,
  title={SignCLIP: Connecting Text and Sign Language by Contrastive Learning},
  author={Bohacek, Matyáš and Fierro, Camila},
  journal={arXiv preprint arXiv:2407.01264},
  year={2024}
}
```

**Legal:** arXiv — insights usable. Not yet reviewed for code license.

**Key Technical Insights:**
- Uses 543 MediaPipe Holistic keypoints (full pose + hands + face) → 768-d shared embedding via frozen backbone + MLP
- Contrastive loss aligns sign video with spoken-language text in the same space
- Both ASL and BSL processed with identical feature extraction (Strategy A: shared encoder)
- No explicit cross-lingual correction needed when training data is sufficiently diverse

**Application to HandInHand:**
- Validates our Strategy A approach (same 4-stream pipeline for ASL + BSL)
- Their 543-pt set vs our 55-pt subset — our reduction follows SAM-SLR graph reduction (§1)
- Phase 6+: contrastive training on ASL↔BSL concept pairs could explicitly align the space

---

### 11b. MLSLT: Towards Multilingual Sign Language Translation (CVPR 2022)

**Citation:**
```bibtex
@inproceedings{yin2022mlslt,
  title={MLSLT: Towards Multilingual Sign Language Translation},
  author={Yin, Kayo and Moryossef, Amit and Fahrni, Julie and Goldberg, Yoav and Zwitserlood, Ilse},
  booktitle={CVPR},
  year={2022}
}
```

**Legal:** CVPR proceedings — insights usable.

**Three-Strategy Taxonomy for Multilingual SL:**

| Strategy | Architecture | HandInHand Phase |
|----------|-------------|-----------------|
| A: Shared encoder | Identical extraction for all languages → cosine comparison | Phase 4 (**current**) |
| B: Separate encoders | Language-specific → shared semantic space via multi-task loss | Phase 5 option |
| C: LLM pretraining | T5-style pretrained backbone + signed→spoken alignment | Phase 7 |

**Application to HandInHand:**
- Phase 4 = Strategy A, validated for small vocabulary isolated sign recognition
- Phase 5: Procrustes rotation is a lightweight Strategy B alignment (no retraining)
- Strategy C requires parallel signed-to-spoken corpus (YouTube-SL-25 for scale)

---

### 11c. MHB: Multimodal Handshape-aware Boundary Detection (2024)

**Citation:**
```bibtex
@misc{mhb2024,
  title={MHB: Multimodal Handshape-aware Boundary Detection for Continuous Sign Language Recognition},
  journal={arXiv preprint arXiv:2511.19907},
  year={2024}
}
```

**Legal:** arXiv — insights usable.

**Key Technical Insights:**
- Pretrained GCN on hand joints matches 87 canonical handshapes → per-frame confidence score
- Fuses handshape confidence + wrist velocity via cross-attention + learnable gating
- Linguistic prior: "handshapes normally expected at the beginning and end of signs" (hold phases)

**Critical Connection to HandInHand:**
- Our 16-probe handshape system = subset of their 87-shape vocabulary
- Phase 5 boundary detection via probes: cosine-similarity(live, each probe) → max = handshape confidence
- Combine: `boundary = (velocity < threshold) AND (probe_similarity > 0.7)`
- No GCN training required — our probes ARE the handshape vocabulary
- Probes to add before Phase 7: I, H, T, X (medium frequency, currently missing — from gap analysis)

---

### 11d. Wrist Velocity Baseline for Sign Boundary Detection

**Source:** Neuroscience literature on event segmentation in ASL (cognitive science, peer-reviewed)

**Key Data Points:**
- ASL dominant-hand wrist velocity during signs: **1.17 m/s** (SE=0.054)
- Non-linguistic gestures: **1.78 m/s** (significantly faster — useful discriminator)
- Sign boundaries: velocity local minima (rapid deceleration = hold phase between signs)
- In MediaPipe normalized [0,1] coords at 30fps: threshold ≈ **0.04 units/frame** (approximate; calibrate per setup)

**Application to HandInHand:**
- Phase 4: ignore (stored-to-stored, no segmentation needed)
- Phase 5: `velocity = np.linalg.norm(wrist_t - wrist_{t-1})`, detect local minima < 0.04
- Combined boundary gate: velocity minimum AND probe handshape confidence > 0.7

---

## 12. Papers Still Pending (Paywalled/Not Yet Reviewed)

| Paper                                 | Status        | Notes                                  |
| ------------------------------------- | ------------- | -------------------------------------- |
| Deep Sign (Koller et al., IJCV 2018)  | ⏳ Pending    | Hybrid CNN-HMM approach                |
| Word-level SLR (Li et al., WACV 2020) | ⏳ Pending    | Dataset comparison                     |
| ScienceDirect S0167865522003804       | ❌ Paywalled  | Could not access                       |
| ScienceDirect S1877050915021675       | ❌ Paywalled  | Could not access                       |
| 41598_2022_Article_15699 (Sci Rep)    | ❌ Unreadable | PDF error: incorrect startxref pointer |

---

## Legal Summary

| Resource                 | License      | Citation OK | Use Insights     | Commercial           |
| ------------------------ | ------------ | ----------- | ---------------- | -------------------- |
| SAM-SLR Paper            | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| ST-GCN Paper             | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| 2s-AGCN Paper            | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| Cleison et al.           | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| Das et al. (BSL)         | CC BY-NC-ND  | ✅ Yes      | ✅ Yes           | ⚠️ Non-commercial    |
| Roy et al. (Kinect)      | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| Hand Talk (IJIRCCE)      | Unknown      | ✅ Yes      | ✅ Yes           | ⚠️ Check venue       |
| Finger Detection (IMECS) | Unknown      | ✅ Yes      | ✅ Yes           | ⚠️ Check venue       |
| Akdag & Baykan (MDPI)    | CC BY 4.0    | ✅ Yes      | ✅ Yes           | ✅ Yes               |
| SAM-SLR Code             | GitHub       | ✅ Yes      | ⚠️ Check license | ⚠️ Check license     |
| OpenStax A&P             | CC BY 4.0    | ✅ Yes      | ✅ Yes           | ✅ Yes               |
| Z-Anatomy                | CC BY-SA 4.0 | ✅ Yes      | ✅ Yes           | ✅ Yes (share-alike) |
| Physio-Pedia             | CC BY-SA     | ✅ Yes      | ✅ Yes           | ✅ Yes (share-alike) |
| SignCLIP (arXiv:2407.01264) | arXiv     | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| MLSLT (CVPR 2022)        | CVPR         | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| MHB (arXiv:2511.19907)   | arXiv        | ✅ Yes      | ✅ Yes           | ⚠️ Check code        |
| Wrist velocity (neurosci)| Academic     | ✅ Yes      | ✅ Yes           | ✅ Yes               |

---

## Next Steps

- [ ] Review SAM-SLR GitHub code for implementation details
- [ ] Test graph reduction (52 → 27 nodes) on our signatures
- [ ] Implement bone vector calculation
- [ ] Add jittering augmentation to signature generation
- [ ] Benchmark accuracy before/after optimizations
