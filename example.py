#!/usr/bin/env python3
"""
Example usage of the GitHub Repository Analysis Agent
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from github_agent import GitHubAnalysisAgent

async def example_usage():
    """Example of how to use the GitHub Analysis Agent"""
    
    # Initialize the agent
    agent = GitHubAnalysisAgent()
    
    # Example 1: Analyze machine learning repositories
    print("🔍 Analyzing machine learning repositories...")
    ml_analyses = await agent.analyze_repositories(
        keyword="machine learning",
        recipient_email="your_email@example.com"
    )
    
    # Print some results
    print(f"✅ Analyzed {len(ml_analyses)} machine learning repositories")
    
    # Example 2: Analyze web development repositories
    print("\n🔍 Analyzing web development repositories...")
    web_analyses = await agent.analyze_repositories(
        keyword="web development",
        recipient_email="your_email@example.com"
    )
    
    print(f"✅ Analyzed {len(web_analyses)} web development repositories")
    
    # Show top repositories from both analyses
    all_analyses = ml_analyses + web_analyses
    top_repos = sorted(all_analyses, key=lambda x: x.contribution_score, reverse=True)[:5]
    
    print("\n⭐ Top 5 repositories by contribution score:")
    for i, repo in enumerate(top_repos, 1):
        print(f"{i}. {repo.full_name} - Score: {repo.contribution_score}/100")
        print(f"   Status: {repo.contribution_status.value.replace('_', ' ').title()}")
        print(f"   Language: {repo.language}")
        print(f"   Stars: {repo.stars:,}")
        print()

if __name__ == "__main__":
    # Make sure you have set up your .env file before running this
    if not os.path.exists('.env'):
        print("❌ Please create a .env file based on .env.example")
        sys.exit(1)
    
    asyncio.run(example_usage())
