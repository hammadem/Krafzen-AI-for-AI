.PHONY: help setup download-dataset recreate-dataset clean-dataset generate-enhanced-dataset train train-resume merge-model upload-model upload-dataset deploy-ollama ollama-start ollama-stop ollama-start-all ollama-stop-all deploy-space update-space package package-with-dataset package-with-enhanced-dataset extract unarchive clean clean-all info test-api test-api-custom infer-local open-webui-start open-webui-stop open-webui-logs open-webui-status

# Configuration
# When running locally (from cadllm root)
SCRIPTS_DIR = scripts
TRAINING_DIR = $(SCRIPTS_DIR)/training
INFERENCE_DIR = $(SCRIPTS_DIR)/inference
TESTING_DIR = $(SCRIPTS_DIR)/testing
MODEL_MGMT_DIR = $(SCRIPTS_DIR)/model_management
DEPLOYMENT_DIR = $(SCRIPTS_DIR)/deployment
UTILS_DIR = $(SCRIPTS_DIR)/utils

DATASET_DIR = dataset
DATASET_SCRIPTS_DIR = $(DATASET_DIR)/scripts
JSONL_DIR = $(DATASET_DIR)/jsonl
RAW_DIR = $(DATASET_DIR)/cadllm_raw
PACKAGE_NAME = cadllm-workspace.tar.gz

# When running on server (from /workspace)
# These paths are used by the 'train' target
SERVER_DATA_PATH = /workspace/dataset/jsonl/cadllm.jsonl
SERVER_OUTPUT_DIR = /workspace/cadllm

# Space deployment
SPACE_DIR = $(DEPLOYMENT_DIR)/space/cad-llm-api

help: ## Show this help message
	@echo "CADLLM Makefile - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

download-dataset: ## Download raw CADLLM dataset from Hugging Face
	@echo "📥 Downloading CADLLM dataset..."
	cd $(SCRIPTS_DIR) && python download_dataset.py
	@echo "✅ Dataset downloaded to $(RAW_DIR)"

recreate-dataset: ## Recreate dataset with descriptions from Excel files
	@echo "🔄 Recreating dataset with descriptions..."
	@if [ ! -d "$(RAW_DIR)/cad_collection_select_V2" ]; then \
		echo "❌ Error: Raw dataset not found. Run 'make download-dataset' first."; \
		exit 1; \
	fi
	cd $(DATASET_SCRIPTS_DIR) && python recreate_dataset_with_descriptions.py \
		--raw-dir ../../cadllm_raw/cad_collection_select_V2/cad_collection_select_V2 \
		--excel-dir ../../cadllm_raw/ccs_description_text \
		--output ../jsonl/cadllm_2d_with_descriptions.jsonl
	@echo "✅ Dataset recreated with descriptions"

clean-dataset: ## Clean dataset (normalize coordinates, close shapes, apply dimensions)
	@echo "🧹 Cleaning dataset..."
	@if [ ! -f "$(JSONL_DIR)/cadllm_2d_with_descriptions.jsonl" ]; then \
		echo "❌ Error: Dataset with descriptions not found. Run 'make recreate-dataset' first."; \
		exit 1; \
	fi
	cd $(DATASET_SCRIPTS_DIR) && python clean_dataset.py \
		--input ../jsonl/cadllm_2d_with_descriptions.jsonl \
		--output ../jsonl/cadllm_2d_cleaned.jsonl
	@echo "✅ Dataset cleaned and ready for training"

generate-enhanced-dataset: ## Generate enhanced dataset (200k+ examples with simple prompts -> enhanced descriptions)
	@echo "🔄 Generating enhanced CAD dataset..."
	@echo "   This creates examples where:"
	@echo "   - Instruction: Simple user prompts (e.g., 'a kitchen floor plan that has sink, gas burners')"
	@echo "   - Output: Enhanced detailed descriptions (e.g., 'Kitchen floor plan (4000mm x 3000mm) with:...')"
	cd $(SCRIPTS_DIR) && python generate_enhanced_dataset.py
	@echo "✅ Enhanced dataset generated!"
	@echo "   File: $(JSONL_DIR)/cadllm_enhanced.jsonl"

