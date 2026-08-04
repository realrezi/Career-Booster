import os
import sys

# Ensure project root is on sys.path so tailor_service and pdf_generator can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
