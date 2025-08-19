#!/usr/bin/env python3
"""
Simple Gemma 2B Fine-tuning Script
This script fine-tunes the Gemma 2B model on question/answer classification data.
"""

import json
import sys


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "torch",
        "transformers",
        "datasets",
        "peft",
        "accelerate",
        "bitsandbytes",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print("pip install -r requirements_training.txt")
        return False
    return True


def install_dependencies():
    """Install required dependencies"""
    print("Installing required dependencies...")
    import subprocess

    packages = [
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "datasets>=2.14.0",
        "peft>=0.6.0",
        "accelerate>=0.24.0",
        "bitsandbytes>=0.41.0",
        "huggingface_hub>=0.17.0",
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            return False

    return True


def main():
    """Main training function"""
    print("Gemma 2B Fine-tuning Script")
    print("=" * 30)

    # Force CPU usage BEFORE any PyTorch imports
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
    os.environ["PYTORCH_DISABLE_MPS"] = "1"  # Completely disable MPS

    # Check dependencies
    if not check_dependencies():
        response = input("Would you like to install missing dependencies? (y/n): ")
        if response.lower() == "y":
            if not install_dependencies():
                print("Failed to install dependencies. Exiting.")
                return
        else:
            print("Dependencies required. Exiting.")
            return

    # Now import the required modules
    try:
        import torch

        # Without a GPU, we must ensure we are not using MPS
        # Additional MPS disabling after torch import
        if hasattr(torch.backends, "mps"):
            torch.backends.mps.is_available = lambda: False
            torch.backends.mps.is_built = lambda: False

        # Force CPU as default device
        torch.set_default_device("cpu")
        torch.set_default_dtype(torch.float32)

        print("PyTorch configured for CPU-only usage")

        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
        )
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from huggingface_hub import login

        print("All dependencies loaded successfully")

    except ImportError as e:
        print(f"Failed to import required modules: {e}")
        return

    # Login to Hugging Face. Needed for model access.
    print("\nLogging into Hugging Face...")
    try:
        login(token="your_huggingface_token_here")  # Replace with your token
        print("Hugging Face login successful")
    except Exception as e:
        print(f"Hugging Face login failed: {e}")
        return

    # Configuration - Using smaller Gemma model
    # Why Gemma 2B?
    # - Smaller size (2B parameters) for faster training and lower memory usage
    # - Still capable of handling complex tasks
    # - Good balance between performance and resource requirements
    model_name = "google/gemma-2b"
    data_path = "./generated_questions"
    output_dir = "./gemma-2b-search-classifier"

    print(f"\nConfiguration:")
    print(f"Model: {model_name}")
    print(f"Data: {data_path}")
    print(f"Output: {output_dir}")

    # Check if data file exists
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}")
        return

    print(f"Data file found: {data_path}")

    def load_training_data(data_folder, file_pattern="*.jsonl", max_files=None):
        """
        Load training data from multiple JSONL files in a folder

        Args:
            data_folder: Path to folder containing JSONL files
            file_pattern: Pattern to match files (default: "*.jsonl")
            max_files: Maximum number of files to load (None for all)

        Returns:
            List of training examples
        """
        import glob

        # Find matching files
        pattern_path = os.path.join(data_folder, file_pattern)
        jsonl_files = glob.glob(pattern_path)

        if not jsonl_files:
            raise ValueError(f"No files matching {file_pattern} found in {data_folder}")

        # Sort files for consistent ordering
        jsonl_files.sort()

        # Limit number of files if specified
        if max_files:
            jsonl_files = jsonl_files[:max_files]

        print(f"Loading from {len(jsonl_files)} files:")

        all_data = []
        file_stats = {}

        for file_path in jsonl_files:
            filename = os.path.basename(file_path)
            file_data = []

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line:
                            try:
                                item = json.loads(line)
                                # Validate required fields
                                if (
                                    isinstance(item, dict)
                                    and "question" in item
                                    and "category" in item
                                ):
                                    file_data.append(item)
                                else:
                                    print(
                                        f"Invalid item in {filename}, line {line_num}"
                                    )
                            except json.JSONDecodeError as e:
                                print(f"JSON error in {filename}, line {line_num}: {e}")
                                continue

                file_stats[filename] = len(file_data)
                all_data.extend(file_data)
                print(f"  {filename}: {len(file_data)} examples")

            except Exception as e:
                print(f"Failed to load {filename}: {e}")
                continue

        print(f"\nSummary:")
        print(f"  Files processed: {len(file_stats)}")
        print(f"  Total examples: {len(all_data)}")

        return all_data, file_stats

    # Load data
    print("\nLoading training data...")
    try:
        data, file_stats = load_training_data(
            data_folder="./generated_questions",
            file_pattern="*.jsonl",  # Load all JSONL files
            max_files=None,  # No limit, or set to a number like 10
        )

        if len(data) == 0:
            print("No valid training data found. Exiting.")
            return

    except Exception as e:
        print(f"Failed to load training data: {e}")
        return

    # Preview data
    print("\nData preview:")
    for i, item in enumerate(data[:3]):
        print(f"Example {i+1}:")
        print(f"  Question: {item.get('question', '')[:100]}...")
        print(f"  Categories: {item.get('category', [])}")

    # Load model and tokenizer
    print(f"\nLoading model and tokenizer: {model_name}")
    print("CPU-only mode enabled - training will be slower but uses less memory")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # More config needed to ensure CPU compatibility
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility.
            device_map=None,  # Don't use device_map at all. Device map tries to use GPU by default.
            low_cpu_mem_usage=False,  # We have a lot of RAM, so disable this.
            trust_remote_code=True,
        )

        # Force model to CPU explicitly
        model = model.to("cpu")
        model = model.float()  # Ensure float32

        # Verify model is on CPU
        print(f"Model device: {next(model.parameters()).device}")
        print("Model and tokenizer loaded on CPU")

    except Exception as e:
        print(f"Failed to load model: {e}")
        print("This might be due to insufficient memory or model access issues.")
        print("For CPU training, ensure you have sufficient RAM (16GB+ recommended).")
        return

    # Setup LoRA
    # We use LoRA for efficient fine-tuning.
    # Original model weights are frozen and only LoRA layers are adjusted.
    print("\nSetting up LoRA for efficient fine-tuning...")
    try:
        # Enable gradient checkpointing BEFORE LoRA setup
        model.gradient_checkpointing_enable()
        # Skip prepare_model_for_kbit_training for CPU training
        model = prepare_model_for_kbit_training(model)

        # Check actual module names for Gemma 2B
        print("Model modules:")
        target_modules_found = []
        for name, module in model.named_modules():
            if any(
                target in name for target in ["q_proj", "v_proj", "k_proj", "o_proj"]
            ):
                print(f"  Found target module: {name}")
                target_modules_found.append(name.split(".")[-1])

        # Use only the modules we actually found
        if not target_modules_found:
            print("No standard target modules found, using fallback...")
            target_modules_found = ["q_proj", "v_proj", "k_proj", "o_proj"]

        lora_config = LoraConfig(
            r=8,  # Rank/Dimension of LoRA layers. Lower is faster but less expressive.
            lora_alpha=16,  # Scaling factor. How much LoRA layers contribute to the output.
            target_modules=list(set(target_modules_found)),  # Only use found modules
            lora_dropout=0.1,  # Regularization/dropout rate. Helps prevent overfitting.
            bias="none",  # Controls if bias terms are added to LoRA layers.
            task_type="CAUSAL_LM",  # Which model architecture this is for.
            inference_mode=False,  # Must be false for training. Otherwise weights are locked.
        )

        model = get_peft_model(model, lora_config)

        # Ensure LoRA model is also on CPU
        model = model.to("cpu")

        model.print_trainable_parameters()
        print("LoRA setup complete")

    except Exception as e:
        print(f"LoRA setup failed: {e}")
        return

    # Prepare training data
    print("\nPreparing training data...")

    def create_training_prompt(question, categories):
        categories_str = ", ".join(categories) if categories else "semantic"

        prompt = f"""<bos>Your job is to identify which type of search is required to gather the appropriate context to answer the attached question.
        The search options are as follows:
                semantic: questions that require a vector similarity search to find relevant information
                explicit: questions that a neo4j cypher query can provide context for
                global: questions that require a broader understanding of the legal domain and may involve multiple documents or sections

        You can choose one or more of these options to answer the question, but try to avoid performing searching that would not be applicable to the question.

        Question: {question}

        Answer: {categories_str}<eos>
        """

        return prompt

    # Prepare training examples
    training_examples = []
    for item in data:
        question = item.get("question", "")
        categories = item.get("category", [])
        prompt = create_training_prompt(question, categories)
        training_examples.append({"text": prompt})

    # Create dataset
    dataset = Dataset.from_list(training_examples)

    # Tokenize
    def tokenize_function(examples):
        # Tokenize the text properly for batched processing
        tokenized = tokenizer(
            examples["text"],  # Because incoming data has "text" key
            truncation=True,  # Cuts off text longer than max_length below
            padding="max_length",  # Use max_length padding for consistent tensor shapes
            max_length=512,  # 512 is a safe length for Gemma 2B
        )
        # For causal language modeling, labels should be the same as input_ids
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    print("Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,  # Remove original text column
    )

    # Debug: Check tokenized dataset structure
    print("Tokenization complete")
    print(f"Dataset columns: {tokenized_dataset.column_names}")
    print(f"First example keys: {list(tokenized_dataset[0].keys())}")

    # Check data types
    sample = tokenized_dataset[0]
    for key, value in sample.items():
        print(
            f"  {key}: type={type(value)}, length={len(value) if hasattr(value, '__len__') else 'N/A'}"
        )

    train_test_split = tokenized_dataset.train_test_split(test_size=0.1)
    train_dataset = train_test_split["train"]
    eval_dataset = train_test_split["test"]

    print(f"Training examples: {len(train_dataset)}")
    print(f"Validation examples: {len(eval_dataset)}")

    # Training arguments
    training_args = TrainingArguments(
        # Core parameters
        output_dir=output_dir,
        num_train_epochs=2,  # More epochs = longer, possibly better training, possibly overfitting.
        per_device_train_batch_size=1,  # Number examples processed simultaneously. 1 is memory safe for CPU.
        per_device_eval_batch_size=1,  # Same for evaluation. Could be larger if memory allows.
        gradient_accumulation_steps=4,  # Number of steps before updating model weights.
        # Learning parameters
        warmup_steps=10,  # Learning rate from 0 to target over this many steps.
        learning_rate=2e-4,  # Size of steps when adjusting model weights.
        weight_decay=0.01,  # Decrease in model weights over time to prevent overfitting.
        fp16=False,  # Disable FP16 for CPU training. We want the full 32.
        bf16=False,  # Disable BF16 as well
        optim="adamw_torch",  # Use standard AdamW for CPU. Good for transformer finetuning.
        # Monitoring and saving
        logging_steps=5,  # How often to log training progress.
        eval_strategy="steps",  # Compared to epoch. Steps are more frequent and can catch issues earlier.
        eval_steps=50,  # Run eval every x steps.
        save_steps=100,  # Save checkpoint every x steps.
        save_total_limit=2,  # Keep the last x checkpoints to save disk space.
        load_best_model_at_end=True,  # Based on validation score, load the best model at the end of training.
        # System Config
        report_to=None,  # No external logging
        dataloader_drop_last=False,  # Whether to drop the last incomplete batch. False means we use it.
        dataloader_pin_memory=False,  # Disable for CPU training.
        dataloader_num_workers=0,  # Single threaded for CPU = 0
        remove_unused_columns=False,  # Shouldn't actually matter here as we don't have unused columns
        use_cpu=True,  # Force CPU usage in training args
        gradient_checkpointing=False,  # Disable in training args since we enable it manually
    )

    # Data collator - use DataCollatorForLanguageModeling without MLM
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # We're doing causal language modeling, not masked language modeling
        pad_to_multiple_of=8,  # Optional: pad to multiple of 8 for efficiency
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    # Start training
    print(f"\nStarting training...")
    print(f"Output directory: {output_dir}")

    try:
        trainer.train()

        # Save the final model
        trainer.save_model()
        tokenizer.save_pretrained(output_dir)

        print(f"Training completed successfully!")
        print(f"Model saved to: {output_dir}")

        # Test the model
        print("\nTesting the trained model...")
        test_question = "What is the process for filing a complaint against a government agency in Canada?"

        input_text = f"""Your job is to identify which type of search is required to gather the appropriate context to answer the attached question.
        The search options are as follows:
                semantic: questions that require a vector similarity search to find relevant information
                explicit: questions that a neo4j cypher query can provide context for
                global: questions that require a broader understanding of the legal domain and may involve multiple documents or sections

        Question: {test_question}

        Answer:"""

        inputs = tokenizer(input_text, return_tensors="pt")

        # Ensure inputs are on CPU
        inputs = {k: v.cpu() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nTest Question: {test_question}")
        print(f"Model Response: {response[len(input_text):]}")
    except KeyboardInterrupt:
        print("\n Training interrupted by user")
        print("Saving current model state...")
        try:
            trainer.save_model(f"{output_dir}_interrupted")
            tokenizer.save_pretrained(f"{output_dir}_interrupted")
            print(f"✓ Model saved to: {output_dir}_interrupted")
        except Exception as e:
            print(f"✗ Failed to save interrupted model: {e}")
        return
    except Exception as e:
        print(f"✗ Training failed: {e}")
        return

    print("\n" + "=" * 50)
    print("Training completed successfully!")
    print(f"Your fine-tuned model is saved in: {output_dir}")
    print("You can now use this model for search type classification.")


if __name__ == "__main__":
    main()
