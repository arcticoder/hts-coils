#!/usr/bin/env python3
"""
Author rewrite script for git history
Changes asciimath-bot to Arcticoder in commit history
"""

def author_callback(commit):
    """
    Callback function for rewriting commit authors
    """
    author_name = commit.author_name
    author_email = commit.author_email
    
    if author_name == b"asciimath-bot":
        return (b"Arcticoder", b"10162808+arcticoder@users.noreply.github.com")
    
    return (author_name, author_email)

def committer_callback(commit):
    """
    Callback function for rewriting commit committers
    """
    committer_name = commit.committer_name
    committer_email = commit.committer_email
    
    if committer_name == b"asciimath-bot":
        return (b"Arcticoder", b"10162808+arcticoder@users.noreply.github.com")
    
    return (committer_name, committer_email)