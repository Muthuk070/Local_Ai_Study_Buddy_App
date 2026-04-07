import json
import math

async def mysql_cosine_fallback(conn, dict_cursor, query_embedding, class_standard, subject,
                                top_k=2, candidate_limit=1000, min_similarity=0.65, min_results=1):
    """
    Query `notes_chunks` for candidates filtered by metadata (class_standard, subject),
    compute cosine similarity in Python and return top_k chunk_text strings.

    Behavior:
    - Filters results by `min_similarity`.
    - If fewer than `min_results` meet `min_similarity`, falls back to top-K by score.
    """
    cls = str(class_standard).lower().strip()
    sub = str(subject).lower().strip()

    sql = """
        SELECT note_id, chunk_text, embedding, metadata_payload
        FROM notes_chunks
        WHERE LCASE(JSON_UNQUOTE(JSON_EXTRACT(metadata_payload, '$.class_standard'))) = %s
          AND LCASE(JSON_UNQUOTE(JSON_EXTRACT(metadata_payload, '$.subject'))) = %s
          AND JSON_UNQUOTE(JSON_EXTRACT(metadata_payload, '$.status')) = 'active'
        LIMIT %s
    """

    await dict_cursor.execute(sql, (cls, sub, candidate_limit))
    rows = await dict_cursor.fetchall()
    if not rows:
        return []

    # ensure query vector is list of floats
    try:
        q = [float(x) for x in query_embedding]
    except Exception:
        return []

    q_norm = math.sqrt(sum(x * x for x in q)) if q else 0.0
    if q_norm == 0.0:
        return []

    candidates = []
    for r in rows:
        emb_raw = r.get('embedding') or r.get('embedding', '')
        try:
            emb = json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw
            emb = [float(x) for x in emb]
        except Exception:
            continue

        emb_norm = math.sqrt(sum(x * x for x in emb)) if emb else 0.0
        if emb_norm == 0.0:
            continue

        dot = sum(a * b for a, b in zip(q, emb))
        sim = dot / (q_norm * emb_norm)
        candidates.append((sim, r.get('chunk_text', '')))

    # sort descending by similarity
    candidates.sort(key=lambda x: x[0], reverse=True)

    # filter by threshold
    filtered = [c for c in candidates if c[0] >= float(min_similarity)]

    if len(filtered) >= int(min_results):
        selected = filtered[:top_k]
    else:
        # not enough above threshold -> return top_k candidates regardless
        selected = candidates[:top_k]

    top_chunks = [text for _, text in selected]
    return top_chunks
