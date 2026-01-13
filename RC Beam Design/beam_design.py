"""
RC Beam Design System using CrewAI
Multi-agent system for reinforced concrete beam design following NBCC code.
"""

import os
from crewai import Agent, Task, Crew, Process
from nbcc_code_tool import NBCCCodeTool
from utils import load_api_keys

# Load API keys
load_api_keys()

# Initialize NBCC code retrieval tool
nbcc_tool = NBCCCodeTool()


# ===========================
# AGENT DEFINITIONS
# ===========================

orchestrator_agent = Agent(
    role='Design Orchestrator',
    goal='Manage the RC beam design workflow and ensure all design aspects are covered systematically',
    backstory=(
        "You are an experienced structural engineering project manager who coordinates "
        "complex design tasks. You ensure proper sequence of design calculations, validate "
        "data flow between design stages, and handle iteration when serviceability requirements "
        "are not met. You NEVER perform calculations yourself - you delegate to specialized agents."
    ),
    verbose=True,
    allow_delegation=True,
    llm="gpt-4o"
)

load_agent = Agent(
    role='Load Analysis Engineer',
    goal='Determine factored loads using NBCC load combinations and prepare load cases for design',
    backstory=(
        "You are a structural engineer specializing in load analysis. You retrieve NBCC load "
        "combination requirements and apply them to determine governing factored loads. You MUST "
        "perform all calculations yourself - multiply the load factors by the given loads, then "
        "calculate moment (w*L²/8) and shear (w*L/2). You provide clear documentation with actual "
        "numerical results, not just formulas."
    ),
    verbose=True,
    tools=[nbcc_tool],
    llm="gpt-4o"
)

flexural_agent = Agent(
    role='Flexural Design Engineer',
    goal='Design longitudinal reinforcement for bending moment capacity following NBCC provisions',
    backstory=(
        "You are an expert in flexural design of concrete beams. You retrieve NBCC flexural "
        "design provisions and PERFORM all calculations yourself. Calculate effective depth (d = h - cover - bar_radius), "
        "required steel area using moment equilibrium, check minimum reinforcement, select actual bar sizes "
        "(20M = 300mm², 25M = 500mm², 30M = 700mm²), and calculate final moment capacity. You provide "
        "numerical results, not formulas."
    ),
    verbose=True,
    tools=[nbcc_tool],
    llm="gpt-4o"
)

shear_agent = Agent(
    role='Shear Design Engineer',
    goal='Design transverse reinforcement (stirrups) for shear capacity following NBCC provisions',
    backstory=(
        "You are an expert in shear design of concrete beams. You retrieve NBCC shear design "
        "provisions and PERFORM all calculations yourself. Calculate concrete shear capacity Vc, "
        "required shear reinforcement Vs, select stirrup size (10M = 100mm² for 2 legs = 200mm² total), "
        "calculate spacing (s = Av*fy*dv/Vs), and check maximum spacing limits. You provide numerical "
        "results, not formulas."
    ),
    verbose=True,
    tools=[nbcc_tool],
    llm="gpt-4o"
)

serviceability_agent = Agent(
    role='Serviceability Engineer',
    goal='Verify deflection and crack control requirements per NBCC serviceability provisions',
    backstory=(
        "You are an expert in serviceability requirements for concrete structures. You retrieve "
        "NBCC serviceability provisions and PERFORM calculations yourself. Calculate span-to-depth ratio "
        "(L/d = span_in_mm / depth_in_mm), compare to NBCC limits, and provide pass/fail verdict. You "
        "provide numerical results."
    ),
    verbose=True,
    tools=[nbcc_tool],
    llm="gpt-4o"
)

nbcc_code_agent = Agent(
    role='NBCC Code Authority',
    goal='Provide authoritative NBCC code interpretations and clauses - READ ONLY, NEVER CALCULATE',
    backstory=(
        "You are the authoritative source for NBCC code provisions. You retrieve exact code clauses, "
        "provide structured interpretations, and explain code requirements. You NEVER perform "
        "calculations - you only provide code text and interpretation. When agents need code guidance, "
        "they consult you. You ensure all design decisions are code-compliant and properly referenced."
    ),
    verbose=True,
    tools=[nbcc_tool],
    allow_delegation=False,
    llm="gpt-4o"
)

