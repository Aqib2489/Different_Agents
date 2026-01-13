# RC Beam Design System - Multi-Agent Architecture

A sophisticated reinforced concrete beam design system using **CrewAI framework** that follows **NBCC (National Building Code of Canada)** provisions. This system employs a multi-agent architecture where specialized agents handle different aspects of structural design while maintaining strict separation between interpretation and calculation.

## 🏗️ System Architecture

### Core Philosophy

**Separation of Concerns**: 
- **Agents** → Interpret results, retrieve code clauses, provide engineering judgment
- **Calculation Engine** → Performs deterministic mathematical calculations
- **NBCC RAG System** → Semantic search on actual code documents using vector embeddings
- **NBCC Tool** → Read-only authority for code provisions (never calculates)

This architecture ensures **auditability**, **transparency**, and eliminates **hallucinated design rules**.

### 🔍 RAG-Based Code Retrieval

The system uses **Retrieval-Augmented Generation (RAG)** for NBCC access:

```
Agent Query → Vector Embedding → Semantic Search → Retrieve Top-K Code Sections → Return to Agent
```

**Benefits**:
- ✅ **Semantic Understanding**: Agents use natural language queries
- ✅ **Actual Code Text**: Retrieves from real NBCC corpus (not hardcoded)
- ✅ **Relevance Ranked**: Most similar sections returned first
- ✅ **Extensible**: Add more code documents without code changes
- ✅ **Verifiable**: All results include clause numbers and source text

**Current Setup**: Mock NBCC corpus (common clauses embedded)  
**Upgrade Path**: Load actual NBCC PDF (see `RAG_SETUP.md`)

---

## 🤖 Agent Roles

### 1. **Load Analysis Engineer**
- Retrieves NBCC load combination requirements
- Applies load factors to determine governing loads
- Calculates maximum factored moment and shear
- Documents which load combination governs

### 2. **Flexural Design Engineer**
- Retrieves NBCC flexural design provisions
- Designs longitudinal reinforcement for bending
- Checks minimum and maximum steel requirements
- Selects practical bar arrangements
- Verifies moment capacity

### 3. **Shear Design Engineer**
- Retrieves NBCC shear design provisions
- Calculates concrete shear capacity
- Designs stirrup reinforcement when needed
- Ensures proper spacing and minimum requirements

### 4. **Serviceability Engineer**
- Retrieves NBCC serviceability provisions
- Checks span-to-depth ratios
- Verifies deflection control requirements
- Recommends design iterations if limits exceeded

### 5. **NBCC Code Authority** ⚖️
- **READ-ONLY** agent - never performs calculations
- Provides authoritative NBCC clause text
- Offers structured interpretation of code requirements
- Ensures all design decisions are code-referenced

### 6. **Design Reviewer**
- Validates complete design for consistency
- Checks code compliance across all stages
- Identifies unsafe assumptions
- Provides final approval or requests corrections

---

## 📁 Project Structure

```
RC_Beam_Design_Agent/
│
├── beam_design.py              # Main orchestration file (agents, tasks, workflow)
├── calculation_engine.py       # Pure calculation functions (no AI)
├── nbcc_code_tool.py          # NBCC code retrieval tool with RAG integration
├── nbcc_rag_system.py         # RAG system: vector store, embeddings, search
├── utils.py                    # API key management
├── requirements.txt            # Dependencies (includes RAG packages)
├── setup_nbcc_pdf.py          # One-time setup to load NBCC PDF
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── RAG_SETUP.md               # Detailed RAG configuration guide
└── nbcc_vectorstore/          # Persisted vector database (auto-created)
```

---

## 🚀 Installation

### Prerequisites
- Python 3.9+
- OpenAI API key

### Setup Steps

1. **Clone the repository**
```bash
cd RC_Beam_Design_Agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

This installs:
- CrewAI framework
- RAG system (LangChain, ChromaDB, PyPDF)
- OpenAI API client
- Numerical libraries

3. **Configure environment**
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_api_key_here
```

4. **(Optional) Load Real NBCC PDF**

**Default**: System uses mock NBCC corpus (works immediately)

**Upgrade to Real PDF**:
```bash
# If you have NBCC PDF
python setup_nbcc_pdf.py path/to/NBCC.pdf

# This creates vector embeddings (one-time, ~5-15 min)
# See RAG_SETUP.md for detailed instructions
```

---

## 💻 Usage

### Basic Example