prepare-dataset: download-dataset recreate-dataset clean-dataset ## Complete dataset preparation pipeline
	@echo "✅ Dataset preparation complete!"
	@echo "   Ready for training: $(JSONL_DIR)/cadllm_2d_cleaned.jsonl"

train: ## Start training (use on RunPod server - sets up scripts and runs training)
	@echo "🚀 Starting training..."
	@echo "   Making scripts executable..."
	@cd $(TRAINING_DIR) && chmod +x train.sh run.sh
	@echo "   Using configuration:"
	@echo "     DATA_PATH: $${DATA_PATH:-$(SERVER_DATA_PATH)}"
	@echo "     OUTPUT_DIR: $${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)}"
	@echo ""
	@echo "   Note: run.sh will automatically install dependencies if needed"
	@echo ""
	@cd $(TRAINING_DIR) && DATA_PATH=$${DATA_PATH:-$(SERVER_DATA_PATH)} \
	OUTPUT_DIR=$${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)} \
	./run.sh

train-resume: ## Resume training from latest checkpoint (auto-detects) or specify CHECKPOINT=path/to/checkpoint
	@echo "🔄 Resuming training from checkpoint..."
	@echo "   Making scripts executable..."
	@cd $(TRAINING_DIR) && chmod +x train.sh
	@echo "   Using configuration:"
	@echo "     DATA_PATH: $${DATA_PATH:-$(SERVER_DATA_PATH)}"
	@echo "     OUTPUT_DIR: $${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)}"
	@if [ -n "$$CHECKPOINT" ]; then \
		echo "     CHECKPOINT: $$CHECKPOINT (specified)"; \
	else \
		echo "     CHECKPOINT: (auto-detect latest)"; \
	fi
	@echo ""
	@echo "   The script will automatically find the latest checkpoint if not specified."
	@echo ""
	@cd $(TRAINING_DIR) && if [ -n "$$CHECKPOINT" ]; then \
		DATA_PATH=$${DATA_PATH:-$(SERVER_DATA_PATH)} \
		OUTPUT_DIR=$${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)} \
		./train.sh \
			--data_path $${DATA_PATH:-$(SERVER_DATA_PATH)} \
			--output_dir $${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)} \
			--resume_from_checkpoint "$$CHECKPOINT"; \
	else \
		DATA_PATH=$${DATA_PATH:-$(SERVER_DATA_PATH)} \
		OUTPUT_DIR=$${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)} \
		./train.sh \
			--data_path $${DATA_PATH:-$(SERVER_DATA_PATH)} \
			--output_dir $${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)}; \
	fi

package: ## Create tarball of workspace for upload to RunPod (excludes large files)
	@echo "📦 Creating workspace package..."
	@echo "   This excludes model checkpoints, raw dataset, and logs"
	@echo "   Includes Makefile for easy training on server"
	@echo "✅ Package created: $(PACKAGE_NAME)"
	@echo "   Size: $$(du -h $(PACKAGE_NAME) | cut -f1)"
	@echo ""
	@echo "📤 Upload to RunPod:"
	@echo "   scp $(PACKAGE_NAME) root@<pod-ip>:/workspace/"
	@echo "   ssh root@<pod-ip>"
	@echo "   cd /workspace && tar --no-same-owner --warning=no-unknown-keyword -xzf $(PACKAGE_NAME)"
	@echo "   make train  # Start training with correct paths"

package-with-dataset: ## Create tarball including cleaned dataset (larger file)
	@echo "📦 Creating workspace package with cleaned dataset..."
	@if [ ! -f "$(JSONL_DIR)/cadllm_2d_cleaned.jsonl" ]; then \
		echo "❌ Error: Cleaned dataset not found. Run 'make prepare-dataset' first."; \
		exit 1; \
	fi
	@tar -czf $(PACKAGE_NAME) \
		--exclude='cad-agent-qwen-*' \
		--exclude='dataset/cadllm_raw' \
		--exclude='logs' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='.DS_Store' \
		--exclude='._*' \
		--exclude='*.tar.gz' \
		--exclude='NVIDIA-H200-NVL' \
		--exclude='ollama-models' \
		scripts/ dataset/ docs/ requirements.txt Makefile README.md
	@echo "✅ Package created: $(PACKAGE_NAME)"
	@echo "   Size: $$(du -h $(PACKAGE_NAME) | cut -f1)"

