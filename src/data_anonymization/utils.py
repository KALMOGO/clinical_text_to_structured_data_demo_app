import logging

def setup_logging(level=logging.INFO):
    """Configure logging for the anonymization module"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )