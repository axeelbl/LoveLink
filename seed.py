from database import run_query

def seed_data():
    query = """
    MERGE (alice:Person {name: "Alice", age: 30, gender: "F", interests: ["cine", "viatges"]})
    MERGE (bob:Person {name: "Bob", age: 32, gender: "M", interests: ["esport", "música"]})
    MERGE (carol:Person {name: "Carol", age: 28, gender: "F", interests: ["lectura", "art"]})
    MERGE (dave:Person {name: "Dave", age: 35, gender: "M", interests: ["viatges", "tecnologia"]})

    MERGE (alice)-[:FRIEND]->(bob)
    MERGE (bob)-[:FRIEND]->(carol)
    MERGE (carol)-[:DATED]->(dave)
    MERGE (alice)-[:INTERACTED_WITH {type: "like", timestamp: datetime()}]->(carol)
    """
    run_query(query)
    print("Dades inicials creades correctament.")

if __name__ == "__main__":
    seed_data()
