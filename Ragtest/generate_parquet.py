from neo4j import GraphDatabase
import pandas as pd
import tiktoken
import os


#NEO4J_URI = ""  
#NEO4J_USER = ""                                  
#NEO4J_PASSWORD = ""         

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


PROJECT_ROOT = r"C:\Users\35542\Desktop\Vscode\NewGraphRAG\Ragtest" 
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "byog")
os.makedirs(OUTPUT_DIR, exist_ok=True)

token_encoder = tiktoken.get_encoding("cl100k_base")


def export_entities(session):
    ENTITY_LABELS = ["PROCESS", "STAGE", "EQUIPMENT", "TOOL", "MATERIAL"]

    result = session.run(
     
        labels=ENTITY_LABELS,
    )

    rows = []
    for idx, rec in enumerate(result, start=1):
        neo4j_id = rec["neo4j_id"]
        labels = rec["labels"]
        name = rec["name"]
        desc = rec["description"]
        tu_ids = rec["tu_ids"]

        ent_type = labels[0] if labels else "UNKNOWN"

        rows.append(
            {
                "id": f"NODE_{neo4j_id}",
                "human_readable_id": idx,
                "title": name,
                "type": ent_type,
                "description": desc,
                "text_unit_ids": tu_ids,
                "frequency": len(tu_ids),
                "degree": 0,  
                "x": 0.0,
                "y": 0.0,
            }
        )

    df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "entities.parquet")
    df.to_parquet(out_path, index=False)
    print(f"entities.parquet 已生成: {out_path}")
    return df


def export_relationships(session, entities_df):
    ENTITY_ID_MAP = {
        int(row["id"].split("_")[1]): row["id"]
        for _, row in entities_df.iterrows()
    }

    REL_TYPES = [
        "HAS_STAGE",
        "HAS_EQUIPMENT",
        "HAS_TOOL",
        "HAS_MATERIAL",
        "PRECEDES",
    ]

    result = session.run(
        """
        MATCH (a)-[r]->(b)
        WHERE type(r) IN $rel_types
        OPTIONAL MATCH (t:TEXT_UNIT)
          -[:ABOUT_PROCESS|:ABOUT_STAGE|:HAS_EQUIPMENT|:HAS_TOOL|:HAS_MATERIAL]->(a)
        OPTIONAL MATCH (t2:TEXT_UNIT)
          -[:ABOUT_PROCESS|:ABOUT_STAGE|:HAS_EQUIPMENT|:HAS_TOOL|:HAS_MATERIAL]->(b)
        WITH a, b, r, collect(DISTINCT coalesce(t.id, t2.id)) AS tu_ids
        RETURN id(r) AS rid, type(r) AS rtype,
               id(a) AS src, id(b) AS dst,
               tu_ids
        """,
        rel_types=REL_TYPES,
    )

    rows = []
    for idx, rec in enumerate(result, start=1):
        src_neo = rec["src"]
        dst_neo = rec["dst"]
        src_id = ENTITY_ID_MAP.get(src_neo)
        dst_id = ENTITY_ID_MAP.get(dst_neo)
        if not src_id or not dst_id:
            continue

        rows.append(
            {
                "id": f"REL_{rec['rid']}",
                "human_readable_id": idx,
                "source": src_id,
                "target": dst_id,
                "description": f"{src_id} {rec['rtype']} {dst_id}",
                "weight": 1.0,
                "combined_degree": 0,
                "text_unit_ids": rec["tu_ids"],
            }
        )

    df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "relationships.parquet")
    df.to_parquet(out_path, index=False)
    print(f"relationships.parquet 已生成: {out_path}")
    return df


def export_text_units(session, entities_df):
   
    ENTITY_ID_MAP = {
        int(row["id"].split("_")[1]): row["id"]
        for _, row in entities_df.iterrows()
    }

    result = session.run(
        """
        MATCH (t:TEXT_UNIT)
        OPTIONAL MATCH (t)-[:ABOUT_PROCESS]->(p:PROCESS)
        OPTIONAL MATCH (t)-[:ABOUT_STAGE]->(s:STAGE)
        OPTIONAL MATCH (t)-[:HAS_EQUIPMENT]->(e:EQUIPMENT)
        OPTIONAL MATCH (t)-[:HAS_TOOL]->(tool:TOOL)
        OPTIONAL MATCH (t)-[:HAS_MATERIAL]->(m:MATERIAL)
        WITH t,
             collect(DISTINCT id(p)) +
             collect(DISTINCT id(s)) +
             collect(DISTINCT id(e)) +
             collect(DISTINCT id(tool)) +
             collect(DISTINCT id(m)) AS ent_ids
        RETURN t.id AS tid,
               t.content AS text,
               ent_ids
        """
    )

    rows = []
    for idx, rec in enumerate(result, start=1):
        text = rec["text"]
        ent_neo_ids = rec["ent_ids"]
        ent_ids = [
            ENTITY_ID_MAP[eid] for eid in ent_neo_ids if eid in ENTITY_ID_MAP
        ]
        n_tokens = len(token_encoder.encode(text))

        rows.append(
            {
                "id": rec["tid"],
                "human_readable_id": idx,
                "text": text,
                "n_tokens": n_tokens,
                "document_ids": ["汽车自动化_知识文档"],
                "entity_ids": ent_ids,
                "relationship_ids": [], 
                "covariate_ids": [],
            }
        )

    df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "text_units.parquet")
    df.to_parquet(out_path, index=False)
    print(f"text_units.parquet 已生成: {out_path}")
    return df

def main():
    with driver.session() as session:
        entities_df = export_entities(session)
        relationships_df = export_relationships(session, entities_df)
        text_units_df = export_text_units(session, entities_df)

    print("Neo4j -> parquet 导出完成！")


if __name__ == "__main__":
    main()
    driver.close()
