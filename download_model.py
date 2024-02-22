import os

from transformers import AutoTokenizer, AutoModel


os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./.cache"


tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")