```python
from beam_design import design_rc_beam

# Design a 6m simply supported beam
result = design_rc_beam(
    span=6.0,               # Beam span (m)
    dead_load=10.0,         # Dead load (kN/m)
    live_load=5.0,          # Live load (kN/m)
    snow_load=2.0,          # Snow load (kN/m)
    width=300,              # Beam width (mm)
    depth=500,              # Beam depth (mm)
    fc_prime=30,            # Concrete strength (MPa)
    fy=400,                 # Steel yield strength (MPa)
    cover=40,               # Concrete cover (mm)
    support_condition="simply supported"
)

print(result)
```

### Run the Example

```bash
python beam_design.py
```

---

## 📊 Design Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN ORCHESTRATION                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: LOAD ANALYSIS                                          │
│  ├─ Retrieve NBCC load combinations                             │
│  ├─ Apply load factors (1.4D+1.5L+0.5S, etc.)                  │
│  ├─ Calculate max moment Mf and shear Vf                        │
│  └─ Document governing combination                              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: FLEXURAL DESIGN                                        │
│  ├─ Retrieve NBCC flexural provisions                           │
│  ├─ Calculate required steel area As                            │
│  ├─ Check minimum/maximum reinforcement                         │
│  ├─ Select bar arrangement (e.g., 4-25M)                        │
│  └─ Verify moment resistance Mr ≥ Mf                            │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: SHEAR DESIGN                                           │
│  ├─ Retrieve NBCC shear provisions                              │
│  ├─ Calculate concrete shear capacity Vc                        │
│  ├─ Design stirrups if Vf > Vc                                  │
│  ├─ Check spacing limits (≤0.7dv, ≤600mm)                      │
│  └─ Verify minimum shear reinforcement                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: SERVICEABILITY CHECK                                   │
│  ├─ Retrieve NBCC serviceability provisions                     │
│  ├─ Check span-to-depth ratio (L/d ≤ 20 for simple support)    │
│  ├─ Verify deflection control                                   │
│  └─ Signal iteration if depth increase needed                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: DESIGN REVIEW                                          │
│  ├─ Validate consistency across all stages                      │
│  ├─ Check NBCC compliance                                       │
│  ├─ Identify unsafe assumptions                                 │
│  ├─ Verify constructability                                     │
│  └─ APPROVE or REQUEST CORRECTIONS                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Key Features

### ✅ **Code Compliance**
- All design decisions referenced to specific NBCC clauses
- Resistance factors properly applied (φc=0.65, φs=0.85)
- Load combinations per NBCC 4.1.3.2

### ✅ **Safety Checks**
- Minimum reinforcement (ductility)
- Maximum reinforcement (prevent brittle failure)
- Shear capacity verification
- Serviceability limits (deflection control)

### ✅ **Practical Design**
- Realistic bar selections (e.g., 3-25M, 4-20M)
- Constructible stirrup spacing
- Proper concrete cover requirements

### ✅ **Auditability**
- Clear separation: agents interpret, engine calculates
- NBCC agent never performs calculations
- All results traceable to code provisions

---

## 📚 NBCC Code Coverage

The system implements the following NBCC clauses:

| Clause | Topic | Implementation |
|--------|-------|----------------|
| 4.1.3.2 | Load Combinations (ULS) | 3 combinations for D+L+S |
| 8.4.2 | Resistance Factors | φc=0.65, φs=0.85 |
| 10.5 | Flexural Design | Rectangular stress block, min/max steel |
| 11.3 | Shear Design | Concrete capacity, stirrup design |
| 9.8 | Serviceability | Span-to-depth ratios, deflection limits |
| 7.4 | Concrete Cover | Minimum cover requirements |
| 7.7 | Bar Spacing | Clear spacing, crack control |

---

## 🎯 Design Output

The system produces a comprehensive report including:

1. **Load Analysis Report**
   - Governing NBCC load combination
   - Factored loads (kN/m)
   - Maximum moment Mf (kN·m)
   - Maximum shear Vf (kN)

2. **Flexural Design Report**
   - Required steel area As (mm²)
   - Selected bar arrangement
   - Provided steel area (mm²)
   - Moment resistance Mr (kN·m)
   - Min/max reinforcement checks

3. **Shear Design Report**
   - Concrete shear capacity Vc (kN)
   - Stirrup size and spacing
   - Shear resistance verification
   - Spacing limit checks

4. **Serviceability Report**
   - Span-to-depth ratio check
   - NBCC limit comparison
   - PASS/FAIL status
   - Recommendations

