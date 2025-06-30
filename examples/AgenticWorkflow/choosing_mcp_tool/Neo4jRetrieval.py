class Neo4jRetrieval:
    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, params={}):
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                return [record for record in result]
        except Exception as e:
            print(f"Error running query: {query}")
            print(f"Exception: {e}")
            return f"Failed to run query: {query}. Exception: {e}"

    def search(self, search_term, label="UpdatedChunk") -> list[dict]:
        query = (
            f"MATCH (n:{label}) WHERE toLower(n.text) CONTAINS '{search_term}' RETURN n"
        )
        return self.run_query(query)

    def search_many(self, terms: list[str], label="UpdatedChunk") -> list[dict]:
        query = f"""
        UNWIND $terms AS term
        MATCH (n:{label})
        WHERE toLower(n.text) CONTAINS term
        RETURN DISTINCT {{text: n.text, actId: n.ActId, elementId: elementId(n), regId: n.RegId, sectionName: n.sectionName, sectionNumber: n.sectionId }} AS n
        """
        with self.driver.session() as session:
            result = session.run(query, terms=terms)
            return [record["n"] for record in result]


# Intended for local development and testing
# NEO4J_URI = "bolt://" + "localhost:7687"  # os.getenv("NEO4J_HOST") + ":7687"
# NEO4J_USERNAME = "admin"  # os.getenv("NEO4J_USER")
# NEO4J_PASSWORD = "admin"  # os.getenv("NEO4J_PASSWORD")

# neo4j = Neo4jRetrieval(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
# # Example usage
# results = neo4j.search_many(["cat", "dog"])
# print(len(results))
# # Close the connection when done
# neo4j.close()
