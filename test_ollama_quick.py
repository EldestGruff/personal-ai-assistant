"""Quick test of OllamaBackend connectivity and analysis"""
import asyncio
from src.services.ai_backends.ollama_backend import OllamaBackend
from src.services.ai_backends.models import BackendRequest

async def test_ollama():
    backend = OllamaBackend(
        base_url="http://192.168.7.187:11434",
        model="gemma3:27b"  # Use available model
    )
    
    # Test health check
    print("Testing Ollama health check...")
    healthy = await backend.health_check()
    print(f"Health check: {'✅ PASS' if healthy else '❌ FAIL'}")
    
    if healthy:
        # Test actual analysis (higher timeout for large models)
        print("\nTesting analysis (this may take 1-2 minutes for large models)...")
        request = BackendRequest(
            request_id="test-req-1",
            thought_content="Should optimize email filtering system",
            timeout_seconds=60  # Increased for large models
        )
        
        response = await backend.analyze(request)
        
        if response.success:
            print("✅ Analysis succeeded!")
            print(f"Backend: {response.analysis.backend_used}")
            print(f"Summary: {response.analysis.summary[:100]}...")
            print(f"Processing time: {response.metadata.processing_time_ms}ms")
        else:
            print(f"❌ Analysis failed: {response.error.error_code}")
            print(f"Message: {response.error.error_message}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
