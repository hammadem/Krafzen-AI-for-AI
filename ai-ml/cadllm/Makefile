.PHONY: help setup download-dataset recreate-dataset clean-dataset train test-api test-api-custom upload-model deploy-space update-space package package-with-dataset clean clean-all info

# Configuration
# When running locally (from cadllm root)
WORKSPACE_DIR = NVIDIA-H200-NVL/workspace
DATASET_DIR = $(WORKSPACE_DIR)/dataset
SCRIPTS_DIR = $(DATASET_DIR)/scripts
JSONL_DIR = $(DATASET_DIR)/jsonl
RAW_DIR = $(DATASET_DIR)/cadllm_raw
PACKAGE_NAME = cadllm-workspace.tar.gz

# When running on server (from /workspace)
# These paths are used by the 'train' target
SERVER_DATA_PATH = /workspace/dataset/jsonl/cadllm.jsonl
SERVER_OUTPUT_DIR = /workspace/cadllm

# Space deployment
SPACE_DIR = $(WORKSPACE_DIR)/space/cad-llm-api

help: ## Show this help message
	@echo "CADLLM Makefile - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	cd $(WORKSPACE_DIR) && pip install -r requirements.txt
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
	cd $(SCRIPTS_DIR) && python recreate_dataset_with_descriptions.py \
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
	cd $(SCRIPTS_DIR) && python clean_dataset.py \
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
	chmod +x train.sh run.sh
	@echo "   Using configuration:"
	@echo "     DATA_PATH: $${DATA_PATH:-$(SERVER_DATA_PATH)}"
	@echo "     OUTPUT_DIR: $${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)}"
	@echo ""
	@echo "   Note: run.sh will automatically install dependencies if needed"
	@echo ""
	DATA_PATH=$${DATA_PATH:-$(SERVER_DATA_PATH)} \
	OUTPUT_DIR=$${OUTPUT_DIR:-$(SERVER_OUTPUT_DIR)} \
	./run.sh

package: ## Create tarball of workspace for upload to RunPod (excludes large files)
	@echo "📦 Creating workspace package..."
	@echo "   This excludes model checkpoints, raw dataset, and logs"
	@echo "   Includes Makefile for easy training on server"
	# Copy Makefile to workspace directory for packaging
	cp Makefile $(WORKSPACE_DIR)/Makefile
	cd $(WORKSPACE_DIR) && tar -czf ../../$(PACKAGE_NAME) \
		--exclude='cad-agent-qwen-*' \
		--exclude='dataset/cadllm_raw' \
		--exclude='logs' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='.DS_Store' \
		--exclude='*.tar.gz' \
		.
	# Remove the copied Makefile from workspace (keep original in root)
	rm -f $(WORKSPACE_DIR)/Makefile
	@echo "✅ Package created: $(PACKAGE_NAME)"
	@echo "   Size: $$(du -h $(PACKAGE_NAME) | cut -f1)"
	@echo ""
	@echo "📤 Upload to RunPod:"
	@echo "   scp $(PACKAGE_NAME) root@<pod-ip>:/workspace/"
	@echo "   ssh root@<pod-ip>"
	@echo "   cd /workspace && tar -xzf $(PACKAGE_NAME)"
	@echo "   make train  # Start training with correct paths"

package-with-dataset: ## Create tarball including cleaned dataset (larger file)
	@echo "📦 Creating workspace package with cleaned dataset..."
	@if [ ! -f "$(JSONL_DIR)/cadllm_2d_cleaned.jsonl" ]; then \
		echo "❌ Error: Cleaned dataset not found. Run 'make prepare-dataset' first."; \
		exit 1; \
	fi
	# Copy Makefile to workspace directory for packaging
	cp Makefile $(WORKSPACE_DIR)/Makefile
	cd $(WORKSPACE_DIR) && tar -czf ../../$(PACKAGE_NAME) \
		--exclude='cad-agent-qwen-*' \
		--exclude='dataset/cadllm_raw' \
		--exclude='logs' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='.DS_Store' \
		--exclude='*.tar.gz' \
		.
	# Remove the copied Makefile from workspace (keep original in root)
	rm -f $(WORKSPACE_DIR)/Makefile
	@echo "✅ Package created: $(PACKAGE_NAME)"
	@echo "   Size: $$(du -h $(PACKAGE_NAME) | cut -f1)"

