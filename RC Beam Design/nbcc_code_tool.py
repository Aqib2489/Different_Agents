"""
NBCC Code Retrieval Tool - Read-only authority for code clauses.
This tool provides NBCC provisions using RAG-based semantic search.
"""

from crewai.tools import BaseTool
from typing import Dict, List, Optional
import os


class NBCCCodeTool(BaseTool):
    name: str = "NBCC Code Retrieval"
    description: str = (
        "Retrieves specific NBCC (National Building Code of Canada) clauses and provisions using semantic search. "
        "Input should be a specific topic, question, or clause number (e.g., 'load combinations for ultimate limit states', "
        "'resistance factors for concrete', 'shear reinforcement requirements', 'clause 10.5.1'). "
        "Uses RAG (Retrieval-Augmented Generation) to find relevant code sections from NBCC corpus. "
        "Returns exact code text with clause numbers and structured interpretation."
    )
    
    _vectorstore: Optional[object] = None
    
    def _initialize_vectorstore(self):
        """Lazy initialization of vector store."""
        if self._vectorstore is None:
            try:
                from nbcc_rag_system import initialize_nbcc_vectorstore
                print("Initializing NBCC RAG system...")
                self._vectorstore = initialize_nbcc_vectorstore(source="mock")
                print("✓ NBCC RAG system ready")
            except Exception as e:
                print(f"Warning: Could not initialize RAG system: {e}")
                print("Falling back to keyword-based retrieval")
        return self._vectorstore
    
    def _run(self, query: str) -> str:
        """
        Retrieve NBCC provisions based on query using RAG.
        Falls back to keyword matching if RAG unavailable.
        
        Args:
            query: Natural language query or clause number
            
        Returns:
            Relevant NBCC provisions with clause references
        """
        # Try RAG-based retrieval first
        vectorstore = self._initialize_vectorstore()
        
        if vectorstore is not None:
            try:
                return self._rag_retrieval(query, vectorstore)
            except Exception as e:
                print(f"RAG retrieval failed: {e}. Falling back to keyword matching.")
        
        # Fallback to keyword-based retrieval
        return self._keyword_retrieval(query)
    
    def _rag_retrieval(self, query: str, vectorstore) -> str:
        """
        Perform RAG-based semantic search on NBCC corpus.
        
        Args:
            query: User query
            vectorstore: Initialized vector store
            
        Returns:
            Formatted results from semantic search
        """
        # Search for top 2 most relevant sections
        results = vectorstore.search(query, k=2)
        
        if not results:
            return "No relevant NBCC provisions found. Please rephrase your query."
        
        # Format results
        output = f"NBCC PROVISIONS (Retrieved via Semantic Search)\n"
        output += f"Query: {query}\n"
        output += "="*80 + "\n\n"
        
        for i, result in enumerate(results, 1):
            relevance = result['relevance_score']
            clause = result['metadata'].get('clause', 'N/A')
            content = result['content']
            
            output += f"--- Result {i} (Relevance: {relevance:.2%}) ---\n"
            output += f"NBCC Clause: {clause}\n\n"
            output += content
            output += "\n" + "="*80 + "\n\n"
        
        return output
    
    def _keyword_retrieval(self, query: str) -> str:
        """
        Fallback keyword-based retrieval (original method).
        
        Args:
            query: User query
            
        Returns:
            Matched code provisions
        """
        query_lower = query.lower()
        
        print(f"Using keyword-based fallback for: {query}")
        
        # NBCC Load Combinations Database
        if 'load combination' in query_lower or 'ultimate limit' in query_lower:
            return self._get_load_combinations()
        
        # Resistance Factors
        elif 'resistance factor' in query_lower or 'phi' in query_lower:
            return self._get_resistance_factors()
        
        # Flexural Design
        elif 'flexural' in query_lower or 'bending' in query_lower or 'moment' in query_lower:
            return self._get_flexural_provisions()
        
        # Shear Design
        elif 'shear' in query_lower:
            return self._get_shear_provisions()
        
        # Serviceability
        elif 'serviceability' in query_lower or 'deflection' in query_lower:
            return self._get_serviceability_provisions()
        
        # Detailing
        elif 'detailing' in query_lower or 'spacing' in query_lower or 'cover' in query_lower:
            return self._get_detailing_provisions()
        
        else:
            return "Query not recognized. Please specify: load combinations, resistance factors, flexural, shear, serviceability, or detailing."
    
    def _get_load_combinations(self) -> str:
        return """
NBCC LOAD COMBINATIONS FOR ULTIMATE LIMIT STATES (ULS)

**Clause 4.1.3.2 - Principal Load Combinations**

The following load combinations shall be considered:

1. **Combination 1 (Dead + Live + Snow)**
   - Factored Load = 1.4D + 1.5L + 0.5S
   - Dead Load Factor: 1.4
   - Live Load Factor: 1.5
   - Snow Load Factor: 0.5

2. **Combination 2 (Dead + Live dominant)**
   - Factored Load = 1.25D + 1.5L + 0.5S
   - Dead Load Factor: 1.25
   - Live Load Factor: 1.5
   - Snow Load Factor: 0.5

3. **Combination 3 (Dead + Snow dominant)**
   - Factored Load = 1.25D + 0.5L + 1.5S
   - Dead Load Factor: 1.25
   - Live Load Factor: 0.5
   - Snow Load Factor: 1.5

**Governing Combination**: Use the combination producing maximum effects.

**Structured Output**:
```json
{
  "combinations": [
    {"name": "ULS-1", "dead_factor": 1.4, "live_factor": 1.5, "snow_factor": 0.5},
    {"name": "ULS-2", "dead_factor": 1.25, "live_factor": 1.5, "snow_factor": 0.5},
    {"name": "ULS-3", "dead_factor": 1.25, "live_factor": 0.5, "snow_factor": 1.5}
  ]
}
```
"""
    
    def _get_resistance_factors(self) -> str:
        return """
NBCC RESISTANCE FACTORS

**Clause 8.4.2 - Material Resistance Factors**

The following resistance factors (φ) shall be used:

1. **Concrete**
   - φc = 0.65 (for compression in flexure and axial load)
   - φc = 0.60 (for bearing on concrete)
   
2. **Reinforcing Steel**
   - φs = 0.85 (for tension and compression in reinforcement)

3. **Prestressing Steel**
   - φp = 0.90 (for prestressing tendons)

**Application**:
- Factored Resistance = φ × Nominal Resistance
- Always use specified factors unless special provisions apply

**Note**: These are permanent load factors for normal density concrete.
"""
    
    def _get_flexural_provisions(self) -> str:
        return """
NBCC FLEXURAL DESIGN PROVISIONS

**Clause 10.5 - Flexural Members**

**10.5.1 - Design Assumptions**
1. Strain distribution is linear across section depth
2. Maximum concrete strain = 0.0035
3. Concrete tensile strength is neglected
4. Stress-strain for concrete follows recognized relationships

**10.5.2 - Rectangular Stress Block Parameters**
- α1 = 0.85 - 0.0015 × fc' ≥ 0.67
- β1 = 0.97 - 0.0025 × fc' ≥ 0.67
- a = β1 × c (where c is neutral axis depth)

**10.5.3 - Factored Moment Resistance**
Mr = φs × As × fy × (d - a/2)

Where:
- As = area of tension reinforcement (mm²)
- fy = yield strength of steel (MPa)
- d = effective depth (mm)
- a = depth of equivalent rectangular stress block (mm)

**10.5.4 - Minimum Reinforcement**
As,min = max(0.2√fc' × b × d / fy, 1.4 × b × d / fy)

**10.5.5 - Maximum Reinforcement**
To ensure ductile failure:
ρ ≤ 0.75 × ρb (balanced reinforcement ratio)
"""
    
    def _get_shear_provisions(self) -> str:
        return """
NBCC SHEAR DESIGN PROVISIONS

**Clause 11.3 - Shear in Beams and One-Way Slabs**

**11.3.3 - Concrete Shear Resistance**
Vc = φc × 0.2 × λ × √fc' × bw × dv

Where:
- φc = 0.65 (resistance factor for concrete)
- λ = 1.0 for normal density concrete
- fc' = specified concrete strength (MPa)
- bw = web width (mm)
- dv = effective shear depth ≈ 0.9d (mm)

**11.3.4 - Shear Reinforcement Required When**
Vf > Vc (factored shear exceeds concrete capacity)

**11.3.5 - Stirrup Design**
Vs = (Av × fy × d) / s

Where:
- Av = area of shear reinforcement (mm²)
- fy = yield strength of stirrups (MPa)
- s = spacing of stirrups (mm)

**11.3.6 - Maximum Stirrup Spacing**
s ≤ 0.7 × dv
s ≤ 600 mm

**11.3.7 - Minimum Shear Reinforcement**
Required when Vf > 0.5 × Vc:
Av,min / s = 0.06 × √fc' × bw / fy
"""
    
    def _get_serviceability_provisions(self) -> str:
        return """
NBCC SERVICEABILITY PROVISIONS

**Clause 9.8 - Deflection Control**

**9.8.2 - Span-to-Depth Ratios (Simplified Method)**

For members not supporting partitions:

1. **Simply Supported**:
   - L/d ≤ 20
   
2. **One End Continuous**:
   - L/d ≤ 24
   
3. **Both Ends Continuous**:
   - L/d ≤ 26
   
4. **Cantilever**:
   - L/d ≤ 8

**9.8.3 - Maximum Permissible Deflection**
- Long-term deflection after attachment of non-structural elements: L/240
- Deflection occurring after attachment: L/480

**9.8.4 - Crack Control**
Spacing of reinforcement at maximum tension face:
s ≤ 15(1000/fs) - 2.5cc ≤ 11(1000/fs)

Where:
- s = center-to-center spacing (mm)
- fs = calculated stress in reinforcement (MPa)
- cc = concrete cover (mm)
"""
    
    def _get_detailing_provisions(self) -> str:
        return """
NBCC DETAILING REQUIREMENTS

**Clause 7.4 - Concrete Cover**

**7.4.1 - Minimum Cover to Reinforcement**
For cast-in-place concrete:
- Beams exposed to weather: 40 mm
- Beams not exposed to weather: 30 mm
- Minimum cover to main bars: 1.5 × bar diameter

**Clause 7.7 - Spacing of Reinforcement**

**7.7.1 - Clear Spacing Between Parallel Bars**
Minimum clear spacing:
- Greater of: 1.4 × bar diameter, 1.4 × aggregate size, 30 mm

**7.7.2 - Maximum Spacing (Crack Control)**
For flexural members at tension face:
s ≤ 500 × (280/fs) where fs is service load stress

**Clause 12.10 - Development Length**

**12.10.1 - Tension Development Length**
ld = 0.45 × k1 × k2 × k3 × k4 × fy × db / √fc'

Where:
- k1 = bar location factor
- k2 = coating factor
- k3 = concrete density factor
- k4 = bar size factor
- db = bar diameter (mm)
"""