package-with-enhanced-dataset: ## Create tarball including enhanced dataset (for training with simple prompts)
	@echo "📦 Creating workspace package with enhanced dataset..."
	@if [ ! -f "$(JSONL_DIR)/cadllm_final.jsonl" ]; then \
		echo "❌ Error: Enhanced dataset not found. Run 'make generate-enhanced-dataset' first."; \
		exit 1; \
	fi
	@tar -czf $(PACKAGE_NAME) \
		--exclude='cad-agent-qwen-*' \
		--exclude='logs' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='.DS_Store' \
		--exclude='._*' \
		--exclude='*.tar.gz' \
		--exclude='NVIDIA-H200-NVL' \
		--exclude='ollama-models' \
		scripts/ dataset/ docs/ requirements.txt Makefile README.md
	@echo "✅ Package created: $(PACKAGE_NAME)"
	@echo "   Size: $$(du -h $(PACKAGE_NAME) | cut -f1)"
	@echo ""
	@echo "📤 Upload to RunPod:"
	@echo "   scp $(PACKAGE_NAME) root@<pod-ip>:/workspace/"
	@echo "   ssh root@<pod-ip>"
	@echo "   cd /workspace && tar --no-same-owner --warning=no-unknown-keyword -xzf $(PACKAGE_NAME)"
	@echo "   make train DATA_PATH=/workspace/dataset/jsonl/cadllm_final.jsonl"

extract: unarchive ## Alias for unarchive target
	@echo "✅ Use 'make unarchive' to extract the package"

unarchive: ## Extract workspace package on training machine (RunPod) - use after manual extraction
	@echo "📦 Verifying extraction..."
	@if [ ! -f "Makefile" ]; then \
		echo "❌ Error: Makefile not found. Please extract the archive first:"; \
		echo "   tar --no-same-owner --warning=no-unknown-keyword -xzf cadllm-workspace.tar.gz"; \
		echo ""; \
		echo "   This suppresses ownership and extended attribute warnings (harmless but noisy)."; \
		exit 1; \
	fi
	@echo "✅ Package already extracted (Makefile found)"
	@echo ""
	@echo "📋 Next steps:"
	@echo "   make train DATA_PATH=/workspace/dataset/jsonl/cadllm_enhanced.jsonl"
	@echo ""
	@echo "   Or to use the cleaned dataset:"
	@echo "   make train DATA_PATH=/workspace/dataset/jsonl/cadllm_2d_cleaned.jsonl"

test-api: ## Test Hugging Face API (requires .env file with HF_TOKEN)
	@echo "🧪 Testing Hugging Face API..."
	cd $(TESTING_DIR) && python test_hf_api.py
	@echo "✅ API test complete"

test-api-custom: ## Test Hugging Face API with custom prompt (usage: make test-api-custom PROMPT="your prompt")
	@if [ -z "$(PROMPT)" ]; then \
		echo "❌ Error: PROMPT not set. Usage: make test-api-custom PROMPT='your prompt'"; \
		exit 1; \
	fi
	@echo "🧪 Testing Hugging Face API with prompt: $(PROMPT)"
	cd $(TESTING_DIR) && python test_hf_api.py "$(PROMPT)"
	@echo "✅ API test complete"

infer-local: ## Run model locally on Mac using Ollama (requires .env with OLLAMA_MODEL_NAME)
	@echo "💻 Running model locally on Mac (Ollama)..."
	@echo "   Loading configuration from .env file..."
	@if [ -n "$$PROMPT" ]; then \
		cd $(INFERENCE_DIR) && python infer_local_mac.py "$$PROMPT"; \
	else \
		cd $(INFERENCE_DIR) && python infer_local_mac.py; \
	fi
	@echo "✅ Local inference complete"

