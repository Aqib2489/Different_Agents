# RAG-Based NBCC Retrieval System

## 🎯 Overview

The RC Beam Design System now uses **RAG (Retrieval-Augmented Generation)** for NBCC code retrieval. This means agents perform **semantic search** on actual code documents rather than using hardcoded responses.

---

## 🔄 How It Works

```
Agent Query: "What are the load combinations for ultimate limit states?"
     ↓
Vector Embedding: Convert query to embedding vector
     ↓
Semantic Search: Find most similar chunks in NBCC corpus
     ↓
Retrieve Top-K: Get 2-3 most relevant code sections
     ↓
Return to Agent: Formatted NBCC provisions with clause numbers
```

---

## 📊 Current Setup: Mock Corpus

**Default Mode**: The system starts with a **mock NBCC corpus** embedded in code.

**What's Included**:
- Clause 4.1.3.2 - Load Combinations
- Clause 8.4.2 - Resistance Factors  
- Clause 10.5 - Flexural Design
- Clause 11.3 - Shear Design
- Clause 9.8 - Serviceability
- Clause 7.4 - Concrete Cover
- Clause 7.7 - Bar Spacing
- Clause 12.10 - Development Length

**Why Mock First?**:
- ✅ Works immediately without external files
- ✅ Demonstrates RAG functionality
- ✅ Fast testing and development
- ✅ No copyright concerns

---

## 🚀 Upgrading to Real NBCC Documents

### Option 1: Load from PDF (Recommended)

If you have the NBCC PDF file:

```python
from nbcc_rag_system import initialize_nbcc_vectorstore

# Initialize from PDF (one-time setup)
vectorstore = initialize_nbcc_vectorstore(
    source="pdf",
    pdf_path="path/to/NBCC_2020.pdf",
    persist_dir="./nbcc_vectorstore"
)

# Vector store is now saved to disk
# Subsequent runs will load from persist_dir automatically
```

**Steps**:
1. Obtain official NBCC PDF (purchase from NRC)
2. Place PDF in project directory
3. Run initialization script (see `setup_nbcc_pdf.py` below)
4. System automatically loads PDF, chunks it, creates embeddings
5. Vector store persists to disk for future use

### Option 2: Load from Text Corpus

If you have NBCC organized as text files:

```
nbcc_corpus/
├── clause_4.1.3.2_load_combinations.txt
├── clause_8.4.2_resistance_factors.txt
├── clause_10.5_flexural_design.txt
└── ... (organized by clause)
```

```python
vectorstore = initialize_nbcc_vectorstore(
    source="text_corpus",
    corpus_dir="./nbcc_corpus",
    persist_dir="./nbcc_vectorstore"
)
```

---

## 🛠️ Setup Script for PDF

Create `setup_nbcc_pdf.py` in your project:

```python
"""
One-time setup script to load NBCC PDF into vector store.
Run this after obtaining the official NBCC PDF.
"""

from nbcc_rag_system import initialize_nbcc_vectorstore
import os

# Path to your NBCC PDF
NBCC_PDF_PATH = "NBCC_2020_Volume_1_Division_B.pdf"

if not os.path.exists(NBCC_PDF_PATH):
    print(f"ERROR: PDF not found at {NBCC_PDF_PATH}")
    print("Please:")
    print("1. Obtain NBCC PDF from National Research Council Canada")
    print("2. Place it in the project root directory")
    print("3. Update NBCC_PDF_PATH in this script")
    exit(1)

print("="*80)
print("NBCC PDF VECTORIZATION")
print("="*80)
print(f"\nProcessing: {NBCC_PDF_PATH}")
print("This will:")
print("- Load PDF pages")
print("- Chunk text intelligently")
print("- Create embeddings (using OpenAI)")
print("- Store in ./nbcc_vectorstore")
print("\nThis may take 5-15 minutes depending on PDF size...")
print("="*80 + "\n")

# Initialize vector store from PDF
vectorstore = initialize_nbcc_vectorstore(
    source="pdf",
    pdf_path=NBCC_PDF_PATH,
    persist_dir="./nbcc_vectorstore"
)

print("\n" + "="*80)
print("✓ SUCCESS! NBCC vector store created")
print("="*80)
print("\nThe vector store is now saved to ./nbcc_vectorstore")
print("Future runs will automatically load from this location.")
print("\nYou can now run: python beam_design.py")
print("="*80)
```

**Run once**:
```bash
python setup_nbcc_pdf.py
```

---

## 🔍 How Agents Use RAG

When an agent needs NBCC information:

```python
# Agent task description includes:
"STEPS:
1. Use the NBCC Code Retrieval tool to get load combination requirements
2. Document all NBCC load combinations with their factors
..."

# Behind the scenes:
# 1. Agent calls: nbcc_tool._run("load combinations for ultimate limit states")
# 2. Tool performs semantic search on vector store
# 3. Returns top 2-3 most relevant code sections
# 4. Agent reads actual NBCC text and applies it
```

**Example Query → Retrieval**:

