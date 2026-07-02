"""ML layer — features, training, scoring (batch only, prediction-as-data).

Implements docs/ml/ml-system-design.md. Nothing here runs at API request
time: models train and score in batch jobs; the API reads their outputs
from gold tables.
"""
