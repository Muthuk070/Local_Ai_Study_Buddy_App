from sentence_transformers import SentenceTransformer
from study_rag_service.ingestion.chunker import get_model

model = get_model()

# Function to generate embedding for a given text
def generate_embedding(text):
    
    vector = model.encode(text)
    return vector.tolist()