```
Query: "minimum reinforcement requirements for flexural members"

Retrieved Results:
┌─────────────────────────────────────────────────────────────┐
│ Result 1 (Relevance: 94.3%)                                 │
│ NBCC Clause: 10.5.4                                         │
│                                                              │
│ 10.5.4 - Minimum Reinforcement Requirement:                 │
│ As,min = maximum of:                                         │
│   - 0.2√fc' × b × d / fy                                    │
│   - 1.4 × b × d / fy                                        │
│                                                              │
│ This ensures ductile behavior and prevents sudden           │
│ brittle failure.                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Vector Store Persistence

**First Run** (with mock corpus):
- Creates embeddings for mock documents
- Saves to `./nbcc_vectorstore/` directory
- ~50 KB disk space

**First Run** (with real PDF):
- Loads PDF (may be 10-50 MB)
- Chunks into ~500-2000 segments
- Creates embeddings via OpenAI API (~$0.10-0.50 cost)
- Saves to `./nbcc_vectorstore/` directory
- ~5-20 MB disk space

**Subsequent Runs**:
- Loads from `./nbcc_vectorstore/` instantly
- No re-embedding needed
- No API costs for retrieval

---

## 🧪 Testing the RAG System

Run the test script:

```bash
python nbcc_rag_system.py
```

**Expected Output**:
```
================================================================================
TESTING NBCC RAG SYSTEM
================================================================================
✓ Mock NBCC vector store created

================================================================================
QUERY: What are the NBCC load combinations for ultimate limit states?
================================================================================

--- Result 1 (Relevance: 0.923) ---
Clause: 4.1.3.2

NBCC Clause 4.1.3.2 - Principal Load Combinations...
[Full clause text]

--- Result 2 (Relevance: 0.856) ---
Clause: 8.4.2
[Related provisions]
```

---

## 📈 RAG vs Keyword Matching

| Feature | Keyword (Old) | RAG (New) |
|---------|---------------|-----------|
| **Search Method** | Exact keyword match | Semantic similarity |
| **Query Flexibility** | Rigid phrases | Natural language |
| **Relevance** | Binary (match/no match) | Scored by similarity |
| **Expansion** | Manual code updates | Add documents to corpus |
| **Understanding** | No context | Understands intent |

**Example**:

```
Query: "How much stirrup spacing is allowed?"

Keyword Method:
- Searches for: "stirrup" AND "spacing"
- May miss: "maximum spacing of shear reinforcement"

RAG Method:
- Understands: User wants shear reinforcement limits
- Retrieves: Clause 11.3.6 (even if words don't match exactly)
- Ranks by semantic relevance
```

---

## 🎓 Advanced Configuration

### Customize Chunking Strategy

```python
from nbcc_rag_system import NBCCVectorStore

vectorstore = NBCCVectorStore(persist_directory="./nbcc_vectorstore")

# Custom chunking for better code structure preservation
vectorstore.load_from_pdf(
    pdf_path="NBCC_2020.pdf",
    chunk_size=1500,      # Larger chunks preserve context
    chunk_overlap=300     # More overlap catches clause boundaries
)
```

### Adjust Retrieval Parameters

```python
# Return more results for comprehensive coverage
results = vectorstore.search(query, k=5)  # Top 5 instead of 3

# Search by specific clause number
content = vectorstore.search_by_clause("10.5.3")
```

### Filter by Metadata

Future enhancement - filter results by:
- Chapter/Division
- Topic category
- Clause hierarchy

---

## 🔐 Data Privacy & Licensing

**Important Notes**:
1. **NBCC Copyright**: NBCC is copyrighted by National Research Council Canada
2. **License Required**: Purchase official NBCC copy for commercial use
3. **Vector Store**: Embeddings are derivative works - check license terms
4. **Mock Corpus**: Simplified provisions for demonstration only

**For Production**:
- Obtain proper NBCC license
- Verify compliance with NRC terms of use
- Consider on-premise deployment if sharing restrictions apply

---

## 🐛 Troubleshooting

### "Vector store not initialized"
**Solution**: Run setup script or let system create mock corpus

### "langchain dependencies not installed"
**Solution**: 
```bash
pip install langchain langchain-openai langchain-community chromadb pypdf
```

### "OpenAI API key not found"
**Solution**: Ensure `.env` file contains `OPENAI_API_KEY`

### RAG returns irrelevant results
**Solution**: 
- Improve query specificity
- Increase chunk overlap during PDF loading
- Add more context to agent task descriptions

### High embedding costs
**Solution**:
- Embeddings are one-time cost during setup
- Retrieval has no API cost (uses local vectors)
- Typical cost: $0.10-0.50 for full NBCC PDF

---

## 📊 Cost Breakdown

### One-Time Setup (PDF Vectorization)
- **Text Extraction**: Free (pypdf)
- **Embeddings**: ~$0.10-0.50 (depends on PDF length)
  - text-embedding-3-small: $0.00002/1K tokens
  - NBCC ~200-500 pages → 500K-1M tokens → $0.10-0.20
- **Storage**: ~5-20 MB local disk

### Runtime (Per Design)
- **Query Embedding**: ~$0.00001 per query
- **Vector Search**: Free (local computation)
- **Agent Token Usage**: Same as before (~$0.012-0.020)

**Total Impact**: Negligible (~$0.0001 per design run)

---

## 🚀 Next Steps

1. **Test Mock System**: Run `python nbcc_rag_system.py`
2. **Test Integration**: Run `python beam_design.py` (uses RAG automatically)
3. **Upgrade to PDF**: Obtain NBCC PDF and run setup script
4. **Verify Results**: Check that agents retrieve relevant clauses

---

## 📚 References

- **LangChain**: https://python.langchain.com/docs/
- **ChromaDB**: https://www.trychroma.com/
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **NBCC**: https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications

---

**✨ Your system now has REAL semantic search on NBCC code provisions!**

Agents no longer rely on hardcoded responses - they retrieve actual code sections based on semantic similarity to their queries.
