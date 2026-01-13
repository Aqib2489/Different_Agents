"""
One-time setup script to load NBCC PDF into vector store.
Run this after obtaining the official NBCC PDF document.
"""

from nbcc_rag_system import initialize_nbcc_vectorstore
import os
import sys

# Path to your NBCC PDF (update this with your actual PDF path)
NBCC_PDF_PATH = "NBCC_2020_Volume_1_Division_B.pdf"

# Alternative: Check command line argument
if len(sys.argv) > 1:
    NBCC_PDF_PATH = sys.argv[1]

def main():
    print("="*80)
    print("NBCC PDF VECTORIZATION SETUP")
    print("="*80)
    
    # Check if PDF exists
    if not os.path.exists(NBCC_PDF_PATH):
        print(f"\n❌ ERROR: PDF not found at '{NBCC_PDF_PATH}'")
        print("\nTo use this script:")
        print("1. Obtain NBCC PDF from National Research Council Canada")
        print("   Website: https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada")
        print("\n2. Place the PDF in this project directory")
        print("\n3. Run the script with PDF path:")
        print(f"   python setup_nbcc_pdf.py path/to/your/NBCC.pdf")
        print("\n   OR update NBCC_PDF_PATH variable in this script")
        print("\n" + "="*80)
        print("ALTERNATIVE: Use mock corpus (no PDF needed)")
        print("="*80)
        print("The system will automatically use mock NBCC corpus if no PDF is provided.")
        print("Run: python beam_design.py")
        print("The mock corpus includes common clauses for testing.")
        sys.exit(1)
    
    print(f"\n✓ Found PDF: {NBCC_PDF_PATH}")
    pdf_size_mb = os.path.getsize(NBCC_PDF_PATH) / (1024 * 1024)
    print(f"  File size: {pdf_size_mb:.2f} MB")
    
    print("\nThis script will:")
    print("  1. Load all pages from NBCC PDF")
    print("  2. Chunk text into semantic segments (~1000 chars each)")
    print("  3. Create embeddings using OpenAI API (text-embedding-3-small)")
    print("  4. Store vectors in local database (./nbcc_vectorstore)")
    print("\n⏱️  Estimated time: 5-15 minutes")
    print("💰 Estimated cost: $0.10-0.50 (one-time embedding cost)")
    print("\n" + "="*80)
    
    # Confirm before proceeding
    response = input("\nProceed with vectorization? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Setup cancelled.")
        sys.exit(0)
    
    print("\n" + "="*80)
    print("PROCESSING PDF...")
    print("="*80 + "\n")
    
    try:
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Warning: OPENAI_API_KEY not found in environment")
            print("Loading from .env file...")
            from utils import load_api_keys
            load_api_keys()
            if not os.getenv("OPENAI_API_KEY"):
                print("❌ ERROR: OpenAI API key required for embeddings")
                print("Please add OPENAI_API_KEY to .env file")
                sys.exit(1)
        
        # Initialize vector store from PDF
        vectorstore = initialize_nbcc_vectorstore(
            source="pdf",
            pdf_path=NBCC_PDF_PATH,
            persist_dir="./nbcc_vectorstore"
        )
        
        print("\n" + "="*80)
        print("✅ SUCCESS! NBCC VECTOR STORE CREATED")
        print("="*80)
        print("\n📊 Summary:")
        print(f"  - Vector store location: ./nbcc_vectorstore/")
        print(f"  - Source document: {NBCC_PDF_PATH}")
        print(f"  - Embedding model: text-embedding-3-small")
        
        # Test the vectorstore
        print("\n" + "="*80)
        print("TESTING RETRIEVAL...")
        print("="*80)
        
        test_query = "What are the load combinations for ultimate limit states?"
        print(f"\nTest Query: {test_query}")
        
        results = vectorstore.search(test_query, k=2)
        if results:
            print(f"\n✓ Retrieved {len(results)} relevant sections:")
            for i, result in enumerate(results, 1):
                clause = result['metadata'].get('clause', 'N/A')
                relevance = result['relevance_score']
                preview = result['content'][:200].replace('\n', ' ')
                print(f"\n  {i}. Clause {clause} (Relevance: {relevance:.1%})")
                print(f"     {preview}...")
        
        print("\n" + "="*80)
        print("SETUP COMPLETE")
        print("="*80)
        print("\n✨ Your system is now ready with RAG-based NBCC retrieval!")
        print("\nNext steps:")
        print("  1. Test the RAG system: python nbcc_rag_system.py")
        print("  2. Run beam design: python beam_design.py")
        print("\nThe vector store will load automatically on future runs.")
        print("No need to re-run this setup unless you update the PDF.")
        print("="*80 + "\n")
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR DURING SETUP")
        print("="*80)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PDF is valid and readable")
        print("  2. Check OpenAI API key in .env file")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Check error message above for specific issue")
        print("\nFor help, see RAG_SETUP.md documentation")
        sys.exit(1)


if __name__ == "__main__":
    main()