test-api: ## Test Hugging Face API (requires .env file with HF_TOKEN)
	@echo "🧪 Testing Hugging Face API..."
	cd $(WORKSPACE_DIR) && python test_hf_api.py
	@echo "✅ API test complete"

test-api-custom: ## Test Hugging Face API with custom prompt (usage: make test-api-custom PROMPT="your prompt")
	@if [ -z "$(PROMPT)" ]; then \
		echo "❌ Error: PROMPT not set. Usage: make test-api-custom PROMPT='your prompt'"; \
		exit 1; \
	fi
	@echo "🧪 Testing Hugging Face API with prompt: $(PROMPT)"
	cd $(WORKSPACE_DIR) && python test_hf_api.py "$(PROMPT)"
	@echo "✅ API test complete"

upload-model: ## Merge LoRA adapter and upload to Hugging Face (requires .env file)
	@echo "📤 Uploading model to Hugging Face..."
	cd $(WORKSPACE_DIR) && python upload_model.py
	@echo "✅ Model upload complete"

update-space: ## Update Space app with latest model name from .env (does not deploy)
	@echo "🔄 Updating Space app configuration..."
	@if [ ! -f "$(WORKSPACE_DIR)/.env" ]; then \
		echo "❌ Error: .env file not found. Please create it first."; \
		exit 1; \
	fi
	@echo "   Loading model name from .env..."
	@cd $(WORKSPACE_DIR) && \
		if [ -f .env ]; then \
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

deploy-space: ## Deploy Space app to Hugging Face (commits and pushes changes)
	@echo "🚀 Deploying Space app to Hugging Face..."
	@if [ ! -d "$(SPACE_DIR)" ]; then \
		echo "❌ Error: Space directory not found at $(SPACE_DIR)"; \
		exit 1; \
	fi
	@echo "   Checking git status..."
	@cd $(SPACE_DIR) && \
		if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$$(git status --porcelain)" ]; then \
			echo "   📝 Staging changes..."; \
			git add -A && \
			echo "   💾 Committing changes..."; \
			git commit -m "Update Space app configuration" || true && \
			echo "   📤 Pushing to Hugging Face Space..."; \
			git push origin main || git push origin master || true && \
			echo "   ✅ Space app deployed!"; \
			echo ""; \
			echo "   🌐 Your Space will rebuild automatically at:"; \
			echo "   https://huggingface.co/spaces/mkmad7/cad-llm-api"; \
		else \
			echo "   ✅ No changes to commit"; \
			echo "   💡 To force rebuild, make a small change or use Hugging Face UI"; \
		fi
	@echo "✅ Deployment complete"

clean: ## Remove generated files (package, __pycache__, etc.)
	@echo "🧹 Cleaning generated files..."
	rm -f $(PACKAGE_NAME)
	find $(WORKSPACE_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(WORKSPACE_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
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
	@echo "Workspace: $(WORKSPACE_DIR)"
	@echo ""
	@echo "Dataset files:"
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
	@echo "Raw dataset:"
	@if [ -d "$(RAW_DIR)/cad_collection_select_V2" ]; then \
		echo "  ✅ Raw dataset downloaded"; \
		echo "     Size: $$(du -sh $(RAW_DIR)/cad_collection_select_V2 2>/dev/null | cut -f1 || echo 'unknown')"; \
	else \
		echo "  ❌ Raw dataset not downloaded"; \
	fi
	@echo ""
	@echo "Python scripts:"
	@find $(WORKSPACE_DIR) -maxdepth 1 -name "*.py" -type f | wc -l | xargs echo "  Total:"
	@echo ""
	@if [ -f "$(PACKAGE_NAME)" ]; then \
		echo "Package: $(PACKAGE_NAME) ($$(du -h $(PACKAGE_NAME) | cut -f1))"; \
	else \
		echo "Package: Not created (run 'make package')"; \
	fi

