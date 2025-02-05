import re
from typing import Tuple, List, Dict

class CypherSecurityValidator:
    def __init__(self):
        # Forbidden operations that could modify or delete data
        self.forbidden_operations = {
            'DELETE': r'\bDELETE\b',
            'REMOVE': r'\bREMOVE\b',
            'DROP': r'\bDROP\b',
            'CREATE': r'\bCREATE\b',
            'SET': r'\bSET\b',
            'MERGE': r'\bMERGE\b',
            'DETACH': r'\bDETACH\b',
            ';': r';',  # Prevent multiple statements
            'CALL': r'\bCALL\b',  # Prevent procedure calls
            'FOREACH': r'\bFOREACH\b',  # Prevent loops that might be used for updates
            'LOAD CSV': r'\bLOAD\s+CSV\b',  # Prevent data import
            'WRITE': r'\bWRITE\b',
        }

        # Required operations for valid read-only queries
        self.required_patterns = {
            'MATCH_START': r'^(?i)\s*(MATCH|WITH)\b',
            'RETURN_END': r'\bRETURN\b.*$',
        }

        # Allowed operations for read-only queries
        self.allowed_operations = {
            'MATCH': r'\bMATCH\b',
            'WHERE': r'\bWHERE\b',
            'RETURN': r'\bRETURN\b',
            'WITH': r'\bWITH\b',
            'ORDER BY': r'\bORDER\s+BY\b',
            'LIMIT': r'\bLIMIT\b',
            'SKIP': r'\bSKIP\b',
            'UNWIND': r'\bUNWIND\b',
        }

        # Patterns that must be used correctly
        self.required_patterns_usage = {
            'NULL_CHECK': r'\bIS\s+(NOT\s+)?NULL\b',
            'EXISTS_CHECK': r'\bEXISTS\b'
        }

    def validate_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validates a Cypher query against security rules.
        
        Args:
            query (str): The Cypher query to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        # Remove comments and normalize whitespace
        cleaned_query = self._clean_query(query)
        
        # Check for forbidden operations
        for op_name, pattern in self.forbidden_operations.items():
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                errors.append(f"Forbidden operation detected: {op_name}")

        # Verify query starts with MATCH or WITH
        if not re.search(self.required_patterns['MATCH_START'], cleaned_query):
            errors.append("Query must start with MATCH or WITH")

        # Verify query ends with RETURN
        if not re.search(self.required_patterns['RETURN_END'], cleaned_query):
            errors.append("Query must end with RETURN clause")

        # Check for incorrect EXISTS usage
        if re.search(self.required_patterns_usage['EXISTS_CHECK'], cleaned_query):
            errors.append("Use 'IS NULL' or 'IS NOT NULL' instead of EXISTS")

        # Check for proper NULL checks
        if 'WHERE' in cleaned_query and not re.search(self.required_patterns_usage['NULL_CHECK'], cleaned_query):
            if any(prop in cleaned_query for prop in ['RegId', 'ActId']):
                errors.append("Property checks must use 'IS NULL' or 'IS NOT NULL'")

        # Check for LIMIT in graph traversal queries
        if '-[' in cleaned_query and 'LIMIT' not in cleaned_query:
            errors.append("Graph traversal queries must include LIMIT clause")

        return len(errors) == 0, errors

    def _clean_query(self, query: str) -> str:
        """
        Removes comments and normalizes whitespace in query.
        
        Args:
            query (str): Original query
            
        Returns:
            str: Cleaned query
        """
        # Remove single-line comments
        query = re.sub(r'//.*$', '', query, flags=re.MULTILINE)
        
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query

    def suggest_fixes(self, query: str) -> Dict[str, str]:
        """
        Suggests fixes for common query issues.
        
        Args:
            query (str): The problematic query
            
        Returns:
            Dict[str, str]: Dictionary of issues and suggested fixes
        """
        suggestions = {}
        
        # Replace EXISTS with IS NOT NULL
        if re.search(r'\bEXISTS\(([^)]+)\)', query):
            fixed_query = re.sub(
                r'\bEXISTS\(([^)]+)\)', 
                r'\1 IS NOT NULL', 
                query
            )
            suggestions['EXISTS usage'] = fixed_query

        # Add LIMIT to graph queries
        if '-[' in query and 'LIMIT' not in query:
            suggestions['Missing LIMIT'] = f"{query} LIMIT 100"

        # Add ORDER BY for predictable results
        if 'ORDER BY' not in query and 'RETURN' in query:
            return_clause = re.search(r'RETURN\s+(.+?)(?:\s+LIMIT|$)', query)
            if return_clause:
                first_return = return_clause.group(1).split(',')[0].strip()
                suggestions['Missing ORDER BY'] = query.replace(
                    'RETURN', 
                    f'RETURN /* Consider adding: ORDER BY {first_return} */'
                )

        return suggestions

# Example usage
def validate_cypher_query(query: str) -> Tuple[bool, List[str], Dict[str, str]]:
    """
    Wrapper function to validate a Cypher query and get suggestions.
    
    Args:
        query (str): The Cypher query to validate
        
    Returns:
        Tuple[bool, List[str], Dict[str, str]]: (is_valid, errors, suggestions)
    """
    validator = CypherSecurityValidator()
    is_valid, errors = validator.validate_query(query)
    suggestions = validator.suggest_fixes(query) if not is_valid else {}
    return is_valid, errors, suggestions

# Example usage:
if __name__ == "__main__":
    test_queries = [
        # Valid query
        """
        MATCH (n:UpdatedChunk) 
        WHERE n.RegId IS NOT NULL 
        RETURN COUNT(n) AS regulation_count
        """,
        
        # Invalid query - uses EXISTS
        """
        MATCH (n:UpdatedChunk) 
        WHERE EXISTS(n.RegId) 
        RETURN n
        """,
        
        # Invalid query - forbidden operation
        """
        MATCH (n:UpdatedChunk) 
        DELETE n 
        RETURN COUNT(n)
        """,
        
        # Invalid query - missing LIMIT in graph traversal
        """
        MATCH (n:UpdatedChunk)-[r*1..2]-(m:UpdatedChunk) 
        WHERE n.RegId IS NOT NULL 
        RETURN n, r, m
        """
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTesting Query {i}:")
        print("Query:", query.strip())
        is_valid, errors, suggestions = validate_cypher_query(query)
        print("Valid:", is_valid)
        if not is_valid:
            print("Errors:", errors)
            if suggestions:
                print("Suggestions:", suggestions)
