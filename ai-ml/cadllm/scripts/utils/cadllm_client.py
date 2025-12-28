"""
Production-ready client for CAD-LLM using Hugging Face Inference API.

Usage:
    from cadllm_client import CADLLMClient
    
    client = CADLLMClient("your-username/cad-agent-qwen-2d")
    result = client.generate("Create a circle with radius 10mm centered at origin")
    print(result)
"""

from huggingface_hub import InferenceClient
import os
from typing import Optional, List
from pathlib import Path

# For Inference Endpoints
try:
    import requests
except ImportError:
    requests = None

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass

# Import DSL parser
try:
    from dsl_parser import parse_dsl_to_dxf
except ImportError:
    # If parser not available, we'll return raw output
    parse_dsl_to_dxf = None


class CADLLMClient:
    """
    Production-ready client for CAD-LLM Inference API.
    """
    
    def __init__(
        self, 
        model_name: str,
        token: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        convert_to_ezdxf: bool = True,
        timeout: int = 180
    ):
        """
        Initialize the CAD-LLM client.
        
        Args:
            model_name: Hugging Face model identifier (e.g., "username/model-name")
            token: HF API token (or set HF_TOKEN env var)
            endpoint_url: Optional custom endpoint URL (if provided, model_name is ignored)
            convert_to_ezdxf: If True, automatically convert DSL output to DXF file
            timeout: Request timeout in seconds (default: 180 for slow Space instances)
        """
        self.model_name = model_name
        self.endpoint_url = endpoint_url
        self.token = token or os.getenv("HF_TOKEN")
        self.convert_to_ezdxf = convert_to_ezdxf
        self.timeout = timeout
        
        # InferenceClient doesn't support endpoint_url parameter
        # For standard Inference API, use model name
        # For Inference Endpoints, we'll handle it differently in generate()
        if endpoint_url:
            # Store endpoint URL for custom handling
            self._endpoint_url = endpoint_url
            self.client = None  # Will use direct HTTP requests for endpoints
        else:
            # Standard Inference API: use model name
            self.client = InferenceClient(
                token=self.token,
                model=model_name
            )
            self._endpoint_url = None
        # System prompt matches training format (from train_qwen.py)
        self.system_prompt = (
            "You are a CAD code assistant. Given a simple CAD description, "
            "output ONLY the strict DSL format shown below. Do not use natural language.\n\n"
            "Required DSL Format (STRICT - must match exactly):\n"
            "UNITS: mm\n"
            "ORIGIN_POLICY: room_center_at_(0,0)\n"
            "ROOM: rect w=WIDTH h=HEIGHT center=(0,0)\n"
            "WALLS: rect_perimeter closed=true layer=WALLS\n"
            "OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n"
            "OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n\n"
            "Rules:\n"
            "- Always start with UNITS, ORIGIN_POLICY, ROOM, WALLS (in that order)\n"
            "- Use rect or circle primitives only\n"
            "- Entity names must use underscores (e.g., COFFEE_TABLE not COFFEE TABLE)\n"
            "- anchor_wall must be: north, south, east, west, or none (for free placement)\n"
            "- All coordinates in mm, room centered at (0,0)\n"
            "- All objects must be within room bounds\n"
            "- Use circle for round objects (burners, round tables, columns)\n"
            "- Use rect for rectangular objects (tables, desks, appliances)\n\n"
            "Default dimensions if not specified:\n"
            "- Rooms: 3000x3000 (bedroom), 4000x3000 (kitchen), 2000x2000 (bathroom)\n"
            "- Simple shapes: r=100 (circles), 200x200 (squares), 300x200 (rectangles)\n"
        )
        
        # Load tokenizer for chat template formatting (only if not using endpoint)
        self.tokenizer = None
        if not endpoint_url:
            try:
                from transformers import AutoTokenizer
                try:
                    # Try to load tokenizer from the model (if it's a local path)
                    # For HF models, we'll use the base model tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                except:
                    # Fallback to base model tokenizer
                    base_model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
                    self.tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
            except ImportError:
                # transformers not available, will use plain text format
                pass
    
    def format_prompt(self, instruction: str, input_text: str = "(none)") -> str:
        """
        Format user instruction using Qwen chat template (matches training format).
        
        Args:
            instruction: User instruction (e.g., "Create a bedroom with a bed and desk")
            input_text: Optional input context (usually "(none)")
        
        Returns:
            Formatted prompt string ready for tokenization
        """
        # Build user message (matches training format_example function)
        user_text = instruction
        if input_text and input_text.lower() not in ["(none)", "none", ""]:
            user_text += "\n\nInput:\n" + input_text
        
        # Format as Qwen chat messages (matches training format)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_text},
        ]
        
        # Apply Qwen chat template if tokenizer is available
        if self.tokenizer:
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,  # Return string, not tokens
                add_generation_prompt=True,  # Add assistant prompt token
            )
            return formatted_prompt
        else:
            # Fallback to plain text format (shouldn't happen in normal usage)
            return f"{self.system_prompt}\n\nUser: {user_text}\n\nAssistant:"
    
    def generate(
        self, 
        instruction: str,
        input_text: str = "(none)",
        max_new_tokens: int = 400,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate DXF file from instruction.
        
        Args:
            instruction: CAD instruction (e.g., "Create a circle with radius 10mm")
            input_text: Optional input context
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
        
        Returns:
            Path to generated DXF file (if convert_to_ezdxf=True) or raw coordinate output
        """
        prompt = self.format_prompt(instruction, input_text)
        
        try:
            # If using Inference Endpoint, use direct HTTP requests
            if self._endpoint_url:
                if requests is None:
                    raise ImportError("The 'requests' library is required for Inference Endpoints. Install it with: pip install requests")
                
                headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
                headers["Content-Type"] = "application/json"
                
                # Try Space API format first (FastAPI), then Inference Endpoint format
                # Space API format
                # Space API can take 2-5 minutes on first request (cold start)
                # Complex prompts may also take longer
                space_timeout = max(self.timeout, 300)  # At least 5 minutes for Space
                
                print(f"   ⏱️  Using timeout: {space_timeout}s (Space API may take time on first request)")
                
                try:
                    response = requests.post(
                        f"{self._endpoint_url}/generate",
                        headers=headers,
                        json={
                            "instruction": prompt,
                            "max_new_tokens": max_new_tokens,
                            "temperature": temperature,
                            "top_p": top_p,
                            **kwargs
                        },
                        timeout=space_timeout
                    )
                except requests.exceptions.ReadTimeout as e:
                    raise RuntimeError(
                        f"Space API request timed out after {space_timeout}s. "
                        f"This may happen if:\n"
                        f"  1. The Space is loading the model (first request takes 2-5 minutes)\n"
                        f"  2. The Space is sleeping (check https://huggingface.co/spaces/mkmad7/cad-llm-api)\n"
                        f"  3. The generation is taking too long (try a simpler prompt first)\n"
                        f"\nTry:\n"
                        f"  - Wait a moment and try again\n"
                        f"  - Check if the Space is running: https://huggingface.co/spaces/mkmad7/cad-llm-api\n"
                        f"  - Use a simpler prompt to test if the Space is working"
                    ) from e
                
                if response.status_code == 404:
                    # Try Inference Endpoint format (with same timeout)
                    try:
                        response = requests.post(
                            f"{self._endpoint_url}/generate",
                        headers=headers,
                        json={
                            "inputs": prompt,
                            "parameters": {
                                "max_new_tokens": max_new_tokens,
                                "temperature": temperature,
                                "top_p": top_p,
                                **kwargs
                            }
                        },
                            timeout=space_timeout
                        )
                    except requests.exceptions.ReadTimeout as e:
                        raise RuntimeError(
                            f"Inference Endpoint request timed out after {space_timeout}s. "
                            f"Try a simpler prompt or check if the endpoint is responsive."
                        ) from e
                
                # Check for errors and provide better error messages
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("detail", str(error_json))
                    except:
                        # If not JSON, try to extract error from HTML or text
                        error_text = response.text[:500]  # First 500 chars
                        if "error" in error_text.lower() or "exception" in error_text.lower():
                            error_detail = error_text
                        else:
                            error_detail = f"HTTP {response.status_code}: {response.reason}"
                    
                    raise RuntimeError(
                        f"Space API returned error {response.status_code}:\n{error_detail}\n\n"
                        f"This may happen if:\n"
                        f"  1. The Space is still rebuilding (check https://huggingface.co/spaces/mkmad7/cad-llm-api)\n"
                        f"  2. There's an error in the Space app code\n"
                        f"  3. The model failed to load\n"
                        f"\nCheck the Space logs at: https://huggingface.co/spaces/mkmad7/cad-llm-api/logs"
                    )
                
                response.raise_for_status()
                result = response.json()
                
                # Handle Space API response format
                if isinstance(result, dict) and "output" in result:
                    output = result["output"]
                # Handle Inference Endpoint format
                elif isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    if generated_text.startswith(prompt):
                        generated_text = generated_text[len(prompt):].strip()
                    output = generated_text
                elif isinstance(result, dict):
                    output = result.get("generated_text", result.get("output", str(result)))
                else:
                    output = str(result)
                
                # Convert to DXF file if requested and parser is available
                if self.convert_to_ezdxf and parse_dsl_to_dxf:
                    # Check if output looks like DSL format
                    if "UNITS:" in output or "ROOM:" in output or "WALLS:" in output:
                        dxf_path = parse_dsl_to_dxf(output)
                        return dxf_path
                
                return output
            else:
                # Standard Inference API
                # text_generation may return a generator/stream, so we need to handle it
                result = self.client.text_generation(
                    prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    return_full_text=False,
                    **kwargs
                )
                # If result is a generator/iterator, convert to string
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    try:
                        # Try to get the full result
                        result = ''.join(result) if hasattr(result, '__next__') else str(result)
                    except StopIteration:
                        # If it's exhausted, try to get it as string
                        result = str(result)
                
                # Convert to DXF file if requested and parser is available
                if self.convert_to_ezdxf and parse_dsl_to_dxf:
                    # Check if output looks like DSL format
                    if "UNITS:" in result or "ROOM:" in result or "WALLS:" in result:
                        dxf_path = parse_dsl_to_dxf(result)
                        return dxf_path
                
                return result
        except Exception as e:
            # Provide detailed error message
            error_msg = str(e) if str(e) else repr(e)
            error_type = type(e).__name__
            
            # Special handling for StopIteration (model not available on Inference API)
            if "StopIteration" in error_type or "StopIteration" in error_msg or isinstance(e.__cause__, StopIteration):
                error_msg = (
                    f"Model '{self.model_name}' is not available on the Inference API.\n"
                    f"This usually means:\n"
                    f"  1. The model was just uploaded and needs time to be indexed (wait 5-15 minutes)\n"
                    f"  2. The model needs to be explicitly enabled for Inference API\n"
                    f"  3. For private models, ensure your token has access\n"
                    f"\nTo check model status: https://huggingface.co/{self.model_name}\n"
                    f"To enable Inference API: Go to model settings and enable 'Inference API'\n"
                    f"Alternative: Use a Dedicated Inference Endpoint at https://huggingface.co/inference-endpoints"
                )
            
            # Try to extract more details from the error
            additional_info = ""
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    additional_info = f"\nAPI Response: {e.response.text[:200]}"
                except:
                    pass
            
            raise RuntimeError(
                f"Generation failed ({error_type}): {error_msg}{additional_info}\n"
                f"Model: {self.model_name}\n"
                f"Using: {self._endpoint_url or 'Standard Inference API'}"
            ) from e
    
    def generate_batch(
        self,
        instructions: List[str],
        **kwargs
    ) -> List[str]:
        """Generate responses for multiple instructions."""
        return [self.generate(inst, **kwargs) for inst in instructions]


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Get token from environment or prompt
    token = os.getenv("HF_TOKEN")
    if not token:
        print("Please set HF_TOKEN environment variable or enter it below:")
        token = input("HF Token: ")
        os.environ["HF_TOKEN"] = token
    
    # Initialize client
    model_name = os.getenv("HF_MODEL_NAME", "your-username/cad-agent-qwen-2d")
    print(f"Initializing client for model: {model_name}")
    client = CADLLMClient(model_name, token=token)
    
    # Test generation
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
    else:
        instruction = "Create a circle with radius 10mm centered at origin"
    
    print(f"\n🔄 Generating response for: {instruction}")
    print("=" * 60)
    result = client.generate(instruction)
    print(result)
    print("=" * 60)

