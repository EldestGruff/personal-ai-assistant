"""
Backend Integration Example

Demonstrates how to integrate the AI backend abstraction layer
with existing services. Shows primary/fallback patterns, error
handling, and backend swapping.

This example shows:
1. Backend initialization and registration
2. Using backends with existing ThoughtAnalyzer
3. Primary/fallback pattern (Claude → Ollama → Mock)
4. Error handling and recovery
5. Backend health checking
"""

import asyncio
from datetime import datetime
from typing import Optional

# Backend imports
from src.services.ai_backends import (
    AIBackendRegistry,
    BackendRequest,
    SuccessResponse,
    ErrorResponse,
)
from src.services.ai_backends.claude_backend import ClaudeBackend
from src.services.ai_backends.ollama_backend import OllamaBackend
from src.services.ai_backends.mock_backend import MockBackend


# ============================================================================
# PART 1: Backend Initialization & Registration
# ============================================================================

def initialize_backends():
    """
    Initialize and register all available backends.
    
    Order matters: first registered becomes default.
    In production, you'd call this during app startup.
    """
    print("\n" + "="*70)
    print("INITIALIZING BACKENDS")
    print("="*70)
    
    # Register Claude as primary (uses ANTHROPIC_API_KEY from env)
    try:
        claude = ClaudeBackend()
        AIBackendRegistry.register("claude", claude)
        print("✅ Registered Claude backend (primary)")
    except Exception as e:
        print(f"⚠️  Could not register Claude: {e}")
    
    # Register Ollama as fallback
    try:
        ollama = OllamaBackend(
            base_url="http://192.168.7.187:11434",
            model="llama2"
        )
        AIBackendRegistry.register("ollama", ollama)
        print("✅ Registered Ollama backend (fallback)")
    except Exception as e:
        print(f"⚠️  Could not register Ollama: {e}")
    
    # Always register Mock for testing
    mock = MockBackend(mode="mock-success")
    AIBackendRegistry.register("mock", mock)
    print("✅ Registered Mock backend (testing)")
    
    # Show available backends
    available = AIBackendRegistry.list_available()
    print(f"\n📋 Available backends: {', '.join(available)}")
    
    default = AIBackendRegistry.get_default()
    if default:
        print(f"🎯 Default backend: {default.name}")


# ============================================================================
# PART 2: Simple Backend Usage
# ============================================================================

async def analyze_with_backend(
    thought_content: str,
    backend_name: str = None
) -> Optional[SuccessResponse]:
    """
    Analyze a thought using specified or default backend.
    
    Args:
        thought_content: Thought to analyze
        backend_name: Optional backend name (uses default if None)
    
    Returns:
        SuccessResponse if successful, None if failed
    """
    # Get backend
    if backend_name:
        backend = AIBackendRegistry.get(backend_name)
    else:
        backend = AIBackendRegistry.get_default()
    
    print(f"\n📊 Analyzing with {backend.name}...")
    
    # Create request
    request = BackendRequest(
        request_id=f"req-{datetime.now().timestamp()}",
        thought_content=thought_content,
        timeout_seconds=30
    )
    
    # Analyze
    response = await backend.analyze(request)
    
    if response.success:
        print(f"✅ Success!")
        print(f"   Summary: {response.analysis.summary}")
        print(f"   Themes: {[t.theme for t in response.analysis.themes]}")
        print(f"   Tokens: {response.metadata.tokens_used}")
        print(f"   Time: {response.metadata.processing_time_ms}ms")
        return response
    else:
        print(f"❌ Error: {response.error.error_code}")
        print(f"   Message: {response.error.error_message}")
        return None


# ============================================================================
# PART 3: Primary/Fallback Pattern with Automatic Retry
# ============================================================================

async def analyze_with_fallback(
    thought_content: str,
    backends_priority: list[str] = None
) -> Optional[SuccessResponse]:
    """
    Analyze thought with automatic fallback to next backend on failure.
    
    This is the recommended pattern for production: try Claude first,
    fall back to Ollama if Claude fails, fall back to Mock if all fail.
    
    Args:
        thought_content: Thought to analyze
        backends_priority: List of backend names to try in order
                          Defaults to ["claude", "ollama", "mock"]
    
    Returns:
        SuccessResponse from first successful backend, None if all fail
    """
    if backends_priority is None:
        backends_priority = ["claude", "ollama", "mock"]
    
    print("\n" + "="*70)
    print(f"ANALYZING WITH FALLBACK STRATEGY")
    print(f"Priority: {' → '.join(backends_priority)}")
    print("="*70)
    
    for backend_name in backends_priority:
        # Check if backend is registered
        if not AIBackendRegistry.is_registered(backend_name):
            print(f"⏭️  Skipping {backend_name} (not registered)")
            continue
        
        backend = AIBackendRegistry.get(backend_name)
        
        # Check health first (optional optimization)
        healthy = await backend.health_check()
        if not healthy:
            print(f"⚠️  {backend_name} health check failed, skipping")
            continue
        
        print(f"\n🎯 Trying {backend_name}...")
        
        # Create request
        request = BackendRequest(
            request_id=f"req-{datetime.now().timestamp()}",
            thought_content=thought_content,
            timeout_seconds=30
        )
        
        # Attempt analysis
        response = await backend.analyze(request)
        
        if response.success:
            print(f"✅ Success with {backend_name}!")
            print(f"   Summary: {response.analysis.summary}")
            return response
        else:
            print(f"❌ {backend_name} failed: {response.error.error_code}")
            print(f"   Message: {response.error.error_message}")
            # Continue to next backend
    
    print("\n❌ All backends failed")
    return None