merge-model: ## Merge LoRA adapter with base model (requires .env file with ADAPTER_PATH, OUTPUT_DIR, BASE_MODEL)
	@echo "🔧 Merging LoRA adapter with base model..."
	@echo "   Loading configuration from .env file..."
	@cd $(MODEL_MGMT_DIR) && python merge_model.py
	@echo "✅ Model merge complete"

upload-model: ## Upload merged model to Hugging Face (requires .env file with MODEL_PATH, BASE_MODEL, HF_TOKEN, HF_USERNAME, HF_FINE_TUNED_MODEL_NAME)
	@echo "📤 Uploading merged model to Hugging Face..."
	@echo "   Loading configuration from .env file..."
	@cd $(MODEL_MGMT_DIR) && python upload_model.py
	@echo "✅ Model upload complete"

upload-dataset: ## Upload dataset to Hugging Face (requires .env file with DATASET_PATH, HF_DATASET_NAME, HF_TOKEN, HF_USERNAME)
	@echo "📤 Uploading dataset to Hugging Face..."
	@echo "   Loading configuration from .env file..."
	@if [ ! -f ".env" ]; then \
		echo "❌ Error: .env file not found. Please create it first."; \
		exit 1; \
	fi
	@cd $(MODEL_MGMT_DIR) && python upload_dataset.py
	@echo "✅ Dataset upload complete"

deploy-ollama: ## Deploy merged model to Ollama (requires .env file with MODEL_PATH, optional: OLLAMA_MODEL_NAME, GGUF_OUTPUT_DIR, LLAMA_CPP_PATH)
	@echo "🦙 Deploying model to Ollama..."
	@echo "   Loading configuration from .env file..."
	@echo "   Note: This requires llama.cpp to be installed"
	@echo "   Install from: https://github.com/ggerganov/llama.cpp"
	@cd $(DEPLOYMENT_DIR) && python deploy_ollama.py
	@echo "✅ Ollama deployment complete"

ollama-start: ## Start Ollama server
	@echo "🚀 Starting Ollama server..."
	@if pgrep -f "ollama serve" > /dev/null 2>&1; then \
		echo "   ✅ Ollama is already running"; \
		echo "   Access at: http://localhost:11434"; \
	else \
		if command -v ollama > /dev/null 2>&1; then \
			echo "   Starting Ollama server in background..."; \
			ollama serve > /dev/null 2>&1 & \
			sleep 2; \
			if pgrep -f "ollama serve" > /dev/null 2>&1; then \
				echo "   ✅ Ollama started successfully"; \
				echo "   Access at: http://localhost:11434"; \
			else \
				echo "   ⚠️  Ollama may have failed to start"; \
				echo "   Try running manually: ollama serve"; \
				echo "   Or open the Ollama app if installed via macOS app"; \
			fi; \
		else \
			echo "   ❌ Ollama command not found"; \
			echo "   Install Ollama from: https://ollama.ai"; \
			echo "   Or via Homebrew: brew install ollama"; \
			exit 1; \
		fi; \
	fi

ollama-stop: ## Stop Ollama server
	@echo "🛑 Stopping Ollama server..."
	@if pgrep -f "ollama serve" > /dev/null 2>&1; then \
		echo "   Found Ollama process, stopping..."; \
		pkill -f "ollama serve" && \
		sleep 1 && \
		if pgrep -f "ollama serve" > /dev/null 2>&1; then \
			echo "   ⚠️  Process still running, trying force kill..."; \
			pkill -9 -f "ollama serve" && \
			sleep 1; \
		fi; \
		if pgrep -f "ollama serve" > /dev/null 2>&1; then \
			echo "   ❌ Failed to stop Ollama. Try manually: killall ollama"; \
			exit 1; \
		else \
			echo "   ✅ Ollama stopped successfully"; \
		fi; \
	else \
		echo "   ⚠️  Ollama is not running"; \
	fi

