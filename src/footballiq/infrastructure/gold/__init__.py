"""Gold-layer adapters — the only tables the API's world contains.

Access is grant-enforced in the database (backend design §3): the runtime
role can SELECT gold and nothing else.
"""
