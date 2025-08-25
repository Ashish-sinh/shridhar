#!/usr/bin/env python3
"""Get URLs for specific file IDs"""
import sys
from src.supabase_client import get_supabase_manager

def get_file_url(file_id):
    """Get the public URL for a file ID"""
    try:
        manager = get_supabase_manager()
        response = manager.client.table("files").select("*").eq("id", file_id).execute()
        
        if response.data:
            file_info = response.data[0]
            print(f"\nFile: {file_info['name']}")
            print(f"Language: {file_info['metadata'].get('language', 'unknown')}")
            print(f"URL: {file_info['url']}")
            return file_info['url']
        else:
            print(f"File ID {file_id} not found")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_id = sys.argv[1]
        get_file_url(file_id)
    else:
        # Example: Get URL for a specific file
        example_id = "dbc6753c-4c9d-4491-b1e4-36ccde50223f"
        print(f"Getting URL for file ID: {example_id}")
        get_file_url(example_id)
