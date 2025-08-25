-- Supabase Database Setup Script
-- Run this SQL in the Supabase SQL Editor to create the required tables

-- Create the files table if it doesn't exist
CREATE TABLE IF NOT EXISTS files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_type ON files (type);
CREATE INDEX IF NOT EXISTS idx_files_name ON files (name);

-- Enable Row Level Security (RLS) - optional but recommended for production
-- ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (modify as needed for your security requirements)
-- CREATE POLICY "Allow all operations" ON files FOR ALL USING (true);

-- Grant necessary permissions (adjust as needed)
GRANT ALL ON files TO authenticated;
GRANT ALL ON files TO anon;
