#!/usr/bin/env python3
"""
Test script to verify PDF loading functionality in the vector store.
Run this to verify that PDFs are being loaded and stored correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from coaches import (
    initialize_agents_and_vector_store,
    verify_vector_store_contents,
    load_pdf_files
)

def test_pdf_loading():
    """Test PDF loading functionality."""
    print("\n" + "="*70)
    print("PDF LOADING TEST")
    print("="*70 + "\n")
    
    try:
        # Initialize components
        print("1️⃣  Initializing agents and vector store...")
        import asyncio
        components = asyncio.run(initialize_agents_and_vector_store())
        print("✅ Components initialized successfully\n")
        
        # Get vector store and results
        vector_store = components.get("vector_store")
        pdf_results = components.get("pdf_load_results", {})
        verification = components.get("vector_store_verification", {})
        
        # Display PDF loading summary
        print("2️⃣  PDF LOADING SUMMARY")
        print("-" * 70)
        if pdf_results:
            print(f"Total PDFs found: {pdf_results.get('total_pdfs', 0)}")
            print(f"Successfully loaded: {pdf_results.get('successful', 0)}")
            
            if pdf_results.get('pdfs_loaded'):
                print("\nDetailed Results:")
                for result in pdf_results['pdfs_loaded']:
                    if result.get('success'):
                        print(f"  ✅ {result['file_name']}")
                        print(f"     Pages: {result['pages_loaded']}, Chunks: {result['chunks_created']}")
                    else:
                        print(f"  ❌ {result['file_name']}: {result.get('error', 'Unknown error')}")
        else:
            print("ℹ️  No PDFs in assets directory or PDFs not loaded")
        
        # Display vector store verification
        print("\n3️⃣  VECTOR STORE VERIFICATION")
        print("-" * 70)
        if verification:
            print(f"Vector store initialized: {verification.get('vector_store_initialized', False)}")
            print(f"Has content: {verification.get('has_content', False)}")
            if verification.get('sample_search_results'):
                print(f"Sample search found {verification.get('sample_search_results')} result(s)")
        
        # Summary
        print("\n4️⃣  FINAL SUMMARY")
        print("-" * 70)
        if verification.get('has_content'):
            print("✅ Vector store is populated and ready for use!")
        else:
            print("⚠️  Vector store is empty. Ensure CSV files or PDFs are in the assets directory.")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    test_pdf_loading()
