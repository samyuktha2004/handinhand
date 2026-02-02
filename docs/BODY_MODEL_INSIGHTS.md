# Body Model - Legal Insights Extracted

**Source:** AndrewEntwistle_Body_Model.ztl (Domestika Free Resource)  
**Date Extracted:** February 1, 2026  
**Legal Status:** Knowledge extraction for non-commercial, personal use (per Domestika Terms)

---

## Extracted Technical Insights

### 1. Model Architecture

The model uses a **rigged, subdivided mesh approach**:

- Base mesh structure with rigging system ("Rig" references found)
- Subdivision surface (SubDiv) technology for smooth details
- Multiple subdivision levels maintained
- Dynamic mesh capabilities

### 2. Mesh Topology Approach

The model employs professional character modeling techniques:

- **Weld, DSDiv (Dynamic Subdivision)** - for maintaining topology
- **Polish, PolyGrp (Polygon Grouping)** - for organized surface management
- **Projection shells** with Outer/Inner layers - for managing geometry detail
- **Smooth operations** (E Smt, S Smt) - for surface quality

### 3. Geometry Optimization Features

- **Thickness management** - suggests body surface with depth
- **Edge smoothing (TCorner, TBorder)** - for natural joint areas
- **Cage geometry** - likely for deformation control
- **Subdivision freezing** - for performance optimization

### 4. Named Components

- **Body_Proxy** - indicates a proxy/simplified version for interactive work
- Main mesh structure with controlled detail levels

---

## Key Takeaways for Your MVP

### Don't Copy

❌ The actual model geometry/mesh  
❌ The rigging system structure  
❌ The mesh topology directly

### You CAN Use These Concepts

✅ **Subdivision surface approach** - use smooth meshes over polygonal bases  
✅ **Rigging philosophy** - maintain separate rig/mesh systems  
✅ **Proxy concept** - create simplified versions for performance  
✅ **Polygon grouping** - organize mesh components logically  
✅ **Joint/edge treatment** - how to handle areas of deformation

---

## Relevance to Your Stickman MVP

**Direct applicability: Low**

- Your MVP uses simplified joint-based stick figures (not mesh-based geometry)
- The model is mesh-sculpting focused; you need skeletal animation

**Future considerations (Post-MVP):**

- If you ever graduate to realistic body meshes, this architecture shows:
  - How to manage complexity with subdivision levels
  - Value of proxy systems for interactive performance
  - Importance of topology planning in character models
  - Joint/edge preservation techniques

---

## What NOT to Do

⚠️ **Don't:**

- Extract or reuse the actual geometry data
- Implement the rigging system as-is
- Copy the mesh topology patterns
- Redistribute any derived models

✅ **DO:**

- Study the architectural concepts
- Apply the design patterns to your own work
- Document your own technical decisions
- Reference these insights in your development notes (not your code)

---

## Recommendation

**For your current stickman MVP:** These insights have minimal value.  
**For future realistic body modeling:** The architectural patterns are worth remembering - especially the proxy/detail level management and rigging separation approach.

Keep your MVP lightweight and skeleton-based. Revisit advanced mesh techniques only when you've validated recognition accuracy at the stick-figure level.

---

## ⚠️ TODO - Future Implementation

**IF you decide to use this body model or any derived version in future stages:**

1. **Contact for licensing rights:**
   - Email: Andrew Entwistle (creator) - found via Domestika profile
   - Or: Domestika directly at legal@domestika.org
   - **Reason:** The model is restricted to personal, non-commercial use only. Any commercial implementation requires explicit written permission.

2. **Source reference:**
   - Resource link: https://www.domestika.org/en/blog/11350-free-library-of-resources-to-help-take-your-creature-design-to-the-next-level?exp_set=1
   - Creator: Andrew Entwistle
   - License: Domestika Terms of Use (Section 3.1 - Personal use only)

3. **Documentation required:**
   - Keep a record of permission grant (if obtained)
   - Document how the model was used/modified
   - Include attribution as per any licensing agreement

**Priority:** Post-MVP only. Do not implement this stage until you've validated stickman-based recognition.
