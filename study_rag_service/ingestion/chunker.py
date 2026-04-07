from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import tiktoken
import warnings
import logging
import os

import sys
# Suppress the symlink warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")



# --- STOP ALL LOGGING BEFORE IMPORTS ---
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


#calculate the text length in tokens using tiktoken
tokenizer = None
def get_tokenizer():
    global tokenizer
    if tokenizer is None:
        tokenizer = tiktoken.get_encoding("cl100k_base")
    return tokenizer

def tiktoken_len(text):
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))





# Global model variable to ensure it's loaded only once -embeddings model
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        # Optional: Control max sequence length up to 8192
        model.max_seq_length = 512
    return model



#chunker for text splitting and object to split text into chunks with overlap and token length calculation
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=tiktoken_len,
    separators=[" ", ""]
)








