import csv

with open("./data/reference_csv/relationships_0000.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Assuming the CSV has columns 'source' and 'target' for the nodes
        source_node = row["source"]
        target_node = row["target"]

        # Create a reference edge between the nodes
        # create_reference_edge(source_node, target_node)
"""
LOAD CSV WITH HEADERS FROM 'file:///yourfile.csv' AS row

MATCH (a:Item)
WHERE (a.meta1 + '-' + a.meta2) = row.source_key

MATCH (b:Item)
WHERE (b.meta1 + '-' + b.meta2) = row.target_key

MERGE (a)-[r:RELATED_TO]->(b)
ON CREATE SET r.weight = 1
ON MATCH SET r.weight = r.weight + 1

"""
