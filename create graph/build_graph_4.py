from neo4j import GraphDatabase

# ========= 1. 配置 Neo4j Aura 连接 =========
# 直接用你前面脚本里的 URI / 用户 / 密码
NEO4J_URI = "neo4j+s://36f08b4f.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Z-kmRY5XTupSahevPpRzQZqpRfFcw0ApigFBfDVFyQo"  

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ========= 2. 四大工艺的顺序 =========
PROCESS_ORDER = [
    "冲压工艺",
    "焊接工艺",
    "涂装工艺",
    "总装工艺",
]


def set_process_order(tx, process_order):
    """
    为四大工艺设置：
    - PROCESS.seq_index
    - (PROCESS)-[:PRECEDES]->(下一个 PROCESS)
    """

    # 可选：先删除已有的 PROCESS 之间的 PRECEDES，避免重复
    tx.run(
        """
        MATCH (p1:PROCESS)-[r:PRECEDES]->(p2:PROCESS)
        DELETE r
        """
    )

    for idx, pname in enumerate(process_order):
        # 设置工艺顺序索引
        tx.run(
            """
            MATCH (p:PROCESS {name:$name})
            SET p.seq_index = $idx
            """,
            {"name": pname, "idx": idx},
        )

        # 建立工艺之间的 PRECEDES 关系
        if idx < len(process_order) - 1:
            next_name = process_order[idx + 1]
            tx.run(
                """
                MATCH (p1:PROCESS {name:$name})
                MATCH (p2:PROCESS {name:$next_name})
                MERGE (p1)-[:PRECEDES]->(p2)
                """,
                {"name": pname, "next_name": next_name},
            )


def main():
    with driver.session() as session:
        def _write(tx):
            set_process_order(tx, PROCESS_ORDER)

        session.execute_write(_write)

    print("四大工艺的 seq_index 和 PRECEDES 关系已设置完成！")


if __name__ == "__main__":
    main()
    driver.close()

