"""Infrastructure layer — adapters for the outside world.

Implements application ports: SQL repositories, warehouse access,
ML model stores, LLM clients, graph engines, blob storage.
The only layer allowed to import third-party I/O libraries.
"""