# ============================================================================
# PART 4: Integration with Existing Services
# ============================================================================

async def integrate_with_thought_analyzer_example():
    """
    Example showing how to integrate with existing ThoughtAnalyzer.
    
    In your actual code, you'd modify ThoughtAnalyzer to use
    AIBackendRegistry instead of calling ClaudeService directly.
    """
    print("\n" + "="*70)
    print("INTEGRATION WITH THOUGHTANALYZER")
    print("="*70)
    
    # In your actual ThoughtAnalyzer.analyze() method, replace:
    #
    #   OLD CODE:
    #   result = self.claude_service.analyze_thought(thought)
    #
    #   NEW CODE:
    #   backend = AIBackendRegistry.get_default()
    #   request = BackendRequest(
    #       request_id=f"thought-{thought.id}",
    #       thought_content=thought.content
    #   )
    #   response = await backend.analyze(request)
    #
    #   if response.success:
    #       # Use response.analysis
    #   else:
    #       # Handle error
    
    print("""
    Integration Steps:
    
    1. In src/services/thought_service.py or wherever ThoughtAnalyzer is:
    
       from src.services.ai_backends import AIBackendRegistry, BackendRequest
       
       async def analyze_thought(self, thought: ThoughtDB):
           # Get backend
           backend = AIBackendRegistry.get_default()
           
           # Create request
           request = BackendRequest(
               request_id=f"thought-{thought.id}",
               thought_content=thought.content,
               context={
                   "user_id": str(thought.user_id),
                   "tags": thought.tags
               }
           )
           
           # Analyze
           response = await backend.analyze(request)
           
           if response.success:
               # Update thought with analysis
               thought.claude_summary = response.analysis.summary
               # ... process themes, actions, etc.
               return response.analysis
           else:
               # Log error, maybe try fallback
               logger.error(f"Analysis failed: {response.error.error_code}")
               return None
    
    2. In src/api/main.py startup:
    
       @app.on_event("startup")
       async def startup_event():
           # Initialize backends
           claude = ClaudeBackend()
           AIBackendRegistry.register("claude", claude)
           
           ollama = OllamaBackend()
           AIBackendRegistry.register("ollama", ollama)
           
           # Set primary
           AIBackendRegistry.set_default("claude")
    """)


# ============================================================================
# PART 5: Health Monitoring
# ============================================================================

async def monitor_backend_health():
    """Check health of all backends"""
    print("\n" + "="*70)
    print("BACKEND HEALTH CHECK")
    print("="*70)
    
    health = await AIBackendRegistry.health_check_all()
    
    for backend_name, is_healthy in health.items():
        status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
        print(f"{status}: {backend_name}")
    
    # Recommend switching if primary is unhealthy
    default = AIBackendRegistry.get_default()
    if default and not health.get(default.name, False):
        print(f"\n⚠️  Primary backend '{default.name}' is unhealthy!")
        print("   Consider switching to a healthy backend:")
        
        for backend_name, is_healthy in health.items():
            if is_healthy and backend_name != default.name:
                print(f"   → AIBackendRegistry.set_default('{backend_name}')")
                break


# ============================================================================
# MAIN DEMO
# ============================================================================

async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("AI BACKEND INTEGRATION EXAMPLES")
    print("="*70)
    
    # 1. Initialize backends
    initialize_backends()
    
    # 2. Monitor health
    await monitor_backend_health()
    
    # 3. Simple usage
    print("\n" + "="*70)
    print("SIMPLE BACKEND USAGE")
    print("="*70)
    
    await analyze_with_backend(
        "Should optimize the email filtering system to better handle subscriptions"
    )
    
    # 4. Fallback pattern
    await analyze_with_fallback(
        "Need to refactor the database layer for better performance"
    )
    
    # 5. Integration guidance
    await integrate_with_thought_analyzer_example()
    
    print("\n" + "="*70)
    print("✅ EXAMPLES COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
