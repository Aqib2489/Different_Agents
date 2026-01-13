"""
RAG-based NBCC Code Retrieval System
Uses vector embeddings and semantic search to retrieve actual NBCC provisions.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
import json

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document
except ImportError:
    print("Warning: langchain dependencies not installed. Install with: pip install langchain langchain-openai langchain-community chromadb pypdf")


class NBCCVectorStore:
    """
    Vector store for NBCC code documents.
    Handles document loading, chunking, embedding, and retrieval.
    """
    
    def __init__(self, persist_directory: str = "./nbcc_vectorstore"):
        """
        Initialize NBCC vector store.
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = None
        
        # Try to load existing vectorstore
        if os.path.exists(persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings
                )
                print(f"✓ Loaded existing NBCC vector store from {persist_directory}")
            except Exception as e:
                print(f"Warning: Could not load existing vectorstore: {e}")
    
    def load_from_pdf(self, pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Load NBCC code from PDF file and create vector embeddings.
        
        Args:
            pdf_path: Path to NBCC PDF file
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"Loading NBCC PDF from {pdf_path}...")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        print(f"Loaded {len(documents)} pages. Chunking text...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(chunks)} chunks. Creating embeddings...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Vector store created with {len(chunks)} chunks")
        return len(chunks)
    
    def load_from_text_corpus(self, corpus_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Load NBCC code from text files organized by clause.
        
        Args:
            corpus_dir: Directory containing NBCC text files
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        if not os.path.exists(corpus_dir):
            raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")
        
        documents = []
        for file_path in Path(corpus_dir).rglob("*.txt"):
            loader = TextLoader(str(file_path))
            docs = loader.load()
            # Add metadata about file/clause
            for doc in docs:
                doc.metadata["source_file"] = file_path.name
                doc.metadata["clause"] = file_path.stem
            documents.extend(docs)
        
        if not documents:
            raise ValueError(f"No text files found in {corpus_dir}")
        
        print(f"Loaded {len(documents)} text files. Chunking...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(chunks)} chunks. Creating embeddings...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Vector store created with {len(chunks)} chunks")
        return len(chunks)
    
    def load_from_mock_corpus(self):
        """
        Create vector store from mock NBCC corpus (for development/testing).
        """
        print("Creating mock NBCC corpus for testing...")
        
        # Create mock documents based on hardcoded knowledge
        mock_documents = [
            Document(
                page_content="""
NBCC Clause 4.1.3.2 - Principal Load Combinations for Ultimate Limit States

The following load combinations shall be considered for ultimate limit states:

1. Combination 1 (Dead + Live + Snow):
   Factored Load = 1.4D + 1.5L + 0.5S
   - Dead Load Factor: 1.4
   - Live Load Factor: 1.5
   - Snow Load Factor: 0.5

2. Combination 2 (Dead + Live dominant):
   Factored Load = 1.25D + 1.5L + 0.5S
   - Dead Load Factor: 1.25
   - Live Load Factor: 1.5
   - Snow Load Factor: 0.5

3. Combination 3 (Dead + Snow dominant):
   Factored Load = 1.25D + 0.5L + 1.5S
   - Dead Load Factor: 1.25
   - Live Load Factor: 0.5
   - Snow Load Factor: 1.5

The governing combination shall be the one producing maximum effects (moment, shear, etc.).
                """,
                metadata={"clause": "4.1.3.2", "topic": "load_combinations"}
            ),
            Document(
                page_content="""
NBCC Clause 8.4.2 - Material Resistance Factors

The following resistance factors (φ) shall be used in design:

1. Concrete in flexure and axial compression:
   φc = 0.65

2. Concrete in bearing:
   φc = 0.60

3. Reinforcing steel in tension and compression:
   φs = 0.85

4. Prestressing steel:
   φp = 0.90

Application: Factored Resistance = φ × Nominal Resistance

These factors account for material variability and workmanship quality.
                """,
                metadata={"clause": "8.4.2", "topic": "resistance_factors"}
            ),
            Document(
                page_content="""
NBCC Clause 10.5 - Flexural Design of Reinforced Concrete Beams

10.5.1 - Design Assumptions:
- Plane sections remain plane (linear strain distribution)
- Maximum concrete compressive strain = 0.0035
- Tensile strength of concrete is neglected
- Stress-strain relationships follow recognized models

10.5.2 - Rectangular Stress Block Parameters:
- α1 = 0.85 - 0.0015 × fc' ≥ 0.67 (stress block intensity factor)
- β1 = 0.97 - 0.0025 × fc' ≥ 0.67 (stress block depth factor)
- a = β1 × c (equivalent rectangular stress block depth)

10.5.3 - Factored Moment Resistance:
Mr = φs × As × fy × (d - a/2)

Where:
- As = area of tension reinforcement (mm²)
- fy = yield strength of reinforcement (MPa)
- d = effective depth from compression face to centroid of tension steel (mm)
- a = depth of equivalent rectangular stress block (mm)

10.5.4 - Minimum Reinforcement Requirement:
As,min = maximum of:
  - 0.2√fc' × b × d / fy
  - 1.4 × b × d / fy

This ensures ductile behavior and prevents sudden brittle failure.

10.5.5 - Maximum Reinforcement for Ductility:
To ensure ductile failure mode (steel yields before concrete crushes):
ρ ≤ 0.75 × ρb

Where ρ is the reinforcement ratio and ρb is the balanced reinforcement ratio.
                """,
                metadata={"clause": "10.5", "topic": "flexural_design"}
            ),
            Document(
                page_content="""
NBCC Clause 11.3 - Shear Design in Beams and One-Way Slabs

11.3.3 - Concrete Shear Resistance:
The factored shear resistance of concrete without shear reinforcement:

Vc = φc × 0.2 × λ × √fc' × bw × dv

Where:
- φc = 0.65 (resistance factor for concrete)
- λ = 1.0 for normal density concrete
- fc' = specified compressive strength of concrete (MPa)
- bw = width of web (mm)
- dv = effective shear depth, may be taken as 0.9d (mm)

11.3.4 - Requirement for Shear Reinforcement:
Shear reinforcement is required when: Vf > Vc

Where Vf is the factored shear force at the section.

11.3.5 - Design of Shear Reinforcement:
The required shear resistance provided by reinforcement:

Vs = Vf - Vc

For vertical stirrups:
Vs = (Av × fy × dv) / s

Where:
- Av = area of shear reinforcement within spacing s (mm²)
- fy = yield strength of shear reinforcement (MPa)
- s = spacing of shear reinforcement (mm)

Solving for spacing: s = (Av × fy × dv) / Vs

11.3.6 - Maximum Spacing of Shear Reinforcement:
The spacing shall not exceed:
- s ≤ 0.7 × dv
- s ≤ 600 mm

11.3.7 - Minimum Shear Reinforcement:
When Vf > 0.5 × Vc, minimum shear reinforcement shall be provided:

Av,min / s = 0.06 × √fc' × bw / fy
                """,
                metadata={"clause": "11.3", "topic": "shear_design"}
            ),
            Document(
                page_content="""
NBCC Clause 9.8 - Deflection Control and Serviceability

9.8.2 - Minimum Thickness (Span-to-Depth Ratios):
For members not supporting or attached to partitions likely to be damaged by large deflections:

1. Simply Supported Beams:
   L/d ≤ 20

2. One End Continuous:
   L/d ≤ 24

3. Both Ends Continuous:
   L/d ≤ 26

4. Cantilever:
   L/d ≤ 8

Where:
- L = span length (mm)
- d = effective depth (mm)

9.8.3 - Maximum Permissible Computed Deflections:
- Long-term deflection after attachment of non-structural elements: L/240
- Deflection occurring after attachment of non-structural elements: L/480

9.8.4 - Control of Cracking:
Distribution of flexural reinforcement at tension face:
Maximum spacing of reinforcement:

s ≤ 15(1000/fs) - 2.5cc
but not greater than: s ≤ 11(1000/fs)

Where:
- s = center-to-center spacing of reinforcement (mm)
- fs = calculated tensile stress in reinforcement at service loads (MPa)
- cc = clear cover from nearest surface in tension to surface of flexural reinforcement (mm)
                """,
                metadata={"clause": "9.8", "topic": "serviceability"}
            ),
            Document(
                page_content="""
NBCC Clause 7.4 - Concrete Cover Requirements

7.4.1 - Minimum Cover for Cast-in-Place Concrete:

For formed surfaces:
- Exposed to weather or ground: 40 mm minimum
- Not exposed to weather (interior): 30 mm minimum

For unformed surfaces (slabs, walls):
- Exposed to weather or ground: 20 mm minimum

Additional requirements:
- Clear cover shall not be less than 1.5 times the maximum nominal aggregate size
- For corrosive environments, increased cover may be required
- Cover measured to outermost surface of reinforcement

Protection against corrosion and fire resistance depends on adequate concrete cover.
                """,
                metadata={"clause": "7.4", "topic": "concrete_cover"}
            ),
            Document(
                page_content="""
NBCC Clause 7.7 - Spacing of Reinforcement

7.7.1 - Minimum Clear Spacing Between Parallel Bars:
The minimum clear spacing between parallel bars in a layer shall be the greatest of:
- 1.4 times the bar diameter
- 1.4 times the maximum aggregate size
- 30 mm

This ensures proper concrete consolidation around reinforcement.

7.7.2 - Maximum Spacing for Crack Control:
For flexural members, spacing of reinforcement closest to the tension face:

s ≤ 500 × (280/fs)

Where:
- s = spacing between bars (mm)
- fs = stress in reinforcement at service loads (MPa)

For estimating fs at service loads:
fs ≈ (2/3) × fy × (service moment / factored moment)
                """,
                metadata={"clause": "7.7", "topic": "bar_spacing"}
            ),
            Document(
                page_content="""
NBCC Clause 12.10 - Development and Lap Splices of Reinforcement

12.10.1 - Tension Development Length:
The basic development length for deformed bars in tension:

ld = 0.45 × k1 × k2 × k3 × k4 × (fy / √fc') × db

Where:
- k1 = bar location factor (1.3 for horizontal bars with > 300mm fresh concrete below, 1.0 otherwise)
- k2 = coating factor (1.5 for epoxy-coated bars with cover < 3db, 1.2 for other epoxy-coated, 1.0 for uncoated)
- k3 = concrete density factor (1.0 for normal density, 1.3 for structural low density)
- k4 = bar size factor (0.8 for 20M and smaller bars, 1.0 for 25M and larger)
- fy = yield strength of reinforcement (MPa)
- fc' = specified concrete strength (MPa)
- db = nominal bar diameter (mm)

12.10.2 - Lap Splices in Tension:
Minimum lap length = 1.3 × ld for Class A splices (≤ 50% of bars spliced at one location)
Minimum lap length = 1.7 × ld for Class B splices (> 50% of bars spliced at one location)

Lap splices shall not be used for bars larger than 35M in tension.
                """,
                metadata={"clause": "12.10", "topic": "development_length"}
            )
        ]
        
        print(f"Creating embeddings for {len(mock_documents)} mock documents...")
        self.vectorstore = Chroma.from_documents(
            documents=mock_documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Mock NBCC vector store created")
        return len(mock_documents)
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """
        Perform semantic search on NBCC corpus.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load documents first.")
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(1 - score)  # Convert distance to similarity
            })
        
        return formatted_results
    
    def search_by_clause(self, clause_number: str) -> Optional[str]:
        """
        Search for specific NBCC clause by number.
        
        Args:
            clause_number: NBCC clause number (e.g., "10.5.3")
            
        Returns:
            Content of the clause if found
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load documents first.")
        
        # Search with clause number as query
        results = self.vectorstore.similarity_search(f"NBCC Clause {clause_number}", k=1)
        
        if results:
            return results[0].page_content
        return None


def initialize_nbcc_vectorstore(
    source: str = "mock",
    pdf_path: Optional[str] = None,
    corpus_dir: Optional[str] = None,
    persist_dir: str = "./nbcc_vectorstore"
) -> NBCCVectorStore:
    """
    Initialize NBCC vector store from various sources.
    
    Args:
        source: Source type - "mock", "pdf", or "text_corpus"
        pdf_path: Path to NBCC PDF (if source="pdf")
        corpus_dir: Path to text corpus directory (if source="text_corpus")
        persist_dir: Directory to persist vector database
        
    Returns:
        Initialized NBCCVectorStore
    """
    vectorstore = NBCCVectorStore(persist_directory=persist_dir)
    
    # Check if already exists
    if vectorstore.vectorstore is not None:
        print("Using existing vector store")
        return vectorstore
    
    # Create new vectorstore based on source
    if source == "mock":
        vectorstore.load_from_mock_corpus()
    elif source == "pdf":
        if not pdf_path:
            raise ValueError("pdf_path required when source='pdf'")
        vectorstore.load_from_pdf(pdf_path)
    elif source == "text_corpus":
        if not corpus_dir:
            raise ValueError("corpus_dir required when source='text_corpus'")
        vectorstore.load_from_text_corpus(corpus_dir)
    else:
        raise ValueError(f"Unknown source type: {source}")
    
    return vectorstore


# Test the system
if __name__ == "__main__":
    # Initialize with mock corpus
    print("="*80)
    print("TESTING NBCC RAG SYSTEM")
    print("="*80)
    
    vectorstore = initialize_nbcc_vectorstore(source="mock")
    
    # Test queries
    test_queries = [
        "What are the NBCC load combinations for ultimate limit states?",
        "resistance factors for concrete and steel",
        "minimum reinforcement requirements for beams",
        "shear design provisions and stirrup spacing",
        "span to depth ratio for simply supported beams"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")
        
        results = vectorstore.search(query, k=2)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} (Relevance: {result['relevance_score']:.3f}) ---")
            print(f"Clause: {result['metadata'].get('clause', 'N/A')}")
            print(f"\n{result['content'][:500]}...")
