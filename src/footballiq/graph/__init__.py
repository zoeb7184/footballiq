"""Graph analytics (scope R2): club <-> nation talent-flow, batch-computed.

Analytics products, not ML features (graph-design §5). A NetworkX batch job
reads the warehouse and writes deterministic metric tables to gold; the API
and BI only read them (prediction-as-data, extended to graph metrics).
"""