5. **Design Review**
   - Consistency validation
   - Code compliance confirmation
   - Safety assessment
   - Final approval status

---

## ⚙️ Configuration

### Beam Parameters

```python
{
    'span': float,              # Beam span (m)
    'dead_load': float,         # Dead load (kN/m)
    'live_load': float,         # Live load (kN/m)
    'snow_load': float,         # Snow load (kN/m)
    'width': int,               # Beam width (mm)
    'depth': int,               # Beam depth (mm)
    'fc_prime': int,            # Concrete strength (MPa)
    'fy': int,                  # Steel yield strength (MPa)
    'cover': int,               # Concrete cover (mm)
    'support_condition': str    # "simply supported", "one end continuous", 
                                # "both ends continuous"
}
```

### Support Conditions & L/d Limits

| Support Condition | NBCC L/d Limit |
|-------------------|----------------|
| Simply Supported | 20 |
| One End Continuous | 24 |
| Both Ends Continuous | 26 |
| Cantilever | 8 |

---

## 🧪 Testing

Run the example design:

```bash
python beam_design.py
```

**Expected Output**: Complete design report for a 6m beam with:
- Load combinations analysis
- Flexural reinforcement selection
- Shear stirrup design
- Serviceability verification
- Final design review

---

## 🛠️ Calculation Engine API

The `calculation_engine.py` module provides pure calculation functions:

```python
from calculation_engine import BeamCalculations

# Apply load combinations
load_results = BeamCalculations.apply_load_combinations(
    dead_load=10.0, live_load=5.0, snow_load=2.0
)

# Calculate bending moment
moment_results = BeamCalculations.calculate_bending_moment(
    span=6.0, load_combination='ULS-1', 
    dead_load=10.0, live_load=5.0, snow_load=2.0
)

# Design flexural reinforcement
flexural_results = BeamCalculations.design_flexural_reinforcement(
    Mf=90.0, b=300, d=450, fc_prime=30, fy=400
)

# Design shear reinforcement
shear_results = BeamCalculations.design_shear_reinforcement(
    Vf=67.5, b=300, d=450, fc_prime=30, fy=400
)

# Check serviceability
serviceability_results = BeamCalculations.check_serviceability(
    span_mm=6000, depth_mm=500, support_condition='simply supported'
)
```

---

## 💰 Cost Estimation

**Approximate Costs per Design Run** (using GPT-3.5-turbo):

- **Input Tokens**: ~3,000 tokens ($0.0015)
- **Output Tokens**: ~5,000 tokens ($0.010)
- **Total per Run**: ~$0.012 - $0.020

**Cost Optimization Tips**:
1. Use `verbose=False` in production to reduce logging tokens
2. Cache NBCC code retrieval results for repeated designs
3. Consider using smaller models for specific agents

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution**: Ensure `.env` file exists with valid API key:
```bash
OPENAI_API_KEY=sk-...your-key...
```

### Issue: Agents not executing tasks
**Solution**: Verify `Process.sequential` is used (not `Process.hierarchical`)

### Issue: NBCC tool returns "Query not recognized"
**Solution**: Use specific queries like "load combinations", "flexural design", "shear provisions"

### Issue: High token usage
**Solution**: 
- Set `verbose=False` in agent definitions
- Use more specific task descriptions
- Cache NBCC retrieval results

---

## 🔮 Future Enhancements

- [ ] Support for continuous beams (multi-span)
- [ ] T-beam and L-beam sections
- [ ] Prestressed concrete design
- [ ] Integration with actual NBCC corpus (RAG system)
- [ ] 3D visualization of reinforcement
- [ ] Export to CAD/BIM formats
- [ ] Cost optimization module
- [ ] Seismic design provisions

---

## 📖 References

- **NBCC**: National Building Code of Canada (latest edition)
- **CrewAI**: https://docs.crewai.com
- **CSA A23.3**: Design of Concrete Structures

---

## 📝 License

This project is for educational and professional use. Ensure all designs are reviewed by licensed professional engineers before construction.

---

## 👨‍💻 Author

Developed using CrewAI multi-agent framework for structural engineering applications.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional NBCC clauses
- More support conditions
- Advanced analysis features
- Integration with structural analysis software

---

**⚠️ IMPORTANT DISCLAIMER**: This system is a design aid tool. All structural designs must be reviewed and sealed by a licensed Professional Engineer before implementation. The system follows NBCC code provisions but does not replace professional engineering judgment.
