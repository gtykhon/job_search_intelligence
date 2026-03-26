from sentence_transformers import SentenceTransformer
m = SentenceTransformer('all-MiniLM-L6-v2')
v = m.encode('test sentence')
print(f"OK — model loaded, embedding dim={len(v)}")
