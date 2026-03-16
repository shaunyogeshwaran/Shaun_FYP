"""Test components using transformers directly (skip sentence-transformers)."""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
print(f"Python: {sys.executable}", flush=True)

print("\nStep 1: Testing PyTorch...", flush=True)
import torch
print(f"  PyTorch version: {torch.__version__}", flush=True)

print("\nStep 2: Testing transformers AutoModel...", flush=True)
from transformers import AutoTokenizer, AutoModel
print("  Import OK", flush=True)

print("\nStep 3: Loading MiniLM via transformers (not sentence-transformers)...", flush=True)
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
print("  Tokenizer loaded", flush=True)
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
print("  Model loaded", flush=True)

print("\nStep 4: Testing embedding...", flush=True)
inputs = tokenizer(["test query"], padding=True, truncation=True, return_tensors='pt')
with torch.no_grad():
    outputs = model(**inputs)
embeddings = outputs.last_hidden_state.mean(dim=1)
print(f"  Embedding shape: {embeddings.shape}", flush=True)

print("\nStep 5: Testing FAISS...", flush=True)
import faiss
import numpy as np
index = faiss.IndexFlatIP(384)
index.add(np.random.rand(5, 384).astype('float32'))
print(f"  FAISS index: {index.ntotal} vectors", flush=True)

print("\nStep 6: Testing RoBERTa-MNLI...", flush=True)
from transformers import AutoModelForSequenceClassification
nli_tokenizer = AutoTokenizer.from_pretrained("FacebookAI/roberta-large-mnli")
nli_model = AutoModelForSequenceClassification.from_pretrained("FacebookAI/roberta-large-mnli")
print("  RoBERTa loaded", flush=True)

print("\n=== All tests passed! ===", flush=True)