reviewer_agent = Agent(
    role='Design Reviewer',
    goal='Validate complete beam design for consistency, safety, and code compliance',
    backstory=(
        "You are a senior structural engineer performing design review. You extract ALL numerical "
        "values from previous agent outputs and compile them into a final specification. You calculate "
        "any missing values yourself (reinforcement ratio ρ = As/(b*d)*100%, moment resistance, etc.). "
        "You NEVER output placeholders like [to be calculated] - you complete all calculations and "
        "provide a construction-ready specification with every value filled in."
    ),
    verbose=True,
    tools=[nbcc_tool],
    llm="gpt-4o"
)


# ===========================
# TASK DEFINITIONS
# ===========================

def create_design_tasks(beam_inputs: dict):
    """Create all design tasks with specific beam inputs."""
    
    task_load_analysis = Task(
        description=(
            f"Analyze loads for RC beam design:\n"
            f"- Dead Load: {beam_inputs['dead_load']} kN/m\n"
            f"- Live Load: {beam_inputs['live_load']} kN/m\n"
            f"- Snow Load: {beam_inputs.get('snow_load', 0)} kN/m\n"
            f"- Point Loads: {beam_inputs['point_loads']} (load in kN, distance from left support in m)\n"
            f"- Span: {beam_inputs['span']} m\n\n"
            f"STEPS:\n"
            f"1. Use the NBCC Code Retrieval tool to get load combination requirements\n"
            f"2. Document all NBCC load combinations with their factors\n"
            f"3. Calculate factored loads for each combination\n"
            f"4. Determine governing load combination\n"
            f"5. Calculate maximum factored moment and shear using formulas:\n"
            f"   - For uniform load w over span L:\n"
            f"     * Maximum Moment Mf_uniform = w × L² / 8\n"
            f"     * Maximum Shear Vf_uniform = w × L / 2\n"
            f"   - For each point load P at distance 'a' from left support:\n"
            f"     * Moment at load point: M = P × a × (L - a) / L\n"
            f"     * Shear (left of load): V = P × (L - a) / L\n"
            f"   - TOTAL MOMENT = Mf_uniform + sum of all point load moments (use maximum)\n"
            f"   - TOTAL SHEAR = Vf_uniform + maximum point load shear\n\n"
            f"Provide clear output with:\n"
            f"- Governing combination name and factors\n"
            f"- Factored uniform load (kN/m)\n"
            f"- Factored point loads (kN) and their contributions\n"
            f"- Maximum factored moment Mf (kN·m)\n"
            f"- Maximum factored shear Vf (kN)\n"
            f"- NBCC clause references"
        ),
        expected_output=(
            "You MUST calculate and output actual numerical values. DO NOT output placeholders like [value] or [name].\n\n"
            "EXAMPLE CORRECT OUTPUT:\n"
            "GOVERNING LOAD COMBINATION: 1.4D + 1.5L\n"
            "FACTORED UNIFORM LOAD: 24.5 kN/m\n"
            "FACTORED POINT LOADS: 70 kN at 2.0m, 45 kN at 4.0m\n"
            "MOMENT FROM UNIFORM LOAD: 110.25 kN·m\n"
            "MOMENT FROM POINT LOADS: 85.0 kN·m\n"
            "MAXIMUM MOMENT (Mf): 195.25 kN·m\n"
            "MAXIMUM SHEAR (Vf): 98.5 kN\n"
            "NBCC REFERENCE: Clause 4.1.3.2\n\n"
            "OUTPUT YOUR CALCULATED VALUES IN THIS EXACT FORMAT with real numbers."
        ),
        agent=load_agent
    )
    
    task_flexural_design = Task(
        description=(
            f"Design flexural reinforcement for RC beam:\n"
            f"- Beam width: {beam_inputs['width']} mm\n"
            f"- Beam depth: {beam_inputs['depth']} mm\n"
            f"- Concrete strength fc': {beam_inputs['fc_prime']} MPa\n"
            f"- Steel yield strength fy: {beam_inputs['fy']} MPa\n"
            f"- Concrete cover: {beam_inputs.get('cover', 40)} mm\n\n"
            f"STEPS:\n"
            f"1. Use NBCC Code Retrieval tool to get flexural design provisions\n"
            f"2. Extract factored moment Mf from load analysis results\n"
            f"3. Calculate effective depth d (d = depth - cover - assumed bar radius)\n"
            f"4. Calculate balanced reinforcement ratio: ρb = 0.85 × β1 × fc' / fy × (700 / (700 + fy))\n"
            f"5. Calculate maximum tension steel ratio for ductility: ρ_max = 0.75 × ρb\n"
            f"6. Calculate maximum moment capacity (singly reinforced):\n"
            f"   As_max = ρ_max × b × d\n"
            f"   Mr_max = φs × As_max × fy × (d - a_max/2)  [where a_max = As_max × fy / (0.85 × α1 × fc' × b)]\n"
            f"7. CHECK: If Mf > Mr_max → DOUBLY REINFORCED REQUIRED\n"
            f"   If doubly reinforced:\n"
            f"   - Calculate compression steel: As' = (Mf - Mr_max) / [fy × (d - d')]\n"
            f"   - Additional tension steel: As2 = As'\n"
            f"   - Total tension steel: As = As_max + As2\n"
            f"   - Specify both top bars (As') and bottom bars (As)\n"
            f"8. If singly reinforced: Calculate required steel area As = Mf / (φs × fy × (d - a/2))\n"
            f"9. Check minimum reinforcement: As,min = max(0.2√fc' × b × d / fy, 1.4 × b × d / fy)\n"
            f"10. Select practical bar arrangements for both top and bottom if doubly reinforced\n"
            f"11. CALCULATE BAR SPACING (NBCC 7.7 & 9.8.4):\n"
            f"    For bottom bars in single layer:\n"
            f"    - Bar diameter (db) from bar size (e.g., 25M → db ≈ 25mm)\n"
            f"    - Clear spacing = (beam width - 2×cover - 2×stirrup_dia - n×bar_dia) / (n-1)\n"
            f"    - Check minimum: s_clear ≥ max(1.4×db, 1.4×agg_size, 30mm) per NBCC 7.7.1\n"
            f"    - Check maximum for crack control: s ≤ 500×(280/fs) per NBCC 7.7.2\n"
            f"    - Center-to-center spacing = clear_spacing + bar_diameter\n"
            f"12. Verify factored moment resistance Mr ≥ Mf\n\n"
            f"Provide clear output with:\n"
            f"- Balanced and maximum reinforcement ratios\n"
            f"- Required steel area As (mm²)\n"
            f"- Selected bars (quantity and size for BOTTOM bars)\n"
            f"- Bar spacing: clear spacing and center-to-center spacing\n"
            f"- If doubly reinforced: Compression steel (TOP bars) size and quantity with spacing\n"
            f"- Provided steel areas (As for bottom, As' for top if applicable)\n"
            f"- Moment resistance Mr (kN·m)\n"
            f"- All NBCC checks with clause references"
        ),
        expected_output=(
            "You MUST calculate and output actual numerical values. DO NOT output placeholders.\n\n"
            "EXAMPLE CORRECT OUTPUT FOR SINGLY REINFORCED:\n"
            "EFFECTIVE DEPTH (d): 450 mm\n"
            "BALANCED REINFORCEMENT RATIO (ρb): 0.0379\n"
            "MAXIMUM REINFORCEMENT RATIO (ρ_max): 0.0284\n"
            "MAXIMUM MOMENT CAPACITY (SINGLY): 180.5 kN·m\n"
            "REQUIRED STEEL AREA (As,req): 720 mm²\n"
            "MINIMUM STEEL AREA (As,min): 536 mm²\n"
            "SELECTED REINFORCEMENT (BOTTOM): 4-20M\n"
            "PROVIDED STEEL AREA (As,prov): 1200 mm²\n"
            "BAR SPACING (Clear): 55 mm\n"
            "BAR SPACING (c/c): 75 mm\n"
            "MOMENT RESISTANCE (Mr): 125.3 kN·m\n"
            "REINFORCEMENT RATIO (ρ): 0.89%\n"
            "BEAM TYPE: Singly Reinforced\n"
            "NBCC COMPLIANCE: Clauses 10.5.2, 10.5.4, 10.5.5, 7.7.1\n\n"
            "EXAMPLE CORRECT OUTPUT FOR DOUBLY REINFORCED:\n"
            "EFFECTIVE DEPTH (d): 450 mm\n"
            "BALANCED REINFORCEMENT RATIO (ρb): 0.0379\n"
            "MAXIMUM REINFORCEMENT RATIO (ρ_max): 0.0284\n"
            "MAXIMUM MOMENT CAPACITY (SINGLY): 180.5 kN·m\n"
            "FACTORED MOMENT (Mf): 250.0 kN·m → DOUBLY REINFORCED REQUIRED\n"
            "COMPRESSION STEEL (TOP BARS): 3-20M\n"
            "COMPRESSION STEEL AREA (As'): 900 mm²\n"
            "COMPRESSION BAR SPACING (c/c): 90 mm\n"
            "TENSION STEEL (BOTTOM BARS): 6-25M\n"
            "TENSION STEEL AREA (As): 3000 mm²\n"
            "TENSION BAR SPACING (c/c): 35 mm\n"
            "MOMENT RESISTANCE (Mr): 252.8 kN·m\n"
            "REINFORCEMENT RATIO (ρ): 2.22%\n"
            "BEAM TYPE: Doubly Reinforced\n"
            "NBCC COMPLIANCE: Clauses 10.5.2, 10.5.4, 10.5.5, 7.7.1\n\n"
            "OUTPUT YOUR CALCULATED VALUES IN THIS EXACT FORMAT with real numbers."
        ),
        agent=flexural_agent,
        context=[task_load_analysis]
    )
    
    task_shear_design = Task(
        description=(
            f"Design shear reinforcement (stirrups) for RC beam:\n"
            f"- Use beam geometry and materials from flexural design\n"
            f"- Stirrup yield strength: {beam_inputs.get('fy_stirrup', beam_inputs['fy'])} MPa\n\n"
            f"STEPS:\n"
            f"1. Use NBCC Code Retrieval tool to get shear design provisions\n"
            f"2. Extract factored shear Vf from load analysis results\n"
            f"3. Calculate concrete shear capacity: Vc = φc × 0.2 × λ × √fc' × bw × dv\n"
            f"   where dv ≈ 0.9d\n"
            f"4. Check if shear reinforcement is required: Vf > Vc\n"
            f"5. If required, calculate stirrup area per spacing: Av/s\n"
            f"   Vs = Vf - Vc\n"
            f"   Av/s = Vs / (fy × dv)\n"
            f"6. Select stirrup size (e.g., 10M double-leg) and calculate spacing\n"
            f"7. Check maximum spacing: s ≤ min(0.7dv, 600mm)\n"
            f"8. Check minimum reinforcement if Vf > 0.5Vc\n\n"
            f"Provide clear output with:\n"
            f"- Concrete shear capacity Vc (kN)\n"
            f"- Required vs Provided shear resistance\n"
            f"- Stirrup size and spacing\n"
            f"- NBCC compliance checks with clause references"
        ),
        expected_output=(
            "You MUST calculate and output actual numerical values. DO NOT output placeholders.\n\n"
            "EXAMPLE CORRECT OUTPUT:\n"
            "CONCRETE SHEAR CAPACITY (Vc): 45.2 kN\n"
            "FACTORED SHEAR (Vf): 73.5 kN\n"
            "SHEAR REINFORCEMENT REQUIRED: Yes\n"
            "STIRRUP SIZE: 10M\n"
            "STIRRUP CONFIGURATION: Double-leg\n"
            "STIRRUP SPACING: 250 mm c/c\n"
            "MAXIMUM ALLOWED SPACING: 283 mm\n"
            "NBCC COMPLIANCE: Clauses 11.3.5, 11.3.6\n\n"
            "OUTPUT YOUR CALCULATED VALUES IN THIS EXACT FORMAT with real numbers."
        ),
        agent=shear_agent,
        context=[task_load_analysis, task_flexural_design]
    )
    
    task_serviceability = Task(
        description=(
            f"Check serviceability requirements:\n"
            f"- Span: {beam_inputs['span']} m ({beam_inputs['span']*1000} mm)\n"
            f"- Depth: {beam_inputs['depth']} mm\n"
            f"- Support conditions: {beam_inputs.get('support_condition', 'simply supported')}\n\n"
            f"STEPS:\n"
            f"1. Use NBCC Code Retrieval tool to get serviceability provisions\n"
            f"2. Calculate span-to-depth ratio: L/d = {beam_inputs['span']*1000} / {beam_inputs['depth']}\n"
            f"3. Check against NBCC limits based on support conditions:\n"
            f"   - Simply supported: L/d ≤ 20\n"
            f"   - One end continuous: L/d ≤ 24\n"
            f"   - Both ends continuous: L/d ≤ 26\n"
            f"4. If span-to-depth ratio exceeds limit, recommend increasing depth\n"
            f"5. Check crack control spacing requirements\n"
            f"6. Signal if design iteration is needed\n\n"
            f"Provide clear output with:\n"
            f"- Calculated L/d ratio\n"
            f"- NBCC limit for support condition\n"
            f"- PASS/FAIL status\n"
            f"- Recommendations if failed\n"
            f"- NBCC clause references"
        ),
        expected_output=(
            "You MUST calculate and output actual numerical values. DO NOT output placeholders.\n\n"
            "EXAMPLE CORRECT OUTPUT:\n"
            "SPAN-TO-DEPTH RATIO (L/d): 12.0\n"
            "NBCC LIMIT: 20\n"
            "STATUS: PASS\n"
            "NBCC REFERENCE: Clause 9.8.2.3\n\n"
            "OUTPUT YOUR CALCULATED VALUE IN THIS EXACT FORMAT with real numbers."
        ),
        agent=serviceability_agent,
        context=[task_load_analysis, task_flexural_design]
    )
    
    task_design_review = Task(
        description=(
            f"Create final comprehensive beam design summary with ACTUAL VALUES.\n\n"
            f"CRITICAL: You MUST extract the actual calculated numbers from previous task outputs.\n"
            f"DO NOT output placeholders like [value], [qty], [size], etc.\n\n"
            f"STEP 1: EXTRACT these specific values from previous task outputs:\n"
            f"  • From Load Analysis: Extract the actual Mf value (e.g., 110.25 kN·m), Vf value (e.g., 73.5 kN), and combination name (e.g., 1.4D+1.5L)\n"
            f"  • From Flexural Design: Extract bar count and size (e.g., 4-20M), As,prov (e.g., 1200 mm²), d value (e.g., 450 mm), beam type (e.g., Singly Reinforced)\n"
            f"  • From Shear Design: Extract stirrup size (e.g., 10M), spacing (e.g., 250 mm), configuration (e.g., Double-leg)\n"
            f"  • From Serviceability: Extract L/d ratio (e.g., 12.0) and status (PASS/FAIL)\n\n"
            f"STEP 2: FILL IN the template below with those extracted values:\n\n"
            f"Known Input Values (use these directly):\n"
            f"  • Span: {beam_inputs['span']} m\n"
            f"  • Width: {beam_inputs['width']} mm\n"
            f"  • Total Depth: {beam_inputs['depth']} mm\n"
            f"  • Cover: {beam_inputs.get('cover', 40)} mm\n"
            f"  • fc': {beam_inputs['fc_prime']} MPa\n"
            f"  • fy: {beam_inputs['fy']} MPa\n"
            f"  • Dead Load: {beam_inputs['dead_load']} kN/m\n"
            f"  • Live Load: {beam_inputs['live_load']} kN/m\n"
            f"  • Snow Load: {beam_inputs.get('snow_load', 0)} kN/m\n"
            f"  • Support: {beam_inputs.get('support_condition', 'simply supported')}\n\n"
            f"STEP 3: Create the final specification by replacing ALL placeholders with actual numbers.\n"
            f"Example: Instead of '[qty]-[size]M', write '4-20M'. Instead of '[value] mm²', write '1200 mm²'."
        ),
        expected_output=(
            "═══════════════════════════════════════════════════════════════\n"
            "         REINFORCED CONCRETE BEAM DESIGN SPECIFICATION\n"
            "═══════════════════════════════════════════════════════════════\n\n"
            "1. BEAM GEOMETRY\n"
            "   • Span: [L] m\n"
            "   • Width (b): [value] mm\n"
            "   • Total Depth (h): [value] mm\n"
            "   • Effective Depth (d): [value] mm\n"
            "   • Clear Cover: [value] mm\n"
            "   • Support Condition: [type]\n\n"
            "2. MATERIAL PROPERTIES\n"
            "   • Concrete Strength (fc'): [value] MPa\n"
            "   • Steel Yield Strength (fy): [value] MPa\n"
            "   • Resistance Factors: φc=0.65, φs=0.85 (NBCC 8.4.2)\n\n"
            "3. DESIGN LOADS (NBCC 4.1.3.2)\n"
            "   • Dead Load: [value] kN/m\n"
            "   • Live Load: [value] kN/m\n"
            "   • Snow Load: [value] kN/m\n"
            "   • Governing Combination: [name]\n"
            "   • Factored Moment (Mf): [value] kN·m\n"
            "   • Factored Shear (Vf): [value] kN\n\n"
            "4. FLEXURAL REINFORCEMENT (NBCC 10.5)\n"
            "   • Beam Type: Singly Reinforced / Doubly Reinforced\n"
            "   • Tension Bars (Bottom): [qty]-[size]M (e.g., 4-25M)\n"
            "   • Tension Steel Area (As): [value] mm²\n"
            "   • Tension Bar Spacing: [value] mm c/c (Clear: [value] mm)\n"
            "   • [IF DOUBLY: Compression Bars (Top): [qty]-[size]M]\n"
            "   • [IF DOUBLY: Compression Steel Area (As'): [value] mm²]\n"
            "   • [IF DOUBLY: Compression Bar Spacing: [value] mm c/c]\n"
            "   • Reinforcement Ratio (ρ): [value]%\n"
            "   • Moment Resistance (Mr): [value] kN·m ✓\n"
            "   • Min. Steel Check: PASS (NBCC 10.5.4)\n"
            "   • Ductility Check: PASS (NBCC 10.5.5)\n"
            "   • Bar Spacing Check: PASS (NBCC 7.7.1)\n\n"
            "5. SHEAR REINFORCEMENT (NBCC 11.3)\n"
            "   • Concrete Shear Capacity (Vc): [value] kN\n"
            "   • Shear Reinforcement: Required / Not Required\n"
            "   • Stirrups: [size]M @ [spacing] mm c/c\n"
            "   • Configuration: Double-leg / Single-leg\n"
            "   • Max. Spacing: [value] mm (NBCC 11.3.6)\n\n"
            "6. SERVICEABILITY (NBCC 9.8)\n"
            "   • Span-to-Depth Ratio (L/d): [value]\n"
            "   • NBCC Limit: [value]\n"
            "   • Status: PASS ✓ / FAIL ✗\n\n"
            "7. DESIGN SUMMARY\n"
            "   ┌─────────────────────────────────────────────────┐\n"
            "   │  BEAM: [b]mm × [h]mm × [L]m                    │\n"
            "   │  TENSION BARS (BOTTOM): [qty]-[size]M          │\n"
            "   │  [IF DOUBLY: COMPRESSION BARS (TOP): [qty]-[size]M] │\n"
            "   │  STIRRUPS: [size]M @ [spacing]mm c/c           │\n"
            "   │  COVER: [value]mm                               │\n"
            "   │  CONCRETE: fc'=[value] MPa                      │\n"
            "   │  STEEL: fy=[value] MPa                          │\n"
            "   └─────────────────────────────────────────────────┘\n\n"
            "8. CODE COMPLIANCE: ✓ APPROVED\n"
            "   All design checks satisfy NBCC requirements.\n\n"
            "═══════════════════════════════════════════════════════════════\n"
            "Designer: Multi-Agent RC Beam Design System\n"
            "Date: [current date]\n"
            "═══════════════════════════════════════════════════════════════\n"
        ),
        agent=reviewer_agent,
        context=[task_load_analysis, task_flexural_design, task_shear_design, task_serviceability]
    )
    
    return [task_load_analysis, task_flexural_design, task_shear_design, 
            task_serviceability, task_design_review]