ollama-start-all: ## Start both Ollama server and Open WebUI
	@echo "🚀 Starting Ollama and Open WebUI..."
	@echo ""
	@$(MAKE) ollama-start
	@echo ""
	@$(MAKE) open-webui-start
	@echo ""
	@echo "✅ Both Ollama and Open WebUI are running!"
	@echo "   Ollama: http://localhost:11434"
	@echo "   Open WebUI: http://localhost:3000"

ollama-stop-all: ## Stop both Ollama server and Open WebUI
	@echo "🛑 Stopping Ollama and Open WebUI..."
	@echo ""
	@$(MAKE) open-webui-stop
	@echo ""
	@$(MAKE) ollama-stop
	@echo ""
	@echo "✅ Both Ollama and Open WebUI have been stopped"

open-webui-start: ## Start Open WebUI container for Ollama (accessible at http://localhost:3000)
	@echo "🌐 Starting Open WebUI for Ollama..."
	@if docker ps -a --format '{{.Names}}' | grep -q '^open-webui$$'; then \
		echo "   Container 'open-webui' already exists"; \
		if docker ps --format '{{.Names}}' | grep -q '^open-webui$$'; then \
			echo "   ✅ Open WebUI is already running"; \
			echo "   Access at: http://localhost:3000"; \
		else \
			echo "   🔄 Starting existing container..."; \
			docker start open-webui && \
			echo "   ✅ Open WebUI started"; \
			echo "   Access at: http://localhost:3000"; \
		fi; \
	else \
		echo "   🐳 Creating and starting Open WebUI container..."; \
		docker run -d -p 3000:8080 \
			--add-host=host.docker.internal:host-gateway \
			-v open-webui:/app/backend/data \
			--name open-webui \
			--restart always \
			ghcr.io/open-webui/open-webui:main && \
		echo "   ✅ Open WebUI started"; \
		echo "   Access at: http://localhost:3000"; \
		echo "   Note: Open WebUI will automatically connect to your local Ollama instance"; \
	fi

open-webui-stop: ## Stop Open WebUI container
	@echo "🛑 Stopping Open WebUI..."
	@if docker ps --format '{{.Names}}' | grep -q '^open-webui$$'; then \
		docker stop open-webui && \
		echo "   ✅ Open WebUI stopped"; \
	else \
		echo "   ⚠️  Open WebUI is not running"; \
	fi

open-webui-logs: ## Show Open WebUI container logs
	@echo "📋 Open WebUI logs (Ctrl+C to exit):"
	@docker logs -f open-webui 2>/dev/null || echo "   ❌ Container 'open-webui' not found. Run 'make open-webui-start' first."

open-webui-status: ## Check Open WebUI container status
	@echo "📊 Open WebUI Status:"
	@if docker ps -a --format '{{.Names}}' | grep -q '^open-webui$$'; then \
		if docker ps --format '{{.Names}}' | grep -q '^open-webui$$'; then \
			echo "   ✅ Running"; \
			echo "   Access at: http://localhost:3000"; \
			docker ps --filter name=open-webui --format "   Container ID: {{.ID}}\n   Status: {{.Status}}"; \
		else \
			echo "   ⏸️  Stopped"; \
			echo "   Run 'make open-webui-start' to start it"; \
		fi; \
	else \
		echo "   ❌ Container not found"; \
		echo "   Run 'make open-webui-start' to create and start it"; \
	fi

update-space: ## Update Space app with latest model name from .env (does not deploy)
	@echo "🔄 Updating Space app configuration..."
	@if [ ! -f ".env" ]; then \
		echo "❌ Error: .env file not found. Please create it first."; \
		exit 1; \
	fi
	@echo "   Loading model name from .env..."
	@if [ -f .env ]; then \
		. .env && \
		if [ -n "$$HF_MODEL_NAME" ]; then \
			echo "   ✅ Found HF_MODEL_NAME=$$HF_MODEL_NAME"; \
			echo "   📝 Updating app.py default model name..."; \
			sed -i.bak "s|MODEL_NAME = os.getenv(\"HF_MODEL_NAME\", \".*\")|MODEL_NAME = os.getenv(\"HF_MODEL_NAME\", \"$$HF_MODEL_NAME\")|g" $(SPACE_DIR)/app.py && \
			rm -f $(SPACE_DIR)/app.py.bak && \
			echo "   ✅ Updated app.py"; \
		else \
			echo "   ⚠️  HF_MODEL_NAME not found in .env, using default"; \
		fi; \
	fi
	@echo "✅ Space app updated (run 'make deploy-space' to push changes)"

