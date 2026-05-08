"""
Semantic embedding-based topic detection using nomic-embed-text.
Provides accurate topic matching for math problems via semantic similarity.
"""

import json
import urllib.request
from typing import Optional
import numpy as np


class EmbeddingEngine:
    """Handles semantic embeddings for topic detection."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.embed_endpoint = f"{self.base_url}/api/embed"
        self.model = "nomic-embed-text"
        self.embedding_cache = {}
    
    def check_model_available(self) -> bool:
        """Check if nomic-embed-text model is available."""
        try:
            # Try to embed a short test string
            response = self._embed_text("test")
            return response is not None
        except Exception:
            return False
    
    def _embed_text(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text from Ollama."""
        payload = {
            "model": self.model,
            "input": text,
        }
        
        request = urllib.request.Request(
            self.embed_endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                # Ollama embed endpoint returns {"embeddings": [[...]]}
                embeddings = resp_data.get("embeddings", [])
                return embeddings[0] if embeddings else None
        except Exception as e:
            raise RuntimeError(f"Embedding error: {e}")
    
    def embed(self, text: str, cache: bool = True) -> Optional[list[float]]:
        """
        Get embedding for text, with optional caching.
        
        Args:
            text: Text to embed
            cache: Whether to cache the embedding
            
        Returns:
            Embedding vector or None if error
        """
        if cache and text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            embedding = self._embed_text(text)
            if cache and embedding:
                self.embedding_cache[text] = embedding
            return embedding
        except Exception:
            return None
    
    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_best_topic(
        self, 
        problem: str, 
        topic_descriptions: dict[str, str],
        threshold: float = 0.5
    ) -> Optional[tuple[str, float]]:
        """
        Find the best matching topic for a problem using semantic similarity.
        
        Args:
            problem: User's math problem
            topic_descriptions: Dict mapping topic name to description
            threshold: Minimum similarity score (0-1)
            
        Returns:
            Tuple of (topic_name, similarity_score) or None if no match above threshold
        """
        problem_embedding = self.embed(problem)
        if problem_embedding is None:
            return None
        
        best_topic = None
        best_score = threshold
        
        for topic, description in topic_descriptions.items():
            topic_embedding = self.embed(description)
            if topic_embedding is None:
                continue
            
            similarity = self.cosine_similarity(problem_embedding, topic_embedding)
            
            if similarity > best_score:
                best_score = similarity
                best_topic = topic
        
        return (best_topic, best_score) if best_topic else None


# Pre-defined topic descriptions for semantic matching
TOPIC_DESCRIPTIONS = {
    "algebra": "Solving equations, factoring polynomials, expanding expressions, simplifying algebraic terms, finding roots",
    "vector": "Vectors, dot product, cross product, vector operations, magnitude, direction, unit vectors",
    "circle": "Circles, radius, diameter, tangent lines, chord, center, circumference, area",
    "straight-line": "Lines, slope, intercepts, linear equations, parallel lines, perpendicular lines, distance",
    "conics": "Conic sections, parabola, ellipse, hyperbola, eccentricity, foci, directrix, asymptotes",
    "matrix": "Matrices, determinant, inverse, eigenvalues, eigenvectors, matrix operations, rank, trace",
    "trigonometry": "Trigonometric functions, sin, cos, tan, angles, identities, inverse trig, wave functions",
    "inverse-trigonometry": "Inverse trigonometric functions, arcsin, arccos, arctan, domain and range",
    "calculus": "Derivatives, integrals, limits, series, differential equations, continuity, optimization",
    "combination": "Permutations, combinations, factorial, nCr, nPr, arrangements, selections, counting",
    "geometry": "Geometric shapes, areas, perimeters, volumes, spatial relationships, triangles, polygons",
}

# Topic-specific prompt enhancements
TOPIC_PROMPT_ENHANCEMENTS = {
    "algebra": "\nUse algebra-specific functions: solve_equation, polynomial_roots, solve_system, solve_inequality.",
    "vector": "\nUse vector-specific functions: dot product (dot), cross product (cross), normalize vectors.",
    "circle": "\nUse circle-specific functions: Circle class, distance calculations, radius, tangent conditions.",
    "straight-line": "\nUse line-specific functions: Line class, slope, intercepts, distance from point to line.",
    "conics": "\nUse conic-specific functions or solve conic equations directly. Identify parabola/ellipse/hyperbola.",
    "matrix": "\nUse matrix operations: Matrix class, det() for determinant, inv() for inverse, eigenvals().",
    "trigonometry": "\nUse trig functions: sin, cos, tan and their combinations. Apply trig identities where needed.",
    "inverse-trigonometry": "\nUse inverse trig: asin, acos, atan. Handle domain restrictions carefully.",
    "calculus": "\nUse calculus functions: diff() for derivative, integrate() for integral, limit() for limits.",
    "combination": "\nUse combinatorial functions: factorial(), binomial(), nC, nP. Count arrangements carefully.",
}


def get_embedding_engine(base_url: str = "http://localhost:11434") -> Optional[EmbeddingEngine]:
    """
    Initialize embedding engine if nomic-embed-text is available.
    Returns None if model is not available.
    """
    engine = EmbeddingEngine(base_url)
    if engine.check_model_available():
        return engine
    return None


def detect_topic_by_embedding(
    problem: str,
    embedding_engine: Optional[EmbeddingEngine] = None,
    threshold: float = 0.55
) -> Optional[tuple[str, float]]:
    """
    Detect topic using semantic embeddings.
    
    Args:
        problem: User's math problem
        embedding_engine: EmbeddingEngine instance (will be created if None)
        threshold: Minimum similarity score
        
    Returns:
        Tuple of (topic_name, similarity_score) or None
    """
    if embedding_engine is None:
        embedding_engine = get_embedding_engine()
        if embedding_engine is None:
            return None
    
    return embedding_engine.find_best_topic(problem, TOPIC_DESCRIPTIONS, threshold)


def get_topic_prompt_enhancement(topic: str) -> str:
    """
    Get topic-specific prompt enhancement for better LLM guidance.
    
    Args:
        topic: The detected or specified topic
        
    Returns:
        Enhancement text to append to main prompt
    """
    return TOPIC_PROMPT_ENHANCEMENTS.get(topic, "")