# ===========================
# MAIN DESIGN FUNCTION
# ===========================

def design_rc_beam(
    span: float,
    dead_load: float,
    live_load: float,
    width: int,
    depth: int,
    fc_prime: int,
    fy: int,
    snow_load: float = 0,
    point_loads: list = None,
    cover: int = 40,
    support_condition: str = "simply supported"
):
    """
    Design an RC beam using multi-agent system.
    
    Args:
        span: Beam span in meters
        dead_load: Dead load in kN/m
        live_load: Live load in kN/m
        width: Beam width in mm
        depth: Beam depth in mm
        fc_prime: Concrete strength in MPa
        fy: Steel yield strength in MPa
        snow_load: Snow load in kN/m (default 0)
        point_loads: List of (load, distance) tuples, e.g., [(50, 2.0), (30, 4.0)] for 50 kN at 2m and 30 kN at 4m (default None)
        cover: Concrete cover in mm (default 40)
        support_condition: "simply supported", "one end continuous", or "both ends continuous"
    
    Returns:
        Design report from crew execution
    """
    
    # Package beam inputs
    beam_inputs = {
        'span': span,
        'dead_load': dead_load,
        'live_load': live_load,
        'snow_load': snow_load,
        'point_loads': point_loads if point_loads else [],
        'width': width,
        'depth': depth,
        'fc_prime': fc_prime,
        'fy': fy,
        'cover': cover,
        'support_condition': support_condition
    }
    
    # Create tasks
    tasks = create_design_tasks(beam_inputs)
    
    # Create crew with sequential process
    crew = Crew(
        agents=[
            load_agent,
            flexural_agent,
            shear_agent,
            serviceability_agent,
            reviewer_agent
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Execute design workflow
    print("\n" + "="*80)
    print("RC BEAM DESIGN - MULTI-AGENT SYSTEM")
    print("="*80)
    print(f"\nBeam Parameters:")
    print(f"  Span: {span} m")
    print(f"  Loads: DL={dead_load} kN/m, LL={live_load} kN/m, SL={snow_load} kN/m")
    if point_loads:
        print(f"  Point Loads: {', '.join([f'{P} kN at {a} m' for P, a in point_loads])}")
    print(f"  Section: {width} mm × {depth} mm")
    print(f"  Materials: fc'={fc_prime} MPa, fy={fy} MPa")
    print(f"  Support: {support_condition}")
    print("="*80 + "\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*80)
    print("DESIGN COMPLETE")
    print("="*80)
    
    return result


# ===========================
# EXAMPLE USAGE
# ===========================

if __name__ == "__main__":
    # Example 1: Design a 6m simply supported beam (may be SINGLY or DOUBLY reinforced)
    # 
    # WHEN DOES A BEAM BECOME DOUBLY REINFORCED?
    # -------------------------------------------
    # A beam needs compression reinforcement (top bars) when the factored moment
    # exceeds the maximum capacity of a singly reinforced section with maximum
    # allowable tension steel (ρ_max = 0.75 × ρ_balanced).
    #
    # TRIGGERS FOR DOUBLY REINFORCED:
    # 1. High moment: Large span, heavy loads, point loads
    # 2. Small section: Narrow width or shallow depth
    # 3. Low concrete strength (fc')
    # 4. High steel yield strength (fy) - paradoxically reduces ρ_balanced
    #
    # TYPICAL SCENARIOS:
    # - Architectural constraints limiting beam depth
    # - Very heavy loads on moderate spans
    # - Long spans with restricted section size
    # - Concentrated loads (machinery, columns, etc.)
    #
    # TO TEST DOUBLY REINFORCED, try:
    # - span=8.0m, dead_load=15.0, live_load=20.0, width=300, depth=500
    # - span=6.0m, dead_load=20.0, live_load=30.0, width=250, depth=450
    # - span=10.0m, dead_load=12.0, live_load=15.0, width=300, depth=550
    # - span=6.0m with point_loads=[(80, 2.0), (100, 4.0)] (heavy concentrated loads)
    
    # Example with point loads:
    # Uncomment to test beam with concentrated loads
    # result = design_rc_beam(
    #     span=6.0,
    #     dead_load=10.0,
    #     live_load=15.0,
    #     snow_load=2.0,
    #     point_loads=[(50, 2.0), (60, 4.0)],  # 50 kN at 2m, 60 kN at 4m
    #     width=300,
    #     depth=500,
    #     fc_prime=30,
    #     fy=400,
    #     cover=40,
    #     support_condition="simply supported"
    # )
    
    result = design_rc_beam(
        span=6.0,               # 6 meters
        dead_load=10.0,         # 10 kN/m (including self-weight)
        live_load=25.0,         # 25 kN/m (INCREASED - may trigger doubly reinforced)
        snow_load=2.0,          # 2 kN/m
        point_loads=None,       # No point loads in this example
        width=300,              # 300 mm
        depth=500,              # 500 mm
        fc_prime=30,            # 30 MPa
        fy=400,                 # 400 MPa
        cover=40,               # 40 mm
        support_condition="simply supported"
    )
    
    print("\n" + "="*80)
    print("FINAL DESIGN REPORT")
    print("="*80)
    print(result)