deploy-space: ## Deploy Space app to Hugging Face (pushes space directory to HF Space repo)
	@echo "🚀 Deploying Space app to Hugging Face..."
	@if [ ! -d "$(SPACE_DIR)" ]; then \
		echo "❌ Error: Space directory not found at $(SPACE_DIR)"; \
		exit 1; \
	fi
	@echo "   Using temporary git repository to push Space directory to Hugging Face..."
	@python $(DEPLOYMENT_DIR)/deploy_space.py \
		--space_dir "$$(cd $(SPACE_DIR) && pwd)" \
		--commit_message "Update Space app configuration"
	@echo "✅ Deployment complete"

clean: ## Remove generated files (package, __pycache__, etc.)
	@echo "🧹 Cleaning generated files..."
	rm -f $(PACKAGE_NAME)
	find $(SCRIPTS_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(SCRIPTS_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	find $(DATASET_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(DATASET_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

clean-all: clean ## Remove all generated files including processed datasets
	@echo "🧹 Cleaning all generated files..."
	rm -f $(JSONL_DIR)/cadllm_2d_with_descriptions.jsonl
	rm -f $(JSONL_DIR)/cadllm_2d_cleaned.jsonl
	@echo "⚠️  Note: Raw dataset in $(RAW_DIR) is preserved"
	@echo "✅ Clean complete"

info: ## Show project information and file sizes
	@echo "📊 CADLLM Project Information"
	@echo "=============================="
	@echo ""
	@echo "Scripts: $(SCRIPTS_DIR)"
	@echo "Dataset: $(DATASET_DIR)"
	@echo "Documentation: docs/"
	@echo ""
	@echo "📁 Directory Structure:"
	@echo "  scripts/"
	@find $(SCRIPTS_DIR) -maxdepth 1 -type d | sed 's|^|    |' || echo "    (empty)"
	@echo "  dataset/"
	@find $(DATASET_DIR) -maxdepth 1 -type d | sed 's|^|    |' || echo "    (empty)"
	@echo ""
	@echo "📄 Python Scripts by Category:"
	@echo "  Training: $$(find $(TRAINING_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo "  Inference: $$(find $(INFERENCE_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo "  Testing: $$(find $(TESTING_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo "  Model Management: $$(find $(MODEL_MGMT_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo "  Deployment: $$(find $(DEPLOYMENT_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo "  Utils: $$(find $(UTILS_DIR) -name "*.py" -type f 2>/dev/null | wc -l | xargs)"
	@echo ""
	@echo "📦 Dataset Files:"
	@if [ -f "$(JSONL_DIR)/cadllm_2d_cleaned.jsonl" ]; then \
		echo "  ✅ cadllm_2d_cleaned.jsonl: $$(du -h $(JSONL_DIR)/cadllm_2d_cleaned.jsonl | cut -f1)"; \
	else \
		echo "  ❌ cadllm_2d_cleaned.jsonl: Not found"; \
	fi
	@if [ -f "$(JSONL_DIR)/cadllm_2d_with_descriptions.jsonl" ]; then \
		echo "  ✅ cadllm_2d_with_descriptions.jsonl: $$(du -h $(JSONL_DIR)/cadllm_2d_with_descriptions.jsonl | cut -f1)"; \
	else \
		echo "  ❌ cadllm_2d_with_descriptions.jsonl: Not found"; \
	fi
	@echo ""
	@echo "📋 Package:"
	@if [ -f "$(PACKAGE_NAME)" ]; then \
		echo "  ✅ $(PACKAGE_NAME): $$(du -h $(PACKAGE_NAME) | cut -f1)"; \
	else \
		echo "  ❌ $(PACKAGE_NAME): Not found"; \
	fi

